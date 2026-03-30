import typer
import subprocess
import os
import json
from datetime import datetime
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

from src.core.llm_client import OmniEngine
from src.core.orchestrator import AgentOrchestrator
from src.utils.file_reader import read_context, read_codebase_for_docs, read_codebase_for_audit_single_batch

app = typer.Typer(help="⚡ Omni Orchestrator - Multi-Agent AI Platform", no_args_is_help=True)
console = Console()
engine = OmniEngine()
orchestrator = AgentOrchestrator()


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


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def agents(
    agent_name: str = typer.Option(None, "--name", "-n", help="Show details for specific agent"),
):
    """List all available specialist agents and their capabilities."""
    if agent_name:
        details = orchestrator.get_agent_details(agent_name)
        if not details:
            console.print(f"[bold red]❌ Agent '{agent_name}' not found[/bold red]")
            raise typer.Exit(code=1)
        
        console.print()
        console.print(Panel(
            f"[bold cyan]{details['name']}[/bold cyan]",
            title="[bold]Agent Details[/bold]",
            border_style="cyan"
        ))
        console.print(f"\n[bold]Job Description:[/bold]\n{details['job_description']}")
        console.print(f"\n[bold]Capabilities:[/bold]")
        for cap in details['capabilities']:
            console.print(f"  • {cap}")
        return

    # List all agents with summary
    agent_list = orchestrator.list_agents()
    console.print()
    console.print(Rule("[bold cyan]  Available Specialist Agents  [/bold cyan]", style="bold cyan"))
    console.print()

    agents_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold white on blue",
        border_style="cyan",
        padding=(0, 1),
    )
    agents_table.add_column("Agent Name", style="bold yellow")
    agents_table.add_column("Job Description", ratio=2)
    agents_table.add_column("Capabilities", ratio=2, no_wrap=False)

    for agent in agent_list:
        caps = ", ".join(agent["capabilities"][:3])
        if len(agent["capabilities"]) > 3:
            caps += ", ..."
        agents_table.add_row(agent["name"], agent["job_description"][:80], caps)

    console.print(agents_table)
    console.print("\n[dim]Use: omni agents --name 'Agent Name' for detailed information[/dim]\n")


@app.command()
def execute(
    goal: str = typer.Argument(..., help="Your objective or goal for the AI"),
    context: str = typer.Option(
        ".",
        "--context", "-c",
        help="Path to file or directory for context (default: current directory)"
    ),
    agent: str = typer.Option(
        None,
        "--agent", "-a",
        help="Force specific agent (optional, uses auto-routing if not specified)"
    ),
    output: str = typer.Option(
        None,
        "--output", "-o",
        help="Save output to file (optional)"
    ),
):
    """Execute a goal using the most appropriate specialist agent."""
    console.print()
    console.print(f"[dim]📋 Goal:[/dim] {goal}")
    
    # Gather context
    console.print(f"[dim]Gathering context from: {context}...[/dim]")
    code_context = read_context(context)
    
    if code_context.startswith("[System Error:"):
        console.print(f"[bold red]❌ {code_context}[/bold red]")
        raise typer.Exit(code=1)

    # Route through orchestrator
    with console.status("[bold cyan]🧠 Omni Orchestrator routing to specialist...", spinner="dots"):
        result = orchestrator.route_goal(goal, code_context, force_agent=agent)

    console.print()
    
    if result.get("status") == "error":
        console.print(f"[bold red]❌ Error: {result.get('error')}[/bold red]")
        if "available_agents" in result:
            console.print(f"[dim]Available agents: {', '.join(result['available_agents'])}[/dim]")
        raise typer.Exit(code=1)

    # Display results based on agent type
    agent_name = result.get("agent", "Unknown")
    console.print(f"[bold green]✅ Executed by: {agent_name}[/bold green]\n")

    if "result" in result:  # Security audit result
        _display_audit_result(result["result"])
    elif "documentation" in result:  # Documentation result
        console.print(Markdown(result["documentation"]))
    elif "generated_code" in result:  # Code generation result
        console.print(Markdown(result["generated_code"]))

    # Save output if requested
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        console.print(f"\n[bold green]✅ Output saved to: {output}[/bold green]")


def _display_audit_result(audit_data: dict) -> None:
    """Display security audit results in formatted table."""
    summary = audit_data.get("audit_summary", {})
    findings = audit_data.get("findings", [])

    total = summary.get("total_vulnerabilities", 0)
    crit  = summary.get("critical_count", 0)
    high  = summary.get("high_count", 0)
    med   = summary.get("medium_count", 0)
    low   = summary.get("low_count", 0)

    # Risk level
    if crit > 0:
        risk_label = Text("  ⚠  CRITICAL RISK  ", style="bold white on red")
    elif high > 0:
        risk_label = Text("  ▲  HIGH RISK      ", style="bold white on dark_orange")
    elif med > 0:
        risk_label = Text("  ◆  MODERATE RISK  ", style="bold black on yellow")
    else:
        risk_label = Text("  ✔  LOW RISK       ", style="bold black on green")

    summary_table = Table(
        box=box.ROUNDED,
        show_header=False,
        border_style="cyan",
        padding=(0, 2),
        expand=False,
    )
    summary_table.add_column("Metric", style="dim", width=24)
    summary_table.add_column("Value", justify="right", min_width=20)
    summary_table.add_row("Risk Level", risk_label)
    summary_table.add_row("Total Vulnerabilities", Text(str(total), style="bold white"))
    summary_table.add_row("● Critical", Text(str(crit), style="bold red"))
    summary_table.add_row("● High",     Text(str(high), style="bold dark_orange"))
    summary_table.add_row("● Medium",   Text(str(med),  style="bold yellow"))
    summary_table.add_row("● Low",      Text(str(low),  style="bold green"))
    console.print(summary_table)
    console.print()


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


