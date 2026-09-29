from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import ROOT, settings
from app.models import QueryRequest
from app.pipeline import run_pipeline
from app.providers import ProviderError
from app.retrieval import Retriever

app = FastAPI(title="Self-RAG Studio", version="1.0.0", description="Retrieve, grade, generate, evaluate, and correct with a bounded retry loop.")
app.mount("/static", StaticFiles(directory=ROOT / "app/static"), name="static")


@app.get("/", include_in_schema=False)
def home():
    """Serve the web playground's HTML entry point."""
    return FileResponse(ROOT / "app/static/index.html")


@app.get("/architecture", include_in_schema=False)
def architecture():
    """Serve the generated, self-contained architecture explorer."""
    return FileResponse(ROOT / "docs/architecture_visualizer.html")


@app.get("/api/health")
def health():
    """Report service configuration and corpus size without disclosing the API key."""
    config = settings()
    return {"status": "ok", "live_configured": bool(config["api_key"]), "model": config["model"], "document_count": len(Retriever().documents)}


@app.get("/api/documents")
def documents():
    """Return sample passages so users can inspect the knowledge base."""
    return {"documents": [doc.model_dump() for doc in Retriever().documents]}


@app.post("/api/query")
def query(request: QueryRequest):
    """Execute a validated query and map sanitized provider failures to HTTP 502."""
    try:
        return run_pipeline(request)
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
