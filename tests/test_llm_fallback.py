import types
import pytest

from src.core import llm_client
from src.core.config import settings, Settings


class DummyResp:
    def __init__(self, status_code=200, json_body=None, text=None):
        self.status_code = status_code
        self._json = json_body or {}
        self.text = text if text is not None else str(self._json)

    def json(self):
        return self._json


def make_requests_post(responses):
    """Return a function that pops from responses sequentially."""
    calls = {"i": 0}

    def _post(url, *args, **kwargs):
        i = calls["i"]
        if i >= len(responses):
            return DummyResp(status_code=500, json_body={"error": "no more responses"})
        resp = responses[i]
        calls["i"] += 1
        return resp

    return _post


def test_gemini_success(monkeypatch):
    # Arrange: Gemini returns text; requests.post should not be called
    class FakeModel:
        def __init__(self, *a, **k):
            pass

        def generate_content(self, prompt, *a, **k):
            return types.SimpleNamespace(text="gemini reply")

    import google.generativeai as genai
    monkeypatch.setattr(genai, "GenerativeModel", FakeModel)
    monkeypatch.setattr(genai, "configure", lambda api_key: None)

    # Ensure settings present
    Settings.GEMINI_API_KEY = "test"
    Settings.GROQ_API_KEY = ""
    Settings.HF_TOKEN = ""

    engine = llm_client.OmniEngine()

    # Act
    out = engine.generate_response("hi")

    # Assert
    assert out == "gemini reply"


def test_gemini_fails_groq_success(monkeypatch):
    # Arrange: Gemini raises, Groq responds with choices.message.content
    class FailModel:
        def __init__(self, *a, **k):
            pass

        def generate_content(self, *a, **k):
            raise Exception("simulated gemini fail")

    import google.generativeai as genai
    monkeypatch.setattr(genai, "GenerativeModel", FailModel)
    monkeypatch.setattr(genai, "configure", lambda api_key: None)

    Settings.GEMINI_API_KEY = "test"
    Settings.GROQ_API_KEY = "grok"
    Settings.HF_TOKEN = ""

    groq_resp = DummyResp(status_code=200, json_body={"choices": [{"message": {"content": "groq reply"}}]})
    monkeypatch.setattr("requests.post", make_requests_post([groq_resp]))

    engine = llm_client.OmniEngine()
    out = engine.generate_response("hello")
    assert out == "groq reply"


def test_gemini_groq_fail_hf_success(monkeypatch):
    # Arrange: Gemini raises, Groq fails, HF succeeds
    class FailModel:
        def __init__(self, *a, **k):
            pass

        def generate_content(self, *a, **k):
            raise Exception("simulated gemini fail")

    import google.generativeai as genai
    monkeypatch.setattr(genai, "GenerativeModel", FailModel)
    monkeypatch.setattr(genai, "configure", lambda api_key: None)

    Settings.GEMINI_API_KEY = "test"
    Settings.GROQ_API_KEY = "grok"
    Settings.HF_TOKEN = "hf"

    groq_resp = DummyResp(status_code=500, json_body={"error": "bad"}, text='error')
    hf_resp = DummyResp(status_code=200, json_body={"choices": [{"message": {"content": "hf reply"}}]})
    monkeypatch.setattr("requests.post", make_requests_post([groq_resp, hf_resp]))

    engine = llm_client.OmniEngine()
    out = engine.generate_response("hello")
    assert out == "hf reply"


def test_all_providers_fail(monkeypatch):
    # Arrange: Gemini raises, Groq and HF both fail
    class FailModel:
        def __init__(self, *a, **k):
            pass

        def generate_content(self, *a, **k):
            raise Exception("simulated gemini fail")

    import google.generativeai as genai
    monkeypatch.setattr(genai, "GenerativeModel", FailModel)
    monkeypatch.setattr(genai, "configure", lambda api_key: None)

    Settings.GEMINI_API_KEY = "test"
    Settings.GROQ_API_KEY = "grok"
    Settings.HF_TOKEN = "hf"

    groq_resp = DummyResp(status_code=500, json_body={"error": "bad"}, text='error')
    hf_resp = DummyResp(status_code=500, json_body={"error": "bad"}, text='error')
    monkeypatch.setattr("requests.post", make_requests_post([groq_resp, hf_resp]))

    engine = llm_client.OmniEngine()
    out = engine.generate_response("hello")
    assert out.startswith("❌ All providers failed")
