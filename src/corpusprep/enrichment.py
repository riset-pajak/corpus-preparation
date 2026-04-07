"""Enrichment: klasifikasi jenis regulasi dan ekstraksi topik pajak."""

from __future__ import annotations

import re

from corpusprep.models import RegulationType, TaxTopic

# Mapping kata kunci -> RegulationType
_TYPE_KEYWORDS: list[tuple[re.Pattern, RegulationType]] = [
    (re.compile(r"^Undang-Undang|^UU\s+No", re.IGNORECASE), RegulationType.UU),
    (re.compile(r"^Peraturan Menteri Keuangan|^PMK\s+No", re.IGNORECASE), RegulationType.PMK),
    (re.compile(r"^Peraturan Pemerintah|^PP\s+No", re.IGNORECASE), RegulationType.PP),
    (re.compile(r"^Surat Edaran|^SE\s+No", re.IGNORECASE), RegulationType.SE),
    (re.compile(r"^Keputusan\s+Menteri|^KEP\s+No", re.IGNORECASE), RegulationType.KEP),
    (re.compile(r"^Instruksi\s+(Dirjen|Direktur)", re.IGNORECASE), RegulationType.INSTR),
    (re.compile(r"^Peraturan(?!.*Menteri Keuangan)", re.IGNORECASE), RegulationType.PER),
]

# Mapping kata kunci -> TaxTopic
_TOPIC_KEYWORDS: list[tuple[str, TaxTopic]] = [
    ("PPh pasal 21", TaxTopic.PPh),
    ("PPh pasal 23", TaxTopic.PPh),
    ("PPh pasal 25", TaxTopic.PPh),
    ("PPh pasal 26", TaxTopic.PPh),
    ("PPh pasal 4", TaxTopic.PPh),
    ("PPh pasal 15", TaxTopic.PPh),
    ("PPh pasal 17", TaxTopic.PPh),
    ("PPh Final", TaxTopic.PPh),
    ("pajak penghasilan", TaxTopic.PPh),
    ("PPN", TaxTopic.PPN),
    ("pajak pertambahan nilai", TaxTopic.PPN),
    ("PPnBM", TaxTopic.PPnBM),
    ("barang mewah", TaxTopic.PPnBM),
    ("PBB", TaxTopic.PBB),
    ("bumi dan bangunan", TaxTopic.PBB),
    ("BPHTB", TaxTopic.BPHTB),
    ("KUP", TaxTopic.KUP),
    ("ketentuan umum dan tata cara", TaxTopic.KUP),
    ("SP2D", TaxTopic.KUP),
    ("pemeriksaan pajak", TaxTopic.KUP),
    ("keberatan pajak", TaxTopic.KUP),
    ("bea materai", TaxTopic.Bea_Materai),
    ("materai", TaxTopic.Bea_Materai),
    ("administrasi perpajakan", TaxTopic.DJP_Admin),
    ("NPWP", TaxTopic.DJP_Admin),
]


def classify_regulation(text: str, max_chars: int = 1000) -> RegulationType:
    """Klasifikasi jenis regulasi dari isi teks."""
    snippet = text[:max_chars]
    for pattern, rtype in _TYPE_KEYWORDS:
        if pattern.search(snippet):
            return rtype
    # Cek dari pattern nama file yang sering muncul
    if re.search(r"PMK[-.\s]\d+", snippet):
        return RegulationType.PMK
    if re.search(r"UU[-.\s]\d+", snippet):
        return RegulationType.UU
    return RegulationType.OTHER


def extract_topics(text: str) -> list[TaxTopic]:
    """Ekstraksi topik pajak dari teks berdasarkan keyword matching."""
    found: list[TaxTopic] = []
    text_lower = text.lower()

    for keyword, topic in _TOPIC_KEYWORDS:
        if keyword.lower() in text_lower:
            if topic not in found:
                found.append(topic)

    return found
