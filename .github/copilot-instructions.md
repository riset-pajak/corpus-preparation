# Copilot Instructions - Corpus Preparation

## Project Overview
Pipeline persiapan corpus regulasi perpajakan Indonesia. Dokumen PDF/DOCX regulasi
diolah (ekstrak, bersihkan, split per pasal, enrich metadata) lalu diekspor ke JSONL
siap untuk embedding dan semantic search.

**CLI:** `riset-pajak` (installable package `corpusprep`)

## Environment Setup

### Python & Virtual Environment
- **Python Version:** 3.11.15 (managed by pyenv)
- **Virtual Environment:** `venv/` folder
- **Activation:** `source venv/bin/activate`
- **Package:** `pip install -e .` -> CLI `riset-pajak`

## Architecture

```
src/corpusprep/
├── cli.py            # CLI commands (click)
├── pipeline.py       # Orchestration: extract -> split -> enrich -> metadata -> doc
├── models.py         # Pydantic models (RegulationDoc, Section, CorpusStats)
├── extractors.py     # PDF (pdfplumber) + DOCX (python-docx) extraction
├── splitter.py       # Pasal/ayat splitting with paragraph fallback
├── enrichment.py     # classify_regulation() + extract_topics()
├── metadata.py       # extract_identifier() + extract_title() - multi-strategy
└── tests/            # 29 unit tests
```

## CLI Commands

| Command | Deskripsi |
|---------|-----------|
| `riset-pajak init` | Inisialisasi folder data/raw, data/processed, data/output, configs |
| `riset-pajak add-pdf <file>` | Tambahkan file PDF/DOCX ke data/raw/ |
| `riset-pajak process` | Jalankan pipeline lengkap |
| `riset-pajak inspect` | Tampilkan statistik corpus |
| `riset-pajak inspect --raw` | Lihat file di data/raw/ |
| `riset-pajak status` | Status ringkas pipeline |

## Metadata Extraction

Ekstraksi identifier regulasi mendukung beberapa format:
- **Slash format:** `NOMOR 99/PMK.03/2024` -> `PMK-99/2024`
- **Tahun format:** `NOMOR 6 TAHUN 1983` -> `UU-6/1983`
- **Filename fallback:** `PMK-68-PMK-03-2024.pdf` -> `PMK-68/2024`

Jenis regulasi: UU, PMK, PP, PER, SE, KEP, INSTR
Topik pajak: PPh, PPN, PPnBM, PBB, KUP, Bea Materai, DJP-Admin

## Testing

```bash
cd corpus-preparation && source venv/bin/activate
pytest tests/ -v
```

## Pipeline

```
1. Extract  -- PDF (pdfplumber) atau DOCX (python-docx)
2. Split    -- Pecah teks per Pasal/ayat (regex -> paragraph fallback)
3. Enrich   -- Klasifikasi jenis regulasi + deteksi topik pajak
4. Metadata -- Ekstraksi nomor, tahun, judul, full_identifier
5. Export   -- JSONL (corpus.jsonl) + Markdown (corpus.md)
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
  "topics": ["PPh", "PPN", "KUP"],
  "sections": [{"number": "Pasal 1", "text": "..."}],
  "source_path": "data/raw/PMK-99-PMK-03-2024.pdf"
}
```

## Development Plan
- [x] Installable package + CLI
- [x] PDF/DOCX extraction
- [x] Pasal/ayat splitting
- [x] Metadata identification
- [x] Tax topic enrichment
- [x] JSONL + Markdown export
- [ ] Web scraping (JDIH Kemenkeu, peraturan.go.id)
- [ ] Vector store integration (ChromaDB/Faiss)
- [ ] Semantic search

## Important Notes
- **Do NOT commit** `venv/`, `data/raw/`, `data/processed/`, `data/output/`
- **Do NOT commit** `.env`
- Selalu aktifkan venv: `source venv/bin/activate`
- Semua path CLI menggunakan `_get_data_dirs()` helper, bukan hardcoded
- Gunakan ruff untuk format: `ruff check . && ruff format .`

---
**Status:** ✅ CLI Installed & Tested (29 unit tests passing)
**Last Updated:** 2026-04-07