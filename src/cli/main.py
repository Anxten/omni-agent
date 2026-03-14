import typer
import subprocess
import os
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm, Prompt
from src.core.llm_client import OmniEngine
from src.utils.file_reader import read_context, read_codebase_for_docs

app = typer.Typer(help="⚡ Omni Agent - Zero-Cost Local AI CLI", no_args_is_help=True)
console = Console()
engine = OmniEngine()

@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Pertanyaan untuk Omni"),
    sys: str = typer.Option(
        "Kamu adalah Senior Software Engineer spesialis Python. Berikan penjelasan ringkas dan kode yang clean.", 
        "--sys", "-s", 
        help="Instruksi sistem / Persona AI"
    ),
    file: str = typer.Option(
        None, 
        "--file", "-f", 
        help="Path ke file ATAU folder yang ingin dijadikan konteks (misal: src/)"
    )
):
    """
    Kirim prompt ke Gemini 2.5 Flash dengan konteks file atau seluruh folder.
    """
    final_prompt = prompt
    if file:
        console.print(f"[dim]Mengumpulkan konteks dari: {file}...[/dim]")
        file_content = read_context(file)
        final_prompt = f"Konteks Codebase:\n{file_content}\n\nPertanyaan/Instruksi:\n{prompt}"

    with console.status("[bold cyan]🧠 Omni sedang menganalisis codebase...", spinner="bouncingBar"):
        response = engine.generate_response(final_prompt, system_instruction=sys)
    
    console.print("\n")
    console.print(Markdown(response))
    console.print("\n[dim]-- OmniEngine Executed --[/dim]\n")

@app.command()
def chat(
    sys: str = typer.Option(
        "Kamu adalah Senior Software Engineer.",
        "--sys",
        "-s",
        help="Persona AI"
    ),
    file: str = typer.Option(
        None,
        "--file",
        "-f",
        help="Path ke file/folder sebagai konteks awal"
    )
):
    """(Interactive) Mulai sesi obrolan yang mengingat konteks."""
    console.print("[bold green]💬 Memulai sesi obrolan dengan Omni... (Ketik 'exit' atau 'quit' untuk berhenti)[/bold green]")

    try:
        chat_session = engine.start_chat_session(system_instruction=sys)

        if file:
            console.print(f"[dim]Membaca konteks awal dari: {file}...[/dim]")
            initial_context = read_context(file)
            with console.status("[bold cyan]🧠 Omni sedang mempelajari codebase-mu...", spinner="bouncingBar"):
                chat_session.send_message(
                    f"Ini adalah konteks codebase-ku:\n{initial_context}\n\n"
                    "Pahami kode di atas. Jangan beri saran apa-apa dulu, cukup katakan: 'Konteks dipahami, saya siap berdiskusi!'"
                )
            console.print("[bold cyan]Omni:[/bold cyan] Konteks dipahami, saya siap berdiskusi!\n")

        while True:
            user_input = Prompt.ask("[bold yellow]Kamu[/bold yellow]")
            if user_input.lower() in ["exit", "quit"]:
                console.print("[dim]Sesi obrolan diakhiri. Selamat beristirahat, Komandan![/dim]")
                break

            if not user_input.strip():
                continue

            with console.status("[bold cyan]🧠 Omni mengetik...", spinner="dots"):
                response = chat_session.send_message(user_input)

            console.print("\n[bold cyan]Omni:[/bold cyan]")
            console.print(Markdown(response.text))
            console.print("")

    except Exception as e:
        console.print(f"[bold red]❌ Terjadi kesalahan: {str(e)}[/bold red]")

