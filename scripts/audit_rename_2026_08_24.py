"""Rename salinan PDF + bersihkan artefak (Langkah 1 audit, 2026-08-24)."""
import shutil
from pathlib import Path

raw = Path("data/raw")
renames = {
    "PMK-unknown-date.pdf": "PMK-61-2026.pdf",
    "PMK-unknown-date_3.pdf": "PMK-60-2026.pdf",
    "PMK-unknown-date_5.pdf": "PMK-52-2020.pdf",
    "PMK-unknown-date_6.pdf": "PMK-52-2020-abstrak.pdf",
    "PMK-unknown-date_7.pdf": "PMK-32-2025.pdf",
    "PMK-unknown-date_8.pdf": "PMK-32-2025-abstrak.pdf",
    "PMK-unknown-date_9.pdf": "PMK-41-2026.pdf",
    "PMK-unknown-date_11.pdf": "PMK-56-2026.pdf",
    "PMK-unknown-date_12.pdf": "PMK-56-2026-abstrak.pdf",
    "PMK-unknown-date_13.pdf": "PMK-53-2026.pdf",
    "PMK-unknown-date_14.pdf": "PMK-53-2026-abstrak.pdf",
    "PMK-unknown-date_15.pdf": "PMK-51-2026.pdf",
    "PMK-unknown-date_16.pdf": "PMK-51-2026-abstrak.pdf",
    "PMK-unknown-date_17.pdf": "PMK-26-2022.pdf",
    "PMK-unknown-date_18.pdf": "PMK-26-2022-abstrak.pdf",
    "PP-unknown-date.pdf": "PP-20-2026.pdf",
    "PERATURAN-unknown-date.pdf": "UU-6-1983-salinan.pdf",
    "PERATURAN-unknown-date_2.pdf": "UU-8-1983-buklet.pdf",
    "PERATURAN-unknown-date_3.pdf": "UU-6-2023-salinan.pdf",
    "PERATURAN-unknown-date_4.pdf": "UU-7-2021-buklet.pdf",
}
n = 0
for src, dst in renames.items():
    f = raw / src
    assert f.exists(), f"missing: {src}"
    t = raw / dst
    assert not t.exists(), f"target exists: {dst}"
    f.rename(t)
    n += 1
print("renamed:", n)

nav = Path("data/quarantine/navigation")
for name in [
    "jdih.kemenkeu.go.id-infografis-22301de4-7241-4bb7-d772-08de0be2da02-unknown-date.html",
    "jdih.kemenkeu.go.id-infografis-b612bb6f-e8fe-4035-a469-7ece5ff03a6d-unknown-date.html",
]:
    f = raw / name
    if f.exists():
        shutil.move(str(f), nav / name)
        print("quarantined:", name[:60])

db = raw / "data.db"
if db.exists():
    db.unlink()
    print("deleted empty stray data/raw/data.db")

files = [f for f in raw.iterdir() if f.is_file()]
print(f"raw final: {len(files)} file")
left = sorted(f.name for f in files if "unknown-date" in f.name)
print("masih mengandung unknown-date:", len(left))
for x in left:
    print("  -", x)
