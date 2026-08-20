# TASKS.md

**Last Updated:** 2026-08-20

> Semua item di bawah ini adalah sub-tahapan dari **Phase 1 (Foundation)** di level proyek.
> Pipeline stages: extract -> clean -> structure -> enrich -> output

## Pipeline Stage: Extraction ✅
- [x] PDF loader (pdfplumber)
- [x] DOCX loader (python-docx)
- [x] HTML loader untuk ingest web
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
- [x] Web source ingest via `riset-pajak add-url`
- [x] Source-specific collectors: JDIH Kemenkeu, peraturan.go.id, MK, DDTC, DJP
- [x] Automatic crawling via `riset-pajak crawl`
- [ ] Embedding -- Phase 3 project-level planned

## Pipeline Stage: Output ✅
- [x] JSONL export (data/output/corpus.jsonl)
- [x] Markdown export (data/output/corpus.md)
- [x] Schema validation via Pydantic models
- [x] SQLite persistence melalui `data.db`
- [x] 31 unit tests passing

---

## Phase 2 (Project-level: Intelligence) -- IN PROGRESS

- [x] Ingest regulasi nyata melalui crawling dan pipeline
- [x] Design & implement SQLite database schema (SCHEMA.md)
- [ ] Audit kualitas dan deduplikasi hasil crawl
- [ ] Implement `db-status`, `db-search`, dan `db-get`
- [ ] Implement SQLite FTS5
- [ ] Tambahkan test database dan crawler
- [ ] Tambahkan mode `process --only-new` dan `--force`
- [ ] Tambahkan metadata `source_name`
- [ ] Implement regulation search handler di bot
- [ ] Article retrieval handler (/pasal, /cari)
- [ ] Summarization engine

### Urutan Langkah Jangka Pendek

1. **Langkah 1 — Audit data crawl:** audit hasil DJP/JDIH, tandai halaman non-regulasi, dokumen `unparsed`, dan duplikasi `full_identifier`.
2. **Langkah 2 — Inspeksi database:** buat `db-status`, `db-search`, dan `db-get` untuk metadata, judul, tahun, dan pasal.
3. **Langkah 3 — FTS5:** tambahkan full-text search untuk judul, full text, nomor pasal, dan isi pasal.
4. **Langkah 4 — Testing:** tambah test schema, upsert, sections/topics, import JSONL, crawler limits, retry, 403, timeout, dan collector DJP.
5. **Langkah 5 — Optimasi process:** tambahkan `process --only-new`, `--force`, dan opsi `--db`.
6. **Langkah 6 — Metadata sumber:** simpan `source_name` untuk DJP, JDIH Kemenkeu, DDTC, peraturan.go.id, dan MK.
7. **Langkah 7 — Review dan rilis:** crawl terbatas, bandingkan hasil, update dokumentasi, jalankan test, commit, dan push.

Embedding, ChromaDB/Faiss, summarization, dan compliance reasoning ditunda sampai kualitas data dan pencarian SQLite stabil.

## Phase 3 (Project-level: Advanced Research) -- PLANNED

- [x] Scraper otomatis JDIH Kemenkeu, peraturan.go.id, MK, DDTC, dan DJP
- [x] Automatic crawl command dengan batas halaman/kedalaman
- [ ] Semantic search (embedding model)
- [ ] Vector store integration (ChromaDB/Faiss)
- [ ] Regulation comparison

## Phase 4 (Project-level: Expert System) -- FUTURE

- [ ] Compliance reasoning
- [ ] Case-based analysis
- [ ] Risk detection

## Validation Target

Target setelah minggu depan: sekitar 40–45 test dengan database dan crawler tervalidasi.
