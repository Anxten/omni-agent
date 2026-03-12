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
        self.model = genai.GenerativeModel('gemini-2.5-flash')

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
            # Menggabungkan instruksi sistem (jika ada) dengan prompt utama
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"System Instruction:\n{system_instruction}\n\nUser Input:\n{prompt}"
                
            response = self.model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            return f"❌ Terjadi kesalahan saat menghubungi Gemini API: {str(e)}"

# Opsional: Uji coba kecil jika file ini dijalankan langsung
if __name__ == "__main__":
    engine = OmniEngine()
    print("Mencoba menghubungi Gemini...")
    jawaban = engine.generate_response("Halo, apakah kamu sudah online?", "Jawab dengan gaya robot militer singkat.")
    print(f"Respon: {jawaban}")