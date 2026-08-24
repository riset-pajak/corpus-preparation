# TOOLS.md

## Extraction
- pdf_to_text(file) -- pdfplumber
- extract_tables(file)
- html_to_text(html) -- BeautifulSoup parser untuk ingest web
- docx_to_text(file) -- python-docx

## Cleaning
- remove_noise(text)
- normalize_format(text)

## Structuring
- split_pasal(text, min_length=50) -> list[Section]
- _fallback_split(text, min_length) -> paragraph-based fallback

## Enrichment
- classify_regulation(text) -> RegulationType (UU/PMK/PP/PER/SE/KEP/INSTR/OTHER)
- extract_topics(text) -> list[TaxTopic] (PPh, PPN, PPnBM, PBB, BPHTB, KUP, Bea Materai, DJP-Admin, Umum)
- _guess_reg_type(text) -> reg type from header keywords

## Metadata
- extract_identifier(text, source_file) -> {number, year, full_identifier, reg_type_short} - multi-strategy
  1. Header standard format (NOMOR 99/PMK.03/2024)
  2. Filename parsing (PMK-68-PMK-03-2024.pdf)  
  3. Preamble "<JENIS> NOMOR <n> TAHUN <tahun>" (cut before "Menimbang" to avoid referenced numbers overriding document identity)
  4. Bare-slash fallback num/TYPE/year in preamble only when reg_type unknown
- extract_title(text) -> str

## Output
- save_json(data) -- JSONL export
- validate_schema(data) -- Pydantic model validation

## Database (SQLite)
- connect(db_path) -> Connection + initialize schema
- save_documents(db_path, documents) -> int saved count (upsert based on full_identifier)
- import_jsonl(db_path, jsonl_path) -> int
- counts(db_path) -> dict{regulations, sections, topics}
- status(db_path) -> dict with total, by_reg_type, by_status, year_range, topics
- search_by_title(db_path, query, limit) -> list[dict]
- search_by_year(db_path, year) -> list[dict]
- get_regulation(db_path, identifier) -> dict|None (with sections + topics joined)

## Collectors
- fetch_page(url) -> html, final_url, headers
- save_web_regulation(url, raw_dir) -> list[DownloadedArtifact]
- crawl_source(seed_url, raw_dir, save_page, max_pages, max_depth, delay) -> CrawlResult
- _is_navigation_url(url) -> bool (filter halaman navigasi/listing seperti search, berita, direktori, tax*/term/*)

## Rules
- Always run validation after transform
- Never skip enrichment for production data
- Always preserve original text in data/raw/
- If parsing fails → mark as "unparsed", never fabricate content
