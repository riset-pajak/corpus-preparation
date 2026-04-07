"""Model data untuk dokumen regulasi perpajakan."""

from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class RegulationType(str, Enum):
    """Jenis regulasi perpajakan."""
    UU = "UU"                   # Undang-Undang
    PP = "PP"                   # Peraturan Pemerintah
    PER = "PER"                 # Peraturan (Dirjen dll)
    PMK = "PMK"                 # Peraturan Menteri Keuangan
    SE = "SE"                   # Surat Edaran
    KEP = "KEP"                 # Keputusan Menteri
    INSTR = "INSTR"             # Instruksi
    OTHER = "OTHER"             # Lainnya


class TaxTopic(str, Enum):
    """Topik pajak utama."""
    PPh = "PPh"                 # Pajak Penghasilan
    PPN = "PPN"                 # Pajak Pertambahan Nilai
    PPnBM = "PPnBM"             # Pajak Penjualan atas Barang Mewah
    PBB = "PBB"                 # Pajak Bumi dan Bangunan
    BPHTB = "BPHTB"             # Bea Perolehan Hak atas Tanah dan Bangunan
    KUP = "KUP"                 # Ketentuan Umum dan Tata Cara
    Bea_Materai = "Bea Materai"
    DJP_Admin = "DJP-Admin"     # Administrasi DJP
    Umum = "Umum"


class Section(BaseModel):
    """Satuan teks per pasal/ayat."""
    number: str                          # e.g. "Pasal 1", "Ayat (1)", "Lampiran"
    title: str = ""
    text: str
    raw_text: str = ""


class RegulationDoc(BaseModel):
    """Representasi satu dokumen regulasi yang sudah diproses."""
    # Metadata dasar
    reg_type: RegulationType = RegulationType.OTHER
    number: str = ""                      # e.g. "68"
    year: int | None = None
    full_identifier: str = ""             # e.g. "PMK-68/PMK.03/2024"
    title: str = ""
    topics: list[TaxTopic] = []

    # Status
    status: str = "aktif"               # aktif/cabut/diganti
    replaced_by: str = ""

    # Content
    sections: list[Section] = []
    full_text: str = ""

    # File tracking
    source_path: str = ""
    source_type: str = ""             # pdf/docx/html/manual
    extracted_at: datetime = Field(default_factory=datetime.now)

    @property
    def section_count(self) -> int:
        return len(self.sections)

    @property
    def char_count(self) -> int:
        return len(self.full_text)


class CorpusStats(BaseModel):
    """Statistik corpus."""
    total_docs: int = 0
    total_sections: int = 0
    total_chars: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_topic: dict[str, int] = Field(default_factory=dict)
    earliest_year: int | None = None
    latest_year: int | None = None
    docs: list[dict] = Field(default_factory=list)
