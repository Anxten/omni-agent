import logging

import google.generativeai as genai
import requests

from src.core.config import settings


logger = logging.getLogger(__name__)

class OmniEngine:
    """
    Core engine untuk berinteraksi dengan Google's Gemini 2.5 Flash API.
    Fokus pada efisiensi, kecepatan, dan pemrosesan konteks (context window besar).
    """
    
    def __init__(self):
        # Centralized genai configuration (called once globally)
        from src.core.config import settings
        settings.configure_genai()
        
        # Kita menggunakan 2.5-flash karena gratis, cepat, dan punya context window 1M token
        self.model_name = "gemini-2.5-flash"
        self.model = genai.GenerativeModel(self.model_name)

    def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        """
        Mengirim prompt dan instruksi sistem ke LLM, lalu mengembalikan teks hasilnya.

        Args:
            prompt (str): Input utama dari user atau kode yang ingin dianalisis.
            system_instruction (str, optional): Konteks persona AI (misal: "Kamu adalah Senior Engineer").

        Returns:
            str: Jawaban dari Gemini AI.
        """
        # Try primary provider (Gemini)
        try:
            if system_instruction:
                model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
            else:
                model = self.model

            response = model.generate_content(prompt)
            text = getattr(response, "text", None)
            if text:
                return text
        except Exception as e:
            gemini_err = str(e)

        # Secondary: Groq (HTTP fallback)
        if settings.has_groq():
            try:
                groq_url = settings.GROQ_API_URL or "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": settings.GROQ_DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                }
                r = requests.post(groq_url, headers=headers, json=payload, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    choices = data.get("choices") if isinstance(data, dict) else None
                    if choices and isinstance(choices, list):
                        message = choices[0].get("message", {}) if choices else {}
                        text = message.get("content")
                        if text:
                            return str(text)
                    text = data.get("text") or data.get("output") or data.get("result")
                    if isinstance(text, list):
                        text = "\n".join(map(str, text))
                    if text:
                        return str(text)
                logger.warning(
                    "Groq fallback failed: status=%s body=%s",
                    r.status_code,
                    r.text[:1000],
                )
            except Exception:
                logger.exception("Groq fallback raised an exception")

        # Tertiary: Hugging Face Inference API
        if settings.has_hf():
            try:
                hf_url = "https://router.huggingface.co/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {settings.HF_TOKEN}",
                    "Content-Type": "application/json",
                }
                candidate_models = [
                    settings.HF_DEFAULT_MODEL,
                    "google/gemma-2-2b-it",
                    "Qwen/Qwen2.5-7B-Instruct-1M",
                    "openai/gpt-oss-120b",
                ]
                tried_models = []
                for model_name in candidate_models:
                    if not model_name or model_name in tried_models:
                        continue
                    tried_models.append(model_name)
                    payload = {
                        "model": model_name,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                    r = requests.post(hf_url, headers=headers, json=payload, timeout=30)
                    if r.status_code == 200:
                        resp = r.json()
                        choices = resp.get("choices") if isinstance(resp, dict) else None
                        if choices and isinstance(choices, list):
                            message = choices[0].get("message", {}) if choices else {}
                            out = message.get("content")
                            if out:
                                return str(out)
                        # Fallback to older HF formats if the proxy returns them
                        if isinstance(resp, list) and len(resp) > 0:
                            out = resp[0].get("generated_text") if isinstance(resp[0], dict) else str(resp[0])
                        elif isinstance(resp, dict) and "generated_text" in resp:
                            out = resp.get("generated_text")
                        else:
                            out = None
                        if out:
                            return str(out)

                    logger.warning(
                        "Hugging Face fallback failed for model=%s: status=%s body=%s",
                        model_name,
                        r.status_code,
                        r.text[:1000],
                    )
            except Exception:
                logger.exception("Hugging Face fallback raised an exception")

        # If none succeeded, surface primary error if available
        try:
            return f"❌ All providers failed. Gemini error: {gemini_err}"
        except NameError:
            return "❌ All providers failed: no provider returned a result."

    def start_chat_session(self, system_instruction: str = None):
        """Memulai sesi obrolan interaktif yang mengingat riwayat percakapan."""
        try:
            if system_instruction:
                model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
            else:
                model = self.model

            return model.start_chat(history=[])
        except Exception as e:
            raise Exception(f"Gagal memulai sesi chat: {str(e)}")

    def generate_security_audit(self, code_context: str) -> str:
        """
        Menjalankan SAST berbasis LLM dengan output STRICT JSON untuk kebutuhan audit keamanan.
        """
        system_prompt = (
            "You are an Elite DevSecOps and Application Security Engineer. Your objective is to perform a brutal, "
            "uncompromising Static Application Security Testing (SAST) on the provided codebase. "
            "Your methodology is strictly based on the OWASP Top 10 vulnerabilities (e.g., SQL Injection, XSS, "
            "Broken Access Control, Hardcoded Secrets, Insecure Direct Object References). "
            "Apply these Web3 Security heuristics carefully: Soroban TTL is paid by the caller, and a public TTL "
            "extension is a feature used to prevent deletion rather than a DoS bug. Also, Rust generic or helper "
            "functions may be protected by wrapping macros such as #[lz_contract] constructors, so do not flag them "
            "as Broken Access Control unless they are directly exposed as public entrypoints. "
            "Analyze the provided code and identify ANY security vulnerabilities, bad practices, or potential attack vectors. "
            "CRITICAL RULE: You MUST return the output EXCLUSIVELY in valid JSON format. "
            "Do not include markdown formatting, conversational text, or explanations outside the JSON structure. "
            "IMPORTANT FORMATTING RULES FOR JSON VALUES: "
            "1. The 'remediation_code' field must contain a plain English description of the fix. Do NOT include actual code, backticks, triple backticks, or code fences inside any JSON string value. "
            "2. Do NOT use backtick characters (`) anywhere in the JSON output. "
            "3. All string values in the JSON must be simple plain text, properly escaped. "
            "JSON STRUCTURE: "
            "{"
            "\"audit_summary\": {"
            "\"total_vulnerabilities\": <int>,"
            "\"critical_count\": <int>,"
            "\"high_count\": <int>,"
            "\"medium_count\": <int>,"
            "\"low_count\": <int>"
            "},"
            "\"findings\": ["
            "{"
            "\"severity\": \"<CRITICAL|HIGH|MEDIUM|LOW>\","
            "\"vulnerability_type\": \"<e.g., SQL Injection, Hardcoded Secret>\","
            "\"file_path\": \"<extracted from context>\","
            "\"line_number_or_function\": \"<approximate location>\","
            "\"description\": \"<Clear explanation of HOW the attack can be executed>\","
            "\"remediation_code\": \"<The exact code snippet to fix the issue>\""
            "}"
            "]"
            "}"
        )

        prompt = (
            "Perform SAST analysis on this codebase context and return only valid JSON.\n\n"
            f"{code_context}"
        )

        try:
            model = genai.GenerativeModel(self.model_name, system_instruction=system_prompt)
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text
        except Exception as e:
            return f"❌ Terjadi kesalahan saat menghubungi Gemini API: {str(e)}"

# Opsional: Uji coba kecil jika file ini dijalankan langsung
if __name__ == "__main__":
    engine = OmniEngine()
    print("Mencoba menghubungi Gemini...")
    jawaban = engine.generate_response("Halo, apakah kamu sudah online?", "Jawab dengan gaya robot militer singkat.")
    print(f"Respon: {jawaban}")