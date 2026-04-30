# Acceptance Checklist (Local)

## Task1 Default Path (must be used)
- Parser default: `pdfplumber`.
- Text fallback: `pypdf`.
- Table extraction: `Camelot`.
- Complex-page fallback: `MinerU`.
- `Docling` is optional only and must not be treated as default.

## Run Command (real sample)
```bash
python scripts/run_task1.py --pdf "B题-示例数据/示例数据/附件2：财务报告/reports-上交所/600080_20230428_FQ2V.pdf" --max-pages 12 --timeout 120
```

## Expected Logs (default)
- `Page parsed page=... source=pdfplumber`
- `Camelot flavor=stream/lattice page=... tables=...`
- `Route selected: summary_kpi_extractor / full_report_extractor`
- `Ingest completed. Counts: ...`

## DB Path
- Official path: `db/app.db`

## Health Check
```bash
python scripts/check_task1_db.py --db-path db/app.db
```
