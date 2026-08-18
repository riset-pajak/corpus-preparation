"""Unit test: collector web regulasi."""

from __future__ import annotations

from pathlib import Path

from corpusprep.collectors.web import save_web_regulation


class _FakeResponse:
    def __init__(self, url: str, text: str = "", content: bytes = b"", headers: dict | None = None):
        self.url = url
        self.text = text
        self.content = content
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        return None


class _FakeClient:
    def __init__(self, page_html: str, pdf_bytes: bytes):
        self.page_html = page_html
        self.pdf_bytes = pdf_bytes

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def get(self, url: str) -> _FakeResponse:
        if url == "https://pajak.go.id/id/peraturan/sample":
            return _FakeResponse(
                url="https://pajak.go.id/id/peraturan/sample",
                text=self.page_html,
                headers={"content-type": "text/html; charset=utf-8"},
            )
        if url == "https://pajak.go.id/sites/default/files/lampiran/sample.pdf":
            return _FakeResponse(
                url=url,
                content=self.pdf_bytes,
                headers={"content-disposition": 'attachment; filename="Lampiran PER 8 Tahun 2026.pdf"'},
            )
        raise AssertionError(f"Unexpected URL: {url}")


def test_save_web_regulation_downloads_html_and_pdf(tmp_path, monkeypatch):
    html = """
    <html>
      <head><title>Peraturan Direktur Jenderal Pajak</title></head>
      <body>
        <h1>Peraturan Direktur Jenderal Pajak</h1>
        <div class="field field--name-field-nomor-dokumen field--type-string field__item">PER-8/PJ/2026</div>
        <div class="field field--name-field-tanggal-peraturan field--type-datetime field--label-inline clearfix">
          <time datetime="2026-07-28T12:00:00Z" class="datetime">28-07-2026</time>
        </div>
        <a href="/sites/default/files/lampiran/sample.pdf">Lampiran PDF</a>
      </body>
    </html>
    """

    fake_client = _FakeClient(html, b"%PDF-1.4 fake")
    monkeypatch.setattr("corpusprep.collectors.web.httpx.Client", lambda *args, **kwargs: fake_client)

    artifacts = save_web_regulation("https://pajak.go.id/id/peraturan/sample", tmp_path)

    assert len(artifacts) == 2
    assert artifacts[0].path.name == "PER-8-PJ-2026-07-28.html"
    assert artifacts[0].kind == "html"
    assert artifacts[0].path.suffix == ".html"
    assert artifacts[0].path.exists()
    assert artifacts[1].path.name == "PER-8-PJ-2026-07-28.pdf"
    assert artifacts[1].kind == "pdf"
    assert artifacts[1].path.suffix == ".pdf"
    assert artifacts[1].path.exists()


def test_save_web_regulation_preserves_dot_in_number(tmp_path, monkeypatch):
    html = """
    <html>
      <body>
        <div class="field field--name-field-nomor-dokumen field--type-string field__item">34/MK/EF.2/2026</div>
        <div class="field field--name-field-tanggal-peraturan field--type-datetime field--label-inline clearfix">
          <time datetime="2026-07-28T12:00:00Z" class="datetime">28-07-2026</time>
        </div>
      </body>
    </html>
    """

    class _NoPdfClient(_FakeClient):
        def get(self, url: str) -> _FakeResponse:
            if url == "https://pajak.go.id/id/peraturan/sample":
                return _FakeResponse(
                    url="https://pajak.go.id/id/peraturan/sample",
                    text=html,
                    headers={"content-type": "text/html; charset=utf-8"},
                )
            raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("corpusprep.collectors.web.httpx.Client", lambda *args, **kwargs: _NoPdfClient(html, b""))

    artifacts = save_web_regulation("https://pajak.go.id/id/peraturan/sample", tmp_path)

    assert len(artifacts) == 1
    assert artifacts[0].path.name == "34-MK-EF.2-2026-07-28.html"
