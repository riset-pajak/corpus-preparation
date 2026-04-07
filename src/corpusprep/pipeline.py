"""Pipeline pemrosesan dokumen regulasi."""

from __future__ import annotations

from pathlib import Path

from corpusprep.extractors import extract_text_from_pdf, extract_text_from_docx
from corpusprep.splitter import split_by_pasal
from corpusprep.enrichment import classify_regulation, extract_topics
from corpusprep.metadata import extract_identifier, extract_title


def process_file(file_path: Path, processed_dir: str) -> "RegulationDoc":
    """Proses satu file menjadi RegulationDoc."""
    from corpusprep.models import RegulationDoc, Section

    ext = file_path.suffix.lower()

    # 1. Extract
    raw_text = ""
    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        raw_text = extract_text_from_docx(file_path)
    else:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

    # 2. Clean & Split
    sections = split_by_pasal(raw_text)

    # 3. Enrich -- klasifikasi jenis regulasi
    reg_type = classify_regulation(raw_text)
    # Enrich -- topik
    topics = extract_topics(raw_text)

    # 4. Metadata: nomor, tahun, identifier, judul
    meta = extract_identifier(raw_text, str(file_path))
    title = extract_title(raw_text)

    # Override reg_type jika diidentifikasi dari header/file
    # (metada lebih akurat karena membaca format resmi)
    from corpusprep.models import RegulationType
    if meta.get("reg_type_short"):
        override_map = {
            "UU": "UU", "PP": "PP", "PMK": "PMK", "PER": "PER",
            "SE": "SE", "KEP": "KEP", "INSTR": "INSTR",
        }
        short = meta["reg_type_short"]
        if short in override_map:
            reg_type = getattr(RegulationType, short, reg_type)

    doc = RegulationDoc(
        reg_type=reg_type,
        number=meta.get("number", ""),
        year=meta.get("year"),
        full_identifier=meta.get("full_identifier", title),
        title=title,
        topics=topics,
        sections=sections,
        full_text=raw_text.strip(),
        source_path=str(file_path),
        source_type=file_path.suffix,
    )

    # 5. Save processed text
    out_path = Path(processed_dir) / f"{file_path.stem}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(raw_text)

    return doc
