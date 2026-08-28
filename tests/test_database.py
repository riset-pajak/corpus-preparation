"""Unit test: database operations -- schema, upsert, sections, topics, FTS5."""

import sqlite3
from pathlib import Path
import pytest

from corpusprep.database import (
    connect,
    save_documents,
    counts,
    status,
    search_by_title,
    search_by_year,
    get_regulation,
    import_jsonl,
    _populate_fts_tables,
    SCHEMA,
)


# -------------------------------------------------------------------------
# Schema creation
# -------------------------------------------------------------------------

def test_schema_creation(tmp_path):
    """Schema SQLite dibuat dengan benar."""
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    
    # Check tables exist
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert "regulations" in tables
    assert "sections" in tables
    assert "topics" in tables
    assert "regulations_fts" in tables
    assert "sections_fts" in tables
    conn.close()


def test_regulations_table_columns(tmp_path):
    """Kolom regulations memiliki struktur yang benar."""
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    
    cursor = conn.execute("PRAGMA table_info(regulations)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    assert "id" in columns
    assert "full_identifier" in columns
    assert columns["full_identifier"] == "TEXT"
    assert "reg_type" in columns
    assert "year" in columns
    assert "title" in columns
    conn.close()


def test_sections_table_columns(tmp_path):
    """Kolom sections memiliki struktur yang benar."""
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    
    cursor = conn.execute("PRAGMA table_info(sections)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    assert "id" in columns
    assert "regulation_id" in columns
    assert "section_order" in columns
    assert "section_number" in columns
    assert "text" in columns
    assert "raw_text" in columns
    conn.close()


# -------------------------------------------------------------------------
# Upsert operations
# -------------------------------------------------------------------------

def test_save_documents_basic(tmp_path):
    """Simpan dokumen baru ke database."""
    db_path = tmp_path / "test.db"
    
    documents = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2024,
            "title": "Test Regulation",
            "status": "aktif",
            "topics": ["PPh", "KUP"],
            "sections": [
                {"number": "Pasal 1", "title": "", "text": "Isi pasal 1", "raw_text": "Isi pasal 1"}
            ],
            "full_text": "Full text here",
            "source_path": "data/raw/test.pdf",
            "source_type": ".pdf",
        }
    ]
    
    count = save_documents(db_path, documents)
    assert count == 1
    
    conn = connect(db_path)
    reg = conn.execute("SELECT * FROM regulations WHERE full_identifier=?", ("PMK-1/2024",)).fetchone()
    assert reg is not None
    assert reg["title"] == "Test Regulation"
    assert reg["year"] == 2024
    conn.close()


def test_upsert_existing_identifier(tmp_path):
    """Update dokumen yang sudah ada (same full_identifier)."""
    db_path = tmp_path / "test.db"
    
    # First insert
    documents = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2024,
            "title": "Original Title",
            "status": "aktif",
            "topics": ["PPh"],
            "sections": [{"number": "Pasal 1", "title": "", "text": "Lama", "raw_text": "Lama"}],
            "full_text": "Lama full text",
            "source_path": "data/raw/old.pdf",
            "source_type": ".pdf",
        }
    ]
    save_documents(db_path, documents)
    
    # Update with same identifier
    documents = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2025,  # Changed year
            "title": "Updated Title",
            "status": "aktif",
            "topics": ["PPh", "KUP"],  # Added topic
            "sections": [
                {"number": "Pasal 1", "title": "", "text": "Baru", "raw_text": "Baru"},
                {"number": "Pasal 2", "title": "", "text": "Pasal baru", "raw_text": "Pasal baru"},
            ],
            "full_text": "Baru full text",
            "source_path": "data/raw/new.pdf",
            "source_type": ".pdf",
        }
    ]
    
    count = save_documents(db_path, documents)
    assert count == 1
    
    conn = connect(db_path)
    reg = conn.execute("SELECT * FROM regulations WHERE full_identifier=?", ("PMK-1/2024",)).fetchone()
    assert reg["title"] == "Updated Title"
    assert reg["year"] == 2025
    
    # Check sections replaced
    sections = list(conn.execute("SELECT * FROM sections WHERE regulation_id=?", (reg["id"],)))
    assert len(sections) == 2  # Replaced, not duplicated
    conn.close()


