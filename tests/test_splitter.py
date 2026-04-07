"""Unit test: splitter - pemecahan teks per pasal."""

import pytest
from corpusprep.splitter import split_by_pasal
from corpusprep.models import Section


def test_split_by_pasal_basic():
    """Test pemecahan teks yang punya pattern Pasal."""
    text = (
        "Pasal 1\n"
        "Pengertian\n"
        "\n"
        "Yang dimaksud dalam peraturan ini adalah sebagai berikut.\n"
        "Beberapa penjelasan lebih lanjut.\n"
        "\n"
        "Pasal 2\n"
        "Ketentuan Umum\n"
        "\n"
        "Setiap wajib pajak wajib melaporkan penghasilannya.\n"
        "\n"
        "Pasal 3\n"
        "Tarif Pajak\n"
        "\n"
        "Tarif pajak adalah sebesar 21 persen dari pendapatan.\n"
    )

    sections = split_by_pasal(text)

    assert len(sections) == 3
    assert "Pasal 1" in sections[0].number
    assert "Pasal 2" in sections[1].number
    assert "Pasal 3" in sections[2].number
    assert "wa" in sections[1].text  # kata "wajib" ada di section 2
    assert "Tarif" in sections[2].text  # judul ada di text


def test_split_pasal_with_variants():
    """Test dengan variasi penulisan pasal."""
    text = (
        "Pasal 1A\n"
        "Ketentuan khusus untuk kasus tertentu.\n"
        "\n"
        "Pasal 2B\n"
        "Aturan tambahan.\n"
    )

    sections = split_by_pasal(text)
    assert len(sections) == 2
    assert "1A" in sections[0].number


def test_split_no_pasal_fallback():
    """Test fallback jika tidak ada pattern Pasal."""
    text = (
        "Ini adalah dokumen tanpa pasal.\n"
        "Paragraf pertama yang cukup panjang untuk dianggap valid.\n"
        "\n"
        "Paragraf kedua yang juga cukup panjang dan punya makna lengkap.\n"
        "\n"
        "Paragraf ketiga sebagai penutup dokumen yang ini.\n"
    )

    sections = split_by_pasal(text)

    assert len(sections) >= 1
    assert all(isinstance(s, Section) for s in sections)


def test_split_empty_text():
    """Test teks kosong."""
    sections = split_by_pasal("")
    assert len(sections) == 1
    assert sections[0].number == "Full Text"
