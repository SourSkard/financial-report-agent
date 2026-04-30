import argparse
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task1_ingest import run_ingest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Task 1 ingestion pipeline.")
    parser.add_argument("--pdf", dest="pdf_path", type=str, help="Path to PDF file.")
    parser.add_argument(
        "--use-sample",
        action="store_true",
        help="Use built-in sample data instead of parsing a PDF.",
    )
    parser.add_argument(
        "--db-path",
        dest="db_path",
        type=str,
        help="Optional SQLite path (default db/app.db).",
    )
    parser.add_argument(
        "--max-pages",
        dest="max_pages",
        type=int,
        help="Only parse the first N pages (debug aid).",
    )
    parser.add_argument(
        "--start-page",
        dest="start_page",
        type=int,
        help="Only parse starting from this page (1-based).",
    )
    parser.add_argument(
        "--end-page",
        dest="end_page",
        type=int,
        help="Only parse up to this page (1-based, inclusive).",
    )
    parser.add_argument(
        "--timeout",
        dest="timeout",
        type=int,
        default=120,
        help="Parser timeout in seconds (default 120s).",
    )
    parser.add_argument(
        "--no-ocr",
        dest="no_ocr",
        action="store_true",
        help="Disable OCR during parsing if the backend supports it.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = args.db_path
    if db_path:
        os.environ["TEDDY_DB_PATH"] = db_path

    sample = None
    if args.use_sample:
        sample = [
            {
                "table": "income_sheet",
                "company": "DemoCorp",
                "report_period": "2023-12-31",
                "item": "Revenue",
                "value": "1200.5",
                "unit": "万元",
                "source_path": args.pdf_path or "sample.pdf",
            },
            {
                "table": "balance_sheet",
                "company": "DemoCorp",
                "report_period": "2023-12-31",
                "item": "Total Assets",
                "value": "3500",
                "unit": "万元",
                "source_path": args.pdf_path or "sample.pdf",
            },
        ]
    counts = run_ingest(
        pdf_path=args.pdf_path,
        raw_tables=sample,
        use_fake_parser=args.use_sample,
        db_path=db_path,
        max_pages=args.max_pages,
        timeout=args.timeout,
        use_ocr=not args.no_ocr,
        start_page=args.start_page,
        end_page=args.end_page,
    )
    print("Ingest done:", counts)


if __name__ == "__main__":
    main()
