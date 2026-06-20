from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class CreateSessionRequest(BaseModel):
    concept: str = Field(min_length=2, max_length=500)


class InitialExplanationRequest(BaseModel):
    explanation: str = Field(min_length=10, max_length=5000)


class FollowupAnswersRequest(BaseModel):
    answers: list[str]

    @model_validator(mode="after")
    def validate_answers(self) -> "FollowupAnswersRequest":
        if len(self.answers) != 2:
            raise ValueError("Exactly two follow-up answers are required")
        cleaned = [answer.strip() for answer in self.answers]
        if any(not answer for answer in cleaned):
            raise ValueError("Follow-up answers cannot be empty")
        self.answers = cleaned
        return self


class SessionCreateResponse(BaseModel):
    session_id: str
    concept: str
    status: str
    next_step: str


class SessionSummary(BaseModel):
    id: str
    concept: str
    understanding_score: int | None = None
    status: str
    created_at: datetime


class ResponseOut(BaseModel):
    id: str
    stage: str
    question: str
    answer: str | None = None
    created_at: datetime


class AnalysisOut(BaseModel):
    id: str
    knowledge_gap: str
    strengths: str
    weaknesses: str
    final_feedback: str
    created_at: datetime


class InitialAnalysisOut(BaseModel):
    knowledge_gap: str
    strengths: str
    weaknesses: str
    followup_questions: list[str]


class FollowupResponseOut(BaseModel):
    session_id: str
    analysis: AnalysisOut
    understanding_score: int
    status: str


class SessionDetailOut(BaseModel):
    session: SessionSummary
    responses: list[ResponseOut]
    analysis: AnalysisOut | None = None
