import typer
from rich.console import Console
from rich.markdown import Markdown
from src.core.llm_client import OmniEngine

app = typer.Typer(help="⚡ Omni Agent - Zero-Cost Local AI CLI", no_args_is_help=True)
console = Console()
engine = OmniEngine()

@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Pertanyaan untuk Omni"),
    sys: str = typer.Option(
        "Kamu adalah Senior Software Engineer spesialis Python. Berikan kode yang clean dan penjelasan singkat.", 
        "--sys", "-s", 
        help="Instruksi sistem / Persona AI"
    )
):
    """
    Kirim prompt ke Gemini 2.5 Flash.
    """
    with console.status("[bold cyan]🧠 Omni sedang berpikir...", spinner="bouncingBar"):
        response = engine.generate_response(prompt, system_instruction=sys)
    
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