def test_sections_replaced_on_upsert(tmp_path):
    """Sections diganti pada saat upsert, bukan ditambahkan."""
    db_path = tmp_path / "test.db"
    
    # Insert with 2 sections
    documents1 = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2024,
            "title": "Test",
            "status": "aktif",
            "topics": [],
            "sections": [
                {"number": "Pasal 1", "title": "", "text": "A", "raw_text": "A"},
                {"number": "Pasal 2", "title": "", "text": "B", "raw_text": "B"},
            ],
            "full_text": "",
            "source_path": "",
            "source_type": ".pdf",
        }
    ]
    save_documents(db_path, documents1)
    
    # Upsert with 1 section - should replace all
    documents2 = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2024,
            "title": "Test",
            "status": "aktif",
            "topics": [],
            "sections": [
                {"number": "Pasal 1", "title": "", "text": "NEW", "raw_text": "NEW"},
            ],
            "full_text": "",
            "source_path": "",
            "source_type": ".pdf",
        }
    ]
    save_documents(db_path, documents2)
    
    conn = connect(db_path)
    sections = list(conn.execute("SELECT * FROM sections WHERE regulation_id=?", 
                                  (conn.execute("SELECT id FROM regulations").fetchone()[0],)))
    assert len(sections) == 1
    assert sections[0]["text"] == "NEW"
    conn.close()


# -------------------------------------------------------------------------
# Counts
# -------------------------------------------------------------------------

def test_counts_empty_db(tmp_path):
    """Counts pada database kosong."""
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    
    result = counts(db_path)
    assert result["regulations"] == 0
    assert result["sections"] == 0
    assert result["topics"] == 0
    conn.close()


def test_counts_with_data(tmp_path):
    """Counts memiliki jumlah yang benar setelah insert."""
    db_path = tmp_path / "test.db"
    
    documents = [
        {
            "full_identifier": f"PMK-{i}/2024",
            "reg_type": "PMK",
            "number": str(i),
            "year": 2024,
            "title": f"Test {i}",
            "status": "aktif",
            "topics": ["PPh"] if i % 2 else [],
            "sections": [
                {"number": "Pasal 1", "title": "", "text": f"Content {i}", "raw_text": f"Content {i}"}
            ],
            "full_text": f"Full {i}",
            "source_path": "",
            "source_type": ".pdf",
        }
        for i in range(1, 4)
    ]
    
    save_documents(db_path, documents)
    result = counts(db_path)
    
    assert result["regulations"] == 3
    assert result["sections"] == 3
    assert result["topics"] == 2  # PPh appears for 2 regulations (PK constraint on reg_id+topic)


# -------------------------------------------------------------------------
# Status
# -------------------------------------------------------------------------

def test_status_empty_db(tmp_path):
    """Status pada database kosong."""
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    
    result = status(db_path)
    assert result["counts"]["regulations"] == 0
    assert result["year_range"] == "(belum ada)"
    assert result["topics"] == {}
    conn.close()


