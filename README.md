# CorpusPrep -- corpus-preparation

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

Membuat struktur folder `data/raw/`, `data/processed/`, `data/output/`, dan `configs/`.

### Tambah Dokumen

```bash
# Tambahkan PDF/DOCX ke data/raw/
riset-pajak add-pdf PMK-68-PMK-03-2024.pdf
riset-pajak add-pdf file1.pdf file2.docx /path/to/anything.pdf
```

### Proses Corpus

```bash
# Ekstrak, bersihkan, split per pasal, enrich metadata, export JSONL
riset-pajak process
```

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
1. add-pdf  -->  taruh file di data/raw/
2. process  -->  extract --> clean --> split --> enrich --> export
3. inspect  -->  lihat statistik corpus
```

## Output

Setelah `process`, tersedia:
- `data/output/corpus.jsonl` -- satu dokumen per baris, siap untuk embedding/training
- `data/output/corpus.md`    -- format markdown untuk human review
- `data/processed/*.txt`     -- teks mentah hasil ekstraksi

## Arsitektur

```
src/corpusprep/
├── cli.py            # Perintah CLI (click)
├── pipeline.py       # Orchestration pipeline
├── extractors.py     # PDF/DOCX extraction
├── splitter.py       # Pemecahan per pasal
├── enrichment.py     # Klasifikasi & tag topik
├── metadata.py       # Ekstraksi nomor, tahun, judul, identifier
└── models.py         # Model data (pydantic)
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
│   └── enrichers/, exporters/, processors/
│
├── data/
│   ├── raw/          -- dokumen sumber (PDF/DOCX)
│   ├── processed/    -- teks hasil ekstraksi
│   └── output/       -- corpus.jsonl, corpus.md
│
├── memory/
│   └── 2026-04-07.md
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

## Testing

```bash
pytest tests/ -v
```

## Next Steps

- [ ] Scraper otomatis JDIH Kemenkeu
- [ ] Scraper peraturan.go.id
- [ ] Vector store integration (ChromaDB)
- [ ] Semantic search
- [ ] Integration dengan telegram-bot

---
**Status:** ✅ CLI Installed & Tested (29 unit tests passing)
**Terakhir Diupdate:** 2026-04-07
