import typer
import subprocess
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm
from src.core.llm_client import OmniEngine
from src.utils.file_reader import read_context

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
        "TANPA markdown, TANPA backtick, TANPA penjelasan."
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

if __name__ == "__main__":
    app()