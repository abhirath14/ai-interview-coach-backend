import json
from typing import List, Tuple

from .config import MODEL_NAME
from .groq_client import create_completion
from .schemas import Message, Report

REPORT_SYSTEM_PROMPT = """You are grading a completed mock technical interview on the \
topic "{topic}" at {difficulty} difficulty, based only on the transcript provided.

Base every point strictly on what the candidate actually said in the transcript. Do \
not invent claims they didn't make.

Return ONLY a single JSON object, no other text, of the exact form:
{{
  "score": <integer 0-100>,
  "strengths": ["<specific thing the candidate did well, referencing what they said>", ...],
  "weaknesses": ["<specific thing the candidate got wrong or missed, referencing what they said>", ...],
  "topics_to_revise": ["<specific sub-topic the candidate should revise>", ...],
  "verdict": "<2-4 sentence overall assessment of the candidate's performance>"
}}

Scoring guide:
- 85-100: excellent — deep, accurate, well-reasoned answers throughout.
- 70-84: good — solid understanding with minor gaps.
- 55-69: adequate — basic understanding but noticeable gaps.
- 0-54: weak — significant gaps or repeated incorrect answers.

Give 2-5 items each for strengths, weaknesses, and topics_to_revise where the \
transcript supports them. If there are genuinely no strengths or no weaknesses, \
return an empty list for that field rather than inventing one.
"""


REPORT_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "interview_report",
        "schema": {
            "type": "object",
            "properties": {
                "score": {"type": "integer"},
                "strengths": {"type": "array", "items": {"type": "string"}},
                "weaknesses": {"type": "array", "items": {"type": "string"}},
                "topics_to_revise": {"type": "array", "items": {"type": "string"}},
                "verdict": {"type": "string"},
            },
            "required": [
                "score",
                "strengths",
                "weaknesses",
                "topics_to_revise",
                "verdict",
            ],
            "additionalProperties": False,
        },
    },
}


def _format_transcript(history: List[Message]) -> str:
    lines = []
    for turn in history:
        speaker = "Interviewer" if turn.role == "interviewer" else "Candidate"
        lines.append(f"{speaker}: {turn.content}")
    return "\n".join(lines)


def _band_and_result(score: int) -> Tuple[str, str]:
    if score >= 85:
        band = "Excellent"
    elif score >= 70:
        band = "Good"
    elif score >= 55:
        band = "Adequate"
    else:
        band = "Weak"

    result = "Pass" if score >= 55 else "Fail"
    return band, result


def generate_report(topic: str, difficulty: str, history: List[Message]) -> Report:
    system_prompt = REPORT_SYSTEM_PROMPT.format(topic=topic, difficulty=difficulty)
    transcript = _format_transcript(history)

    completion = create_completion(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
        temperature=0.3,
        response_format=REPORT_SCHEMA,
    )

    raw = completion.choices[0].message.content
    data = json.loads(raw)

    score = max(0, min(100, int(data["score"])))
    band, result = _band_and_result(score)

    return Report(
        score=score,
        band=band,
        strengths=list(data.get("strengths", [])),
        weaknesses=list(data.get("weaknesses", [])),
        topics_to_revise=list(data.get("topics_to_revise", [])),
        verdict=str(data.get("verdict", "")).strip(),
        result=result,
    )
