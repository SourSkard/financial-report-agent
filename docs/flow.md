# Development Flow

## Phases
1. Task1 (implemented): PDF -> extraction -> mapping -> cleaning -> validation -> SQLite.
2. Task2 (implemented): Question -> structured intent -> clarification -> constrained SQL -> query -> JSON/chart/result_2.xlsx.
3. Task3 (implemented minimal): planning -> structured query + retrieval -> merge -> references -> result_3.xlsx.

## Task1 Default Chain
- Page parsing: pdfplumber (default), pypdf text fallback.
- Table extraction: Camelot (stream/lattice).
- Complex-page fallback: MinerU backend.
- Docling: optional/deprecated backend only, NOT default.

Expected default logs include:
- `Page parsed page=... source=pdfplumber`
- `Camelot flavor=stream/lattice page=... tables=...`
- `Route selected: summary_kpi_extractor / full_report_extractor`
- `Ingest completed. Counts: ...`

## Constraints
- Keep constrained SQL in Task2/Task3.
- Keep output path conventions (`db/app.db`, `./result/...`, `result_2.xlsx`, `result_3.xlsx`).
