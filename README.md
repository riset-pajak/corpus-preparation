# CorpusPrep - corpus-preparation

Peralatan persiapan corpus regulasi perpajakan Indonesia.

## Instalasi

```bash
cd corpus-preparation
source venv/bin/activate
pip install -e .
```

## Penggunaan

Setelah instalasi, perintah `riset-pajak` tersedia di CLI dari mana saja.

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

Sumber yang tersedia: `djp_pemerintah`, `jdih_kemenkeu`, `peraturan_gov_id`,
`mahkamah_konstitusi`, dan `ddtc`.

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

## Arsitektur

```
src/corpusprep/
├── collectors/web.py   # Ingest halaman regulasi dan lampiran dari web
├── collectors/crawler.py # Crawling katalog regulasi berbasis sumber
├── database.py          # Persistensi SQLite lokal
├── cli.py              # Perintah CLI (click)
├── pipeline.py         # Orchestration pipeline
├── extractors.py       # PDF/DOCX extraction
├── splitter.py         # Pemecahan per pasal
├── enrichment.py       # Klasifikasi & tag topik
├── metadata.py         # Ekstraksi nomor, tahun, judul, identifier
└── models.py           # Model data (pydantic)
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
├── src/corpusprep/
│   ├── cli.py
│   ├── pipeline.py
│   ├── extractors.py
│   ├── splitter.py
│   ├── enrichment.py
│   ├── metadata.py
│   ├── models.py
│   └── collectors/, enrichers/, exporters/, processors/
│
├── data.db           -- database SQLite contoh/lokal
├── data/
│   ├── raw/          -- dokumen sumber (PDF/DOCX/HTML)
│   ├── processed/    -- teks hasil ekstraksi
│   └── output/       -- corpus.jsonl, corpus.md
│
├── memory/
│   └── 2026-08-18.md
│
├── tests/
├── scripts/
└── README.md
```

## Deteksi Identifier

Sistem mengenali beberapa format standar dokumen regulasi Indonesia:

| Format | Contoh | Hasil |
|--------|--------|-------|
| HEADER (slash) | `NOMOR 99/PMK.03/2024` | `PMK-99/2024` |
| HEADER (tahun) | `NOMOR 6 TAHUN 1983` | `UU-6/1983` |
| FILENAME | `PMK-68-PMK-03-2024.pdf` | `PMK-68/2024` |
| WEB HTML | `PER-8-PJ-2026-07-28.html` | `PER-8/PJ/2026` |

Prioritas ekstraksi:
1. **Scan header teks** -- format standar `NOMOR <angka>/<jenis>.<bidang>/<tahun>` atau `NOMOR <angka> TAHUN <tahun>`
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

Database contoh yang di-commit saat ini berisi 110 regulasi, 1.360 sections,
dan 161 topic associations. Jika JSONL sudah tersedia tetapi database kosong,
jalankan `process` kembali agar database terisi dari sumber di `data/raw/`.

## Testing

```bash
pytest tests/ -v
```

## Next Steps

- [x] SQLite lokal untuk regulations, sections, dan topics
- [x] Persistensi database dari command `process`
- [x] Crawling katalog JDIH Kemenkeu, DJP, DDTC, MK, dan peraturan.go.id
- [ ] Implement regulation search handler di bot
- [ ] Article retrieval handler (`/pasal`, `/cari`)
- [ ] Summarization engine
- [ ] Semantic search (embedding model)
- [ ] Vector store integration (ChromaDB/Faiss)

---
**Status:** CLI, crawling, dan SQLite lokal implemented; 31 unit tests passing
**Terakhir Diupdate:** 2026-08-20
