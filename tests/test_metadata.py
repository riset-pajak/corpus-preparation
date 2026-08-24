"""Unit test: metadata extraction -- nomor, tahun, judul, identifier."""

from corpusprep.metadata import extract_identifier, extract_title


# -------------------------------------------------------------------------
# extract_identifier: format header standar
# -------------------------------------------------------------------------

def test_pmk_format_slash():
    """PMK: NOMOR 99/PMK.03/2024"""
    text = (
        "PERATURAN MENTERI KEUANGAN\n"
        "NOMOR 99/PMK.03/2024\n"
        "TENTANG\n"
        "Ketentuan Pemotongan PPh Pasal 21"
    )
    result = extract_identifier(text, source_file="dummy.pdf")
    assert result["number"] == "99"
    assert result["year"] == 2024
    assert result["reg_type_short"] == "PMK"
    assert "99" in result["full_identifier"]


def test_uu_format_tahun():
    """UU: NOMOR 6 TAHUN 1983"""
    text = (
        "UNDANG-UNDANG REPUBLIK INDONESIA\n"
        "NOMOR 6 TAHUN 1983\n"
        "TENTANG\n"
        "Ketentuan Umum dan Tata Cara Perpajakan"
    )
    result = extract_identifier(text, source_file="dummy.pdf")
    assert result["number"] == "6"
    assert result["year"] == 1983


def test_pp_format_tahun():
    """PP: NOMOR 55 TAHUN 2022"""
    text = (
        "PERATURAN PEMERINTAH REPUBLIK INDONESIA\n"
        "NOMOR 55 TAHUN 2022\n"
        "TENTANG\n"
        "Pajak Penghasilan atas Penghasilan yang Diterima"
    )
    result = extract_identifier(text, source_file="dummy.pdf")
    assert result["number"] == "55"
    assert result["year"] == 2022


def test_se_format():
    """SE: NOMOR SE-42/PJ.2/2023"""
    text = (
        "SURAT EDARAN\n"
        "NOMOR SE-42/PJ.2/2023\n"
        "TENTANG\n"
        "Pemenuhan Kewajiban Perpajakan"
    )
    result = extract_identifier(text, source_file="SE-42-PJ2-2023.pdf")
    assert result["number"] == "42"
    assert result["year"] == 2023
    assert result["reg_type_short"] == "SE"


# -------------------------------------------------------------------------
# extract_identifier: dari nama file
# -------------------------------------------------------------------------

def test_filename_pmk():
    """Fallback ke nama file: PMK-68-PMK-03-2024.pdf"""
    text = "Dokumen tanpa header resmi, hanya isi pasal."
    result = extract_identifier(text, source_file="PMK-68-PMK-03-2024.pdf")
    assert result["reg_type_short"] == "PMK"
    assert "68" in result["number"]
    assert result["year"] == 2024


def test_filename_uu():
    """Fallback ke nama file: UU-7-2021.pdf"""
    text = "Isi dokumen tanpa nomor resmi."
    result = extract_identifier(text, source_file="UU-7-2021.pdf")
    assert result["reg_type_short"] == "UU"
    assert result["number"] == "7"
    assert result["year"] == 2021


def test_filename_with_spaces():
    """Nama file dengan underscore dan spasi."""
    text = "Isi dokumen."
    result = extract_identifier(text, source_file="PMK_99_PMK_03_2024.pdf")
    assert result["reg_type_short"] == "PMK"
    assert result["number"] == "99"
    assert result["year"] == 2024


# -------------------------------------------------------------------------
# extract_identifier: full_identifier building
# -------------------------------------------------------------------------

def test_full_identifier_builtin():
    """Full identifier dibangun otomatis: PMK-99/2024"""
    text = (
        "PERATURAN MENTERI KEUANGAN\n"
        "NOMOR 99/PMK.03/2024\n"
    )
    result = extract_identifier(text)
    assert "99" in result["full_identifier"]
    assert "2024" in result["full_identifier"]


def test_full_identifier_from_filename():
    """Full identifier dari nama file jika header minim."""
    text = "Isi pasal yang pendek."
    result = extract_identifier(text, source_file="PER-12-2023.pdf")
    assert "12" in result["full_identifier"]


