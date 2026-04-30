# Task1 Real Integration Notes

## Current Default Parser Path
- Default: `pdfplumber` for page text/layout.
- Text fallback: `pypdf`.
- Table extraction: `Camelot`.
- Complex-page fallback: `MinerU`.
- `Docling`: optional backend only, not the default path.

## Row Contract (unchanged)
Each extracted row should keep:
- required: `table`, `company`, `report_period`, `item`, `value`, `unit`, `source_path`
- optional: `page`, `raw_headers`

## Why this setup
- Stable on local sample set and easier to debug with page-level logs.
- Keeps Task1 outputs compatible with mapper/cleaner/validator/loader.
