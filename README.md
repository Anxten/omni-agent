# ⚡ Omni Agent: Local AI Engineering CLI

![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![LLM](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-orange.svg)
![Security](https://img.shields.io/badge/SAST-OWASP%20Top%2010-red.svg)
![Mode](https://img.shields.io/badge/Execution-Local%20First-green.svg)

**Omni Agent** adalah CLI AI-native untuk engineer yang ingin kecepatan eksekusi tinggi langsung dari terminal.  
Fokus utama Omni: **code assistance**, **automated commit intelligence**, **technical docs generation**, dan **Automated Zero-Cost Local SAST** dengan output laporan formal untuk kebutuhan B2B.

> *"High-velocity engineering needs automation that is not only fast, but auditable."*

## 🎯 Core Capabilities
- **Context-Aware Assistance** — membaca file/folder lokal sebagai konteks diskusi kode.
- **Interactive AI Chat** — sesi chat terminal dengan konteks codebase yang persisten.
- **Auto Commit Intelligence** — generate commit message profesional dari perubahan `git diff`.
- **Technical Documentation Automation** — generate dokumen proyek ke `OMNI_DOCS.md`.
- **Automated Zero-Cost Local SAST Tool** — jalankan `omni audit` untuk audit keamanan berbasis OWASP Top 10.

## 🛡️ Omni Audit: B2B Security Reporting Layer
`omni audit` memposisikan Omni sebagai engine audit keamanan aplikasi yang dapat dipakai software agency, internal engineering team, dan technical consultant.

Setiap eksekusi audit sekarang otomatis menghasilkan dua output:
- **`OMNI_AUDIT.json`** → temuan terstruktur untuk pipeline, integrasi internal, atau post-processing.
- **`OMNI_SECURITY_REPORT.md`** → executive report formal berstandar B2B dengan format:
  - Executive Summary (Total, Critical, High, Medium, Low)
  - Methodology (Automated SAST Engine aligned with OWASP Top 10)
  - Detailed Findings (sorted by severity + remediation guidance)

Dengan pendekatan ini, Omni bukan hanya AI assistant, tetapi **security intelligence layer** yang siap dimonetisasi sebagai layanan audit modern.

## 🧩 CLI Commands
- `ask` — Tanya ke AI dengan konteks file/folder opsional.
- `chat` — Sesi interaktif multi-turn di terminal.
- `commit` — Generate pesan commit dari `git diff` + opsi commit/push langsung.
- `doc [path]` — Generate dokumentasi otomatis ke `OMNI_DOCS.md`.
- `audit [path]` — Jalankan automated SAST dan simpan output ke `OMNI_AUDIT.json` + `OMNI_SECURITY_REPORT.md`.

## 🚀 Quick Start
### 1) Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Run Omni CLI
```bash
python -m src.cli.main --help
```

### 3) Run Security Audit
```bash
omni audit .
```

## 🛠️ Tech Stack
- **Core Runtime:** Python 3.11+
- **LLM Engine:** Google Generative AI (Gemini 2.5 Flash)
- **CLI Framework:** Typer
- **Terminal UI:** Rich

---

**Developed by Allan Bendatu**  
*Informatics Student*  
*Building the "Truth Engine" for the Capital Markets.*