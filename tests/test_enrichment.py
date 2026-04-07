"""Unit test: enrichment - klasifikasi dan topic extraction."""

from corpusprep.enrichment import classify_regulation, extract_topics
from corpusprep.models import RegulationType, TaxTopic


def test_classify_uu():
    text = "Undang-Undang Nomor 6 Tahun 1983 tentang Ketentuan Umum"
    assert classify_regulation(text) == RegulationType.UU


def test_classify_pmk():
    text = "Peraturan Menteri Keuangan Nomor 68/PMK.03/2024 tentang"
    assert classify_regulation(text) == RegulationType.PMK


def test_classify_se():
    text = "Surat Edaran Nomor SE-42/PJ.2/2023 tentang Pemenuhan Kewajiban Perpajakan"
    assert classify_regulation(text) == RegulationType.SE


def test_classify_from_filename_pattern():
    text = "Ini mengatur tentang PMK-68/PMK.03/2024 yang terbaru."
    assert classify_regulation(text) == RegulationType.PMK


def test_classify_unknown():
    text = "Dokumen tanpa pola regulasi yang jelas."
    assert classify_regulation(text) == RegulationType.OTHER


def test_extract_topics_pph():
    text = "PPh pasal 21 dikenakan atas penghasilan yang diterima karyawan."
    topics = extract_topics(text)
    assert TaxTopic.PPh in topics


def test_extract_topics_multiple():
    text = "PPN dan PPh pasal 23 diatur dalam peraturan ini."
    topics = extract_topics(text)
    assert TaxTopic.PPN in topics
    assert TaxTopic.PPh in topics


def test_extract_topics_kup():
    text = "Ketentuan Umum dan Tata Cara Perpajakan mengatur SP2D dan pemeriksaan pajak."
    topics = extract_topics(text)
    assert TaxTopic.KUP in topics


def test_extract_topics_empty():
    text = "Dokumen ini tidak membahas topik pajak spesifik."
    topics = extract_topics(text)
    assert topics == []
