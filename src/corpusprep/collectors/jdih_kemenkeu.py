"""Scraper untuk JDIH Kementerian Keuangan (jdih.kemenkeu.go.id)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Iterable, List, Optional

from urllib.parse import urljoin, urlparse, unquote

import httpx
from bs4 import BeautifulSoup


@dataclass(slots=True)
class DownloadedArtifact:
    """Satu artefak yang diunduh dari halaman web."""

    url: str
    path: Path
    kind: str  # "html" atau "pdf"


def fetch_page(url: str, timeout: float = 30.0) -> tuple[str, str, dict[str, str]]:
    """Ambil halaman HTML dan kembalikan isi, final URL, dan headers."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        )
    }
    with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text, str(response.url), dict(response.headers)


def _extract_regulation_meta(soup: BeautifulSoup, fallback_url: str) -> dict[str, str]:
    """Ekstraksi metadata regulasi dari halaman HTML."""
    number = ""
    issue_date = ""

    # Coba cari nomor regulasi di berbagai selector
    for selector in [
        ".field--name-field-nomor-dokumen",
        ".nomor-dokumen",
        "[property='dc:identifier']",
        ".document-number",
    ]:
        node = soup.select_one(selector)
        if node:
            number = _canonicalize_regulation_number(node.get_text(" ", strip=True))
            break

    # Cari tanggal
    for selector in [
        ".field--name-field-tanggal-peraturan time[datetime]",
        "time[datetime]",
        ".tanggal-peraturan",
        "[property='dc:date']",
    ]:
        node = soup.select_one(selector)
        if node and node.has_attr("datetime"):
            raw_dt = node["datetime"].strip()
            try:
                from datetime import datetime as dt_mod
                issue_date = dt_mod.fromisoformat(raw_dt.replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                issue_date = _normalize_date_text(node.get_text(" ", strip=True))
            break
    if not issue_date:
        for selector in [
            ".field--name-field-tanggal-peraturan",
            ".tanggal-peraturan",
        ]:
            node = soup.select_one(selector)
            if node:
                issue_date = _normalize_date_text(node.get_text(" ", strip=True))
                break

    # Fallback: ambil dari judul halaman
    if not number:
        title = _extract_page_title(soup)
        number = _number_from_text(title)

    if not issue_date:
        issue_date = _normalize_date_text(_extract_page_title(soup))

    if not number:
        number = _slug_from_url(fallback_url)

    if not issue_date:
        issue_date = "unknown-date"

    filename_base = _sanitize_filename(f"{_filename_safe_number(number)}-{issue_date}")

    return {
        "number": number,
        "issue_date": issue_date,
        "filename_base": filename_base,
    }


def _extract_page_title(soup: BeautifulSoup) -> str:
    """Ambil judul halaman."""
    candidates = [soup.find("h1"), soup.find("title")]
    for candidate in candidates:
        if candidate and candidate.get_text(strip=True):
            return candidate.get_text(" ", strip=True)
    return ""


def _normalize_regulation_number(value: str) -> str:
    return _filename_safe_number(_canonicalize_regulation_number(value))


def _canonicalize_regulation_number(value: str) -> str:
    """Normalisasi nomor regulasi Indonesia."""
    text = value.strip().upper()
    text = text.replace("／", "/")
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s*/\s*", "/", text)
    text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"\s+", "", text)
    text = text.replace("__", "_")
    return text


def _filename_safe_number(value: str) -> str:
    """Buat nama file yang aman dari nomor regulasi."""
    text = re.sub(r"[/-](19\d{2}|20\d{2})$", "", value)
    text = text.replace("/", "-")
    return _sanitize_filename(text)


def _number_from_text(value: str) -> str:
    """Ekstraksi nomor regulasi dari teks."""
    text = value.upper()
    # Pola standar: PER-8-PJ-2026-07-28 atau PMK-99/2024
    match = re.search(
        r"\b((?:PER|PMK|PP|UU|SE|KEP|INSTR)?-?\d+(?:/[A-Z0-9.]+)+/\d{4})\b",
        text,
    )
    if match:
        return _canonicalize_regulation_number(match.group(1))
    # Fallback: cari kata jenis di awal
    for token in text.replace("/", " ").replace("-", " ").split():
        if token.startswith(("PER", "PMK", "PP", "UU", "SE", "KEP", "INSTR")):
            return _canonicalize_regulation_number(token)
    return ""


