# AGENTS.md

## Project Name
Corpus Preparation - RisetPajak

## Mission
Transform raw tax regulation documents into structured, AI-ready corpus for Indonesian tax regulation intelligence.

## Objectives
- Extract text from PDF/DOCX/HTML regulations
- Clean and normalize data
- Structure into legal hierarchy (pasal, ayat, huruf)
- Enrich with metadata (type, year, topics)
- Persist to SQLite with FTS5 full-text search
- Prepare for AI (embedding, semantic search, compliance reasoning)

## Pipeline Stages
1. **Extract** → PDF/DOCX/HTML to raw text (pdfplumber, python-docx, BeautifulSoup)
2. **Clean** → Remove noise, normalize whitespace, fix encoding, cut at "Menimbang"
3. **Transform** → Split by pasal/ayat using regex; fallback to paragraph blocks
4. **Enrich** → Classify regulation type, extract tax topics, extract identifier (nomor, tahun, judul)
5. **Output** → JSONL, Markdown, SQLite (regulations, sections, topics + FTS5)

## Core Rules
- Never skip validation step (Pydantic models)
- Always preserve original text in `data/raw/`
- Never overwrite raw data
- Always log transformation steps
- If parsing fails → mark as "unparsed", never fabricate content

## Agent Workflow
- Read TASKS.md before starting
- Check SCHEMA.md before modifying data structure
- Log all changes in `memory/YYYY-MM-DD.md`
- Update MEMORY.md only for stable patterns

## Data Principles
- Accuracy > completeness
- Structure > raw text
- Traceability is mandatory (source_path, source_type, raw_text preserved)

## Safety Rules
- Never fabricate regulation content
- If parsing fails → mark as "unparsed"
- Referenced numbers in "Menimbang" section must NOT override document identity
- Always cut header at "Menimbang" before extracting identifier

## Project Structure
```
corpus-preparation/
├── AGENTS.md, MEMORY.md, SOUL.md, TOOLS.md, TASKS.md, SCHEMA.md
├── pyproject.toml
├── data.db                    # SQLite database (committed)
├── src/corpusprep/
│   ├── cli.py                 # Click CLI (riset-pajak command)
│   ├── pipeline.py            # Orchestration: process_file()
│   ├── database.py            # SQLite + FTS5 persistence
│   ├── extractors.py          # PDF/DOCX extraction
│   ├── metadata.py            # Identifier extraction (multi-strategy)
│   ├── enrichment.py          # Type classification + topic tagging
│   ├── splitter.py            # Pasal/ayat splitting
│   ├── models.py              # Pydantic models (RegulationDoc, Section)
│   ├── collectors/            # Web ingestion & crawling
│   │   ├── web.py             # Generic web collector
│   │   ├── crawler.py         # Index crawler with nav filter
│   │   ├── pajak_gov_id.py    # DJP collector (pajak.go.id)
│   │   ├── jdih_kemenkeu.py   # JDIH Kemenkeu collector
│   │   ├── peraturan_gov_id.py # Peraturan.go.id collector
│   │   ├── mahkamah_konstitusi.py # MK collector
│   │   └── ddtc.py            # DDTC collector
│   ├── processors/            # Pipeline step helpers (empty __init__)
│   ├── enrichers/             # Enrichment helpers (empty __init__)
│   └── exporters/             # Output writers (empty __init__)
├── data/
│   ├── raw/                   # Source documents (PDF/DOCX/HTML)
│   ├── processed/             # Extracted text files
│   └── output/                # corpus.jsonl, corpus.md
├── configs/
│   └── sources.yaml           # Crawler config (gitignored, created by init)
├── memory/
│   └── YYYY-MM-DD.md          # Daily logs
├── tests/                     # 67 tests (66 passed, 1 skipped pdfminer dep)
├── scripts/                   # Audit, dummy PDF, DB rebuild utilities
└── web/                       # Flask web app for DB verification/editing
    ├── app.py
    ├── templates/
    └── static/
```

