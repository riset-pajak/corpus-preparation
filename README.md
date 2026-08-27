# CorpusPrep - corpus-preparation

Peralatan persiapan corpus regulasi perpajakan Indonesia.

## Instalasi

```bash
cd corpus-preparation
source venv/bin/activate       # Windows Git Bash: source venv/Scripts/activate
pip install -e .
```

## Penggunaan

Setelah instalasi, perintah `riset-pajak` tersedia di CLI dari mana saja.

| Command | Deskripsi |
|---------|-----------|
| `riset-pajak init` | Inisialisasi struktur folder data |
| `riset-pajak add-pdf <file...>` | Tambahkan PDF/DOCX/HTML/TXT ke data/raw/ |
| `riset-pajak add-url <url...>` | Unduh halaman regulasi + lampiran PDF |
| `riset-pajak add-pajak-gov-id <url...>` | Unduh regulasi dari pajak.go.id |
| `riset-pajak crawl --source <nama>` | Crawl katalog regulasi berbasis sumber |
| `riset-pajak process [--format all\|markdown\|jsonl]` | Jalankan pipeline lengkap |
| `riset-pajak inspect [--raw]` | Statistik corpus / daftar file raw |
| `riset-pajak status` | Status ringkas pipeline |
| `riset-pajak db-status` | Statistik database SQLite (total, jenis, status, topik) |
| `riset-pajak db-search "query" [--year N]` | Pencarian LIKE di judul/identifier |
| `riset-pajak db-get <ID> [--text]` | Detail regulasi + pasal-pasal |

### Inisialisasi

```bash
riset-pajak init
```

Membuat struktur folder `data/raw/`, `data/processed/`, `data/output/`, dan `configs/`. Database SQLite lokal berada di `data.db` pada root proyek dan dibuat/diinisialisasi saat `process` dijalankan.

### Tambah Dokumen

```bash
# Tambahkan PDF/DOCX ke data/raw/
riset-pajak add-pdf PMK-68-PMK-03-2024.pdf
riset-pajak add-pdf file1.pdf file2.docx /path/to/anything.pdf

# Unduh dari URL regulasi dan simpan HTML + lampiran PDF ke data/raw/
riset-pajak add-url https://pajak.go.id/id/peraturan/...
```

### Proses Corpus

```bash
# Ekstrak, bersihkan, split per pasal, enrich metadata,
# export JSONL/Markdown, dan upsert ke SQLite data.db
riset-pajak process
```

### Crawling Otomatis

Crawl katalog regulasi tanpa memasukkan URL dokumen satu per satu. Crawler hanya
mengikuti link internal, memiliki batas halaman/kedalaman, dan memberi jeda antar-request.

```bash
# Gunakan crawl_url dari configs/sources.yaml
riset-pajak crawl --source djp_pemerintah
riset-pajak crawl --source jdih_kemenkeu --max-pages 100 --max-depth 2 --delay 1.0

# Override seed URL bila situs memiliki katalog khusus
riset-pajak crawl --source djp_pemerintah \
  --seed https://pajak.go.id/id/peraturan
```

Sumber yang tersedia: `djp_pemerintah` (pajak.go.id), `jdih_kemenkeu`,
`peraturan_gov_id`, `mahkamah_konstitusi`, dan `ddtc`. Seed URL diambil dari
`configs/sources.yaml` (file ini tidak di-commit; jalankan `init` untuk membuat
contoh config atau salin manual).

### Inspeksi

```bash
# Tampilkan statistik corpus
riset-pajak inspect

# Lihat file yang menunggu diproses
riset-pajak inspect --raw

# Status ringkas pipeline
riset-pajak status
```

## Alur Pipeline

```
1. add-pdf / add-url / crawl -> simpan sumber asli di data/raw/
2. process -> extract -> clean -> split -> enrich -> export JSONL/Markdown + SQLite
3. inspect / status -> lihat statistik dan status pipeline
```

## Output

