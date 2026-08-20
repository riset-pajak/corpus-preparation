# MEMORY.md

## Project Identity
Corpus pipeline for tax regulation intelligence system.

## Key Decisions
- Use SQLite `data.db` as the local canonical database
- Keep structured JSONL and Markdown as audit/review exports
- Use pasal-level granularity
- Preserve raw + processed data
- Preserve original web HTML alongside downloaded PDF attachments
- Use filename pattern `nomor-YYYY-MM-DD` for web ingest artifacts
- Crawl sources with internal-link, max-pages, max-depth, and delay safeguards

## Current Implementation
- `riset-pajak process` upserts regulations, sections, and topics into `data.db`
- `riset-pajak crawl --source <name>` crawls configured source indexes
- Supported sources: JDIH Kemenkeu, peraturan.go.id, Mahkamah Konstitusi, DDTC, and DJP
- Sample database is committed with 110 regulations, 1,360 sections, and 161 topics
- Database code lives in `src/corpusprep/database.py`

## Lessons Learned
- PDF extraction is unreliable; manual correction layer may be needed
- Legal documents require hierarchical parsing
- Cleaning step is critical
- Web pages can expose useful metadata directly in HTML fields, not only in visible text

## Future Direction
- Add semantic embedding
- Build regulation knowledge graph
