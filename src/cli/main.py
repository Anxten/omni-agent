import typer
import subprocess
import os
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm, Prompt
from rich.table import Table
from src.core.llm_client import OmniEngine
from src.utils.file_reader import read_context, read_codebase_for_docs

app = typer.Typer(help="⚡ Omni Agent - Zero-Cost Local AI CLI", no_args_is_help=True)
console = Console()
engine = OmniEngine()


def _extract_json_payload(raw_text: str) -> dict:
    """Parse JSON ketat dengan fallback ekstraksi objek JSON terbesar dari response LLM."""
    stripped = raw_text.strip()

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start_index = stripped.find("{")
        if start_index == -1:
            raise
        candidate = stripped[start_index:]
        decoder = json.JSONDecoder()
        parsed, _ = decoder.raw_decode(candidate)
        return parsed


def _severity_style(severity: str) -> str:
    mapping = {
        "CRITICAL": "bold red",
        "HIGH": "orange3",
        "MEDIUM": "yellow",
        "LOW": "green"
    }
    return mapping.get((severity or "").upper(), "white")


def _is_token_limit_error(raw_text: str) -> bool:
    lowered = (raw_text or "").lower()
    is_api_error = lowered.startswith("❌") or lowered.startswith("error")
    return is_api_error and "token" in lowered and ("limit" in lowered or "exceed" in lowered)


def _build_summary_from_findings(findings: list[dict]) -> dict:
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0

    for finding in findings:
        severity = str(finding.get("severity", "")).upper()
        if severity == "CRITICAL":
            critical_count += 1
        elif severity == "HIGH":
            high_count += 1
        elif severity == "MEDIUM":
            medium_count += 1
        elif severity == "LOW":
            low_count += 1

    return {
        "total_vulnerabilities": len(findings),
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
    }

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
        else:
            # Check if there are also unstaged changes that weren't included
            unstaged = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True).stdout.strip()
            if unstaged:
                console.print(f"[bold yellow]⚠️  Ada file yang belum di-stage:[/bold yellow] {unstaged.replace(chr(10), ', ')}")
                if Confirm.ask("Tambahkan semua perubahan yang belum di-stage juga?"):
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


@app.command()
def audit(
    path: str = typer.Argument(
        ".",
        help="Path direktori/file codebase yang ingin diaudit (default: direktori saat ini)."
    )
):
    """Jalankan audit keamanan SAST berbasis OWASP dan simpan hasil ke OMNI_AUDIT.json."""
    console.print(f"[dim]Mengumpulkan konteks codebase untuk audit dari: {path}...[/dim]")
    code_context = read_codebase_for_docs(path)

    if code_context.startswith("[System Error:"):
        console.print(f"[bold red]❌ {code_context}[/bold red]")
        raise typer.Exit()

    chunk_size = 60_000
    chunks = [code_context[i:i + chunk_size] for i in range(0, len(code_context), chunk_size)]
    all_findings: list[dict] = []

    with console.status("[bold cyan]🛡️ Omni sedang menjalankan SAST audit...", spinner="bouncingBar"):
        for index, chunk in enumerate(chunks, start=1):
            raw_audit = engine.generate_security_audit(chunk)

            if _is_token_limit_error(raw_audit):
                console.print(
                    f"[bold red]❌ Chunk audit ke-{index} masih melebihi batas token model.[/bold red]"
                )
                console.print("[yellow]Coba audit pada subfolder lebih kecil, misalnya: omni audit src/[/yellow]")
                raise typer.Exit(code=1)

            try:
                parsed = _extract_json_payload(raw_audit)
            except json.JSONDecodeError:
                debug_path = os.path.join(os.getcwd(), f"OMNI_AUDIT_chunk_{index}.raw.txt")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(raw_audit)
                console.print(
                    f"[bold red]❌ Response chunk audit ke-{index} bukan JSON valid.[/bold red]"
                )
                console.print(f"[yellow]Raw chunk disimpan di: {debug_path}[/yellow]")
                raise typer.Exit(code=1)

            findings = parsed.get("findings", [])
            if isinstance(findings, list):
                all_findings.extend(findings)

    audit_data = {
        "audit_summary": _build_summary_from_findings(all_findings),
        "findings": all_findings,
    }

    output_path = os.path.join(os.getcwd(), "OMNI_AUDIT.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, ensure_ascii=False, indent=2)

    summary = audit_data.get("audit_summary", {})
    findings = audit_data.get("findings", [])

    summary_table = Table(title="SECURITY AUDIT REPORT", show_header=True, header_style="bold cyan")
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value", justify="right")
    summary_table.add_row("Total Vulnerabilities", str(summary.get("total_vulnerabilities", 0)))
    summary_table.add_row("Critical", str(summary.get("critical_count", 0)), style="bold red")
    summary_table.add_row("High", str(summary.get("high_count", 0)), style="orange3")
    summary_table.add_row("Medium", str(summary.get("medium_count", 0)), style="yellow")
    summary_table.add_row("Low", str(summary.get("low_count", 0)), style="green")
    console.print(summary_table)

    findings_table = Table(show_header=True, header_style="bold magenta")
    findings_table.add_column("Severity", width=10)
    findings_table.add_column("Type", width=24)
    findings_table.add_column("File", width=32)
    findings_table.add_column("Location", width=20)
    findings_table.add_column("Description", width=52)
    findings_table.add_column("Remediation Code", width=52)

    if findings:
        for finding in findings:
            severity = str(finding.get("severity", "LOW")).upper()
            row_style = _severity_style(severity)
            findings_table.add_row(
                severity,
                str(finding.get("vulnerability_type", "-")),
                str(finding.get("file_path", "-")),
                str(finding.get("line_number_or_function", "-")),
                str(finding.get("description", "-")),
                str(finding.get("remediation_code", "-")),
                style=row_style
            )
    else:
        findings_table.add_row("-", "No vulnerabilities found", "-", "-", "-", "-", style="green")

    console.print(findings_table)
    console.print(f"[bold green]✅ Raw audit berhasil disimpan di: {output_path}[/bold green]")

if __name__ == "__main__":
    app()