def test_status_with_data(tmp_path):
    """Status memiliki statistik lengkap."""
    db_path = tmp_path / "test.db"
    
    documents = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2024,
            "title": "Test 2024",
            "status": "aktif",
            "topics": ["PPh", "KUP"],
            "sections": [{"number": "Pasal 1", "title": "", "text": "A", "raw_text": "A"}],
            "full_text": "",
            "source_path": "",
            "source_type": ".pdf",
        },
        {
            "full_identifier": "UU-10/2023",
            "reg_type": "UU",
            "number": "10",
            "year": 2023,
            "title": "Test 2023",
            "status": "aktif",
            "topics": ["PPN"],
            "sections": [
                {"number": "Pasal 1", "title": "", "text": "B", "raw_text": "B"},
                {"number": "Pasal 2", "title": "", "text": "C", "raw_text": "C"},
            ],
            "full_text": "",
            "source_path": "",
            "source_type": ".pdf",
        },
        {
            "full_identifier": "PMK-2/2025",
            "reg_type": "PMK",
            "number": "2",
            "year": 2025,
            "title": "Test 2025",
            "status": "cabut",
            "topics": ["PPh"],
            "sections": [{"number": "Pasal 1", "title": "", "text": "D", "raw_text": "D"}],
            "full_text": "",
            "source_path": "",
            "source_type": ".pdf",
        },
    ]
    
    save_documents(db_path, documents)
    result = status(db_path)
    
    assert result["counts"]["regulations"] == 3
    assert result["counts"]["sections"] == 4
    assert result["counts"]["topics"] == 4  # PPh(2 regs), KUP(1), PPN(1) - PK constraint counts unique combos
    assert result["year_range"] == "2023 -- 2025"
    assert result["by_reg_type"]["PMK"] == 2
    assert result["by_reg_type"]["UU"] == 1
    assert result["by_status"]["aktif"] == 2
    assert result["by_status"]["cabut"] == 1


# -------------------------------------------------------------------------
# Search operations
# -------------------------------------------------------------------------

def test_search_by_title_found(tmp_path):
    """Pencarian judul ditemukan."""
    db_path = tmp_path / "test.db"
    
    documents = [
        {
            "full_identifier": "PMK-61/2026",
            "reg_type": "PMK",
            "number": "61",
            "year": 2026,
            "title": "TATA CARA PEMANFAATAN TARIF BEA MASUK",
            "status": "aktif",
            "topics": [],
            "sections": [],
            "full_text": "",
            "source_path": "",
            "source_type": ".pdf",
        }
    ]
    save_documents(db_path, documents)
    
    results = search_by_title(db_path, "TATA CARA", limit=10)
    assert len(results) == 1
    assert "PMK-61/2026" in results[0]["full_identifier"]


def test_search_by_title_not_found(tmp_path):
    """Pencarian judul tidak ditemukan."""
    db_path = tmp_path / "test.db"
    
    documents = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2024,
            "title": "Test Regulation",
            "status": "aktif",
            "topics": [],
            "sections": [],
            "full_text": "",
            "source_path": "",
            "source_type": ".pdf",
        }
    ]
    save_documents(db_path, documents)
    
    results = search_by_title(db_path, "NOTFOUND", limit=10)
    assert len(results) == 0


def test_search_by_year(tmp_path):
    """Filter berdasarkan tahun."""
    db_path = tmp_path / "test.db"
    
    documents = [
        {
            "full_identifier": f"PMK-{i}/2024",
            "reg_type": "PMK",
            "number": str(i),
            "year": 2024,
            "title": f"Test {i}",
            "status": "aktif",
            "topics": [],
            "sections": [],
            "full_text": "",
            "source_path": "",
            "source_type": ".pdf",
        }
        for i in range(1, 4)
    ]
    save_documents(db_path, documents)
    
    results = search_by_year(db_path, 2024)
    assert len(results) == 3
    
    results = search_by_year(db_path, 2023)
    assert len(results) == 0


def test_get_regulation_full_details(tmp_path):
    """Dapatkan detail regulasi lengkap."""
    db_path = tmp_path / "test.db"
    
    documents = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2024,
            "title": "Test Regulation",
            "status": "aktif",
            "topics": ["PPh", "KUP"],
            "sections": [
                {"number": "Pasal 1", "title": "", "text": "Isi pasal 1", "raw_text": "Isi pasal 1"},
                {"number": "Pasal 2", "title": "Sub-passal", "text": "Isi pasal 2", "raw_text": ""},
            ],
            "full_text": "Full text",
            "source_path": "data/raw/test.pdf",
            "source_type": ".pdf",
        }
    ]
    save_documents(db_path, documents)
    
    result = get_regulation(db_path, "PMK-1/2024")
    assert result is not None
    assert result["title"] == "Test Regulation"
    assert len(result["sections"]) == 2
    assert result["sections"][0]["section_number"] == "Pasal 1"
    assert result["sections"][0]["text"] == "Isi pasal 1"
    assert len(result["topics"]) == 2
    assert "PPh" in result["topics"]


