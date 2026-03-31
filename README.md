# Omni Agent

![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![LLM](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-orange.svg)
![Security](https://img.shields.io/badge/SAST-OWASP%20Top%2010-red.svg)

Omni Agent is a local-first multi-agent CLI platform.
It routes your goal to specialist agents for security, documentation, coding, study, sales, and DeFi investment analysis.

## Quick Card (1-Minute Start)
1. Setup once:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Verify CLI:
```bash
python -m src.cli.main --help
```

3. See available agents:
```bash
omni agents
```

4. Use the most common commands:
```bash
omni execute "Analyze this repository" --context .
omni audit .
omni study ./study-materials
omni pitch ./OMNI_SECURITY_REPORT.md --company "Target Protocol" --persona ceo --tone assertive
omni invest https://docs.uniswap.org/contracts/v3/overview
```

5. Check generated outputs:
1. OMNI_AUDIT.json
2. OMNI_SECURITY_REPORT.md
3. OMNI_STUDY_GUIDE.md
4. OMNI_SALES_PITCH.txt
5. OMNI_INVESTMENT_THESIS.md

## What You Can Do
1. Run orchestrated AI tasks from local files or live URLs.
2. Generate security audits and executive reports.
3. Create study guides from PDF, markdown, text, and web pages.
4. Produce B2B outreach copy from technical reports.
5. Build DeFi investment theses from whitepapers and tokenomics docs.
6. Generate commit messages from Git changes.

## Installation
1. Clone repository.
```bash
git clone https://github.com/Anxten/omni-agent.git
cd omni-agent
```

2. Create and activate virtual environment.
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies.
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Set API key.
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## Quick Start
Use module mode:
```bash
python -m src.cli.main --help
```

If installed as shell command:
```bash
omni --help
```

## Agent Roster
Use this to inspect all available specialists:
```bash
omni agents
omni agents --name "Security Audit Specialist"
```

Current specialist agents:
1. Security Audit Specialist
2. Documentation Specialist
3. Code Generator Specialist
4. Academic Strategist
5. B2B Sales Closer
6. DeFi Financial Analyst

## Command Reference

### 1) agents
Purpose: list agents or show one agent detail.
```bash
omni agents
omni agents --name "Academic Strategist"
```
Options:
1. --name, -n

### 2) execute
Purpose: generic orchestrated execution with auto-routing.
```bash
omni execute "Analyze this repository" --context .
omni execute "Summarize risks" --context https://example.com/report
omni execute "Find issues" --context src --agent "Security Audit Specialist"
```
Options:
1. --context, -c
2. --agent, -a
3. --output, -o

### 3) ask
Purpose: single-turn prompt with optional local file or folder context.
```bash
omni ask "Refactor this function" --file src/
```
Options:
1. --sys, -s
2. --file, -f

### 4) chat
Purpose: multi-turn interactive session with optional starting context.
```bash
omni chat --file src/
```
Options:
1. --sys, -s
2. --file, -f

### 5) audit
Purpose: security SAST run and report generation.
```bash
omni audit .
omni audit src/
```
Output files:
1. OMNI_AUDIT.json
2. OMNI_SECURITY_REPORT.md

### 6) doc
Purpose: project documentation generation.
```bash
omni doc .
```
Output file:
1. OMNI_DOCS.md

### 7) study
Purpose: generate high-yield study guide from local path or URL.
```bash
omni study ./study-materials
omni study https://example.com/course-note --goal "Focus on exam-critical topics"
```
Options:
1. --goal, -g
Output file:
1. OMNI_STUDY_GUIDE.md

### 8) pitch
Purpose: generate outreach copy from security report input.
```bash
omni pitch ./OMNI_SECURITY_REPORT.md
omni pitch https://rekt.news/euler-rekt/ --company "Acme Protocol" --persona cto --tone assertive
```
Options:
1. --goal, -g
2. --company
3. --persona
4. --tone

Valid persona values:
1. cto
2. ceo
3. founder
4. ciso
5. security-lead

Valid tone values:
1. professional
2. assertive
3. aggressive

Output file:
1. OMNI_SALES_PITCH.txt

### 9) invest
Purpose: generate DeFi investment thesis from local docs or URL.
```bash
omni invest ./docs/tokenomics
omni invest https://docs.uniswap.org/contracts/v3/overview --goal "Focus on audit viability and risk"
```
Options:
1. --goal, -g
Output file:
1. OMNI_INVESTMENT_THESIS.md

### 10) commit
Purpose: generate commit message from git diff and optionally commit/push.
```bash
omni commit
```

## URL and Local Path Support
URL-native ingestion is enabled for:
1. execute (via --context)
2. study
3. pitch
4. invest

All other commands keep their original local-context behavior.

## Practical Workflows

### Workflow A: Security Audit to Sales Outreach
```bash
omni audit .
omni pitch ./OMNI_SECURITY_REPORT.md --company "Target Protocol" --persona ceo --tone assertive
```

### Workflow B: Whitepaper to Investment Thesis
```bash
omni invest https://example.com/whitepaper
```

### Workflow C: Study Pack to Exam Notes
```bash
omni study ./materi_tes
```

### Workflow D: Generic Orchestrated Analysis
```bash
omni execute "Analyze architecture risks and recommend fixes" --context .
```

## Generated Files Summary
1. OMNI_AUDIT.json
2. OMNI_SECURITY_REPORT.md
3. OMNI_DOCS.md
4. OMNI_STUDY_GUIDE.md
5. OMNI_SALES_PITCH.txt
6. OMNI_INVESTMENT_THESIS.md

## Troubleshooting
1. Missing API key: set GEMINI_API_KEY in .env.
2. Command not found: use module mode python -m src.cli.main ...
3. URL fetch failed: check internet, SSL, and URL accessibility.
4. Empty output: retry with a clearer goal and a more focused input source.
5. Large project audit fails: run on subfolder first, for example omni audit src/

## Developer Extension
To build new specialist agents, see AGENT_DEVELOPMENT_GUIDE.md.