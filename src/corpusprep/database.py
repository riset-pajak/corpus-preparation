"""Persistensi corpus regulasi ke SQLite lokal."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Iterable


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS regulations (
    id TEXT PRIMARY KEY,
    full_identifier TEXT UNIQUE NOT NULL,
    reg_type TEXT NOT NULL,
    number TEXT NOT NULL,
    year INTEGER,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'aktif',
    replaced_by TEXT,
    full_text TEXT,
    source_path TEXT,
    source_type TEXT,
    extracted_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sections (
    id TEXT PRIMARY KEY,
    regulation_id TEXT NOT NULL REFERENCES regulations(id) ON DELETE CASCADE,
    section_order INTEGER NOT NULL,
    section_number TEXT NOT NULL,
    section_title TEXT DEFAULT '',
    text TEXT NOT NULL,
    raw_text TEXT DEFAULT '',
    UNIQUE(regulation_id, section_number)
);

CREATE TABLE IF NOT EXISTS topics (
    regulation_id TEXT NOT NULL REFERENCES regulations(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    PRIMARY KEY(regulation_id, topic)
);

CREATE INDEX IF NOT EXISTS idx_reg_identifier ON regulations(full_identifier);
CREATE INDEX IF NOT EXISTS idx_reg_type ON regulations(reg_type);
CREATE INDEX IF NOT EXISTS idx_reg_year ON regulations(year);
CREATE INDEX IF NOT EXISTS idx_sections_regulation ON sections(regulation_id);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Buka database dan pastikan schema tersedia."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    return connection


def save_documents(db_path: Path, documents: Iterable[dict]) -> int:
    """Upsert dokumen dan child rows; kembalikan jumlah dokumen tersimpan."""
    documents = list(documents)
    if not documents:
        return 0

    with connect(db_path) as connection:
        for document in documents:
            identifier = str(document.get("full_identifier") or document.get("title") or "UNKNOWN")
            existing = connection.execute(
                "SELECT id FROM regulations WHERE full_identifier = ?", (identifier,)
            ).fetchone()
            regulation_id = existing["id"] if existing else str(uuid.uuid4())

            connection.execute(
                """
                INSERT INTO regulations (
                    id, full_identifier, reg_type, number, year, title, status,
                    replaced_by, full_text, source_path, source_type, extracted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(full_identifier) DO UPDATE SET
                    reg_type=excluded.reg_type,
                    number=excluded.number,
                    year=excluded.year,
                    title=excluded.title,
                    status=excluded.status,
                    replaced_by=excluded.replaced_by,
                    full_text=excluded.full_text,
                    source_path=excluded.source_path,
                    source_type=excluded.source_type,
                    extracted_at=excluded.extracted_at
                """,
                (
                    regulation_id,
                    identifier,
                    str(document.get("reg_type", "OTHER")),
                    str(document.get("number", "")),
                    document.get("year"),
                    str(document.get("title", "")),
                    str(document.get("status", "aktif")),
                    str(document.get("replaced_by", "")),
                    str(document.get("full_text", "")),
                    str(document.get("source_path", "")),
                    str(document.get("source_type", "")),
                    str(document.get("extracted_at", "")),
                ),
            )
            regulation_id = connection.execute(
                "SELECT id FROM regulations WHERE full_identifier = ?", (identifier,)
            ).fetchone()["id"]

            connection.execute("DELETE FROM sections WHERE regulation_id = ?", (regulation_id,))
            connection.execute("DELETE FROM topics WHERE regulation_id = ?", (regulation_id,))

            used_section_numbers: set[str] = set()
            for order, section in enumerate(document.get("sections", [])):
                section_number = str(section.get("number", ""))
                if section_number in used_section_numbers:
                    section_number = f"{section_number} [{order + 1}]"
                used_section_numbers.add(section_number)
                connection.execute(
                    """
                    INSERT INTO sections (
                        id, regulation_id, section_order, section_number,
                        section_title, text, raw_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        regulation_id,
                        order,
                        section_number,
                        str(section.get("title", "")),
                        str(section.get("text", "")),
                        str(section.get("raw_text", "")),
                    ),
                )

            for topic in document.get("topics", []):
                connection.execute(
                    "INSERT OR IGNORE INTO topics(regulation_id, topic) VALUES (?, ?)",
                    (regulation_id, str(topic)),
                )

    return len(documents)


def import_jsonl(db_path: Path, jsonl_path: Path) -> int:
    """Import corpus JSONL yang sudah ada ke SQLite."""
    with jsonl_path.open(encoding="utf-8") as stream:
        documents = [json.loads(line) for line in stream if line.strip()]
    return save_documents(db_path, documents)


def counts(db_path: Path) -> dict[str, int]:
    """Ambil jumlah row tiap tabel utama."""
    with connect(db_path) as connection:
        return {
            table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("regulations", "sections", "topics")
        }


def status(db_path: Path) -> dict:
    """Statistik lengkap database: per jenis, status, tahun, topik."""
    with connect(db_path) as connection:
        result: dict = {"counts": counts(db_path)}

        result["by_reg_type"] = {
            r[0]: r[1]
            for r in connection.execute(
                "SELECT reg_type, COUNT(*) FROM regulations GROUP BY reg_type ORDER BY COUNT(*) DESC"
            )
        }

        result["by_status"] = {
            r[0]: r[1]
            for r in connection.execute(
                "SELECT status, COUNT(*) FROM regulations GROUP BY status ORDER BY COUNT(*) DESC"
            )
        }

        # Rentang tahun
        yrange = connection.execute("SELECT MIN(year), MAX(year) FROM regulations WHERE year IS NOT NULL").fetchone()
        result["year_range"] = f"{yrange[0]} -- {yrange[1]}" if yrange[0] is not None else "(belum ada)"

        # Topik populer
        result["topics"] = {
            r[0]: r[1]
            for r in connection.execute(
                "SELECT topic, COUNT(*) FROM topics GROUP BY topic ORDER BY COUNT(*) DESC LIMIT 15"
            )
        }

        return result


def search_by_title(db_path: Path, query: str, limit: int = 20) -> list[dict]:
    """Cari regulasi berdasarkan judul atau identifier (LIKE case-insensitive)."""
    with connect(db_path) as connection:
        rows = connection.execute(
            """SELECT id, full_identifier, reg_type, number, year, title
               FROM regulations
               WHERE title LIKE ? OR full_identifier LIKE ?
               ORDER BY year DESC
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]


def search_by_year(db_path: Path, year: int) -> list[dict]:
    """Cari regulasi berdasarkan tahun terbit."""
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, full_identifier, reg_type, number, year, title FROM regulations WHERE year=? ORDER BY full_identifier",
            (year,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_regulation(db_path: Path, identifier: str) -> dict | None:
    """Ambil detail satu regulasi beserta pasal-pasalnya."""
    with connect(db_path) as connection:
        reg = connection.execute(
            "SELECT * FROM regulations WHERE full_identifier=?",
            (identifier,),
        ).fetchone()
        if not reg:
            return None
        result = dict(reg)
        # Sections
        result["sections"] = [
            dict(s)
            for s in connection.execute(
                "SELECT id, section_order, section_number, section_title, text, raw_text FROM sections WHERE regulation_id=? ORDER BY section_order",
                (reg["id"],),
            ).fetchall()
        ]
        # Topics
        result["topics"] = [
            t["topic"]
            for t in connection.execute(
                "SELECT topic FROM topics WHERE regulation_id=?",
                (reg["id"],),
            ).fetchall()
        ]
        return result