def test_get_regulation_not_found(tmp_path):
    """Get regulation dengan identifier tidak ada."""
    db_path = tmp_path / "test.db"
    
    result = get_regulation(db_path, "NOTEXIST")
    assert result is None


# -------------------------------------------------------------------------
# FTS5 Full-Text Search
# -------------------------------------------------------------------------

def test_fts_tables_populated(tmp_path):
    """FTS5 tables terisi setelah data dimasukkan."""
    db_path = tmp_path / "test.db"
    
    documents = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2024,
            "title": "TAX NAME TAX REGULATION",
            "status": "aktif",
            "topics": [],
            "sections": [
                {"number": "Pasal 1", "title": "Intro", "text": "BEA MASUK TARIFF", "raw_text": ""}
            ],
            "full_text": "FULL TEXT WITH IMPORTANT WORDS",
            "source_path": "",
            "source_type": ".pdf",
        }
    ]
    save_documents(db_path, documents)
    
    conn = connect(db_path)
    
    # Check FTS tables populated
    fts_count = conn.execute("SELECT COUNT(*) FROM regulations_fts").fetchone()[0]
    assert fts_count == 1
    
    fts_sections_count = conn.execute("SELECT COUNT(*) FROM sections_fts").fetchone()[0]
    assert fts_sections_count == 1
    conn.close()


def test_fts_search_regulations(tmp_path):
    """FTS5 pencarian di tabel regulations."""
    db_path = tmp_path / "test.db"
    
    documents = [
        {
            "full_identifier": "PMK-1/2024",
            "reg_type": "PMK",
            "number": "1",
            "year": 2024,
            "title": "TAX REGULATION ABOUT PPN",
            "status": "aktif",
            "topics": [],
            "sections": [],
            "full_text": "Full text about TAX NAME",
            "source_path": "",
            "source_type": ".pdf",
        }
    ]
    save_documents(db_path, documents)
    status(db_path)  # Populates FTS tables
    
    conn = connect(db_path)
    # Use from corpusprep.database import search_by_fts for proper FTS5 search
    from corpusprep.database import search_by_fts
    rows = search_by_fts(db_path, "TAX", limit=10)
    assert len(rows) == 1
    conn.close()


# -------------------------------------------------------------------------
# Import JSONL
# -------------------------------------------------------------------------

def test_import_jsonl(tmp_path):
    """Import database dari file JSONL."""
    db_path = tmp_path / "test.db"
    jsonl_path = tmp_path / "corpus.jsonl"
    
    jsonl_content = '''{"full_identifier": "JSONL-1/2024", "reg_type": "PMK", "number": "1", "year": 2024, "title": "JSONL Test", "status": "aktif", "topics": [], "sections": [{"number": "Pasal 1", "title": "", "text": "Content", "raw_text": "Content"}], "full_text": "Full", "source_path": "", "source_type": ".pdf"}
{"full_identifier": "JSONL-2/2024", "reg_type": "UU", "number": "2", "year": 2024, "title": "JSONL Test 2", "status": "aktif", "topics": [], "sections": [], "full_text": "Full 2", "source_path": "", "source_type": ".pdf"}
'''
    jsonl_path.write_text(jsonl_content, encoding="utf-8")
    
    count = import_jsonl(db_path, jsonl_path)
    assert count == 2
    
    conn = connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM regulations").fetchone()[0] == 2
    conn.close()


def test_import_jsonl_empty_file(tmp_path):
    """Import file JSONL kosong."""
    db_path = tmp_path / "test.db"
    jsonl_path = tmp_path / "empty.jsonl"
    jsonl_path.write_text("", encoding="utf-8")
    
    count = import_jsonl(db_path, jsonl_path)
    assert count == 0