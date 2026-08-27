# SCHEMA.md -- Corpus & Database Schema

**Last Updated:** 2026-08-28
**Status:** SQLite lokal + FTS5 implemented; JSONL/Markdown tersedia sebagai export audit dan review

---

## 1. Data Model (Pydantic -- Current)

Sumber kebenaran: `src/corpusprep/models.py`

### RegulationType
`UU | PP | PER | PMK | SE | KEP | INSTR | OTHER`

### TaxTopic
`PPh | PPN | PPnBM | PBB | BPHTB | KUP | Bea_Materai | DJP_Admin | Umum`

### Section
| Field | Type | Contoh |
|-------|------|--------|
| number | str | `"Pasal 1"`, `"Ayat (1)"`, `"Lampiran"` |
| title | str | `""` (optional) |
| text | str | Isi pasal yang sudah dibersihkan |
| raw_text | str | Teks asli dari PDF (sebelum full cleaning) |

### RegulationDoc
| Field | Type | Keterangan |
|-------|------|------------|
| reg_type | RegulationType | Klasifikasi otomatis dari dokumen |
| number | str | `"68"`, `"13"`, dll |
| year | int \| None | Tahun terbit |
| full_identifier | str | `"PMK-68/PMK.03/2024"`, `"UU-6/1983"` |
| title | str | Judul regulasi (dari dokumen atau filename) |
| topics | list[TaxTopic] | Topik pajak terdeteksi |
| status | str | `"aktif"` \| `"cabut"` \| `"diganti"` |
| replaced_by | str | Identifier regulasi pengganti (jika ada) |
| sections | list[Section] | Pasal-pasal yang sudah di-split |
| full_text | str | Teks lengkap dokumen |
| source_path | str | Path file sumber |
| source_type | str | `"pdf"` \| `"docx"` \| `"html"` \| `"manual"` |
| extracted_at | datetime | Waktu ekstraksi |

---

## 2. JSONL Output Format (Phase 1 -- Current)

Output `data/output/corpus.jsonl` -- satu dokumen per baris, serialized dari `RegulationDoc`:

```json
{
  "reg_type": "PMK",
  "number": "68",
  "year": 2024,
  "full_identifier": "PMK-68/PMK.03/2024",
  "title": "KETENTUAN PEMOTONGAN PPh PASAL 21",
  "topics": ["PPh"],
  "status": "aktif",
  "replaced_by": "",
  "sections": [
    {"number": "Pasal 1", "title": "", "text": "...", "raw_text": "..."},
    {"number": "Pasal 2", "title": "", "text": "...", "raw_text": "..."}
  ],
  "full_text": "...",
  "source_path": "data/raw/PMK-68-PMK-03-2024.pdf",
  "source_type": ".pdf",
  "extracted_at": "2026-04-07T22:00:00.000000"
}
```

**Aturan:**
- Satu baris = satu dokumen regulasi lengkap
- Valid JSON, UTF-8 encoded
- Semua field wajib ada (default: `""`, `[]`, `null` jika kosong)

---

## 3. SQLite Database Schema (Implemented + FTS5)

Untuk integrasi dengan telegram-bot (search, retrieval, cross-reference).

### Tabel: regulations

```sql
CREATE TABLE IF NOT EXISTS regulations (
    id                  TEXT PRIMARY KEY,       -- UUID
    full_identifier     TEXT UNIQUE NOT NULL,   -- "PMK-68/PMK.03/2024"
    reg_type           TEXT NOT NULL,           -- "UU", "PMK", "PP", etc
    number             TEXT NOT NULL,           -- "68"
    year               INTEGER,                 -- 2024
    title              TEXT NOT NULL,           -- judul regulasi
    status             TEXT DEFAULT 'aktif',    -- "aktif", "cabut", "diganti"
    replaced_by        TEXT REFERENCES regulations(full_identifier),
    full_text          TEXT,                    -- teks lengkap
    source_path        TEXT,                    -- path file asal
    source_type        TEXT,                    -- "pdf", "docx", "html"
    extracted_at       TEXT,                    -- ISO datetime
    created_at         TEXT DEFAULT (datetime('now'))
);
```

### Tabel: sections

```sql
CREATE TABLE IF NOT EXISTS sections (
    id                  TEXT PRIMARY KEY,       -- UUID
    regulation_id       TEXT NOT NULL REFERENCES regulations(id),
    section_order       INTEGER NOT NULL,       -- urutan pasal (0, 1, 2, ...)
    section_number      TEXT NOT NULL,          -- "Pasal 1", "Ayat (1)"
    section_title       TEXT DEFAULT '',
    text                TEXT NOT NULL,          -- isi pasal yang sudah dibersihkan
    raw_text            TEXT DEFAULT '',        -- teks asli dari PDF
    UNIQUE(regulation_id, section_number)
);
```

