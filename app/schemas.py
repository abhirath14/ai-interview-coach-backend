from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

Difficulty = Literal["Easy", "Medium", "Hard"]

MAX_TOPIC_LENGTH = 200
MAX_ANSWER_LENGTH = 4000
MAX_HISTORY_LENGTH = 200


def _non_empty_stripped(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("This field cannot be empty or whitespace only.")
    return value


class Message(BaseModel):
    role: Literal["interviewer", "candidate"]
    content: str = Field(..., min_length=1, max_length=MAX_ANSWER_LENGTH)


class InterviewerReply(BaseModel):
    message: str
    is_complete: bool


class Report(BaseModel):
    score: int
    band: Literal["Excellent", "Good", "Adequate", "Weak"]
    strengths: List[str]
    weaknesses: List[str]
    topics_to_revise: List[str]
    verdict: str
    result: Literal["Pass", "Fail"]


class StartRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH)
    difficulty: Difficulty

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        return _non_empty_stripped(v)


class AnswerRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH)
    difficulty: Difficulty
    history: List[Message] = Field(default_factory=list, max_length=MAX_HISTORY_LENGTH)
    answer: str = Field(..., min_length=1, max_length=MAX_ANSWER_LENGTH)

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        return _non_empty_stripped(v)

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, v: str) -> str:
        return _non_empty_stripped(v)


class ReportRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=MAX_TOPIC_LENGTH)
    difficulty: Difficulty
    history: List[Message] = Field(default_factory=list, max_length=MAX_HISTORY_LENGTH)

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        return _non_empty_stripped(v)
