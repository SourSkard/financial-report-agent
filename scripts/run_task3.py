import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task3_rag import run_rag


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Task 3 RAG pipeline.")
    parser.add_argument("question", type=str, help="User question text.")
    parser.add_argument("--db-path", type=str, default=None, help="SQLite path (default db/app.db).")
    parser.add_argument("--reports-dir", type=str, default="kb", help="Directory of Attachment 5 reports.")
    parser.add_argument("--qid", type=str, default="T3Q001", help="Question id for optional export.")
    parser.add_argument(
        "--out-xlsx",
        type=str,
        default="tmp/run_task3_preview.xlsx",
        help="Optional single-question preview workbook path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_rag(
        args.question,
        reports_dir=args.reports_dir,
        db_path=args.db_path,
        qid=args.qid,
        export_path=args.out_xlsx,
    )
    print(result)


if __name__ == "__main__":
    main()
