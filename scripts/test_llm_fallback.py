#!/usr/bin/env python3
"""
Non-destructive test for LLM provider fallback.
Simulasikan kegagalan Gemini dengan mengganti ``genai.GenerativeModel``
sementara sehingga panggilan ke Gemini melempar exception.
Kemudian jalankan ``OmniEngine.generate_response`` dan lihat apakah
fallback ke Groq atau Hugging Face berhasil.

Usage: python scripts/test_llm_fallback.py
"""
import os
import sys
from contextlib import contextmanager
from dotenv import load_dotenv

# Ensure repo root is on sys.path so `src` package imports work when running script directly
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

load_dotenv()

from src.core.config import settings
from src.core import llm_client

def mask(s: str) -> str:
    if not s:
        return "<missing>"
    return s[:4] + "..." + s[-4:]


@contextmanager
def force_groq_failure():
    import requests

    original_post = requests.post

    def patched_post(url, *args, **kwargs):
        if "api.groq.com" in str(url):
            class ForcedResponse:
                status_code = 500
                text = "{" + '"error":{"message":"forced Groq failure for fallback test"}' + "}"

                def json(self):
                    return {"error": {"message": "forced Groq failure for fallback test"}}

            return ForcedResponse()
        return original_post(url, *args, **kwargs)

    requests.post = patched_post
    try:
        yield
    finally:
        requests.post = original_post

def main():
    print("=== LLM Fallback Test (simulate Gemini failure) ===")
    print(f"Has GROQ key: {settings.has_groq()} | GROQ_API_KEY: {mask(settings.GROQ_API_KEY)}")
    print(f"Has HF key: {settings.has_hf()} | HF_TOKEN: {mask(settings.HF_TOKEN)}")

    # Ensure genai is importable
    try:
        import google.generativeai as genai
    except Exception as e:
        print("ERROR: google.generativeai not importable:", e)
        sys.exit(2)

    # Save original
    original_generative_model = getattr(genai, "GenerativeModel", None)

    # Define a failing model that raises on generate_content
    class FailModel:
        def __init__(self, *args, **kwargs):
            # instantiate fine, but will fail at runtime
            pass

        def generate_content(self, *args, **kwargs):
            raise Exception("Simulated Gemini failure for testing fallback")

        def start_chat(self, *args, **kwargs):
            raise Exception("Simulated Gemini failure for testing fallback")

    # Patch to simulate failure
    genai.GenerativeModel = FailModel

    try:
        engine = llm_client.OmniEngine()
        prompt = "Tuliskan satu kalimat singkat: 'Fallback test berhasil.'"
        print("Running generate_response with patched Gemini (should fallback)...")
        resp = engine.generate_response(prompt)
        print("--- Response ---")
        print(resp)
        print("--- End Response ---")

        if resp and not resp.startswith("❌"):
            print("Result: SUCCESS — at least one fallback provider returned a response.")
            print("\nRunning second pass with Groq forcibly failed to verify Hugging Face fallback...")
            with force_groq_failure():
                resp2 = engine.generate_response(prompt)
            print("--- HF Fallback Response ---")
            print(resp2)
            print("--- End HF Fallback Response ---")
            if resp2 and not resp2.startswith("❌"):
                print("Result: SUCCESS — Hugging Face fallback also returned a response.")
                sys.exit(0)
            print("Result: FAILURE — Groq was blocked but HF fallback did not return a response.")
            sys.exit(4)
        else:
            print("Result: FAILURE — all providers failed. See response above.")
            # Run direct diagnostics for Groq and Hugging Face to surface errors
            try:
                import requests
                print("\n--- Running direct provider diagnostics ---")
                if settings.has_groq():
                    groq_url = settings.GROQ_API_URL or "https://api.groq.com/openai/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"}
                    payload = {
                        "model": settings.GROQ_DEFAULT_MODEL,
                        "messages": [{"role": "user", "content": "Health check: respond 'ok'"}],
                    }
                    try:
                        r = requests.post(groq_url, headers=headers, json=payload, timeout=15)
                        print(f"Groq status: {r.status_code}\nBody: {r.text}")
                    except Exception as e:
                        print(f"Groq request exception: {e}")
                else:
                    print("Groq: no key configured.")

                if settings.has_hf():
                    hf_model = settings.HF_DEFAULT_MODEL
                    hf_url = "https://router.huggingface.co/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {settings.HF_TOKEN}",
                        "Content-Type": "application/json",
                    }
                    try:
                        r = requests.post(
                            hf_url,
                            headers=headers,
                            json={"model": hf_model, "messages": [{"role": "user", "content": "Health check: respond 'ok'"}]},
                            timeout=20,
                        )
                        print(f"HF status: {r.status_code}\nBody: {r.text}")
                        # If router returns a model error, try alternate stable models to validate token and routing
                        if r.status_code != 200:
                            for alt in (
                                "HuggingFaceH4/zephyr-7b-beta",
                                "google/gemma-2-2b-it",
                                "Qwen/Qwen2.5-7B-Instruct-1M",
                                "openai/gpt-oss-120b",
                            ):
                                try:
                                    r2 = requests.post(
                                        hf_url,
                                        headers=headers,
                                        json={"model": alt, "messages": [{"role": "user", "content": "Health check: respond 'ok'"}]},
                                        timeout=20,
                                    )
                                    print(f"HF alt model {alt} status: {r2.status_code}\nBody: {r2.text}")
                                except Exception as e:
                                    print(f"HF alt model {alt} request exception: {e}")
                    except Exception as e:
                        print(f"HF request exception: {e}")
                else:
                    print("Hugging Face: no token configured.")
            except Exception as e:
                print("Diagnostics failed to run:", e)

            sys.exit(3)
    finally:
        # Restore original to avoid side-effects
        if original_generative_model is not None:
            genai.GenerativeModel = original_generative_model

if __name__ == '__main__':
    main()