def _normalize_date_text(value: str) -> str:
    """Normalisasi tanggal ke format ISO."""
    if not value:
        return ""
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            from datetime import datetime as dt_mod
            return dt_mod.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def _extract_pdf_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Ekstrak semua link PDF dari halaman."""
    seen: set[str] = set()
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href:
            continue
        absolute = urljoin(base_url, href)
        # Hanya ambil link yang terlihat seperti PDF
        path = urlparse(absolute).path.lower()
        if not (path.endswith(".pdf") or ".pdf" in path):
            # Cek teks anchor juga
            text = anchor.get_text(" ", strip=True).lower()
            if "pdf" not in text and "lampiran" not in text:
                continue
        if absolute in seen:
            continue
        seen.add(absolute)
        links.append(absolute)
    return links


def _download_file(url: str, raw_dir: Path, timeout: float = 30.0, base_name: str = "") -> Path:
    """Unduh file dari URL ke direktori raw."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        )
    }
    with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
        # Coba dapatkan nama dari content-disposition
        filename = _filename_from_response(url, response.headers.get("content-disposition"))
        if not filename:
            filename = _slug_from_url(str(response.url))
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
        if base_name:
            filename = f"{base_name}{Path(filename).suffix.lower() or '.pdf'}"
        path = _unique_path(raw_dir, filename)
        path.write_bytes(response.content)
        return path


def _filename_from_response(url: str, content_disposition: str | None) -> str:
    """Dapatkan nama file dari header response."""
    if content_disposition:
        for token in content_disposition.split(";"):
            token = token.strip()
            if token.lower().startswith("filename*="):
                raw_name = token.split("=", 1)[1].strip().strip('"')
                if "''" in raw_name:
                    raw_name = raw_name.split("''", 1)[1]
                return _sanitize_filename(unquote(raw_name))
            if token.lower().startswith("filename="):
                raw_name = token.split("=", 1)[1].strip().strip('"')
                return _sanitize_filename(unquote(raw_name))
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return _sanitize_filename(unquote(name))


def _slug_from_url(url: str) -> str:
    """Buat slug dari URL."""
    parsed = urlparse(url)
    parts = [parsed.netloc, parsed.path.strip("/")]
    slug = "-".join(part for part in parts if part)
    if not slug:
        slug = "download"
    return _sanitize_filename(slug)


def _sanitize_filename(value: str) -> str:
    """Bersihkan string menjadi nama file yang valid."""
    cleaned = value.strip().replace("\n", " ").replace("\r", " ")
    cleaned = cleaned.replace("/", "-").replace("\\", "-")
    cleaned = "".join(ch if ch.isalnum() or ch in {" ", "-", "_", ".", "(", ")"} else "-" for ch in cleaned)
    cleaned = " ".join(cleaned.split())
    cleaned = cleaned.strip(" ._")
    return cleaned or "download"


def _unique_path(directory: Path, filename: str) -> Path:
    """Dapatkan path unik (tanpa overwrite)."""
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    suffix = candidate.suffix
    stem = candidate.stem
    counter = 2
    while True:
        next_candidate = directory / f"{stem}_{counter}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        counter += 1


def save_web_regulation(url: str, raw_dir: Path) -> list[DownloadedArtifact]:
    """
    Unduh halaman regulasi dari JDIH Kemenkeu dan semua lampiran PDF yang ditemukan.

    Strategi:
    - Simpan HTML halaman sebagai sumber asli
    - Simpan PDF lampiran jika ada
    - Hindari overwrite dengan nama file unik
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    html, final_url, _ = fetch_page(url)
    soup = BeautifulSoup(html, "html.parser")
    meta = _extract_regulation_meta(soup, final_url)
    base_name = meta["filename_base"]
    artifacts: list[DownloadedArtifact] = []

    html_path = _unique_path(raw_dir, f"{base_name}.html")
    html_path.write_text(html, encoding="utf-8")
    artifacts.append(DownloadedArtifact(url=final_url, path=html_path, kind="html"))

    for attachment_url in _extract_pdf_links(soup, final_url):
        pdf_path = _download_file(attachment_url, raw_dir, base_name=base_name)
        artifacts.append(DownloadedArtifact(url=attachment_url, path=pdf_path, kind="pdf"))

    return artifacts