def export_audit_to_markdown(audit_data: dict, output_path: str) -> None:
    """Generate formal B2B executive security report in Markdown format."""
    summary = audit_data.get("audit_summary", {})
    findings = audit_data.get("findings", [])

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    sorted_findings = sorted(
        findings,
        key=lambda finding: severity_order.get(str(finding.get("severity", "LOW")).upper(), 99)
    )

    generated_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Executive Security Audit Report",
        "",
        f"Generated on: {generated_on}",
        "",
        "## 1. Executive Summary",
        "",
        "This report provides a formal overview of the current application security posture based on the automated static analysis execution.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total Vulnerabilities | {summary.get('total_vulnerabilities', 0)} |",
        f"| Critical | {summary.get('critical_count', 0)} |",
        f"| High | {summary.get('high_count', 0)} |",
        f"| Medium | {summary.get('medium_count', 0)} |",
        f"| Low | {summary.get('low_count', 0)} |",
        "",
        "## 2. Methodology",
        "",
        "The assessment was performed using an Automated SAST Engine aligned with OWASP Top 10 security principles to identify, categorize, and prioritize application-level risks.",
        "",
        "## 3. Detailed Findings",
        "",
    ]

    if not sorted_findings:
        lines.extend([
            "No vulnerabilities were identified during this assessment.",
            "",
        ])
    else:
        for finding in sorted_findings:
            severity = str(finding.get("severity", "LOW")).upper()
            vuln_type = str(finding.get("vulnerability_type", "Unknown Vulnerability"))
            file_path = str(finding.get("file_path", "-"))
            location = str(finding.get("line_number_or_function", "-"))
            description = str(finding.get("description", "-"))
            remediation = str(finding.get("remediation_code", "-"))

            lines.extend([
                f"### [{severity}] {vuln_type}",
                "",
                f"Location: {file_path} (Line: {location})",
                "",
                "Description:",
                description,
                "",
                "Remediation:",
                remediation,
                "",
                "---",
                "",
            ])

    with open(output_path, "w", encoding="utf-8") as markdown_file:
        markdown_file.write("\n".join(lines).strip() + "\n")


def _truncate_path(path: str, max_len: int = 30) -> str:
    """Shorten a file path from the front if it exceeds max_len, e.g. '…/cli/main.py'."""
    if len(path) <= max_len:
        return path
    parts = path.replace("\\", "/").split("/")
    for n in [3, 2, 1]:
        candidate = "…/" + "/".join(parts[-n:])
        if len(candidate) <= max_len:
            return candidate
    return "…" + path[-(max_len - 1):]


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
    ),
):
    """Jalankan audit keamanan SAST berbasis OWASP dan simpan hasil ke OMNI_AUDIT.json."""
    console.print(f"[dim]Mengumpulkan konteks codebase untuk audit dari: {path}...[/dim]")
    code_context = read_codebase_for_audit_single_batch(path)

    if code_context.startswith("[System Error:"):
        console.print(f"[bold red]❌ {code_context}[/bold red]")
        raise typer.Exit()

    # Use orchestrator to route to security agent
    with console.status("[bold cyan]🛡️ Omni sedang menjalankan SAST audit...", spinner="bouncingBar"):
        result = orchestrator.route_goal(
            "Perform comprehensive security audit",
            code_context,
            force_agent="Security Audit Specialist"
        )

    if result.get("status") == "error":
        console.print(f"[bold red]❌ Audit failed: {result.get('error')}[/bold red]")
        raise typer.Exit(code=1)

    audit_data = result.get("result", {})
    findings = audit_data.get("findings", [])
    
    # Generate summary if not present
    if not audit_data.get("audit_summary"):
        audit_data["audit_summary"] = _build_summary_from_findings(findings)

    # Save results
    output_path = os.path.join(os.getcwd(), "OMNI_AUDIT.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, ensure_ascii=False, indent=2)

    markdown_output_path = os.path.join(os.getcwd(), "OMNI_SECURITY_REPORT.md")
    export_audit_to_markdown(audit_data, markdown_output_path)

    console.print()
    console.print(Rule("[bold cyan]  OMNI SECURITY AUDIT REPORT  [/bold cyan]", style="bold cyan"))
    console.print()
    
    _display_audit_result(audit_data)

    console.print(f"[bold green]✅ Audit reports saved:[/bold green]")
    console.print(f"  • JSON: {output_path}")
    console.print(f"  • Markdown: {markdown_output_path}\n")


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

if __name__ == "__main__":
    app()