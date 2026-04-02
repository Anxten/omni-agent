import google.generativeai as genai
from src.core.config import settings

class OmniEngine:
    """
    Core engine untuk berinteraksi dengan Google's Gemini 2.5 Flash API.
    Fokus pada efisiensi, kecepatan, dan pemrosesan konteks (context window besar).
    """
    
    def __init__(self):
        # Validasi API Key sebelum melakukan inisialisasi
        settings.validate()
        
        # Konfigurasi library genai dengan API Key kita
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
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
        try:
            if system_instruction:
                model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
            else:
                model = self.model

            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"❌ Terjadi kesalahan saat menghubungi Gemini API: {str(e)}"

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