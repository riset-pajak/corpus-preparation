"""Unit test: crawler -- filter halaman navigasi (hasil audit 2026-08-24)."""

from __future__ import annotations

from corpusprep.collectors.crawler import _is_navigation_url, _extract_links


def test_navigation_urls_are_detected():
    nav_urls = [
        "https://jdih.kemenkeu.go.id/search",
        "https://jdih.kemenkeu.go.id/search?page=5",
        "https://jdih.kemenkeu.go.id/berita",
        "https://jdih.kemenkeu.go.id/direktori",
        "https://jdih.kemenkeu.go.id/tematik/2178",
        "https://jdih.kemenkeu.go.id/infografis",
        "https://jdih.kemenkeu.go.id/atom.xml",
        "https://pajak.go.id/taxonomy/term/14025",
    ]
    for url in nav_urls:
        assert _is_navigation_url(url), url


def test_regulation_urls_are_not_flagged():
    doc_urls = [
        "https://pajak.go.id/id/peraturan/PER-8-PJ-2026",
        "https://jdih.kemenkeu.go.id/dok/100-puu-xx",
        "https://peraturan.go.id/id/peraturan/PMK-61-2026",
        "https://jdih.kemenkeu.go.id/simplifikasi-regulasi/dokumen/123",  # path dokumen di bawah menu
    ]
    for url in doc_urls:
        assert not _is_navigation_url(url), url


def test_extract_links_skips_navigation_pages():
    html = """
    <html><body>
      <a href="/dok/100-puu-xx">Putusan 100/PUU-XX/2022</a>
      <a href="/search">Pencarian</a>
      <a href="/berita-jdihn">Berita JDIHN</a>
      <a href="/peraturan/lainnya">Peraturan Lainnya</a>
    </body></html>
    """
    links = _extract_links(html, "https://jdih.kemenkeu.go.id/halaman", "/halaman")
    assert "https://jdih.kemenkeu.go.id/dok/100-puu-xx" in links
    assert "https://jdih.kemenkeu.go.id/search" not in links
    assert not any("/berita" in link for link in links)
