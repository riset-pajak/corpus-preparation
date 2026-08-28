# TOOLS.md

## Extraction
- pdf_to_text(file) -- pdfplumber
- extract_tables(file) -- pdfplumber (if needed)
- html_to_text(html) -- BeautifulSoup parser untuk ingest web
- docx_to_text(file) -- python-docx
- fetch_page(url) -> html, final_url, headers -- httpx with browser UA

## Cleaning
- remove_noise(text) -- page numbers, footer artifacts
- normalize_format(text) -- whitespace, encoding
- cut_at_menimbang(text) -- prevent referenced number override

## Structuring
- split_pasal(text, min_length=50) -> list[Section] -- regex Pasal/ayat
- _fallback_split(text, min_length) -> paragraph-based fallback
- _clean_section_body(body) -- remove page numbers, short artifacts
- _split_title_and_body(body) -> (title, text) -- first line if short

## Enrichment
- classify_regulation(text) -> RegulationType (UU/PMK/PP/PER/SE/KEP/INSTR/OTHER)
- extract_topics(text) -> list[TaxTopic] (PPh, PPN, PPnBM, PBB, BPHTB, KUP, Bea_Materai, DJP_Admin, Umum)
- _guess_reg_type(text) -> reg type from header keywords
- _TYPE_KEYWORDS, _TOPIC_KEYWORDS -- regex/keyword mappings

## Metadata
- extract_identifier(text, source_file) -> {number, year, full_identifier, reg_type_short} - multi-strategy:
  1. Header standard format (NOMOR 99/PMK.03/2024)
  2. Filename parsing (PMK-68-PMK-03-2024.pdf)
  3. Preamble "<JENIS> NOMOR <n> TAHUN <tahun>" (cut before "Menimbang")
  4. Bare-slash fallback num/TYPE/year in preamble only when reg_type unknown
  5. Loose regex fallback
- extract_title(text) -> str -- after "TENTANG" or first long non-header line
- _canonicalize_regulation_number -- normalize slashes, dashes, spaces
- _filename_safe_number -- strip year suffix, replace slashes

## Output
- save_json(data) -- JSONL export
- save_markdown(data) -- Markdown export
- validate_schema(data) -- Pydantic model validation

## Database (SQLite + FTS5)
- connect(db_path) -> Connection + initialize schema
- save_documents(db_path, documents) -> int saved count (upsert on full_identifier)
- import_jsonl(db_path, jsonl_path) -> int
- counts(db_path) -> dict{regulations, sections, topics}
- status(db_path) -> dict with total, by_reg_type, by_status, year_range, topics
- search_by_title(db_path, query, limit) -> list[dict] (LIKE)
- search_by_fts(db_path, query, limit) -> list[dict] (FTS5 two-step: MATCH then IN lookup)
- search_by_year(db_path, year) -> list[dict]
- get_regulation(db_path, identifier) -> dict|None (with sections + topics joined)
- _populate_fts_tables(connection) -- sync FTS5 via INSERT OR REPLACE using rowid
  * Uses try/except per table for DELETE to handle malformed DB edge case
  * Uses INSERT OR REPLACE instead of DELETE+INSERT for robustness

## Collectors (Web Ingestion)
- fetch_page(url) -> html, final_url, headers
- save_web_regulation(url, raw_dir) -> list[DownloadedArtifact] (html + pdf attachments)
- _extract_regulation_meta(soup, fallback_url) -> {number, issue_date, filename_base}
- _extract_pdf_links(soup, base_url) -> list[str]
- _download_file(url, raw_dir, base_name) -> Path
- _sanitize_filename, _unique_path -- safe file naming

## Crawler (Index Crawling)
- crawl_source(seed_url, raw_dir, save_page, max_pages, max_depth, delay) -> CrawlResult
- _is_navigation_url(url) -> bool (filters: search, berita, bantuan, direktori, taxonomy/term, atom.xml, rss.xml)
- _extract_links(html, base_url, seed_path) -> list[str] (internal, non-nav, regulation-like)
- _fetch_html(url, timeout, retries) -- retry on 429/5xx, fail fast on 403
- _looks_like_regulation_link(url, text, seed_path) -- keyword + path matching

## Tests
### test_database.py (20 tests)
- Schema creation & column structure
- Upsert operations: basic, existing identifier, sections replaced
- Counts: empty db, with data
- Status: empty db, full statistics with type/status/years/topics
- Search: title found/not found, year filter, regulation detail
- FTS5: tables populated, search working
- Import JSONL: with data, empty file

### test_crawler_detailed.py (11 tests)
- Navigation URL detection (extensive cases)
- Regulation URL non-detection
- Link extraction with nav filtering
- Internal-only link filtering
- Regulation link type detection (multi-seed-path)
- Edge cases: empty HTML, duplicates, depth limit, result structure

## Rules
- Always run validation after transform (Pydantic)
- Never skip enrichment for production data
- Always preserve original text in data/raw/
- If parsing fails -> mark as "unparsed", never fabricate content
- Cut header at "Menimbang" before identifier extraction
- Navigation pages never saved as artifacts (only visited for link discovery)