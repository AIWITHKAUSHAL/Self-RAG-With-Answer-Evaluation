import pytest

from app.models import Document, DocumentGrade, Evaluation, QueryRequest
from app.pipeline import ABSTENTION, run_pipeline
from app.providers import DemoProvider
from app.retrieval import Retriever


def test_first_pass_is_supported_and_cited():
    """Verify the refund example succeeds once with supporting text and a citation."""
    result = run_pipeline(QueryRequest(question="What is the refund policy?"))
    assert result["status"] == "accepted"
    assert result["attempt_count"] == 1
    assert result["retries_used"] == 0
    assert "7 calendar days" in result["answer"]
    assert "[refund-policy]" in result["answer"]
    assert result["attempts"][0]["evaluation"]["grounding"] == 1


def test_unsupported_draft_causes_full_correction_cycle():
    """Verify an injected false claim triggers every correction stage before acceptance."""
    question = "Does Northstar Academy guarantee a job or salary?"
    result = run_pipeline(QueryRequest(question=question, correction_demo=True))
    first, second = result["attempts"]
    assert result["status"] == "accepted"
    assert first["injected_draft"] and not first["accepted"]
    assert first["evaluation"]["grounding"] == 0
    assert first["rewrite"] == second["query"]
    assert second["accepted"]
    assert "does not guarantee" in result["answer"]
    assert "50 lakh" not in result["answer"]
    assert [event["stage"] for event in result["events"]] == [
        "question", "retrieve", "grade", "generate", "evaluate", "rewrite",
        "retrieve", "grade", "generate", "evaluate", "end",
    ]


@pytest.mark.parametrize("retry_limit", [0, 1, 2, 4])
def test_unknown_question_stops_at_budget_and_abstains(retry_limit):
    """Check that missing evidence exhausts each tested budget without generating a draft."""
    result = run_pipeline(QueryRequest(question="What is the lunar observatory telescope diameter?", max_retries=retry_limit))
    assert result["status"] == "abstained"
    assert result["attempt_count"] == retry_limit + 1
    assert result["retries_used"] == retry_limit
    assert result["answer"] == ABSTENTION
    assert result["sources"] == []
    assert all(attempt["draft"] is None for attempt in result["attempts"])


def test_zero_retries_does_not_return_bad_draft():
    """Ensure a failed first draft is withheld when no additional attempts are allowed."""
    result = run_pipeline(QueryRequest(question="Is employment guaranteed?", correction_demo=True, max_retries=0))
    assert result["status"] == "abstained"
    assert result["attempt_count"] == 1
    assert "50 lakh" not in result["answer"]


class ControlledProvider(DemoProvider):
    """Configurable test double that records pipeline inputs and fixes judge outputs."""

    def __init__(self, relevance=1.0, grounding=1.0, supported=True, claims=None, citation="refund-policy"):
        """Set evaluation and citation outcomes and initialize call-observation lists."""
        self.relevance, self.grounding, self.supported = relevance, grounding, supported
        self.claims, self.citation = claims or [], citation
        self.questions, self.feedback_received, self.contexts = [], [], []

    def grade(self, question, documents):
        """Record the question and retain only the refund policy for controlled tests."""
        self.questions.append(question)
        return [DocumentGrade(document_id=doc.id, relevance=1.0 if doc.id == "refund-policy" else 0.0, reason="Controlled test grade") for doc in documents]

    def generate(self, question, documents, feedback):
        """Record generation inputs and return a draft with the configured citation."""
        self.questions.append(question)
        self.feedback_received.append(feedback)
        self.contexts.append(documents)
        return "A draft with evidence" + (f" [{self.citation}]" if self.citation else "")

    def evaluate(self, question, documents, answer):
        """Record the original question and return the configured judge decision."""
        self.questions.append(question)
        return Evaluation(answer_relevance=self.relevance, grounding=self.grounding, supported=self.supported, unsupported_claims=self.claims, feedback="Find the refund eligibility window.")

    def rewrite(self, question, query, feedback):
        """Record the original question and return a distinct, fixed refund search."""
        self.questions.append(question)
        return "refund eligibility purchase window"


@pytest.mark.parametrize("kwargs", [
    {"relevance": 0.74}, {"grounding": 0.84}, {"supported": False},
    {"claims": ["invented claim"]}, {"citation": "unknown-document"}, {"citation": ""},
])
def test_every_acceptance_gate_is_required(kwargs):
    """Verify each independently failing acceptance gate causes bounded abstention."""
    result = run_pipeline(QueryRequest(question="What is the refund policy?", max_retries=1), provider=ControlledProvider(**kwargs))
    assert result["status"] == "abstained"
    assert result["attempt_count"] == 2


def test_original_question_survives_rewrite_and_feedback_reaches_generator():
    """Check intent preservation, feedback propagation, and retained generation context."""
    provider = ControlledProvider(grounding=0.1)
    question = "What is the refund policy?"
    result = run_pipeline(QueryRequest(question=question, max_retries=1), provider=provider)
    assert all(value == question for value in provider.questions)
    assert result["attempts"][1]["query"] != question
    assert provider.feedback_received == ["", "Find the refund eligibility window."]
    assert all(doc.id == "refund-policy" for docs in provider.contexts for doc in docs)


def test_low_relevance_documents_are_filtered_before_generation():
    """Ensure a retrieved but irrelevant passage never reaches the generator."""
    docs = [Document(id="refund-policy", title="Refund", text="Refund within 7 days."),
            Document(id="irrelevant", title="Refund system logs", text="Refund service runs Python.")]
    provider = ControlledProvider()
    result = run_pipeline(QueryRequest(question="Refund policy?"), provider, Retriever(docs))
    assert len(result["attempts"][0]["retrieved"]) == 2
    assert result["attempts"][0]["kept_ids"] == ["refund-policy"]
    assert [doc.id for doc in provider.contexts[0]] == ["refund-policy"]


def test_retrieval_ranks_specific_policy_and_handles_empty_corpus():
    """Check policy ranking and empty results for missing corpora or unmatched queries."""
    assert Retriever().search("refund cancellation", 3)[0]["document"].id == "refund-policy"
    assert Retriever([]).search("refund", 3) == []
    assert Retriever().search("xyznonexistent", 3) == []
