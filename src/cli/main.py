import typer
from rich.console import Console
from rich.markdown import Markdown
from src.core.llm_client import OmniEngine
from src.utils.file_reader import read_file_content

app = typer.Typer(help="⚡ Omni Agent - Zero-Cost Local AI CLI", no_args_is_help=True)
console = Console()
engine = OmniEngine()

@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Pertanyaan untuk Omni"),
    sys: str = typer.Option(
        "Kamu adalah Senior Software Engineer spesialis Python. Berikan kode yang clean.", 
        "--sys", "-s", 
        help="Instruksi sistem / Persona AI"
    ),
    file: str = typer.Option(
        None,
        "--file", "-f",
        help="Path ke file yang ingin dijadikan konteks (misal: src/main.py)"
    )
):
    """
    Kirim prompt ke Gemini 2.5 Flash, opsional dengan menyertakan isi file lokal sebagai konteks.
    """
    # Jika user memberikan flag --file, baca file tersebut dan gabungkan ke prompt
    final_prompt = prompt
    if file:
        file_content = read_file_content(file)
        final_prompt = f"Konteks File:\n{file_content}\n\nPertanyaan/Instruksi:\n{prompt}"
        console.print(f"[dim]Membaca konteks dari: {file}...[/dim]")

    with console.status("[bold cyan]🧠 Omni sedang berpikir...", spinner="bouncingBar"):
        response = engine.generate_response(final_prompt, system_instruction=sys)
    
    console.print("\n")
    console.print(Markdown(response))
    console.print("\n[dim]-- OmniEngine Executed --[/dim]\n")

@app.command()
def commit():
    """
    (Coming Soon) Generate auto-commit message berbasis Conventional Commits.
    """
    console.print("[bold yellow]🚧 Fitur Auto-Commit sedang dibangun![/bold yellow]")

if __name__ == "__main__":
    app()