## CLI Commands (riset-pajak)
| Command | Description |
|---------|-------------|
| `init` | Initialize data folders + configs/sources.yaml |
| `add-pdf <files...>` | Add PDF/DOCX/HTML/TXT to data/raw/ |
| `add-url <urls...>` | Download regulation page + PDF attachments |
| `add-pajak-gov-id <urls...>` | Download from pajak.go.id (DJP) |
| `crawl --source <name>` | Crawl regulation catalog (max-pages, max-depth, delay) |
| `process [--format all\|jsonl\|markdown]` | Full pipeline: extract→clean→split→enrich→export+DB |
| `inspect [--raw]` | Corpus statistics / list raw files |
| `status` | Pipeline status summary |
| `db-status` | Full DB stats (counts, by type, by status, year range, topics) |
| `db-search "query" [--year N] [--limit N]` | Search title/identifier (LIKE or FTS5) or by year |
| `db-get <ID> [--text]` | Regulation detail + sections |

## Supported Crawl Sources
- `jdih_kemenkeu` — jdih.kemenkeu.go.id
- `peraturan_gov_id` — peraturan.go.id
- `mahkamah_konstitusi` — mk.go.id
- `ddtc` — perpajakan.ddtc.co.id / DPPajak
- `djp_pemerintah` — pajak.go.id (DJP)

Crawler features: internal-link only, max-pages, max-depth, delay between requests, navigation URL filter (search, berita, direktori, taxonomy/term, atom.xml) to avoid saving non-regulation pages.

## Regulation Types
`UU` (Undang-Undang), `PP` (Peraturan Pemerintah), `PMK` (Peraturan Menteri Keuangan), `PER` (Peraturan Dirjen), `SE` (Surat Edaran), `KEP` (Keputusan Menteri), `INSTR` (Instruksi), `OTHER`

## Tax Topics
`PPh`, `PPN`, `PPnBM`, `PBB`, `BPHTB`, `KUP`, `Bea_Materai`, `DJP_Admin`, `Umum`

## Identifier Extraction Priority
1. **Standard header** — `NOMOR 99/PMK.03/2024` or `NOMOR 6 TAHUN 1983`
2. **Filename** — `PMK-68-PMK-03-2024.pdf`
3. **Preamble pattern** — `<JENIS> NOMOR <n> TAHUN <tahun>` (before "Menimbang")
4. **Bare slash in web HTML** — `969/KMK.04/1983` (only when reg_type unknown)
5. **Fallback regex** — loose patterns

Known limitations:
- Non-numeric bidang not handled: `488/KMK.010/2026`, `34/MK/EF.2/2026`
- Web filenames like `228-PMK.03-2026-02-11.html` need HTML field extraction

## Database Schema (SQLite + FTS5)
Tables:
- `regulations` — metadata + full_text (UUID PK, full_identifier UNIQUE)
- `sections` — pasal/ayat with order, text, raw_text
- `topics` — many-to-many regulation↔topic

FTS5 virtual tables:
- `regulations_fts` — FTS5 on title, full_text
- `sections_fts` — FTS5 on section_number, text

Indexes on: full_identifier, reg_type, year, regulation_id

FTS5 population: `_populate_fts_tables()` uses INSERT OR REPLACE via `rowid` matching.
FTS5 search: `search_by_fts()` does two-step query — MATCH on FTS table then IN lookup on regulations.

## Current Status (2026-08-28)
- 74 regulations, 1,901 sections, 178 topic associations
- Years: 1983–2026
- Types: UU (23), PMK (21), PER (8), KEP (1), PP (2), OTHER (19)
- Active: 73, Unparsed: 1
- FTS5 fully implemented and populated
- Web app (Flask) operational for verification/editing
- Tests: 67 total (66 passed, 1 skipped pdfminer)

## Next Steps (Phase 2)
Completed:
- ✅ Testing — 67 tests covering DB schema, upsert, crawler nav filter, link extraction, retry logic, metadata extraction, enrichment, pipeline flow

Remaining:
1. **Process optimization** — `--only-new`, `--force`, `--db` options
2. **Source metadata** — Add `source_name` field for filtering by origin
3. **Review & release** — Limited re-crawl, compare, update docs, test, push

## Phase 3 (Planned)
- Semantic search (embeddings)
- Vector store (ChromaDB/Faiss)
- Regulation comparison

## Phase 4 (Future)
- Compliance reasoning
- Case-based analysis
- Risk detection
