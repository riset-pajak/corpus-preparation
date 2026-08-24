# TASKS.md

**Last Updated:** 2026-08-24

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
- [x] Source-specific collectors: JDIH Kemenkeu, peraturan.go.id, MK, DDTC, DJP (`add-pajak-gov-id` untuk pajak.go.id)
- [x] Automatic crawling via `riset-pajak crawl`
- [ ] Embedding -- Phase 3 project-level planned

## Pipeline Stage: Output ✅
- [x] JSONL export (data/output/corpus.jsonl)
- [x] Markdown export (data/output/corpus.md)
- [x] Schema validation via Pydantic models
- [x] SQLite persistence melalui `data.db`
- [x] 32 unit tests (31 passed + 1 skipped: reportlab tidak terpasang untuk PDF dummy)

---

## Phase 2 (Project-level: Intelligence) -- IN PROGRESS

- [x] Ingest regulasi nyata melalui crawling dan pipeline
- [x] Design & implement SQLite database schema (SCHEMA.md)
- [x] Audit kualitas dan deduplikasi hasil crawl
- Implement `db-status`, `db-search`, dan `db-get` untuk metadata, judul, tahun, dan pasal.
- ✅ Sudah diimplementasi (2026-08-24):
  - `riset-pajak db-status` -> statistik lengkap DB (total, per jenis, per status, rentang tahun, topik)
  - `riset-pajak db-search "query" [--year N]` -> pencarian LIKE di title/identifier (+ filter tahun)
  - `riset-pajak db-get <ID> [--text]` -> detail regulasi + daftar pasal (+ full text)
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

## Todo Hari Ini (2026-08-24) -- Langkah 1: Audit data crawl

Baseline terverifikasi: 246 file di `data/raw/` (192 HTML, 54 PDF);
`data.db`: 110 regulasi / 1.360 sections / 161 topics.

- [x] Bersihkan 7 halaman navigasi JDIH yang ikut tersimpan (`atom.xml`, `bantuan`,
      `berita`, `direktori`) lalu tambah skip-pattern di crawler agar tidak terulang
- [x] Review 40 regulasi dengan `reg_type=OTHER`; prioritas:
  - [x] 1 row `full_identifier = UNKNOWN` (hanya punya 1 section) -> status unparsed
  - [x] 3 row identifier berupa judul panjang (termasuk KMK `488/KMK.010/2021`) -> masih OTHER tapi bukan sampah, perbaiki parser
  - [x] 13 row tanpa tahun -> sebagian dari pengumuman nilai kurs (dikarantina), sisanya halaman web detail
- [x] Verifikasi 6 grup duplikat number+tahun; kasus `20/2026`, `PP-20/2026`, `UU-20/2026` adalah 3 regulasi berbeda — bukan duplikat
- [x] Tandai dokumen gagal parsing dengan `status = 'unparsed'` (otomatis di pipeline)
- [x] Catat temuan audit di `memory/2026-08-24.md`
- [x] Kurasi & rename 24+ dokumen bernama "unknown-date" menjadi kanonis (PDF fulltext + abstrak)
- [x] Karantina ~110 halaman navigasi/sampah ke `data/quarantine/`
- [x] Fix bug kelas: Menimbang override identitas dokumen -> potong header pada kata "Menimbang"

Sisa waktu: mulai Langkah 2 (`db-status`) menggunakan fungsi `counts()` yang sudah ada.

## Catatan Status Dokumentasi (2026-08-24)

- SQLite schema aktif hanya `regulations`, `sections`, `topics` + index; FTS5 belum diimplementasikan (Langkah 3).
- `configs/sources.yaml` tidak di-commit (gitignore); jalankan `riset-pajak init` atau buat manual sebelum crawl.
- Parser identifier belum menangani nomor dengan bidang non-numerik (`488/KMK.010/2026`, `34/MK/EF.2/2026`) -- masuk Langkah 1.
