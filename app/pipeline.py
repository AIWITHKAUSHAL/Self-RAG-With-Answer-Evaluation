"""Explicit Self-RAG state machine. Only an accepted draft becomes the final answer."""
import re
from time import perf_counter

from app.models import QueryRequest
from app.providers import DemoProvider, EuriProvider, Provider
from app.retrieval import Retriever

DOCUMENT_THRESHOLD = 0.55
ANSWER_THRESHOLD = 0.75
GROUNDING_THRESHOLD = 0.85
UNSUPPORTED_DEMO_DRAFT = "Northstar Academy guarantees every learner a job paying ₹50 lakh per year. [career-support]"
ABSTENTION = "I couldn't produce a sufficiently supported answer within the retry limit. Please narrow your question or add relevant documents to the knowledge base."


def run_pipeline(request: QueryRequest, provider: Provider | None = None, retriever: Retriever | None = None) -> dict:
    started = perf_counter()
    provider = provider if provider is not None else EuriProvider() if request.mode == "live" else DemoProvider()
    retriever = retriever if retriever is not None else Retriever()
    query, feedback = request.question, ""
    attempts, events = [], []

    def event(stage: str, attempt: int, message: str):
        events.append({"stage": stage, "attempt": attempt, "message": message, "elapsed_ms": round((perf_counter() - started) * 1000)})

    def finish(status: str, answer: str, sources: list) -> dict:
        event("end", len(attempts), "Supported answer accepted." if status == "accepted" else "Retry budget exhausted; abstained.")
        return {
            "status": status, "question": request.question, "answer": answer,
            "mode": request.mode, "model": provider.model if isinstance(provider, EuriProvider) else "offline-extractive-demo",
            "correction_demo": request.correction_demo, "attempt_count": len(attempts),
            "retries_used": max(0, len(attempts) - 1), "max_retries": request.max_retries,
            "thresholds": {"document_relevance": DOCUMENT_THRESHOLD, "answer_relevance": ANSWER_THRESHOLD, "grounding": GROUNDING_THRESHOLD},
            "attempts": attempts, "events": events, "sources": [doc.model_dump() for doc in sources],
            "duration_ms": round((perf_counter() - started) * 1000),
        }

    event("question", 0, request.question)
    # max_retries counts ADDITIONAL tries: 0 means exactly one attempt.
    for index in range(request.max_retries + 1):
        number = index + 1
        hits = retriever.search(query, request.top_k)
        docs = [hit["document"] for hit in hits]
        event("retrieve", number, f"Retrieved {len(docs)} documents for: {query}")
        grades = provider.grade(request.question, docs) if docs else []
        relevant_ids = {grade.document_id for grade in grades if grade.relevance >= DOCUMENT_THRESHOLD}
        kept = [doc for doc in docs if doc.id in relevant_ids]
        event("grade", number, f"Kept {len(kept)} of {len(docs)} documents at relevance ≥ {DOCUMENT_THRESHOLD}.")
        attempt = {"number": number, "query": query, "retrieved": [{**hit["document"].model_dump(), "retrieval_score": hit["score"]} for hit in hits],
                   "grades": [grade.model_dump() for grade in grades], "kept_ids": [doc.id for doc in kept],
                   "draft": None, "evaluation": None, "accepted": False, "injected_draft": False, "rewrite": None}
        attempts.append(attempt)
        if kept:
            draft = provider.generate(request.question, kept, feedback)
            if request.correction_demo and index == 0:
                draft = UNSUPPORTED_DEMO_DRAFT
                attempt["injected_draft"] = True
            attempt["draft"] = draft
            event("generate", number, "Teaching fault injection: replaced first draft with an unsupported salary guarantee." if attempt["injected_draft"] else "Generated a cited draft from graded context.")
            evaluation = provider.evaluate(request.question, kept, draft)
            citations = re.findall(r"\[([a-zA-Z0-9_-]+)\]", draft)
            citation_ok = bool(citations) and set(citations).issubset({doc.id for doc in kept})
            accepted = bool(draft.strip()) and citation_ok and evaluation.supported and not evaluation.unsupported_claims and evaluation.answer_relevance >= ANSWER_THRESHOLD and evaluation.grounding >= GROUNDING_THRESHOLD
            attempt["evaluation"] = {**evaluation.model_dump(), "citation_valid": citation_ok}
            attempt["accepted"] = accepted
            event("evaluate", number, f"{'PASS' if accepted else 'RETRY'} · relevance {evaluation.answer_relevance:.2f} · grounding {evaluation.grounding:.2f} · {evaluation.feedback}")
            if accepted:
                return finish("accepted", draft, [doc for doc in kept if doc.id in citations])
            feedback = evaluation.feedback
            if not citation_ok:
                feedback += " Use at least one valid citation and cite only supplied document IDs."
        else:
            feedback = "No sufficiently relevant documents were found. Search for missing evidence using terms from the original question."
            event("evaluate", number, "No relevant context; skipped generation and requested retrieval correction.")
        if index < request.max_retries:
            query = provider.rewrite(request.question, query, feedback)
            attempt["rewrite"] = query
            event("rewrite", number, query)
    return finish("abstained", ABSTENTION, [])
