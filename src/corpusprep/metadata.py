"""Ekstraksi metadata dokumen regulasi: nomor, tahun, judul."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_identifier(text: str, source_file: Optional[str] = None) -> dict:
    """
    Ekstrak nomor, tahun, dan judul dari sebuah dokumen regulasi.

    Priority:
      1. Scan teks header untuk format standar: NOMOR 99/PMK.03/2024
      2. Jika tidak ditemukan, coba parse dari nama file
      3. Fallback: regex longgar + filename parts

    Returns dict dengan key:
      number (str), year (int | None), full_identifier (str), title (str)
    """
    header = text[:2000] if len(text) > 2000 else text
    filename = Path(source_file).name if source_file else ""

    result = _from_standard_header(header) or {}

    # Enrich dari filename jika ada yang kurang
    if not result:
        result = _from_filename(filename)
    else:
        result = _enrich_from_filename(result, filename)

    # Fallback akhir: regex longgar di header
    if not result.get("number"):
        m = re.search(r'(?:UU|PMK|PP|PER|SE|KEP|INSTR)[-\.\s]*(\d+)', header, re.IGNORECASE)
        if m:
            result.setdefault("number", m.group(1))

    if not result.get("year"):
        m = re.search(r'\b(19[5-9]\d|20[0-2]\d|2030)\b', header)
        if m:
            result.setdefault("year", int(m.group(1)))

    # Bangun full_identifier jika belum ada
    if not result.get("full_identifier"):
        rt = result.get("reg_type_short", "")
        no = result.get("number", "")
        yr = str(result["year"]) if result.get("year") else ""
        if no and yr:
            result["full_identifier"] = f"{rt}-{no}/{yr}" if rt else f"{no}/{yr}"
        elif no:
            result["full_identifier"] = f"{rt}-{no}" if rt else no
        else:
            result["full_identifier"] = result.get("title", "")

    return result


# ---------------------------------------------------------------------------
# Strategi 1: Format standar header regulasi
# ---------------------------------------------------------------------------

def _from_standard_header(header: str) -> Optional[dict]:
    """
    Kenali format header resmi:

        PERATURAN MENTERI KEUANGAN
        NOMOR 99/PMK.03/2024
        TENTANG
        KETENTUAN PEMOTONGAN...

   atau variasi:

        UNDANG-UNDANG REPUBLIK INDONESIA
        NOMOR 6 TAHUN 1983
        TENTANG
        ...
    """
    # Pola: NOMOR <angka>/<jenis>.<bidang>/<tahun>
    #       Contoh: NOMOR 99/PMK.03/2024
    m = re.search(
        r'NOMOR\s+(\d+)\s*/\s*'           # NOMOR 99
        r'(UU|PMK|PP|PER|SE|KEP|INSTR)'    # PMK
        r'(?:\.\d+)?'                      # .03 (opsional)
        r'\s*/\s*'                         # /
        r'(\d{4})',                        # 2024
        header,
        re.IGNORECASE
    )
    if m:
        number = m.group(1)
        reg_type = m.group(2).upper()
        year = int(m.group(3))
        return {
            "number": number,
            "year": year,
            "reg_type_short": reg_type,
        }

    # Pola: NOMOR <angka> TAHUN <tahun>  (untuk UU, PP)
    #       Contoh: NOMOR 6 TAHUN 1983
    m = re.search(
        r'NOMOR\s+(\d+)\s+TAHUN\s+(\d{4})',
        header,
        re.IGNORECASE
    )
    if m:
        number = m.group(1)
        year = int(m.group(2))
        reg_type = _guess_reg_type(header)
        return {
            "number": number,
            "year": year,
            "reg_type_short": reg_type,
        }

    return None


# ---------------------------------------------------------------------------
# Strategi 2: Parse nama file
# ---------------------------------------------------------------------------

def _from_filename(filename: str) -> dict:
    """Ekstrak dari nama file: PMK-99-PMK-03-2024.pdf  -> number=99, year=2024."""
    if not filename:
        return {}

    name = filename.rsplit(".", 1)[0]  # hapus ekstensi

    # Format: TYPE-NUMBER-something-YEAR  (mis: PMK-99-PMK-03-2024)
    m = re.match(
        r'^\s*(UU|PMK|PP|PER|SE|KEP|INSTR)'     # jenis
        r'[-_\s](\d+)'                           # nomor
        r'.*?[-_\s](\d{4})\s*$',                 # tahun di akhir
        name,
        re.IGNORECASE | re.DOTALL
    )
    if m:
        return {
            "reg_type_short": m.group(1).upper(),
            "number": m.group(2),
            "year": int(m.group(3)),
        }

    # Fallback: cari angka tahun dan nomor dari filename
    year_m = re.search(r'\b(19[5-9]\d|20[0-2]\d|2030)\b', name)
    number_m = re.search(r'(?<!\d)[-_\s](\d{1,4})[-_\s]', name)
    if year_m:
        return {
            "year": int(year_m.group(1)),
            "number": number_m.group(1) if number_m else "",
        }
    return {}


def _enrich_from_filename(result: dict, filename: str) -> dict:
    """Lengkapi field yang kosong dari nama file."""
    if not filename:
        return result

    name = filename.rsplit(".", 1)[0]

    # Tambah reg_type_short jika belum ada
    if "reg_type_short" not in result:
        m = re.match(r'(UU|PMK|PP|PER|SE|KEP|INSTR)', name, re.IGNORECASE)
        if m:
            result["reg_type_short"] = m.group(1).upper()

    # Tambah year jika belum ada
    if "year" not in result:
        m = re.search(r'\b(19[5-9]\d|20[0-2]\d|2030)\b', name)
        if m:
            result["year"] = int(m.group(1))

    # Tambah number jika belum ada
    if "number" not in result:
        m = re.search(r'[^\d](\d{1,4})[^\d]', name)
        if m:
            result["number"] = m.group(1)

    return result


# ---------------------------------------------------------------------------
# Judul
# ---------------------------------------------------------------------------

def extract_title(text: str) -> str:
    """
    Ambil judul regulasi dari teks.

    Strategi:
    1. Cari 'TENTANG' lalu ambil baris setelahnya
    2. Atau ambillah baris panjang pertama yang bukan header regulasi
    """
    header = text[:1500] if len(text) > 1500 else text

    # Strategi 1: Cari TENTANG dan ambil baris setelahnya
    lines = header.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.upper() == "TENTANG" and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if 10 < len(next_line) < 500:
                return next_line

    # Strategi 2: Baris pertama yang cukup panjang dan bukan header standar
    skip_patterns = [
        r'^REPUBLIK', r'^MENTERI', r'^PERATURAN', r'^UNDANG-UNDANG',
        r'^NOMOR\s', r'^TENTANG', r'^KEPUTUSAN', r'^INSTRUKSI',
        r'^\d+$',  # page number
    ]
    for line in lines:
        stripped = line.strip()
        if len(stripped) < 10 or len(stripped) > 500:
            continue
        if any(re.match(p, stripped, re.IGNORECASE) for p in skip_patterns):
            continue
        return stripped

    return ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REG_TYPE_MAP = {
    r'UNDANG-UNDANG|UU\s+NO': 'UU',
    r'PERATURAN\s+PEMERINTAH|PP\s+NO': 'PP',
    r'PERATURAN\s+MENTERI\s+KEUANGAN|PMK\s+NO': 'PMK',
    r'SURAT\s+EDARAN|SE\s+NO': 'SE',
    r'KEPUTUSAN\s+MENTERI|KEP\s+NO': 'KEP',
    r'INSTRUKSI': 'INSTR',
    r'PERATURAN': 'PER',
}


def _guess_reg_type(text: str) -> str:
    """Tebak jenis regulasi dari teks header."""
    for pattern, rtype in _REG_TYPE_MAP.items():
        if re.search(pattern, text, re.IGNORECASE):
            return rtype
    return ""
