# MEMORY.md

## Project Identity
Corpus pipeline for Indonesian tax regulation intelligence system (RisetPajak).

## Key Decisions
- Use SQLite `data.db` as the local canonical database
- Keep structured JSONL and Markdown as audit/review exports
- Use pasal-level granularity for sections
- Preserve raw + processed data for traceability
- Preserve original web HTML alongside downloaded PDF attachments
- Use filename pattern `nomor-YYYY-MM-DD` for web ingest artifacts
- Crawl sources with internal-link, max-pages, max-depth, and delay safeguards
- Navigation pages (search, berita, direktori, taxonomy/term, atom.xml) are filtered during crawl
- FTS5 implemented for full-text search on regulations and sections
- Web app (Flask) provides verification and editing interface

## Current Implementation
- `riset-pajak process` upserts regulations, sections, and topics into `data.db`
- `riset-pajak crawl --source <name>` crawls configured source indexes with nav filtering
- Supported sources: JDIH Kemenkeu, peraturan.go.id, Mahkamah Konstitusi, DDTC, DJP
- Database committed with 74 regulations, 1,901 sections, 178 topics (as of 2026-08-28)
- Database code lives in `src/corpusprep/database.py`
- SQLite schema: `regulations` + `sections` + `topics` + indexes + FTS5 virtual tables
- `configs/sources.yaml` is gitignored; `riset-pajak init` creates default config
- CLI inspection commands: `db-status`, `db-search`, `db-get`
- Web app at `http://127.0.0.1:5000` with dashboard, search, detail, edit pages
- Identifier parser handles header, filename, preamble, and bare-slash web formats
- "Menimbang" cutoff prevents referenced regulation numbers from overriding document identity
- FTS5 uses INSERT OR REPLACE via rowid matching for robust population
- FTS5 search uses two-step approach: MATCH on FTS table then IN lookup on regulations

## Lessons Learned
- PDF extraction is unreliable; manual correction layer may be needed
- Legal documents require hierarchical parsing (pasal → ayat → huruf)
- Cleaning step is critical (whitespace, page numbers, header/footer noise)
- Web pages expose useful metadata in HTML fields (nomor, tanggal), not just visible text
- Crawler navigation filter prevents ~110 non-regulation pages from being saved
- Duplicate `full_identifier` with different `reg_type` are distinct regulations (e.g., `20/2026` as UU, PP, PMK)
- `_populate_fts_tables()` DELETE can fail in some environments; use INSERT OR REPLACE instead
- `search_by_fts()` cannot JOIN FTS table directly with regulations via rowid; must do two-step query

## Future Direction
- Add semantic embedding (sentence-transformers + ChromaDB/Faiss)
- Build regulation knowledge graph (cross-references, replaced_by chains)
- Implement regulation comparison engine
- Compliance reasoning for case-based analysis
- Risk detection from regulation changes

## Audit History
- 2026-08-24: Cleaned 7 JDIH nav pages, reviewed 40 OTHER-type regulations, quarantined ~110 nav pages, fixed Menimbang override bug, renamed 24+ unknown-date documents
- 2026-08-28: Fixed FTS5 `_populate_fts_tables()` to use INSERT OR REPLACE; fixed `search_by_fts()` to use two-step query; added 30 new tests (now 67 total, 66 passed)
