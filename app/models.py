from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Base schema that rejects extra fields and implicit type coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class Document(StrictModel):
    """A knowledge-base passage with a stable citation ID, title, and text."""

    id: str
    title: str
    text: str


class DocumentGrade(StrictModel):
    """Relevance score and justification for a single retrieved document."""

    document_id: str
    relevance: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1)


class GradeBatch(StrictModel):
    """Structured response containing the retrieved documents' relevance grades."""

    grades: list[DocumentGrade]


class Evaluation(StrictModel):
    """Answer relevance, grounding, support judgment, and correction feedback."""

    answer_relevance: float = Field(ge=0, le=1)
    grounding: float = Field(ge=0, le=1)
    supported: bool
    feedback: str = Field(min_length=1)
    unsupported_claims: list[str]


class Rewrite(StrictModel):
    """Validated replacement search query used to retrieve missing evidence."""

    query: str = Field(min_length=3, max_length=1000)


class QueryRequest(BaseModel):
    """User question and run settings, including a budget of additional retries."""

    question: str = Field(min_length=3, max_length=1000)
    mode: Literal["demo", "live"] = "demo"
    max_retries: int = Field(default=2, ge=0, le=4)
    top_k: int = Field(default=3, ge=1, le=6)
    correction_demo: bool = False

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        """Trim surrounding whitespace and reject questions shorter than three characters."""
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Please enter at least three non-whitespace characters.")
        return value
