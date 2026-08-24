"""Crawler indeks regulasi berbasis sumber.

Crawler ini hanya mengikuti link internal pada host sumber, membatasi jumlah
halaman, dan mendelegasikan penyimpanan dokumen ke collector sumber terkait.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import re
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# Path halaman navigasi/listing yang bukan dokumen regulasi.
# Dipelajari dari audit crawl JDIH/pajak.go.id (memory/2026-08-24.md).
_NAV_PATH_PATTERN = re.compile(
    r"/(search|berita|bantuan|direktori|faq|kamus-hukum|kebijakan-privasi"
    r"|prasyarat|prestasi-dan-penghargaan|rating|simplifikasi|sosialisasi"
    r"|statistik|struktur-organisasi|tentang-jdih|jdihn|infografis|tematik)"
    r"(/|$)"
    r"|/(atom|rss)\.xml$"
    r"|/taxonomy/term/\d+$",
    re.IGNORECASE,
)


def _is_navigation_url(url: str) -> bool:
    """True bila URL adalah halaman navigasi/listing, bukan dokumen regulasi."""
    return bool(_NAV_PATH_PATTERN.search(urlparse(url).path.lower()))


@dataclass(slots=True)
class CrawlResult:
    """Ringkasan hasil crawling."""

    discovered: int
    visited: int
    saved: int
    failed: list[str]


def _fetch_html(
    url: str,
    timeout: float = 30.0,
    retries: int = 2,
    retry_delay: float = 1.0,
) -> tuple[str, str]:
    """Ambil HTML dengan retry untuk kegagalan jaringan sementara.

    HTTP 403 tidak di-retry karena biasanya merupakan penolakan akses yang
    disengaja oleh server. Status 429 dan 5xx serta exception transport
    dicoba ulang secara terbatas.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        )
    }
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=httpx.Timeout(timeout, connect=timeout, read=timeout),
                headers=headers,
            ) as client:
                response = client.get(url)
                if response.status_code == 403:
                    response.raise_for_status()
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "html" not in content_type and not response.text.lstrip().startswith("<"):
                    return "", str(response.url)
                return response.text, str(response.url)
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_error = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            retryable = status is None or status == 429 or status >= 500
            if not retryable or attempt >= retries:
                raise
            time.sleep(retry_delay * (attempt + 1))

    assert last_error is not None
    raise last_error


def _normalise_url(url: str) -> str:
    url, _ = urldefrag(url)
    return url.rstrip("/") or url


def _is_internal(url: str, host: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() == host.lower()


def _looks_like_regulation_link(url: str, text: str, seed_path: str) -> bool:
    value = f"{url} {text}".lower()
    path = urlparse(url).path.lower()
    keywords = (
        "peraturan",
        "regulasi",
        "putusan",
        "keputusan",
        "permen",
        "perdirjen",
        "peraturan-direktur",
        "instruksi",
        "surat-edaran",
        "download",
        "dokumen",
    )
    if any(keyword in value for keyword in keywords):
        return True
    return path.startswith(seed_path.rstrip("/") + "/")


def _extract_links(html: str, base_url: str, seed_path: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    host = urlparse(base_url).netloc
    links: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"]).strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:")):
            continue
        absolute = _normalise_url(urljoin(base_url, href))
        if not _is_internal(absolute, host):
            continue
        if _is_navigation_url(absolute):
            continue
        text = anchor.get_text(" ", strip=True)
        if not _looks_like_regulation_link(absolute, text, seed_path):
            continue
        if absolute not in seen:
            seen.add(absolute)
            links.append(absolute)
    return links


def crawl_source(
    seed_url: str,
    raw_dir: Path,
    save_page: Callable[[str, Path], list[object]],
    *,
    max_pages: int = 100,
    max_depth: int = 2,
    delay: float = 0.25,
    timeout: float = 30.0,
) -> CrawlResult:
    """Crawl katalog regulasi dan simpan halaman yang terdeteksi.

    ``save_page`` menerima URL halaman regulasi dan raw directory, lalu
    mengembalikan artefak hasil ingest dari collector sumber.
    """
    if max_pages < 1:
        raise ValueError("max_pages harus >= 1")
    if max_depth < 0:
        raise ValueError("max_depth harus >= 0")

    raw_dir.mkdir(parents=True, exist_ok=True)
    seed_url = _normalise_url(seed_url)
    seed = urlparse(seed_url)
    queue: deque[tuple[str, int]] = deque([(seed_url, 0)])
    queued = {seed_url}
    visited: set[str] = set()
    failed: list[str] = []
    saved = 0

    while queue and len(visited) < max_pages:
        url, depth = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        # Halaman navigasi tetap dikunjungi untuk menemukan link dokumen,
        # tetapi tidak pernah disimpan sebagai artefak.
        if url != seed_url and _is_navigation_url(url):
            if delay:
                time.sleep(delay)
            continue

        try:
            html, final_url = _fetch_html(url, timeout=timeout)
            if not html:
                continue
            final_url = _normalise_url(final_url)
            if final_url not in visited:
                visited.add(final_url)

            # Simpan hanya halaman kandidat regulasi, bukan seluruh navigasi situs.
            if url != seed_url and _looks_like_regulation_link(
                final_url, BeautifulSoup(html, "html.parser").title.get_text(" ", strip=True)
                if BeautifulSoup(html, "html.parser").title
                else "",
                seed.path,
            ):
                try:
                    artifacts = save_page(final_url, raw_dir)
                    saved += len(artifacts)
                except Exception as exc:  # satu halaman gagal tidak menghentikan crawl
                    failed.append(f"{final_url} -- {exc}")

            if depth < max_depth:
                for link in _extract_links(html, final_url, seed.path):
                    if link not in queued and link not in visited:
                        queued.add(link)
                        queue.append((link, depth + 1))
        except Exception as exc:
            failed.append(f"{url} -- {exc}")

        if delay:
            time.sleep(delay)

    return CrawlResult(
        discovered=len(queued),
        visited=len(visited),
        saved=saved,
        failed=failed,
    )
