from types import SimpleNamespace

import httpx
import pytest
from openai import AuthenticationError

from app.models import Document, Evaluation
from app.providers import EuriProvider, ProviderError


def provider_with_response(raw):
    provider = object.__new__(EuriProvider)
    provider._chat = lambda system, payload: raw
    return provider


@pytest.mark.parametrize("raw", [
    "not json", '{"supported": true}',
    '{"answer_relevance": 8, "grounding": 1, "supported": true, "feedback": "ok", "unsupported_claims": []}',
    '{"answer_relevance": 1, "grounding": 1, "supported": "yes", "feedback": "ok", "unsupported_claims": []}',
])
def test_bad_judge_output_fails_closed(raw):
    with pytest.raises(ProviderError, match="invalid grading format"):
        provider_with_response(raw)._json("audit", {}, Evaluation)


def test_fenced_valid_json_is_parsed():
    raw = '```json\n{"answer_relevance": 1, "grounding": 0.9, "supported": true, "feedback": "ok", "unsupported_claims": []}\n```'
    assert provider_with_response(raw)._json("audit", {}, Evaluation).supported


def test_missing_and_duplicate_document_grades_rejected():
    doc = Document(id="known", title="Test", text="Evidence")
    for raw in ['{"grades": []}', '{"grades":[{"document_id":"unknown","relevance":1,"reason":"ok"}]}',
                '{"grades":[{"document_id":"known","relevance":1,"reason":"ok"},{"document_id":"known","relevance":1,"reason":"ok"}]}']:
        with pytest.raises(ProviderError, match="document grades"):
            provider_with_response(raw).grade("question", [doc])


def test_live_client_uses_exact_requested_model_and_server_key(monkeypatch):
    import app.providers as providers
    seen = {}
    monkeypatch.setattr(providers, "settings", lambda: {"api_key": "test-secret", "base_url": "https://api.euron.one/api/v1/euri", "model": "gemini-3.5-flash-lite"})
    def create(**kwargs):
        seen["request"] = kwargs
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Answer"), finish_reason="stop")])
    def client(**kwargs):
        seen["client"] = kwargs
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(providers, "OpenAI", client)
    provider = EuriProvider()
    assert provider._chat("Helpful", {"question": "hello"}) == "Answer"
    assert seen["request"]["model"] == "gemini-3.5-flash-lite"
    assert seen["client"]["base_url"] == "https://api.euron.one/api/v1/euri"
    assert seen["client"]["api_key"] == "test-secret"


def test_sdk_error_body_is_not_exposed():
    provider = object.__new__(EuriProvider)
    provider.model = "gemini-3.5-flash-lite"
    def fail(**kwargs):
        raise AuthenticationError("sensitive-provider-body", response=httpx.Response(401, request=httpx.Request("POST", "https://example.com")), body={"secret": "do-not-show"})
    provider.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fail)))
    with pytest.raises(ProviderError) as error:
        provider._chat("Helpful", {})
    assert "401" in str(error.value)
    assert "sensitive" not in str(error.value)
    assert "do-not-show" not in str(error.value)


def test_missing_key_has_actionable_error(monkeypatch):
    monkeypatch.setattr("app.providers.settings", lambda: {"api_key": ""})
    with pytest.raises(ProviderError, match="EURI_API_KEY"):
        EuriProvider()
