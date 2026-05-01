import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load variabel dari file .env ke environment sistem
load_dotenv()

# Global flag untuk memastikan genai.configure() hanya dipanggil sekali
_genai_configured = False

class Settings:
    """
    Kelas untuk mengelola semua konfigurasi dan rahasia aplikasi.
    Prinsip: Fail-fast. Jika konfigurasi penting hilang, hentikan program lebih awal.
    """
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_URL: str = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    HF_DEFAULT_MODEL: str = os.getenv("HF_DEFAULT_MODEL", "HuggingFaceH4/zephyr-7b-beta")
    GROQ_DEFAULT_MODEL: str = os.getenv("GROQ_DEFAULT_MODEL", "llama-3.1-8b-instant")

    @classmethod
    def validate(cls) -> None:
        """Memvalidasi apakah semua konfigurasi esensial sudah terisi."""
        if not cls.GEMINI_API_KEY or cls.GEMINI_API_KEY == "masukkan_api_key_gemini_kamu_disini":
            raise ValueError(
                "❌ GEMINI_API_KEY tidak ditemukan atau belum diubah! "
                "Silakan periksa file .env Anda."
            )

    @classmethod
    def configure_genai(cls) -> None:
        """Configure genai library once globally. Safe to call multiple times (idempotent)."""
        global _genai_configured
        if not _genai_configured:
            cls.validate()
            genai.configure(api_key=cls.GEMINI_API_KEY)
            _genai_configured = True

    @classmethod
    def has_groq(cls) -> bool:
        return bool(cls.GROQ_API_KEY and cls.GROQ_API_KEY.strip())

    @classmethod
    def has_hf(cls) -> bool:
        return bool(cls.HF_TOKEN and cls.HF_TOKEN.strip())

# Instansiasi objek global untuk dipakai di file lain
settings = Settings()