Setelah `process`, tersedia:
- `data/output/corpus.jsonl` -- satu dokumen per baris, siap untuk embedding/training
- `data/output/corpus.md` -- format markdown untuk human review
- `data/processed/*.txt` -- teks mentah hasil ekstraksi
- `data/raw/*.html|*.pdf|*.docx` -- sumber asli hasil ingest dari web atau file lokal
- `data.db` -- database SQLite lokal untuk regulations, sections, dan topics

`data.db` di root proyek adalah database contoh yang dapat di-commit. Data hasil crawl
atau process berikutnya akan memperbarui database lokal tersebut; artefak mentah tetap
tersimpan di `data/raw/` untuk traceability.

Catatan naming untuk ingest web:
- HTML dan lampiran disimpan dengan pola `nomor-YYYY-MM-DD`
- nomor regulasi asli tetap dipertahankan di metadata, termasuk format seperti `34/MK/EF.2/2026`
- Jika nomor/tanggal tidak ditemukan di halaman, fallback memakai slug URL dan
  tanggal menjadi `unknown-date`

## Arsitektur

```
src/corpusprep/
├── cli.py              # Perintah CLI (click)
├── pipeline.py         # Orchestration pipeline utama
├── database.py          # Persistensi SQLite + FTS5
├── extractors.py       # PDF/DOCX extraction
├── metadata.py         # Ekstraksi nomor, tahun, judul, identifier
├── enrichment.py       # Klasifikasi jenis & tag topik
├── splitter.py         # Pemecahan per pasal/ayat
├── models.py           # Model data (pydantic)
├── collectors/         # Ingest web & crawling
│   ├── web.py          # Ingest halaman regulasi dan lampiran dari web umum
│   ├── crawler.py      # Crawling katalog berbasis sumber
│   ├── pajak_gov_id.py # Collector DJP (pajak.go.id)
│   ├── jdih_kemenkeu.py    # Collector JDIH Kemenkeu
│   ├── peraturan_gov_id.py # Collector peraturan.go.id
│   ├── mahkamah_konstitusi.py  # Collector MK
│   └── ddtc.py             # Collector DDTC
├── processors/         # Pipeline steps helpers (__init__.py kosong)
├── enrichers/          # Enrichment helpers (__init__.py kosong)
└── exporters/          # Output writers (__init__.py kosong)
```

## Struktur Folder & File

```
corpus-preparation/
│
├── AGENTS.md
├── MEMORY.md
├── SOUL.md
├── TOOLS.md
├── TASKS.md
├── SCHEMA.md
├── pyproject.toml
│
├── src/corpusprep/          # Paket utama aplikasi
│   ├── cli.py               # Perintah CLI (click)
│   ├── pipeline.py          # Orchestration pipeline utama
│   ├── database.py          # Persistensi SQLite + FTS5
│   ├── extractors.py        # PDF/DOCX extraction
│   ├── metadata.py          # Ekstraksi nomor, tahun, judul, identifier
│   ├── enrichment.py        # Klasifikasi jenis & tag topik
│   ├── splitter.py          # Pemecahan per pasal/ayat
│   ├── models.py            # Model data (pydantic)
│   ├── collectors/          # Ingest web & crawling
│   │   ├── web.py           # Ingest halaman regulasi umum
│   │   ├── crawler.py       # Crawling katalog berbasis sumber
│   │   ├── pajak_gov_id.py  # Collector DJP (pajak.go.id)
│   │   ├── jdih_kemenkeu.py    # Collector JDIH Kemenkeu
│   │   ├── peraturan_gov_id.py # Collector peraturan.go.id
│   │   ├── mahkamah_konstitusi.py # Collector MK
│   │   └── ddtc.py             # Collector DDTC
│   ├── processors/          # Pipeline steps helpers
│   ├── enrichers/           # Enrichment helpers
│   └── exporters/           # Output writers
│
├── data.db           -- database SQLite contoh/lokal
├── data/
│   ├── raw/          -- dokumen sumber (PDF/DOCX/HTML)
│   ├── processed/    -- teks hasil ekstraksi
│   └── output/       -- corpus.jsonl, corpus.md
│
├── memory/
│   └── YYYY-MM-DD.md       # log harian
│
├── tests/
├── scripts/
│   ├── audit_rename_2026_08_24.py  # Rename dokumen hasil audit
│   ├── make_dummy_pdf.py          # Pembuat PDF dummy untuk testing
│   └── rebuild_db_from_processed.py # Rebuild DB dari data processed
└── README.md
```

