"""CLI untuk corpusprep -- pipeline persiapan corpus regulasi pajak."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from corpusprep import __version__

console = Console()

# Default paths
DEFAULT_DATA_DIR = Path("data")
DEFAULT_RAW_DIR = DEFAULT_DATA_DIR / "raw"
DEFAULT_PROCESSED_DIR = DEFAULT_DATA_DIR / "processed"
DEFAULT_OUTPUT_DIR = DEFAULT_DATA_DIR / "output"
DEFAULT_CONFIG = Path("configs/sources.yaml")


def _get_data_dirs(root: Path):
    """Dapatkan path folder data relatif terhadap root proyek."""
    return {
        "raw": root / "data" / "raw",
        "processed": root / "data" / "processed",
        "output": root / "data" / "output",
        "configs": root / "configs",
    }


def _ensure_dirs(root: Path) -> None:
    """Pastikan folder data ada."""
    dirs = _get_data_dirs(root)
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)


def _load_config(config_path: Path) -> dict:
    """Muat konfigurasi sumber data."""
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_corpus(output_dir: Path, docs: list[dict]) -> None:
    """Simpan corpus sebagai JSONL."""
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "corpus.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    console.print(f"[green bold]Corpus disimpan[/] ke [cyan]{jsonl_path}[/] ({len(docs)} dokumen)")


# -------------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------------

@click.group()
@click.version_option(version=__version__, prog_name="riset-pajak")
def main() -> None:
    """CorpusPrep -- Peralatan persiapan corpus regulasi perpajakan Indonesia."""
    pass


# ---- init ----------------------------------------------------------------

@main.command()
@click.option("--dir", "data_dir", default=".", help="Direktori root proyek (default: cwd)")
def init(data_dir: str) -> None:
    """Inisialisasi struktur direktori data."""
    root = Path(data_dir).resolve()
    _ensure_dirs(root)

    # Buat config default jika belum ada
    cfg_path = root / "configs" / "sources.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if not cfg_path.exists():
        default_cfg = {
            "sources": {
                "jdih_kemenkeu": {
                    "enabled": False,
                    "base_url": "https://jdih.kemenkeu.go.id",
                    "note": "Scraper JDIH Kemenkeu -- belum diimplementasi",
                },
                "peraturan_gov": {
                    "enabled": False,
                    "base_url": "https://peraturan.go.id",
                    "note": "Scraper peraturan.go.id -- belum diimplementasi",
                },
            },
            "processing": {
                "split_by": "pasal",
                "min_section_length": 50,
            },
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump(default_cfg, f, allow_unicode=True, default_flow_style=False)
        console.print(f"  Config dibuat: [cyan]{cfg_path}[/]")

    console.print(f"\n[green bold]Inisialisasi selesai![/]\n")
    console.print(f"  data/raw/        -- Taruh dokumen PDF/Word di sini")
    console.print(f"  data/processed/  -- Hasil pemrosesan teks")
    console.print(f"  data/output/     -- Corpus akhir (JSONL)")
    console.print(f"  configs/         -- Konfigurasi sumber data")
    console.print(f"\n  Mulai dengan:  [bold]riset-pajak add-pdf <file>[/]")


# ---- add-pdf -------------------------------------------------------------

@main.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--dir", "data_dir", default=".", help="Direktori root proyek")
def add_pdf(files: tuple[str, ...], data_dir: str) -> None:
    """Tambahkan file PDF/DOCX ke data/raw/."""
    root = Path(data_dir).resolve()
    _ensure_dirs(root)
    raw_dir = root / "raw"

    supported = {".pdf", ".docx", ".html", ".htm", ".txt"}
    dirs = _get_data_dirs(root)
    raw_dir = dirs["raw"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    added: list[str] = []
    skipped: list[str] = []

    for fp in files:
        src = Path(fp).resolve()
        ext = src.suffix.lower()
        if ext not in supported:
            skipped.append(f"{src.name} (format {ext} belum didukung)")
            continue

        dst = raw_dir / src.name
        # Hindari duplikasi
        if dst.exists():
            dst = raw_dir / f"{src.stem}_{len(list(raw_dir.iterdir()))}{src.suffix}"

        shutil.copy2(src, dst)
        added.append(dst.name)

    if added:
        console.print(f"\n[green bold]{len(added)} file ditambahkan[/] ke [cyan]data/raw/[/]")
        for name in added:
            console.print(f"  [green]+[/] {name}")
    if skipped:
        console.print(f"\n[yellow]{len(skipped)} file dilewati[/]")
        for msg in skipped:
            console.print(f"  [yellow]-[/] {msg}")


# ---- process -------------------------------------------------------------

@main.command()
@click.option("--dir", "data_dir", default=".", help="Direktori root proyek")
@click.option("--format", "fmt", default="all", type=click.Choice(["all", "markdown", "jsonl"]),
              help="Output format (default: all)")
def process(data_dir: str, fmt: str) -> None:
    """Proses dokumen di data/raw/ -- ekstrak, bersihkan, split, enrich."""
    root = Path(data_dir).resolve()
    dirs = _get_data_dirs(root)
    raw_dir = dirs["raw"]
    processed_dir = dirs["processed"]
    output_dir = dirs["output"]
    _ensure_dirs(root)

    files = list(raw_dir.glob("*"))
    if not files:
        console.print("[red]data/raw/ kosong. Tambahkan file dulu dengan:[/][bold] riset-pajak add-pdf <file>[/][/]")
        raise SystemExit(1)

    console.print(f"\n[bold]Memproses {len(files)} dokumen...[/]\n")

    docs_processed: list[dict] = []
    from corpusprep.pipeline import process_file

    for fp in sorted(files):
        try:
            doc = process_file(fp, str(processed_dir))
            docs_processed.append(doc.model_dump(mode="json"))
            console.print(f"  [green]OK[/] {fp.name:50s} -- {doc.section_count} sections, {doc.char_count} chars")
        except Exception as e:
            console.print(f"  [red]FAIL[/] {fp.name:50s} -- {e}")

    # Output
    if fmt in ("all", "jsonl"):
        _save_corpus(output_dir, docs_processed)
    if fmt in ("all", "markdown"):
        _save_markdown(output_dir, docs_processed)

    console.print(f"\n[green bold]Selesai![/] {len(docs_processed)} dokumen diproses.")


def _save_markdown(output_dir: Path, docs: list[dict]) -> None:
    """Simpan corpus sebagai satu file markdown besar."""
    md_path = output_dir / "corpus.md"
    with open(md_path, "w", encoding="utf-8") as f:
        for doc in docs:
            f.write(f"# {doc.get('full_identifier', doc.get('title', 'Dokumen Tanpa Judul'))}\n\n")
            if doc.get("topics"):
                f.write(f"Topik: {', '.join(doc['topics'])}\n\n")
            for sec in doc.get("sections", []):
                f.write(f"## {sec['number']}\n")
                if sec.get("title"):
                    f.write(f"{sec['title']}\n\n")
                f.write(f"{sec['text']}\n\n")
            f.write("---\n\n")
    console.print(f"  Markdown disimpan ke [cyan]{md_path}[/]")


# ---- inspect -------------------------------------------------------------

@main.command()
@click.option("--dir", "data_dir", default=".", help="Direktori root proyek")
@click.option("--raw", "show_raw", is_flag=True, help="Tampilkan daftar file di data/raw/")
def inspect(data_dir: str, show_raw: bool) -> None:
    """Tampilkan statistik corpus."""
    root = Path(data_dir).resolve()
    dirs = _get_data_dirs(root)
    output_dir = dirs["output"]

    # Check raw files
    raw_dir = dirs["raw"]
    raw_files = sorted(raw_dir.glob("*")) if raw_dir.exists() else []

    if show_raw:
        console.print("\n[bold]File di data/raw/:[/]")
        if raw_files:
            for f in raw_files:
                size_kb = f.stat().st_size / 1024
                console.print(f"  {f.name:50s}  {size_kb:>8.1f} KB")
        else:
            console.print("  [dim](kosong)[/]")

    # Check corpus
    jsonl_path = output_dir / "corpus.jsonl"
    if not jsonl_path.exists():
        console.print(f"\n[yellow]Belum ada corpus. Jalankan:[/][bold] riset-pajak process[/]")
        return

    docs: list[dict] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))

    total_sections = sum(len(d.get("sections", [])) for d in docs)

    # Tabel
    table = Table(title=f"Corpus Statistik -- {len(docs)} dokumen, {total_sections} sections")
    table.add_column("Jenis", style="cyan")
    table.add_column("Jumlah", justify="right")

    by_type: dict[str, int] = {}
    by_topic: dict[str, int] = {}
    years: list[int] = []

    for d in docs:
        rt = d.get("reg_type", "OTHER")
        by_type[rt] = by_type.get(rt, 0) + 1
        for t in d.get("topics", []):
            by_topic[t] = by_topic.get(t, 0) + 1
        if d.get("year"):
            years.append(d["year"])

    for k, v in sorted(by_type.items()):
        table.add_row(k, str(v))

    table.add_row("Total", str(len(docs)))

    console.print(table)

    if by_topic:
        console.print("\n[bold]Topik:[/]")
        for t, c in sorted(by_topic.items(), key=lambda x: -x[1]):
            console.print(f"  {t:15s}  {c}")

    if years:
        console.print(f"\n[bold]Rentang tahun:[/] {min(years)} -- {max(years)}")


# ---- status --------------------------------------------------------------

@main.command()
@click.option("--dir", "data_dir", default=".", help="Direktori root proyek")
def status(data_dir: str) -> None:
    """Tampilkan status pipeline secara ringkas."""
    root = Path(data_dir).resolve()
    _ensure_dirs(root)
    dirs = _get_data_dirs(root)

    raw_files = sorted(dirs["raw"].glob("*"))
    processed_files = sorted(dirs["processed"].glob("*"))
    jsonl = dirs["output"] / "corpus.jsonl"

    console.print("\n[bold]Status Pipeline CorpusPrep[/]\n")

    console.print(f"  data/raw/       : [cyan]{len(raw_files)}[/] file menunggu diproses")
    console.print(f"  data/processed/ : [cyan]{len(processed_files)}[/] file hasil proses")

    if jsonl.exists():
        count = sum(1 for _ in open(jsonl, encoding="utf-8") if _.strip())
        console.print(f"  data/output/    : corpus.jsonl ([cyan]{count}[/] dokumen)")
    else:
        console.print(f"  data/output/    : [dim]belum ada corpus[/]")

    console.print()


if __name__ == "__main__":
    main()
