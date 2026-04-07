# TASKS.md

**Last Updated:** 2026-04-08

> Semua item di bawah ini adalah sub-tahapan dari **Phase 1 (Foundation)** di level proyek.
> Pipeline stages: extract -> clean -> structure -> enrich -> output

## Pipeline Stage: Extraction ✅
- [x] PDF loader (pdfplumber)
- [x] DOCX loader (python-docx)
- [x] Raw text storage (data/processed/)

## Pipeline Stage: Cleaning ✅
- [x] Remove artifacts (header/footer noise)
- [x] Normalize whitespace & formatting
- [x] Handle encoding issues

## Pipeline Stage: Structuring ✅
- [x] Pasal detection (regex Pasal/ayat)
- [x] Ayat parsing
- [x] Hierarchy mapping (pasal -> ayat -> huruf)
- [x] Fallback paragraph splitting

## Pipeline Stage: Enrichment ✅
- [x] Topic tagging (PPh, PPN, PPnBM, PBB, KUP, Bea Materai)
- [x] Regulation type classification (UU, PMK, PP, PER, SE, KEP, INSTR)
- [x] Metadata extraction (nomor, tahun, judul, identifier) - 3 strategi
- [ ] Embedding -- Phase 3 project-level planned

## Pipeline Stage: Output ✅
- [x] JSONL export (data/output/corpus.jsonl)
- [x] Markdown export (data/output/corpus.md)
- [x] Schema validation via Pydantic models
- [x] 29 unit tests passing

---

## Phase 2 (Project-level: Intelligence) -- NEXT

- [ ] Ingest 10-20 regulasi nyata via pipeline
- [ ] Design & implement SQLite database schema (SCHEMA.md)
- [ ] Implement regulation search handler di bot
- [ ] Article retrieval handler (/pasal, /cari)
- [ ] Summarization engine

## Phase 3 (Project-level: Advanced Research) -- PLANNED

- [ ] Scraper otomatis JDIH Kemenkeu / peraturan.go.id
- [ ] Semantic search (embedding model)
- [ ] Vector store integration (ChromaDB/Faiss)
- [ ] Regulation comparison

## Phase 4 (Project-level: Expert System) -- FUTURE

- [ ] Compliance reasoning
- [ ] Case-based analysis
- [ ] Risk detection
