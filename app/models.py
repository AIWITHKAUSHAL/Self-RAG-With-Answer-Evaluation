from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Document(StrictModel):
    id: str
    title: str
    text: str


class DocumentGrade(StrictModel):
    document_id: str
    relevance: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1)


class GradeBatch(StrictModel):
    grades: list[DocumentGrade]


class Evaluation(StrictModel):
    answer_relevance: float = Field(ge=0, le=1)
    grounding: float = Field(ge=0, le=1)
    supported: bool
    feedback: str = Field(min_length=1)
    unsupported_claims: list[str]


class Rewrite(StrictModel):
    query: str = Field(min_length=3, max_length=1000)


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    mode: Literal["demo", "live"] = "demo"
    max_retries: int = Field(default=2, ge=0, le=4)
    top_k: int = Field(default=3, ge=1, le=6)
    correction_demo: bool = False

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Please enter at least three non-whitespace characters.")
        return value