# -------------------------------------------------------------------------
# extract_title
# -------------------------------------------------------------------------

def test_title_after_tentang():
    """Judul diambil dari baris setelah 'TENTANG'."""
    text = (
        "PERATURAN MENTERI KEUANGAN\n"
        "NOMOR 99/PMK.03/2024\n"
        "TENTANG\n"
        "KETENTUAN PEMOTONGAN PPh PASAL 21 ATAU PAJAK PENGHASILAN PASAL 22\n"
        "Pasal 1\n"
    )
    assert "PEMOTONGAN" in extract_title(text)
    assert "PPh PASAL 21" in extract_title(text)


def test_title_no_tentang():
    """Fallback: baris panjang pertama yang bukan header standar."""
    text = (
        "PERATURAN MENTERI\n"
        "NOMOR 1/PMK.03/2024\n"
        "TENTANG\n"
        "Ketentuan Perpajakan yang Baru Diberlakukan"
    )
    result = extract_title(text)
    assert "Peraturan" not in result  # bukan header
    assert "Pemotongan" in result or "Ketentuan" in result


def test_title_short_lines_skipped():
    """Baris pendek dilewati."""
    text = "A\nB\nC\n\nKetentuan lengkap tentang perpajakan yang cukup panjang untuk dideteksi."
    result = extract_title(text)
    assert "Ketentuan lengkap" in result


def test_title_empty():
    """Teks sangat pendek."""
    assert extract_title("Pasal 1") == ""


# -------------------------------------------------------------------------
# Preamble: nomor yang DIRUJUK di Menimbang tidak boleh jadi identitas
# (regresi dari audit 2026-08-24: PMK 61/2026 terbaca UU-17/2006)
# -------------------------------------------------------------------------

def test_referenced_number_in_menimbang_is_ignored():
    """PMK dicetak 'NOMOR 61 TAHUN 2026'; menimbang merujuk UU 17/2006."""
    text = (
        "PERATURAN MENTERI KEUANGAN REPUBLIK INDONESIA\n"
        "NOMOR 61 TAHUN 2026\n"
        "TENTANG\n"
        "TATA CARA PEMANFAATAN TARIF BEA MASUK\n"
        "\n"
        "DENGAN RAHMAT TUHAN YANG MAHA ESA\n"
        "MENTERI KEUANGAN REPUBLIK INDONESIA,\n"
        "Menimbang : a. bahwa untuk memberikan kepastian hukum berdasarkan\n"
        "Undang-Undang Nomor 17 TAHUN 2006 tentang Bea Masuk;\n"
    )
    result = extract_identifier(text, source_file="PMK-61-2026.pdf")
    assert result["number"] == "61"
    assert result["year"] == 2026
    assert result["reg_type_short"] == "PMK"
    assert result["full_identifier"] == "PMK-61/2026"


def test_preamble_number_year_without_slash_format():
    """Pola '<JENIS> NOMOR <n> TAHUN <tahun>' pada preamble."""
    text = (
        "KEPUTUSAN MENTERI KEUANGAN REPUBLIK INDONESIA\n"
        "NOMOR 300 TAHUN 2025\n"
        "TENTANG\n"
        "PENUNJUKAN PPID\n"
        "Menimbang : bahwa berdasarkan PERATURAN MENTERI KEUANGAN NOMOR 110/PMK.01/2022;\n"
    )
    result = extract_identifier(text, source_file="KMK-300-2025.pdf")
    assert result["full_identifier"] == "KEP-300/2025" or (
        result["number"] == "300" and result["year"] == 2025
    )


def test_bare_slash_number_in_web_detail_page():
    """Halaman detail DJP: nomor tanpa kata 'NOMOR' (969/KMK.04/1983)."""
    text = (
        "Dokumen Peraturan | Direktorat Jenderal Pajak\n"
        "Lompat ke isi utama\n"
        "969/KMK.04/1983\n"
        "PEDOMAN PENGHITUNGAN KREDIT PAJAK PERTAMBAHAN NILAI\n"
        "Menimbang: bahwa dalam rangka melaksanakan ketentuan\n"
    )
    result = extract_identifier(text, source_file="PERATURAN-1983-12-31.html")
    assert result["full_identifier"] == "KMK-969/1983"
