"""Pemisahan teks regulasi per pasal/ayat."""

from __future__ import annotations

import re

from corpusprep.models import Section


def split_by_pasal(text: str, min_length: int = 50) -> list[Section]:
    """
    Pecah teks regulasi berdasarkan Pasal/ayat.

    Strategi:
    1. Cari pattern 'Pasal XX' dengan variasi whitespace
    2. Jika tidak ada pasal, bagi berdasarkan blok paragraf
    3. Merging section yang terlalu pendek (misal header)
    """
    # Pattern: "Pasal 1", "Pasal 1A", "Pasal 1 ayat (1)", dll
    pasal_pattern = re.compile(
        r"^(Pasal\s+\d+[A-Za-z]*\s*(?:Ayat\s*\(\d+\))?.*?)\s*$",
        re.MULTILINE | re.IGNORECASE
    )

    matches = list(pasal_pattern.finditer(text))

    if not matches:
        # Fallback: split paragraf, group by proximity
        return _fallback_split(text, min_length)

    sections: list[Section] = []
    for i, match in enumerate(matches):
        number = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        body = text[start:end].strip()

        # Bersihkan
        body = _clean_section_body(body)

        # Tentukan title vs text
        title, body_text = _split_title_and_body(body)

        sections.append(Section(
            number=number,
            title=title,
            text=body_text,
        ))

    return sections


def _clean_section_body(body: str) -> str:
    """Bersihkan section dari noise."""
    lines = body.split("\n")
    cleaned: list[str] = []
    for line in lines:
        line = line.strip()
        # Skip page numbers, footer-like patterns
        if re.match(r"^\d+\s*$", line):
            continue
        # Skip terlalu pendek tanpa konteks (header artifacts)
        if len(line) < 3:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _split_title_and_body(body: str) -> tuple[str, str]:
    """Pisahkan baris pertama sebagai title jika singkat."""
    lines = body.split("\n", 1)
    if len(lines) == 1:
        return "", lines[0]
    first = lines[0].strip()
    rest = lines[1].strip()
    if len(first) < 200:
        return first, rest
    return "", body


def _fallback_split(text: str, min_length: int) -> list[Section]:
    """Fallback: split berdasarkan paragraf jika tidak ada pattern Pasal."""
    paragraphs = [
        p.strip() for p in text.split("\n\n")
        if p.strip() and len(p.strip()) >= min_length
    ]

    if not paragraphs:
        # Satu section besar
        return [Section(number="Full Text", text=text.strip())]

    sections: list[Section] = []
    for i, para in enumerate(paragraphs):
        sections.append(Section(number=f"Blok {i + 1}", text=para))

    return sections
