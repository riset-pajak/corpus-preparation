"""Rebuild baris DB dari teks processed yang sudah ada (audit 2026-08-24).

Memakai raw_text dari data/processed/ sehingga PDF besar tidak diekstrak ulang.
Jalur kode sama dengan `riset-pajak process` (process_file + save_documents).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpusprep.database import save_documents
from corpusprep.pipeline import process_file


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    db_path = root / "data.db"

    docs: list[dict] = []
    failed: list[str] = []
    files = sorted(f for f in raw_dir.iterdir() if f.is_file())
    for fp in files:
        stem = fp.stem
        txt_path = processed_dir / f"{stem}.txt"
        override: str | None = None
        if txt_path.exists():
            override = txt_path.read_text(encoding="utf-8")
        try:
            doc = process_file(fp, str(processed_dir), raw_text_override=override)
            docs.append(doc.model_dump(mode="json"))
            status = doc.status
            print(f"OK {status:9} {fp.name[:52]:52} id={doc.full_identifier[:40]}")
        except Exception as exc:
            failed.append(f"{fp.name}: {exc}")
            print(f"FAIL {fp.name[:52]} -- {exc}")

    saved = save_documents(db_path, docs)
    print(f"\nsaved={saved} failed={len(failed)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