### Tabel: topics

```sql
CREATE TABLE IF NOT EXISTS topics (
    regulation_id       TEXT NOT NULL REFERENCES regulations(id),
    topic               TEXT NOT NULL,          -- "PPh", "PPN", "KUP", etc
    PRIMARY KEY (regulation_id, topic)
);
```

### Index untuk pencarian

```sql
-- Pencarian berdasarkan identifier (exact match)
CREATE INDEX idx_reg_identifier ON regulations(full_identifier);

-- Pencarian berdasarkan jenis regulasi
CREATE INDEX idx_reg_type ON regulations(reg_type);

-- Pencarian berdasarkan tahun
CREATE INDEX idx_reg_year ON regulations(year);

-- Index tambahan yang juga aktif:
CREATE INDEX idx_sections_regulation ON sections(regulation_id);
```

**Catatan FTS5:** Implementasi sudah selesai sejak Langkah 3 (2026-08-27). Tabel virtual
`regulations_fts` dan `sections_fts` sudah aktif di `src/corpusprep/database.py` dan
terisi otomatis saat `riset-pajak db-status` dipanggil melalui fungsi `_populate_fts_tables()`.
FTS5 mengisi data dari tabel utama saat query status dijalankan, sehingga data selalu sinkron tanpa trigger tambahan.

```sql
-- Text search pada title dan full text regulasi
CREATE VIRTUAL TABLE IF NOT EXISTS regulations_fts USING fts5(
    title, full_text,
    content=regulations,
    content_rowid=rowid
);

-- Text search pada isi pasal
CREATE VIRTUAL TABLE IF NOT EXISTS sections_fts USING fts5(
    section_number, text,
    content=sections,
    content_rowid=rowid
);
```

### Entity Relationship

```
regulations (1) ──< sections (N)    → satu regulasi punya banyak pasal
regulations (1) ──< topics (N)      → satu regulasi punya banyak topik
regulations (M) ──< replaced_by >── regulations (N)  → relasi pengganti
```

---

## 4. Identifier Format Support

Sisten mengenali dan menghasilkan standar:

| Sumber | Format Input | Output full_identifier |
|--------|-------------|----------------------|
| HEADER (slash) | `NOMOR 99/PMK.03/2024` | `PMK-99/2024` |
| HEADER (tahun) | `NOMOR 6 TAHUN 1983` | `UU-6/1983` (jenis ditebak dari header) |
| FILENAME | `PMK-68-PMK-03-2024.pdf` | `PMK-68/2024` |
| WEB HTML | halaman JDIH dengan field nomor dokumen | kanonis, mis. `PMK-228/2017` (dari field HTML) |

Keterbatasan yang diketahui (masuk Langkah 1 audit):
- Filename web seperti `228-PMK.03-2026-02-11.html` belum menghasilkan
  identifier bila field HTML tidak tersedia.
- Nomor dengan bidang non-numerik (`488/KMK.010/2026`, `34/MK/EF.2/2026`)
  belum tertangani parser filename/header.

---

## 5. Persistence Flow (Implemented)

```
Step 1: `riset-pajak process` membaca sumber dari `data/raw/`
Step 2: Ekstrak, clean, split, dan enrich menjadi `RegulationDoc`
Step 3: Export audit ke `data/output/corpus.jsonl` dan `corpus.md`
Step 4: Upsert ke `data.db` berdasarkan `full_identifier`
Step 5: Replace sections/topics untuk dokumen yang sama
Step 6: Populate FTS5 tables via `_populate_fts_tables()` saat db-status dipanggil
Step 7: Verify row counts dengan query SQLite

Untuk migrasi JSONL lama secara manual, gunakan `import_jsonl` dari
`src/corpusprep/database.py`. Database saat ini berisi 74 regulasi,
1.901 sections, dan 178 topics.
```

---

## 6. Design Decisions

| Keputusan | Alasan |
|-----------|--------|
| UUID untuk PK | Tidak bergantung pada autoincrement, aman untuk distributed |
| full_identifier UNIQUE | Natural key untuk lookup dan cross-reference |
| Section order integer | Preserve urutan asli tanpa rely pada string sort |
| FTS5 untuk text search | Built-in SQLite, tidak perlu deps eksternal |
| Separate topics table | Memudahkan filter/query berdasarkan topik |
| replaced_by FK | Traceability regulasi yang dicabut/diganti |
| raw_text dipisah | Auditability -- selalu bisa trace ke teks asli PDF |
