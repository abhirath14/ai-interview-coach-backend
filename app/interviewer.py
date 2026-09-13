import json
from typing import List

from .config import MODEL_NAME
from .groq_client import create_completion
from .schemas import InterviewerReply, Message

DIFFICULTY_GUIDANCE = {
    "Easy": "Ask basic, definition- and recall-level questions. Test whether the "
    "candidate knows what things are and how they work at a foundational level.",
    "Medium": "Ask applied, scenario-based questions. Test whether the candidate "
    "can use the concept to solve a concrete problem, not just define it.",
    "Hard": "Ask about trade-offs, edge cases, and system-level thinking. Test "
    "whether the candidate can reason about design decisions and their "
    "consequences at scale.",
}

SYSTEM_PROMPT_TEMPLATE = """You are an experienced, professional technical interviewer \
conducting a live mock interview on the topic "{topic}" at {difficulty} difficulty.

{difficulty_guidance}

How to conduct the interview:
- Ask exactly ONE question at a time. Never ask multiple questions in one message.
- If the candidate's last answer was strong, briefly acknowledge it (one short \
line) and move on to a different aspect of the topic with a new question.
- If the candidate's last answer was partly right, ask exactly one probing \
follow-up question that targets the gap. Do not reveal what the gap is beyond \
what's needed to ask the follow-up, and do not give away the answer.
- If the candidate's last answer was wrong, note the gap in one short, neutral \
line and move on to a new question on a different aspect. Do not explain the \
correct answer.
- Never teach, never hint, never reveal correct answers, even indirectly.
- Stay professional, encouraging, and concise. This is an interview, not a lecture.
- Cover a reasonable spread of the topic before ending. Do not end after only \
one or two exchanges unless the candidate is clearly and repeatedly struggling.

When to end the interview (set "is_complete" to true):
- The candidate is clearly struggling across several consecutive questions — end \
early and kindly, with a brief closing remark. Do not pile on more questions once \
this is evident.
- The candidate is doing very well and the key areas of the topic have been \
reasonably covered — wrap up once that happens, with a brief closing remark.
- In either case, the closing message should feel like a natural end to an \
interview (e.g. thank them for their time), not abrupt.
- Otherwise, keep "is_complete" false and ask the next question.

Output format:
Respond with ONLY a single JSON object, no other text, of the exact form:
{{"message": "<what you say next to the candidate>", "is_complete": <true or false>}}
"""

KICKOFF_MESSAGE = (
    "[This is the start of the interview. There is no candidate answer yet. "
    "Ask your first question now.]"
)

REPLY_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "interviewer_reply",
        "schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "is_complete": {"type": "boolean"},
            },
            "required": ["message", "is_complete"],
            "additionalProperties": False,
        },
    },
}


def _build_messages(topic: str, difficulty: str, history: List[Message]) -> list:
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        topic=topic,
        difficulty=difficulty,
        difficulty_guidance=DIFFICULTY_GUIDANCE[difficulty],
    )
    messages = [{"role": "system", "content": system_prompt}]

    if not history:
        messages.append({"role": "user", "content": KICKOFF_MESSAGE})
    else:
        for turn in history:
            role = "assistant" if turn.role == "interviewer" else "user"
            messages.append({"role": role, "content": turn.content})

    return messages


def get_next_message(
    topic: str, difficulty: str, history: List[Message]
) -> InterviewerReply:
    messages = _build_messages(topic, difficulty, history)

    completion = create_completion(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.7,
        response_format=REPLY_SCHEMA,
    )

    raw = completion.choices[0].message.content
    data = json.loads(raw)

    return InterviewerReply(
        message=str(data["message"]).strip(),
        is_complete=bool(data.get("is_complete", False)),
    )
