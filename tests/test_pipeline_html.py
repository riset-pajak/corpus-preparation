"""Unit test: pipeline untuk HTML regulasi."""

from __future__ import annotations

from corpusprep.pipeline import process_file


def test_process_file_html(tmp_path):
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        """
        <html>
          <body>
            <div>PERATURAN MENTERI KEUANGAN</div>
            <div>NOMOR 99/PMK.03/2024</div>
            <div>TENTANG</div>
            <div>Ketentuan Pemotongan PPh Pasal 21</div>
            <div>Pasal 1</div>
            <div>Setiap wajib pajak wajib melaporkan penghasilannya.</div>
            <div>Pasal 2</div>
            <div>Tarif pajak ditetapkan sebesar 21 persen.</div>
          </body>
        </html>
        """,
        encoding="utf-8",
    )

    processed_dir = tmp_path / "processed"
    doc = process_file(html_path, str(processed_dir))

    assert doc.title
    assert "99" in doc.full_identifier
    assert doc.section_count >= 2
    assert "Pasal 1" in doc.sections[0].number
    assert "Setiap wajib pajak" in doc.full_text
    assert "<html>" not in doc.full_text.lower()
