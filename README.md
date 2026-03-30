# Omni Agent

![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![LLM](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-orange.svg)
![Security](https://img.shields.io/badge/SAST-OWASP%20Top%2010-red.svg)

Omni Agent is a local-first AI CLI with an orchestrator that routes tasks to specialist agents.

## Core Features
- Multi-agent orchestration (`omni agents`, `omni execute`)
- Context-aware coding assistant (`omni ask`, `omni chat`)
- Automated security audit (`omni audit`)
- Academic study guide generation from PDFs/text (`omni study`)
- Commit message generation from git diff (`omni commit`)

## Installation
1. Clone repository
```bash
git clone https://github.com/Anxten/omni-agent.git
cd omni-agent
```

2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Create `.env`
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Quick Start
Use module mode:
```bash
python -m src.cli.main --help
```

Or CLI mode (if installed in your shell):
```bash
omni --help
```

## Command Usage
List commands:
```bash
omni --help
```

List available specialist agents:
```bash
omni agents
```

General task execution with auto-routing:
```bash
omni execute "Analyze this repository and suggest improvements" --context .
```

Academic study mode (reads PDFs/texts, outputs terminal + file):
```bash
omni study ./study-materials
```

Ask with optional context:
```bash
omni ask "Refactor this function for readability" --file src/
```

Interactive chat session:
```bash
omni chat --file src/
```

Generate commit message from git diff:
```bash
omni commit
```

Generate project documentation:
```bash
omni doc .
```

Run SAST audit:
```bash
omni audit .
```

## Generated Output Files
- `OMNI_AUDIT.json`
- `OMNI_SECURITY_REPORT.md`
- `OMNI_DOCS.md`
- `OMNI_STUDY_GUIDE.md`

## Optional Developer Reference
If you want to create custom specialist agents, read:
- `AGENT_DEVELOPMENT_GUIDE.md`

## Troubleshooting
- Missing API key: make sure `.env` exists and `GEMINI_API_KEY` is set.
- `omni` command not found: use `python -m src.cli.main ...`.
- Audit context too large: audit a smaller folder, for example `omni audit src/`.