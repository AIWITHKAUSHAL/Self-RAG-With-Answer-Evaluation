from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.providers import ProviderError

client = TestClient(app)


def test_health_does_not_expose_key():
    """Verify the health response exposes only the intended non-secret fields."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert set(response.json()) == {"status", "live_configured", "model", "document_count"}


@pytest.mark.parametrize("payload", [
    {"question": " "}, {"question": "x" * 1001}, {"question": "refund", "max_retries": -1},
    {"question": "refund", "max_retries": 5}, {"question": "refund", "mode": "unknown"},
    {"question": "refund", "top_k": 0},
])
def test_invalid_inputs(payload):
    """Verify invalid questions and out-of-range run settings receive HTTP 422."""
    assert client.post("/api/query", json=payload).status_code == 422


def test_demo_endpoint_success_and_correction():
    """Check first-pass and corrected answers through the public query endpoint."""
    for correction in (False, True):
        response = client.post("/api/query", json={"question": "Does Northstar Academy guarantee a job or salary?", "correction_demo": correction})
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
        assert response.json()["attempt_count"] == (2 if correction else 1)


def test_provider_failure_becomes_safe_http_error(monkeypatch):
    """Verify the route converts a sanitized provider failure into HTTP 502."""
    def fail(_request):
        """Simulate an authentication failure without making a network request."""
        raise ProviderError("EURI request failed (HTTP 401). Check your EURI_API_KEY.")
    monkeypatch.setattr("app.main.run_pipeline", fail)
    response = client.post("/api/query", json={"question": "refund", "mode": "live"})
    assert response.status_code == 502
    assert response.json()["detail"].startswith("EURI request failed")


@pytest.mark.parametrize("path", ["/", "/static/app.js", "/static/style.css", "/architecture", "/api/documents", "/docs"])
def test_app_assets(path):
    """Verify each public page, static asset, and corpus route is available."""
    assert client.get(path).status_code == 200