@app.command()
def commit():
    """Membaca git diff dan men-generate pesan auto-commit berstandar profesional."""
    # 1. Ambil perubahan kode (git diff)
    try:
        # Coba ambil yang sudah di-stage dulu (git add)
        diff_process = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True)
        diff_text = diff_process.stdout.strip()
        is_staged = True

        # Jika kosong, ambil yang belum di-stage
        if not diff_text:
            diff_process = subprocess.run(["git", "diff"], capture_output=True, text=True)
            diff_text = diff_process.stdout.strip()
            is_staged = False

        if not diff_text:
            console.print("[bold red]❌ Tidak ada perubahan kode yang terdeteksi di repositori ini.[/bold red]")
            raise typer.Exit()

    except Exception as e:
        console.print(f"[bold red]❌ Gagal menjalankan Git: {str(e)}[/bold red]")
        raise typer.Exit()

    # 2. Siapkan Persona Khusus untuk Commit
    sys_prompt = (
        "Kamu adalah Senior AI Engineer. Buat 1 pesan commit berdasarkan git diff ini. "
        "WAJIB gunakan format EXACTLY seperti ini: 'Tipe: Pesan komit dengan huruf kapital di awal'. "
        "Contoh valid: 'Feat: Implement auto-commit command', 'Fix: Resolve dependency bug'. "
        "Pilihan Tipe HANYA: Feat, Fix, Chore, Refactor, Docs (Harus diawali huruf Kapital). "
        "JANGAN gunakan scope dalam kurung seperti feat(cli):. "
        "HANYA berikan 1 baris pesan judul (Title) saja. JANGAN berikan deskripsi panjang di bawahnya. "
        "TANPA markdown, TANPA backtick, TANPA penjelasan. "
        "ALWAYS write the final commit message in English, following the Conventional Commits standard, regardless of the language used in the code or git diff."
    )

    # Batasi teks diff agar tidak terlalu panjang (hemat token & waktu)
    diff_limit = diff_text[:5000]

    with console.status("[bold cyan]🧠 Omni sedang menganalisis perubahan kodemu...", spinner="dots"):
        commit_msg = engine.generate_response(f"Git Diff:\n{diff_limit}", system_instruction=sys_prompt).strip()
    
    # 3. Tampilkan Hasil dan Minta Persetujuan (The Interactive Vibe)
    console.print(f"\n[bold green]✨ Saran Pesan Commit:[/bold green]")
    console.print(f"[cyan on black] {commit_msg} [/cyan on black]\n")

    if Confirm.ask("Apakah kamu ingin mengeksekusi commit ini sekarang?"):
        if not is_staged:
            console.print("[dim]Melakukan 'git add .' secara otomatis...[/dim]")
            subprocess.run(["git", "add", "."])
            
        subprocess.run(["git", "commit", "-m", commit_msg])
        console.print("[bold green]✅ Kode berhasil di-commit![/bold green]")

        if Confirm.ask("Langsung push ke origin main?"):
            console.print("[dim]Mendorong ke GitHub...[/dim]")
            subprocess.run(["git", "push", "origin", "main"])
            console.print("[bold green]🚀 Operasi Selesai. Energi berhasil dihemat![/bold green]")
    else:
        console.print("[dim]Operasi dibatalkan.[/dim]")


@app.command()
def doc(
    path: str = typer.Argument(
        ".",
        help="Path direktori/file codebase yang ingin didokumentasikan (default: direktori saat ini)."
    )
):
    """Generate dokumentasi codebase otomatis dan simpan ke OMNI_DOCS.md."""
    console.print(f"[dim]Mengumpulkan konten codebase dari: {path}...[/dim]")
    combined_code = read_codebase_for_docs(path)

    if combined_code.startswith("[System Error:"):
        console.print(f"[bold red]❌ {combined_code}[/bold red]")
        raise typer.Exit()

    sys_prompt = (
        "Kamu adalah Senior Technical Writer. Analisis codebase ini dan hasilkan 3 bagian: "
        "[BAGIAN 1: README.md] berisi deskripsi, tech stack, dan cara instalasi. "
        "[BAGIAN 2: API DOCS/FUNGSI] berisi tabel endpoint atau penjelasan fungsi utama. "
        "[BAGIAN 3: MERMAID.JS] berisi kode block ```mermaid untuk arsitektur/flowchart sistem. "
        "Jangan berikan teks basa-basi."
    )

    prompt = (
        "Berikut adalah gabungan isi codebase. Hasilkan dokumen sesuai format yang diminta pada system prompt.\n\n"
        f"{combined_code}"
    )

    with console.status("[bold cyan]🧠 Omni sedang menyusun dokumentasi project...", spinner="bouncingBar"):
        docs_output = engine.generate_response(prompt, system_instruction=sys_prompt)

    output_path = os.path.join(os.getcwd(), "OMNI_DOCS.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(docs_output)

    console.print(f"[bold green]✅ Dokumentasi berhasil dibuat di: {output_path}[/bold green]")

if __name__ == "__main__":
    app()