## Deteksi Identifier

Sistem mengenali beberapa format standar dokumen regulasi Indonesia:

|| Format | Contoh | Hasil Asli | Hasil Saat Ini (singkat) | Catatan |
||--------|--------|-----------|--------------------------|---------|
|| HEADER (slash) | `NOMOR 99/PMK.03/2024` | `99/PMK.03/2024` | `PMK-99/2024` | Bidang `PMK.03` (penyusun) diabaikan di singkat |
|| HEADER (tahun) | `NOMOR 6 TAHUN 1983` | `6/1983` | `UU-6/1983` | Jenis UU ditambahkan oleh parser (teteapi format asli hanya `6/1983`) |
|| FILENAME | `PMK-68-PMK-03-2024.pdf` | `68/PMK.03/2024` | `PMK-68/2024` | Bidang `PMK.03` diabaikan di singkat |
|| WEB HTML | `228-PMK.03-2026-02-11.html` | `228/PMK.03/2026` | `PMK-228/2017` | Tahun 2026 → 2017 salah (data lama); bidang `PMK.03` hilang |

Catatan: untuk ingest web, nomor kanonis (`PMK-228/2017`) diekstrak dari field
HTML `field--name-field-nomor-dokumen` oleh collector, bukan dari nama file.
Format dengan bidang non-numerik seperti `488/KMK.010/2026` atau `34/MK/EF.2/2026`
belum sepenuhnya tertangani oleh parser filename/header (masuk Langkah 1 audit).

Prioritas ekstraksi:
1. **Scan header teks** -- format standar `NOMOR <angka>/<jenis>.<bidang>/<tahun>` atau `NOMOR <angka> TAHUN <tahun>`; jenis UU/PP/PER juga ditebak dari kata kunci header
2. **Parse nama file** -- pola `<JENIS>-<NOMOR>-<TAHUN>` atau variasi
3. **Fallback** -- regex longgar + bagian-bagian filename

## Struktur Data (JSONL)

Setiap baris di `corpus.jsonl` berisi satu dokumen dengan struktur:

```json
{
  "reg_type": "PMK",
  "number": "99",
  "year": 2024,
  "full_identifier": "PMK-99/2024",
  "title": "KETENTUAN PEMOTONGAN PPh PASAL 21",
  "topics": ["PPh", "PPN", "KUP"],
  "status": "aktif",
  "sections": [
    {"number": "Pasal 1", "text": "..."},
    {"number": "Pasal 2", "text": "..."}
  ],
  "source_path": "data/raw/PMK-99-PMK-03-2024.pdf",
  "source_type": ".pdf"
}
```

## Database SQLite

`process` otomatis melakukan upsert ke `data.db` berdasarkan `full_identifier`.
Database memiliki tabel:

- `regulations` -- metadata dan full text regulasi
- `sections` -- pasal/ayat dengan urutan
- `topics` -- relasi topik pajak

Database contoh yang di-commit saat ini berisi 74 regulasi, 1.901 sections,
dan 178 topic associations. Database berisi 73 regulasi aktif dan 1 unparsed,
merentang tahun 1983–2026 dengan jenis UU (23), PMK (21), PER (8), KEP (1), PP (2), OTHER (19).

Topik paling populer: KUP (42), DJP-Admin (31), PPN (30), PPh (27), PBB (19),
PPnBM (14), BPHTB (10), Bea Materai (5).

Full-text search (FTS5) sudah terimplementasi melalui tabel virtual
`regulations_fts` (title, full_text) dan `sections_fts` (section_number, text).

## Testing

```bash
pytest tests/ -v
```

## Langkah Selesai

Berikut langkah-langkah jangka pendek yang telah diselesaikan:

