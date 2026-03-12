import os

# Ekstensi file yang aman dibaca oleh AI (hindari gambar/binary/database)
ALLOWED_EXTENSIONS = {'.py', '.md', '.txt', '.env.example', '.json', '.yaml', '.yml'}

# Folder yang pantang untuk dibaca (karena berat & tidak relevan)
IGNORED_DIRS = {'.git', '__pycache__', 'venv', 'env', '.vscode', '.idea', 'node_modules'}


def is_text_file(filepath: str) -> bool:
    """Mengecek apakah file aman untuk dibaca berdasarkan ekstensinya."""
    _, ext = os.path.splitext(filepath)
    return ext.lower() in ALLOWED_EXTENSIONS


def _read_single_file(filepath: str) -> str:
    """Fungsi internal untuk membaca satu file dengan aman."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return f"\n--- File: {filepath} ---\n```\n{content}\n```\n"
    except Exception as e:
        return f"\n[Warning: Gagal membaca file {filepath}: {str(e)}]\n"


def read_context(path: str) -> str:
    """
    Core Aggregator: Membaca konteks dari sebuah path.
    Jika path = file, baca file tersebut.
    Jika path = folder, baca SEMUA file yang diizinkan di dalam folder tersebut.
    """
    if not os.path.exists(path):
        return f"[System Error: Path '{path}' tidak ditemukan.]"

    # Skenario 1: User menginput 1 file tunggal
    if os.path.isfile(path):
        if is_text_file(path):
            return _read_single_file(path)
        return f"[System Error: '{path}' bukan file teks yang diizinkan.]"

    # Skenario 2: User menginput direktori/folder (The God Mode)
    aggregated_content = f"--- START CONTEXT DIRECTORY: {path} ---\n"
    file_count = 0

    for root, dirs, files in os.walk(path):
        # Modifikasi list 'dirs' in-place untuk mengabaikan folder sampah
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            filepath = os.path.join(root, file)
            if is_text_file(filepath):
                aggregated_content += _read_single_file(filepath)
                file_count += 1

    aggregated_content += f"--- END CONTEXT DIRECTORY ({file_count} files read) ---\n"

    if file_count == 0:
        return f"[System Error: Tidak ada file teks yang valid di folder '{path}'.]"

    return aggregated_content