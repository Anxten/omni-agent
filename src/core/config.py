import os
from dotenv import load_dotenv

# Load variabel dari file .env ke environment sistem
load_dotenv()

class Settings:
    """
    Kelas untuk mengelola semua konfigurasi dan rahasia aplikasi.
    Prinsip: Fail-fast. Jika konfigurasi penting hilang, hentikan program lebih awal.
    """
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    @classmethod
    def validate(cls) -> None:
        """Memvalidasi apakah semua konfigurasi esensial sudah terisi."""
        if not cls.GEMINI_API_KEY or cls.GEMINI_API_KEY == "masukkan_api_key_gemini_kamu_disini":
            raise ValueError(
                "❌ GEMINI_API_KEY tidak ditemukan atau belum diubah! "
                "Silakan periksa file .env Anda."
            )

# Instansiasi objek global untuk dipakai di file lain
settings = Settings()