### ✅ Langkah 1 — Audit data crawl

Audit hasil crawl DJP/JDIH Kemenkeu, bersihkan halaman navigasi sampah,
tandai dokumen gagal parsing sebagai `unparsed`, karsina ~110 halaman non-regulasi,
dan kurasi dokumen bernama "unknown-date".

### ✅ Langkah 2 — Inspeksi dan pencarian database

Implement `db-status`, `db-search`, dan `db-get`:

```bash
riset-pajak db-status          # Statistik lengkap DB (total, jenis, status, topik)
riset-pajak db-search "query"   # Pencarian LIKE di judul/identifier
riset-pajak db-get "PMK-68/2024" # Detail regulasi + pasal-pasal
```

### ✅ Langkah 3 — SQLite FTS5

Full-text search via FTS5 virtual tables untuk judul, full text, nomor pasal,
dan isi pasal. Diprioritaskan sebelum embedding karena cepat, lokal, dan
tidak memerlukan model eksternal.

### Langkah Selanjutnya

### Langkah Jangka Pendek 4 — Test database dan crawler

Tambahan test untuk:

- pembuatan schema SQLite;
- upsert tanpa duplikasi regulasi;
- penyimpanan sections dan topics;
- import JSONL;
- link internal dan batas crawl;
- retry, 403, timeout, dan error per halaman;
- collector DJP dengan HTML/PDF mock.

Target: sekitar 40–45 test.

### Langkah Jangka Pendek 5 — Optimasi process

Opsi baru pada `process`:

```bash
riset-pajak process --only-new   # Hanya proses file belum ada di DB
riset-pajak process --force      # Reprocess semua
riset-pajak process --db data.db # Gunakan path database custom
```

### Langkah Jangka Pendek 6 — Metadata sumber

Simpan `source_name` pada metadata/database untuk setiap sumber ingest:

```text
djp_pemerintah | jdih_kemenkeu | ddtc |
peraturan_gov_id | mahkamah_konstitusi
```

Memungkinkan filter berdasarkan sumber pada inspeksi dan pencarian.

### Langkah Jangka Pendek 7 — Review dan rilis

- Crawl terbatas ulang.
- Bandingkan jumlah/kualitas data sebelum-sesudah.
- Perbarui README, SCHEMA, TASKS.
- Jalankan test suite penuh.
- Commit dan push.

### Belum diprioritaskan

Embedding, ChromaDB/Faiss, summarization, dan compliance reasoning dikerjakan
setelah kualitas data dan pencarian SQLite stabil.

## Next Steps

- [x] SQLite lokal untuk regulations, sections, dan topics
- [x] Persistensi database dari command `process`
- [x] Crawling katalog JDIH Kemenkeu, DJP, DDTC, MK, dan peraturan.go.id
- [x] Audit kualitas dan deduplikasi hasil crawl (Langkah 1)
- [x] Implement `db-status`, `db-search`, dan `db-get` (Langkah 2)
- [x] Implement SQLite FTS5 (Langkah 3)
- [ ] Tambahkan test database dan crawler (Langkah 4) — target 40–45 test
- [ ] Tambahkan mode `process --only-new` dan `--force` (Langkah 5)
- [ ] Tambahkan metadata `source_name` (Langkah 6)
- [ ] Review dan rilis (Langkah 7)
- [ ] Implement regulation search handler di bot
- [ ] Article retrieval handler (`/pasal`, `/cari`)
- [ ] Summarization engine
- [ ] Semantic search (embedding model)
- [ ] Vector store integration (ChromaDB/Faiss)

---
**Status:** CLI, crawling, FTS5 full-text search, dan database upsert fully implemented.
74 regulasi | 1901 sections | 178 topic associations. Tahun: 1983–2026.
FTS5: `regulations_fts` (title, full_text) + `sections_fts` (section_number, text).
Test: 37 passed, 1 skipped (pdfminer dep — expected).

---
**Status Terakhir:** 28 Agustus 2026, 14:30 SE Asia Standard Time (UTC+07:00)
**Terakhir Diupdate:** 2026-08-28
