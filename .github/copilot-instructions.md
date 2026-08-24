# Copilot Instructions - Corpus Preparation

## Project Overview
Pipeline persiapan corpus regulasi perpajakan Indonesia. Dokumen PDF/DOCX/HTML regulasi
diolah (ekstrak, bersihkan, split per pasal, enrich metadata) lalu diekspor ke JSONL,
Markdown, dan database SQLite lokal (`data.db`) siap untuk pencarian dan embedding.

**CLI:** `riset-pajak` (installable package `corpusprep`)

## Environment Setup

### Python & Virtual Environment
- **Python Version:** 3.11 (lihat `.python-version`)
- **Virtual Environment:** `venv/` folder
- **Activation:** `source venv/bin/activate` (Windows Git Bash: `source venv/Scripts/activate`)
- **Package:** `pip install -e .` -> CLI `riset-pajak`

## Architecture

```
src/corpusprep/
├── cli.py            # CLI commands (click): init, add-pdf, add-url, add-pajak-gov-id, crawl, process, inspect, status
├── pipeline.py       # Orchestration: extract -> split -> enrich -> metadata -> doc
├── models.py         # Pydantic models (RegulationDoc, Section, CorpusStats)
├── extractors.py     # PDF (pdfplumber) + DOCX (python-docx) extraction
├── splitter.py       # Pasal/ayat splitting with paragraph fallback
├── enrichment.py     # classify_regulation() + extract_topics()
├── metadata.py       # extract_identifier() + extract_title() - multi-strategy
├── database.py       # SQLite persistence: upsert regulations/sections/topics ke data.db
└── collectors/       # web.py, crawler.py + collector per sumber (JDIH, DJP, dst.)
```

## CLI Commands

| Command | Deskripsi |
|---------|-----------|
| `riset-pajak init` | Inisialisasi folder data/raw, data/processed, data/output, configs |
| `riset-pajak add-pdf <file>` | Tambahkan file PDF/DOCX/HTML/TXT ke data/raw/ |
| `riset-pajak add-url <url>` | Unduh halaman regulasi web + lampiran PDF ke data/raw/ |
| `riset-pajak add-pajak-gov-id <url>` | Unduh regulasi dari situs resmi DJP (pajak.go.id) |
| `riset-pajak crawl --source <nama>` | Crawl katalog sumber: jdih_kemenkeu, peraturan_gov_id, mahkamah_konstitusi, ddtc, djp_pemerintah |
| `riset-pajak process` | Jalankan pipeline lengkap; hasil di-upsert ke `data.db` |
| `riset-pajak inspect [--raw]` | Statistik corpus / lihat file di data/raw/ |
| `riset-pajak status` | Status ringkas pipeline |

## Metadata Extraction

Ekstraksi identifier regulasi mendukung beberapa format:
- **Slash format:** `NOMOR 99/PMK.03/2024` -> `PMK-99/2024`
- **Tahun format:** `NOMOR 6 TAHUN 1983` -> jenis ditebak dari header (mis. `UU-6/1983`)
- **Filename fallback:** `PMK-68-PMK-03-2024.pdf` -> `PMK-68/2024`
- **Web ingest:** nomor kanonis diambil dari field HTML `field--name-field-nomor-dokumen`
  oleh collector (bukan dari nama file)

Keterbatasan saat ini: nomor dengan bidang non-numerik (`488/KMK.010/2026`,
`34/MK/EF.2/2026`) belum tertangani parser filename/header.

Jenis regulasi: UU, PMK, PP, PER, SE, KEP, INSTR
Topik pajak: PPh, PPN, PPnBM, PBB, BPHTB, KUP, Bea Materai, DJP-Admin, Umum

## Database (SQLite)

- `riset-pajak process` melakukan upsert ke `data.db` berdasarkan `full_identifier`,
  lalu me-replace sections/topics untuk dokumen yang sama.
- Tabel aktif: `regulations`, `sections`, `topics` (+ index identifier/type/year/regulation).
- **FTS5 belum diimplementasikan** -- jangan berasumsi tabel `_fts` ada.
- Detail schema: lihat `SCHEMA.md`.
- Sample DB yang di-commit: 110 regulations, 1.360 sections, 161 topics.

## Testing

```bash
source venv/Scripts/activate   # atau venv/bin/activate di Unix
pytest tests/ -v               # 32 tests saat ini (31 passed + 1 skipped tanpa reportlab)
```

## Pipeline

```
1. Ingest    -- add-pdf / add-url / add-pajak-gov-id / crawl -> data/raw/
2. Extract   -- PDF (pdfplumber), DOCX (python-docx), HTML (BeautifulSoup)
3. Split     -- Pecah teks per Pasal/ayat (regex -> paragraph fallback)
4. Enrich    -- Klasifikasi jenis regulasi + deteksi topik pajak
5. Metadata  -- Ekstraksi nomor, tahun, judul, full_identifier
6. Export    -- JSONL (corpus.jsonl) + Markdown (corpus.md) + upsert SQLite (data.db)
```

## Output Structure

Setiap dokumen di `corpus.jsonl`:
```json
{
  "reg_type": "PMK",
  "number": "99",
  "year": 2024,
  "full_identifier": "PMK-99/2024",
  "title": "KETENTUAN PEMOTONGAN PPh PASAL 21",
  "topics": ["PPh"],
  "sections": [{"number": "Pasal 1", "text": "..."}],
  "source_path": "data/raw/PMK-99-PMK-03-2024.pdf"
}
```

## Development Plan

Sinkron dengan `TASKS.md` (Phase 2 sedang berjalan):
- [x] Installable package + CLI
- [x] PDF/DOCX/HTML extraction
- [x] Pasal/ayat splitting
- [x] Metadata identification
- [x] Tax topic enrichment
- [x] JSONL + Markdown export
- [x] Web ingest + crawler multi-sumber
- [x] SQLite persistence dari `process`
- [ ] Audit kualitas & deduplikasi hasil crawl
- [ ] `db-status`, `db-search`, `db-get`
- [ ] SQLite FTS5
- [ ] Test database & crawler (target ~40–45 test)
- [ ] Vector store integration (ChromaDB/Faiss) -- Phase 3
- [ ] Semantic search -- Phase 3

## Important Notes
- **Do NOT commit** `venv/`, `data/`, `data.db` sudah di-commit sebagai sample --
  hati-hati saat menjalankan `process` agar tidak menimpa sample secara tidak sengaja.
- **Do NOT commit** `.env`
- `configs/sources.yaml` di-gitignore; dibuat oleh `riset-pajak init` atau salin manual.
- Selalu aktifkan venv sebelum pytest/CLI.
- Semua path CLI menggunakan `_get_data_dirs()` helper, bukan hardcoded
- Gunakan ruff untuk format: `ruff check . && ruff format .`
- Dokumen yang gagal diparsing ditandai `unparsed`; jangan pernah mengarang isi regulasi.

---
**Status:** CLI + crawl + SQLite implemented; 32 tests (31 passed + 1 skipped)
**Last Updated:** 2026-08-24
