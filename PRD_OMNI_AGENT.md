# Product Requirement Document (PRD): Project Omni - Local Agentic CLI

## 1. Visi Produk
Project Omni adalah jembatan otonom (Zero-Cost Local Agent) yang menghubungkan *local codebase* dengan *Google Gemini 1.5 Flash API*. Tujuannya adalah mengeliminasi proses *copy-paste* manual ke antarmuka web, memungkinkan *developer* untuk melakukan "vibe coding" langsung dari terminal Linux/VSCode dengan konteks repositori yang utuh.

## 2. Peran & Persona AI
* **Role Utama:** Senior Python & AI Engineer.
* **Karakteristik:** Pragmatis, berorientasi pada efisiensi eksekusi, penulisan kode yang *clean* (Clean Architecture), dan selalu menyertakan *type hinting* serta *docstrings*.
* **Domain Expertise:** Data Engineering, Financial/Quant Sentiment Analysis (menggunakan Pandas, Scikit-learn, Hugging Face), dan Web Automation/Scraping.

## 3. Fitur Utama (MVP - Minimum Viable Product)
1.  **Context Injector:** Mampu membaca struktur direktori dan isi file tertentu dalam *project* untuk dijadikan konteks.
2.  **CLI Interface:** Interaksi berbasis terminal yang elegan (menggunakan library `Typer` dan `Rich`).
3.  **Smart Code Generator:** Mengirim *prompt* + konteks lokal ke Gemini API, lalu mengembalikan respons kode langsung ke terminal.
4.  **Auto-Commit Message Generator:** Membaca `git diff` dan menghasilkan pesan komit menggunakan konvensi *Conventional Commits*.

## 4. Tech Stack & Dependensi
* **Bahasa:** Python 3.11+
* **Otak AI:** `google-generativeai` (Gemini 1.5 Flash API - Free Tier)
* **CLI Framework:** `typer` 
* **Terminal UI:** `rich`
* **Environment:** `python-dotenv`

## 5. Arsitektur Folder (Modular Clean Architecture)
```text
omni-agent/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py         # Load .env variables
│   │   └── llm_client.py     # Setup Gemini API connection
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py           # Typer CLI entry point
│   └── utils/
│       ├── __init__.py
│       └── file_reader.py    # Logika membaca context/file lokal
├── .env.example
├── .gitignore
├── requirements.txt
└── PRD_OMNI_AGENT.md
```

## 6. Standar Penulisan Kode (Code Guidelines)
1.  **Kerapian:** Gunakan PEP 8 dan wajib menggunakan *Type Hinting*.
2.  **Keamanan:** Tidak ada API Key yang di-*hardcode*. Gunakan `.env`.
3.  **Dokumentasi:** *Docstring* wajib untuk setiap fungsi utama.