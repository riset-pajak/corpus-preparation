# TASKS.md

**Last Updated:** 2026-04-07

## Phase 1 - Extraction ✅ COMPLETE
- [x] PDF loader (pdfplumber)
- [x] DOCX loader (python-docx)
- [x] Raw text storage (data/processed/)

## Phase 2 - Cleaning ✅ COMPLETE
- [x] Remove artifacts (header/footer noise)
- [x] Normalize whitespace & formatting
- [x] Handle encoding issues

## Phase 3 - Structuring ✅ COMPLETE
- [x] Pasal detection (regex Pasal/ayat)
- [x] Ayat parsing
- [x] Hierarchy mapping (pasal -> ayat -> huruf)
- [x] Fallback paragraph splitting

## Phase 4 - Enrichment ✅ COMPLETE
- [x] Topic tagging (PPh, PPN, PPnBM, PBB, KUP, Bea Materai)
- [x] Regulation type classification (UU, PMK, PP, PER, SE, KEP, INSTR)
- [x] Metadata extraction (nomor, tahun, judul, identifier) - 3 strategi
- [ ] Embedding -- Phase 3 planned

## Phase 5 - Output ✅ COMPLETE
- [x] JSONL export (data/output/corpus.jsonl)
- [x] Markdown export (data/output/corpus.md)
- [x] 29 unit tests passing
- [x] Sample data: PMK-99-PMK-03-2024

## Phase 2 (Integration) -- NEXT
- [ ] Ingest 10-20 regulasi nyata
- [ ] Design DB schema (SQLite/JSON) untuk telegram-bot
- [ ] Implement regulation search di bot
- [ ] Article retrieval handler
- [ ] Summarization engine

## Phase 3 (Advanced) -- PLANNED
- [ ] Scraper JDIH Kemenkeu
- [ ] Scraper peraturan.go.id
- [ ] Vector store integration (ChromaDB/Faiss)
- [ ] Semantic search
