import typer
import subprocess
import hashlib
import os
import json
from datetime import datetime, timezone
from pathlib import Path
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
from src.utils.web_scraper import scrape_url_to_markdown

app = typer.Typer(help="⚡ Omni Orchestrator - Multi-Agent AI Platform", no_args_is_help=True)
console = Console()

# Lazy initialization - only created when needed
_engine = None
_orchestrator = None
PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMMIT_CACHE_PATH = PROJECT_ROOT / ".omni" / "commit_cache.json"

def get_engine():
    """Get or create OmniEngine lazily to avoid unnecessary initialization."""
    global _engine
    if _engine is None:
        _engine = OmniEngine()
    return _engine

def get_orchestrator():
    """Get or create orchestrator lazily to avoid unnecessary agent initialization."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


def _load_commit_cache() -> dict:
    """Load cached commit messages keyed by diff signature."""
    if not COMMIT_CACHE_PATH.exists():
        return {}

    try:
        with open(COMMIT_CACHE_PATH, "r", encoding="utf-8") as cache_file:
            payload = json.load(cache_file)
            return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _save_commit_cache(cache: dict) -> None:
    """Persist commit cache locally."""
    try:
        COMMIT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(COMMIT_CACHE_PATH, "w", encoding="utf-8") as cache_file:
            json.dump(cache, cache_file, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _build_commit_signature(diff_text: str, changed_files: str, is_staged: bool) -> str:
    digest = hashlib.sha256()
    digest.update(("staged" if is_staged else "unstaged").encode("utf-8"))
    digest.update(changed_files.strip().encode("utf-8"))
    digest.update(diff_text.strip().encode("utf-8"))
    return digest.hexdigest()


def _parse_changed_file_paths(changed_files: str) -> list[str]:
    paths: list[str] = []
    for raw_line in changed_files.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        status = parts[0]
        file_parts = parts[1:]

        if status.startswith(("R", "C")) and len(file_parts) >= 2:
            paths.extend([file_parts[0], file_parts[-1]])
            continue

        paths.append(file_parts[-1])

    return paths


def _classify_commit_subject(paths: list[str], best_type: str) -> str:
    lowered_paths = [path.lower() for path in paths]

    if any(path.endswith((".md", ".rst", ".txt")) or "/docs/" in path or path.startswith("docs/") for path in lowered_paths):
        return "documentation"

    if any(
        path.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env"))
        or path in {"package.json", "package-lock.json", "pnpm-lock.yaml", "requirements.txt", "pyproject.toml", "poetry.lock", "tsconfig.json"}
        or path.endswith(".gitignore")
        for path in lowered_paths
    ):
        return "project configuration"

    if any(path.startswith("src/cli/") for path in lowered_paths):
        return "commit workflow"

    if any(path.startswith("src/core/") for path in lowered_paths):
        return "LLM pipeline"

    if any(path.startswith("src/agents/") for path in lowered_paths):
        return "agent orchestration"

    if any(path.startswith("src/") for path in lowered_paths):
        return "codebase workflow"

    if best_type == "Docs":
        return "documentation"
    if best_type == "Chore":
        return "project configuration"
    if best_type == "Fix":
        return "bug handling"
    if best_type == "Feat":
        return "new capability"
    return "codebase"


def _build_local_commit_message(changed_files: str, diff_text: str) -> tuple[str, float, str]:
    paths = _parse_changed_file_paths(changed_files)
    lowered_diff = diff_text.lower()

    scores = {"Feat": 0, "Fix": 0, "Chore": 0, "Refactor": 0, "Docs": 0}

    for path in paths:
        lowered_path = path.lower()
        if lowered_path.endswith((".md", ".rst")) or "/docs/" in lowered_path or lowered_path.startswith("docs/"):
            scores["Docs"] += 4
        if lowered_path.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env")) or lowered_path in {
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "requirements.txt",
            "pyproject.toml",
            "poetry.lock",
            "tsconfig.json",
        } or lowered_path.endswith(".gitignore"):
            scores["Chore"] += 4
        if lowered_path.startswith("src/cli/") or lowered_path.startswith("src/core/") or lowered_path.startswith("src/agents/"):
            scores["Refactor"] += 1
            scores["Feat"] += 1

    keyword_groups = {
        "Refactor": ["refactor", "cleanup", "clean up", "simplify", "simplify", "centralize", "lazy", "cache", "optimize", "consolidate"],
        "Fix": ["fix", "bug", "error", "fail", "prevent", "guard", "validate", "handle", "edge case", "exception"],
        "Feat": ["add", "implement", "introduce", "support", "create", "enable", "feature"],
        "Chore": ["config", "dependency", "dependencies", "setup", "version", "lockfile", "ignore"],
        "Docs": ["doc", "docs", "readme", "guide", "documentation"],
    }

    for commit_type, keywords in keyword_groups.items():
        for keyword in keywords:
            if keyword in lowered_diff:
                scores[commit_type] += 2 if commit_type != "Refactor" else 3

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    sorted_scores = sorted(scores.values(), reverse=True)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0

    confidence = 0.0
    if best_score > 0:
        confidence = min(1.0, (best_score + max(best_score - second_score, 0)) / 10)

    subject = _classify_commit_subject(paths, best_type)
    if best_type == "Docs":
        message = f"Docs: Update {subject}"
    elif best_type == "Chore":
        message = f"Chore: Update {subject}"
    elif best_type == "Fix":
        message = f"Fix: Improve {subject}"
    elif best_type == "Feat":
        message = f"Feat: Add {subject}"
    else:
        message = f"Refactor: Simplify {subject}"

    return message, confidence, best_type


def _is_url(value: str) -> bool:
    lowered = (value or "").strip().lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def _resolve_context_source(source: str, local_reader) -> str:
    """Resolve context from URL or local path using the appropriate ingestion flow."""
    if _is_url(source):
        return scrape_url_to_markdown(source)
    return local_reader(source)


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
        details = get_orchestrator().get_agent_details(agent_name)
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
    agent_list = get_orchestrator().list_agents()
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
        help="Path or URL for context (default: current directory)"
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
    
    # Gather context from URL or local path
    console.print(f"[dim]Gathering context from: {context}...[/dim]")
    code_context = _resolve_context_source(context, read_context)
    
    if code_context.startswith("[System Error:"):
        console.print(f"[bold red]❌ {code_context}[/bold red]")
        raise typer.Exit(code=1)

    # Route through orchestrator
    with console.status("[bold cyan]🧠 Omni Orchestrator routing to specialist...", spinner="dots"):
        result = get_orchestrator().route_goal(
            goal,
            code_context,
            force_agent=agent,
            context_path=None if _is_url(context) else context,
        )

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
    elif "markdown" in result:  # Academic result
        console.print(Markdown(result["markdown"]))
    elif "pitch" in result:  # Sales result
        console.print(Markdown(result["pitch"]))

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
        response = get_engine().generate_response(final_prompt, system_instruction=sys)
    
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
        chat_session = get_engine().start_chat_session(system_instruction=sys)

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

    # Ambil daftar file yang berubah agar model tidak terkunci pada satu bagian diff saja
    name_status_args = ["git", "diff", "--cached", "--name-status"] if is_staged else ["git", "diff", "--name-status"]
    changed_files = subprocess.run(name_status_args, capture_output=True, text=True).stdout.strip()

    # 2. Siapkan Persona Khusus untuk Commit
    sys_prompt = (
        "Kamu adalah Senior AI Engineer. Buat 1 pesan commit berdasarkan daftar file berubah dan git diff ini. "
        "Wajib menangkap perubahan paling penting secara keseluruhan, bukan hanya 1 file yang kebetulan muncul lebih dulu. "
        "WAJIB gunakan format EXACTLY seperti ini: 'Tipe: Pesan komit dengan huruf kapital di awal'. "
        "Contoh valid: 'Feat: Implement auto-commit command', 'Fix: Resolve dependency bug'. "
        "Pilihan Tipe HANYA: Feat, Fix, Chore, Refactor, Docs (Harus diawali huruf Kapital). "
        "JANGAN gunakan scope dalam kurung seperti feat(cli):. "
        "HANYA berikan 1 baris pesan judul (Title) saja. JANGAN berikan deskripsi panjang di bawahnya. "
        "TANPA markdown, TANPA backtick, TANPA penjelasan. "
        "ALWAYS write the final commit message in English, following the Conventional Commits standard, regardless of the language used in the code or git diff."
    )

    # Batasi teks diff agar tidak terlalu panjang (hemat token & waktu), tetapi ambil dua sisi
    # agar konteks tidak bias ke bagian awal saja.
    head = diff_text[:3000]
    tail = diff_text[-2000:] if len(diff_text) > 3000 else ""
    diff_limit = f"{head}\n\n--- DIFF TAIL ---\n{tail}" if tail else head

    commit_prompt = (
        f"Changed Files (name-status):\n{changed_files or '-'}\n\n"
        f"Git Diff:\n{diff_limit}"
    )

    signature = _build_commit_signature(diff_text, changed_files, is_staged)
    commit_cache = _load_commit_cache()
    cached_entry = commit_cache.get(signature)
    cached_message = ""

    if isinstance(cached_entry, dict):
        cached_message = str(cached_entry.get("message", "")).strip()
    elif isinstance(cached_entry, str):
        cached_message = cached_entry.strip()

    if cached_message:
        commit_msg = cached_message
        console.print("[dim]Cache hit: pesan commit diambil dari diff yang sama.[/dim]")
    else:
        heuristic_msg, confidence, heuristic_type = _build_local_commit_message(changed_files, diff_text)

        if confidence >= 0.72:
            commit_msg = heuristic_msg
            console.print(
                f"[dim]Heuristik lokal dipakai ({heuristic_type}, confidence {confidence:.2f}).[/dim]"
            )
        else:
            console.print(
                f"[dim]Heuristik lokal kurang yakin ({heuristic_type}, confidence {confidence:.2f}); fallback ke LLM.[/dim]"
            )
            with console.status("[bold cyan]🧠 Omni sedang menganalisis perubahan kodemu...", spinner="dots"):
                commit_msg = get_engine().generate_response(commit_prompt, system_instruction=sys_prompt).strip()

            if not commit_msg or commit_msg.startswith("❌") or commit_msg.lower().startswith("error"):
                console.print("[dim]LLM fallback gagal, memakai hasil heuristik lokal.[/dim]")
                commit_msg = heuristic_msg

        commit_cache[signature] = {
            "message": commit_msg,
            "mode": "cache" if cached_message else ("heuristic" if confidence >= 0.72 else "llm"),
            "confidence": round(confidence, 2),
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "type": heuristic_type,
        }
        _save_commit_cache(commit_cache)
    
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
        docs_output = get_engine().generate_response(prompt, system_instruction=sys_prompt)

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
        result = get_orchestrator().route_goal(
            "Perform comprehensive security audit",
            code_context,
            force_agent="Security Audit Specialist",
            context_path=path,
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


@app.command()
def study(
    path: str = typer.Argument(
        ".",
        help="Path atau URL materi kuliah (PDF/TXT/MD/Web) yang ingin dianalisis."
    ),
    goal: str = typer.Option(
        "Analyze these study materials and produce a high-yield study guide.",
        "--goal",
        "-g",
        help="Custom objective for the Academic Strategist."
    ),
):
    """Alias akademik: force-route ke Academic Strategist, tampilkan output, dan simpan OMNI_STUDY_GUIDE.md."""
    if not _is_url(path) and not os.path.exists(path):
        console.print(f"[bold red]❌ Path tidak ditemukan: {path}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[dim]Mengumpulkan materi pembelajaran dari: {path}...[/dim]")
    preloaded_context = ""
    if _is_url(path):
        preloaded_context = scrape_url_to_markdown(path)
        if preloaded_context.startswith("[System Error:"):
            console.print(f"[bold red]❌ {preloaded_context}[/bold red]")
            raise typer.Exit(code=1)

    with console.status("[bold cyan]🎓 Academic Strategist sedang menyusun study guide...", spinner="bouncingBar"):
        result = get_orchestrator().route_goal(
            goal,
            preloaded_context,
            force_agent="Academic Strategist",
            context_path=None if _is_url(path) else path,
        )

    if result.get("status") == "error":
        console.print(f"[bold red]❌ Study generation failed: {result.get('error')}[/bold red]")
        raise typer.Exit(code=1)

    markdown_output = str(result.get("markdown", "")).strip()
    if not markdown_output:
        console.print("[bold red]❌ Academic Strategist tidak mengembalikan konten study guide.[/bold red]")
        raise typer.Exit(code=1)

    output_path = os.path.join(os.getcwd(), "OMNI_STUDY_GUIDE.md")
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(markdown_output + "\n")

    console.print()
    console.print(Rule("[bold cyan]  OMNI STUDY GUIDE  [/bold cyan]", style="bold cyan"))
    console.print(Markdown(markdown_output))
    console.print(f"\n[bold green]✅ Study guide saved to: {output_path}[/bold green]\n")


@app.command()
def pitch(
    path: str = typer.Argument(
        ...,
        help="Path atau URL report audit yang akan diubah menjadi sales pitch."
    ),
    goal: str = typer.Option(
        "Generate a high-converting cold email and LinkedIn DM from this audit report.",
        "--goal",
        "-g",
        help="Custom objective for the B2B Sales Closer."
    ),
    company: str = typer.Option(
        "Target Company",
        "--company",
        help="Target company name for personalization."
    ),
    persona: str = typer.Option(
        "cto",
        "--persona",
        help="Target role (cto, ceo, founder, ciso, security-lead)."
    ),
    tone: str = typer.Option(
        "professional",
        "--tone",
        help="Desired tone (professional, assertive, aggressive)."
    ),
):
    """Alias sales: force-route ke B2B Sales Closer, tampilkan pitch, dan simpan OMNI_SALES_PITCH.txt."""
    if not _is_url(path) and not os.path.exists(path):
        console.print(f"[bold red]❌ Path not found: {path}[/bold red]")
        raise typer.Exit(code=1)

    allowed_personas = {"cto", "ceo", "founder", "ciso", "security-lead"}
    normalized_persona = persona.strip().lower()
    if normalized_persona not in allowed_personas:
        console.print(
            "[bold red]❌ Invalid --persona. Use one of: cto, ceo, founder, ciso, security-lead[/bold red]"
        )
        raise typer.Exit(code=1)

    normalized_tone = tone.strip().lower()
    if normalized_tone not in {"professional", "assertive", "aggressive"}:
        console.print("[bold red]❌ Invalid --tone. Use one of: professional, assertive, aggressive[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[dim]Reading security report from: {path}...[/dim]")
    preloaded_context = ""
    if _is_url(path):
        preloaded_context = scrape_url_to_markdown(path)
        if preloaded_context.startswith("[System Error:"):
            console.print(f"[bold red]❌ {preloaded_context}[/bold red]")
            raise typer.Exit(code=1)

    with console.status("[bold cyan]💼 B2B Sales Closer crafting your outreach...", spinner="dots"):
        effective_goal = (
            f"{goal}\n"
            f"Target Company: {company}\n"
            f"Target Persona: {normalized_persona.upper()}\n"
            f"Desired Tone: {normalized_tone}\n"
            "Hard Constraint: Cold Email must be 120-150 words."
        )
        result = get_orchestrator().route_goal(
            effective_goal,
            preloaded_context,
            force_agent="B2B Sales Closer",
            context_path=None if _is_url(path) else path,
        )

    if result.get("status") == "error":
        console.print(f"[bold red]❌ Pitch generation failed: {result.get('error')}[/bold red]")
        raise typer.Exit(code=1)

    pitch_output = str(result.get("pitch", "")).strip()
    if not pitch_output:
        console.print("[bold red]❌ B2B Sales Closer returned empty pitch output.[/bold red]")
        raise typer.Exit(code=1)

    output_path = os.path.join(os.getcwd(), "OMNI_SALES_PITCH.txt")
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(pitch_output + "\n")

    console.print()
    console.print(Rule("[bold cyan]  OMNI SALES PITCH  [/bold cyan]", style="bold cyan"))
    console.print(Markdown(pitch_output))
    console.print(f"\n[bold green]✅ Sales pitch saved to: {output_path}[/bold green]\n")


@app.command()
def invest(
    path: str = typer.Argument(
        ...,
        help="Path or URL to whitepaper/tokenomics/financial report source."
    ),
    goal: str = typer.Option(
        "Analyze this DeFi project and produce a structured investment thesis.",
        "--goal",
        "-g",
        help="Custom objective for the DeFi Financial Analyst."
    ),
):
    """Alias finance: force-route to DeFi Financial Analyst, print markdown, and save OMNI_INVESTMENT_THESIS.md."""
    if not _is_url(path) and not os.path.exists(path):
        console.print(f"[bold red]❌ Path not found: {path}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[dim]Reading finance context from: {path}...[/dim]")
    preloaded_context = ""
    if _is_url(path):
        preloaded_context = scrape_url_to_markdown(path)
        if preloaded_context.startswith("[System Error:"):
            console.print(f"[bold red]❌ {preloaded_context}[/bold red]")
            raise typer.Exit(code=1)

    with console.status("[bold cyan]📊 DeFi Financial Analyst building thesis...", spinner="dots"):
        result = get_orchestrator().route_goal(
            goal,
            preloaded_context,
            force_agent="DeFi Financial Analyst",
            context_path=None if _is_url(path) else path,
        )

    if result.get("status") == "error":
        console.print(f"[bold red]❌ Investment analysis failed: {result.get('error')}[/bold red]")
        raise typer.Exit(code=1)

    thesis_output = str(result.get("markdown", "")).strip()
    if not thesis_output:
        console.print("[bold red]❌ DeFi Financial Analyst returned empty output.[/bold red]")
        raise typer.Exit(code=1)

    output_path = os.path.join(os.getcwd(), "OMNI_INVESTMENT_THESIS.md")
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(thesis_output + "\n")

    console.print()
    console.print(Rule("[bold cyan]  OMNI INVESTMENT THESIS  [/bold cyan]", style="bold cyan"))
    console.print(Markdown(thesis_output))
    console.print(f"\n[bold green]✅ Investment thesis saved to: {output_path}[/bold green]\n")


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