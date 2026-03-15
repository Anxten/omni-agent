# ⚡ Omni Agent: Local AI Engineering CLI

![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![LLM](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-orange.svg)
![Security](https://img.shields.io/badge/SAST-OWASP%20Top%2010-red.svg)
![Mode](https://img.shields.io/badge/Execution-Local%20First-green.svg)

**Omni Agent** is a local-first AI CLI for high-velocity software engineering workflows.  
It combines **context-aware coding assistance**, **AI commit intelligence**, **automatic documentation generation**, and an **Automated Zero-Cost Local SAST Tool** for practical security reporting.

> *"High-velocity engineering needs automation that is not only fast, but auditable."*

## 🎯 Core Capabilities
- **Context-Aware Assistance** — asks the model using your file/folder context.
- **Interactive AI Chat** — multi-turn terminal chat with retained context.
- **Auto Commit Intelligence** — generates commit messages from `git diff` and can commit/push interactively.
- **Technical Documentation Automation** — generates project documentation into `OMNI_DOCS.md`.
- **Automated Zero-Cost Local SAST** — scans your codebase with OWASP-oriented checks.

## 🛡️ Omni Audit: B2B Security Reporting Layer
`omni audit` is designed as a production-oriented security layer for agencies, consulting teams, and internal engineering squads.

Each audit run automatically generates:
- **`OMNI_AUDIT.json`** — structured findings for pipeline integration and machine-readable processing.
- **`OMNI_SECURITY_REPORT.md`** — formal B2B executive report containing:
  - Executive Summary (Total, Critical, High, Medium, Low)
  - Methodology (Automated SAST Engine aligned with OWASP Top 10)
  - Detailed Findings (severity-sorted with remediation guidance)

## 📦 Installation
### 1) Clone Repository
```bash
git clone https://github.com/Anxten/omni-agent.git
cd omni-agent
```

### 2) Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3) Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Configure API Key
Create a `.env` file in project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Without this key, Omni will fail fast by design.

## 🚀 Quick Start
### Option A: Run Directly as Python Module
```bash
python -m src.cli.main --help
```

### Option B: Use Installed CLI Command
If `omni` is already installed/available in your shell:
```bash
omni --help
```

## 🧩 Command Usage
### Ask with Optional Context
```bash
omni ask "Refactor this function for readability" --file src/
```

### Interactive Chat Session
```bash
omni chat --file src/
```

### Auto Commit From Git Diff
```bash
omni commit
```

### Generate Documentation
```bash
omni doc .
```

### Run Automated SAST Audit
```bash
omni audit .
```

Expected artifacts after audit:
- `OMNI_AUDIT.json`
- `OMNI_SECURITY_REPORT.md`

## 🛠️ Tech Stack
- **Core Runtime:** Python 3.11+
- **LLM Engine:** Google Generative AI (Gemini 2.5 Flash)
- **CLI Framework:** Typer
- **Terminal UI:** Rich
- **Config Management:** python-dotenv

## 🧯 Troubleshooting
- **`GEMINI_API_KEY` missing**: ensure `.env` exists and key is valid.
- **No changes detected in `omni commit`**: run `git status` and ensure files are modified/staged.
- **Audit token/context too large**: run audit on a subfolder, e.g. `omni audit src/`.
- **CLI command not found (`omni`)**: use module mode `python -m src.cli.main ...`.

---

**Developed by Allan Bendatu**  
*Informatics Student*  
*Building the "Truth Engine" for the Capital Markets.*