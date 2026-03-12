import os

def read_file_content(filepath: str) -> str:
    """
    Membaca isi file dan mengembalikannya sebagai string.
    Menangani error jika file tidak ditemukan atau bukan file teks (misal: gambar).
    """
    if not os.path.exists(filepath):
        return f"[System Error: File '{filepath}' tidak ditemukan.]"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Bungkus konten dalam format markdown agar LLM mudah membedakan mana file mana instruksi
            filename = os.path.basename(filepath)
            return f"\n--- Isi file: {filename} ---\n```\n{content}\n```\n--- Akhir file ---\n"
    except UnicodeDecodeError:
        return f"[System Error: File '{filepath}' tampaknya bukan file teks yang bisa dibaca.]"
    except Exception as e:
        return f"[System Error: Gagal membaca '{filepath}': {str(e)}]"