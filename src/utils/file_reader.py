import os

# Ekstensi file yang aman dibaca oleh AI (hindari gambar/binary/database)
ALLOWED_EXTENSIONS = {'.py', '.md', '.txt', '.env.example', '.json', '.yaml', '.yml'}

# Folder yang pantang untuk dibaca (karena berat & tidak relevan)
IGNORED_DIRS = {'.git', '__pycache__', 'venv', 'env', '.vscode', '.idea', 'node_modules'}

IMAGE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif', '.heic', '.avif'
}

BINARY_EXTENSIONS = {
    '.pdf', '.zip', '.tar', '.gz', '.7z', '.rar', '.exe', '.dll', '.so', '.dylib',
    '.class', '.jar', '.pyc', '.pyo', '.db', '.sqlite', '.sqlite3', '.bin'
}

AUDIT_ALLOWED_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.sol', '.rs', '.go', '.java', '.kt', '.swift',
    '.php', '.rb', '.c', '.h', '.cpp', '.hpp', '.cs', '.scala', '.sh', '.bash', '.zsh',
    '.yaml', '.yml', '.json', '.toml', '.ini', '.cfg', '.conf', '.md', '.txt'
}


def is_text_file(filepath: str) -> bool:
    """Mengecek apakah file aman untuk dibaca berdasarkan ekstensinya."""
    if _is_sensitive_env_file(filepath):
        return False

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


def _is_ignored_directory(dirname: str) -> bool:
    return dirname in IGNORED_DIRS


def _is_sensitive_env_file(filepath: str) -> bool:
    filename = os.path.basename(filepath).lower()
    # Memblokir: .env, prod.env, .env.local, .env.development, dll.
    return '.env' in filename


def _looks_binary(filepath: str) -> bool:
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(2048)
        if b'\x00' in chunk:
            return True
        return False
    except Exception:
        return True


def _is_allowed_code_file(filepath: str) -> bool:
    if _is_sensitive_env_file(filepath):
        return False

    _, ext = os.path.splitext(filepath)
    lowered = ext.lower()

    if lowered in IMAGE_EXTENSIONS or lowered in BINARY_EXTENSIONS:
        return False

    return not _looks_binary(filepath)


def _is_allowed_audit_file(filepath: str) -> bool:
    if _is_sensitive_env_file(filepath):
        return False

    if not os.path.isfile(filepath):
        return False

    filename = os.path.basename(filepath).lower()
    if filename in {'dockerfile', 'makefile'}:
        return not _looks_binary(filepath)

    _, ext = os.path.splitext(filepath)
    if ext.lower() not in AUDIT_ALLOWED_EXTENSIONS:
        return False

    return not _looks_binary(filepath)


def _read_text_file_robust(filepath: str) -> str:
    encodings = ('utf-8', 'utf-8-sig', 'latin-1')
    last_error = None

    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            last_error = e

    raise RuntimeError(f"Gagal membaca file '{filepath}': {last_error}")


def read_codebase_for_docs(path: str) -> str:
    """
    Membaca seluruh isi file kode/teks dari direktori secara rekursif untuk kebutuhan dokumentasi.
    Wajib mengabaikan folder seperti .git, node_modules, venv, __pycache__, dan file biner/gambar.
    """
    if not os.path.exists(path):
        return f"[System Error: Path '{path}' tidak ditemukan.]"

    if os.path.isfile(path):
        if not _is_allowed_code_file(path):
            return f"[System Error: '{path}' termasuk file biner/gambar atau tidak dapat dibaca.]"
        return _read_single_file(path)

    aggregated_content = [f"--- START DOC CONTEXT DIRECTORY: {path} ---"]
    file_count = 0

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not _is_ignored_directory(d)]

        for file in files:
            filepath = os.path.join(root, file)
            if _is_allowed_code_file(filepath):
                aggregated_content.append(_read_single_file(filepath))
                file_count += 1

    aggregated_content.append(f"--- END DOC CONTEXT DIRECTORY ({file_count} files read) ---")

    if file_count == 0:
        return f"[System Error: Tidak ada file kode/teks yang valid di folder '{path}'.]"

    return "\n".join(aggregated_content)


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


def read_codebase_for_audit_single_batch(path: str) -> str:
    """
    Membaca semua file source yang relevan untuk audit, lalu menggabungkannya dalam
    satu string besar dengan separator per file untuk single-shot LLM request.
    """
    if not os.path.exists(path):
        return f"[System Error: Path '{path}' tidak ditemukan.]"

    files_to_read: list[str] = []
    normalized_path = os.path.abspath(path)

    if os.path.isfile(normalized_path):
        if not _is_allowed_audit_file(normalized_path):
            return f"[System Error: '{path}' bukan file source yang valid untuk audit.]"
        files_to_read.append(normalized_path)
    else:
        for root, dirs, files in os.walk(normalized_path):
            dirs[:] = [d for d in dirs if not _is_ignored_directory(d)]
            for filename in sorted(files):
                filepath = os.path.join(root, filename)
                if _is_allowed_audit_file(filepath):
                    files_to_read.append(filepath)

    if not files_to_read:
        return f"[System Error: Tidak ada file source yang valid di path '{path}'.]"

    files_to_read.sort()
    merged_parts = [
        f"--- START AUDIT BATCH: {normalized_path} ---",
        f"--- TOTAL FILES: {len(files_to_read)} ---"
    ]

    for filepath in files_to_read:
        display_path = os.path.relpath(filepath, start=normalized_path) if os.path.isdir(normalized_path) else os.path.basename(filepath)
        try:
            content = _read_text_file_robust(filepath)
            merged_parts.append(f"--- START FILE: {display_path} ---")
            merged_parts.append(content)
            merged_parts.append("--- END FILE ---")
        except Exception as e:
            merged_parts.append(f"--- START FILE: {display_path} ---")
            merged_parts.append(f"[Warning: Gagal membaca file ini: {str(e)}]")
            merged_parts.append("--- END FILE ---")

    merged_parts.append("--- END AUDIT BATCH ---")
    return "\n\n".join(merged_parts)