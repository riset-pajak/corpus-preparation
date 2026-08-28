# TASKS.md

**Last Updated:** 2026-08-28

> Semua item di bawah ini adalah sub-tahapan dari **Phase 1 (Foundation)** di level proyek.
> Pipeline stages: extract -> clean -> structure -> enrich -> output

## Pipeline Stage: Extraction ✅
- [x] PDF loader (pdfplumber)
- [x] DOCX loader (python-docx)
- [x] HTML loader untuk ingest web (BeautifulSoup)
- [x] Raw text storage (data/processed/)

## Pipeline Stage: Cleaning ✅
- [x] Remove artifacts (header/footer noise, page numbers)
- [x] Normalize whitespace & formatting
- [x] Handle encoding issues
- [x] Cut at "Menimbang" to prevent referenced number override

## Pipeline Stage: Structuring ✅
- [x] Pasal detection (regex Pasal/ayat)
- [x] Ayat parsing
- [x] Hierarchy mapping (pasal -> ayat -> huruf)
- [x] Fallback paragraph splitting

## Pipeline Stage: Enrichment ✅
- [x] Topic tagging (PPh, PPN, PPnBM, PBB, KUP, Bea Materai, DJP-Admin, Umum)
- [x] Regulation type classification (UU, PMK, PP, PER, SE, KEP, INSTR, OTHER)
- [x] Metadata extraction (nomor, tahun, judul, identifier) - multi-strategy with bare-slash web
- [x] Web source ingest via `riset-pajak add-url`
- [x] Source-specific collectors: JDIH Kemenkeu, peraturan.go.id, MK, DDTC, DJP (`add-pajak-gov-id`)
- [x] Automatic crawling via `riset-pajak crawl` with nav filter
- [ ] Embedding -- Phase 3 project-level planned

## Pipeline Stage: Output ✅
- [x] JSONL export (data/output/corpus.jsonl)
- [x] Markdown export (data/output/corpus.md)
- [x] Schema validation via Pydantic models
- [x] SQLite persistence melalui `data.db`
- [x] FTS5 full-text search (regulations_fts, sections_fts)
- [x] 67 unit tests (66 passed + 1 skipped: pdfminer dep — expected)
- [x] Web app verifikasi & editing database (`app.py`, Flask) -- DONE (2026-08-28)

---

## Phase 2 (Project-level: Intelligence) -- IN PROGRESS

- [x] Ingest regulasi nyata melalui crawling dan pipeline
- [x] Design & implement SQLite database schema (SCHEMA.md)
- [x] Audit kualitas dan deduplikasi hasil crawl
- [x] Implement `db-status`, `db-search`, dan `db-get` untuk metadata, judul, tahun, dan pasal -- DONE (2026-08-24)
  - `riset-pajak db-status` -> statistik lengkap DB (total, jenis, status, rentang tahun, topik)
  - `riset-pajak db-search "query"` -> pencarian LIKE di title/identifier (+ filter tahun via `--year`)
  - `riset-pajak db-get <ID>` -> detail regulasi + daftar pasal (+ full text via `--text`)
- [x] Implement SQLite FTS5 -- DONE (2026-08-27)
  - Uses INSERT OR REPLACE for robust population
  - Two-step search: MATCH on FTS table then IN lookup on regulations
- [x] Web app verifikasi & editing database (`app.py`, Flask) -- DONE (2026-08-28)
  - Dashboard dengan statistik total
  - Daftar regulasi dengan FTS5 search, filter, pagination
  - Detail regulasi, edit metadata, edit section/pasal, tambah/hapus topik
- [ ] Tambahkan mode `process --only-new` dan `--force`
- [ ] Tambahkan metadata `source_name`
- [ ] Implement regulation search handler di bot
- [ ] Article retrieval handler (/pasal, /cari)
- [ ] Summarization engine

### Urutan Langkah Jangka Pendek

1. **✅ Langkah 1 — Audit data crawl:** selesai -- hasil DJP/JDIH diaudit, halaman non-regasi dibersihkan, dokumen unparsed ditandai, dan duplikasi `full_identifier` diperiksa.
2. **✅ Langkah 2 — Inspeksi database:** selesai -- `riset-pajak db-status`, `db-search`, dan `db-get` tersedia untuk metadata, judul, tahun, dan pasal.
3. **✅ Langkah 3 — FTS5:** selesai -- full-text search via FTS5 virtual tables untuk judul, full text, nomor pasal, dan isi pasal.
4. **✅ Langkah 4 — Testing:** selesai -- 67 tests written and passing (66 passed, 1 skipped pdfminer):
   - `test_database.py`: 20 tests covering schema, upsert, sections, topics, import_jsonl, counts, status, search_by_title, search_by_year, get_regulation, FTS5
   - `test_crawler_detailed.py`: 11 tests covering nav filter, link extraction, depth limit, retry logic, internal URL detection, regulation link detection
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

✅ **Ditargetkan 40–45 test** — saat ini **67 passed**, 1 skipped (pdfminer). Target terlampaui.

## Next Steps Checklist

- [ ] **Langkah 5:** Implement `--only-new` (skip existing full_identifier), `--force` (reprocess all), `--db <path>`
- [ ] **Langkah 6:** Tambah kolom `source_name` ke tabel regulations dan propagasi ke JSONL/model
- [ ] **Langkah 7:** Crawl terbatas 1 sumber, bandingkan before/after, update README/SCHEMA/TASKS, `pytest`, commit, push
