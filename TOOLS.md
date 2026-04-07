# TOOLS.md

## Extraction
- pdf_to_text(file)
- extract_tables(file)

## Cleaning
- remove_noise(text)
- normalize_format(text)

## Structuring
- split_pasal(text)
- split_ayat(text)

## Enrichment
- tag_topic(text) → (PPh, PPN, KUP)
- generate_embedding(text)

## Output
- save_json(data)
- validate_schema(data)

## Rules
- Always run validation after transform
- Never skip enrichment for production data
