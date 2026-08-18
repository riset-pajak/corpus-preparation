# MEMORY.md

## Project Identity
Corpus pipeline for tax regulation intelligence system.

## Key Decisions
- Use structured JSON as main output
- Use pasal-level granularity
- Preserve raw + processed data
- Preserve original web HTML alongside downloaded PDF attachments
- Use filename pattern `nomor-YYYY-MM-DD` for web ingest artifacts

## Lessons Learned
- PDF extraction is unreliable; manual correction layer may be needed
- Legal documents require hierarchical parsing
- Cleaning step is critical
- Web pages can expose useful metadata directly in HTML fields, not only in visible text

## Future Direction
- Add semantic embedding
- Build regulation knowledge graph
