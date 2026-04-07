# SCHEMA.md -- Corpus & Database Schema

**Last Updated:** 2026-04-08
**Status:** Phase 1 implemented (JSONL), Phase 2 planned (SQLite)

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

## 3. SQLite Database Schema (Phase 2 -- Planned)

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
    source_type        TEXT,                    -- "pdf", "docx"
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

-- Text search pada title
-- SQLite FTS5 akan dipakai untuk full-text search
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
| HEADER (tahun) | `NOMOR 6 TAHUN 1983` | `UU-6/1983` |
| FILENAME | `PMK-68-PMK-03-2024.pdf` | `PMK-68/2024` |

---

## 5. Migration Plan (JSONL → SQLite)

```
Step 1: Baca semua baris di corpus.jsonl
Step 2: Deserialize ke RegulationDoc (pydantic)
Step 3: Insert ke tabel regulations
Step 4: Insert sections dengan order dan FK
Step 5: Insert topics ke tabel topics
Step 6: Build FTS5 indexes
Step 7: Verify row counts match
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
