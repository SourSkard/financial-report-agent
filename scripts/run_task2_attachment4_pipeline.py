import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_batch_pipeline import run_attachment4_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full reusable Task2 Attachment 4 pipeline.")
    parser.add_argument("--questions-xlsx", default=None, help="Attachment 4 style workbook path. If omitted, auto-discover the first matching .xlsx.")
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--bucket-json", default=str(ROOT / "tmp" / "task2_bucket.json"))
    parser.add_argument("--bucket-txt", default=str(ROOT / "tmp" / "task2_bucket.txt"))
    parser.add_argument("--skeleton-json", default=str(ROOT / "tmp" / "task2_answer_skeleton.json"))
    parser.add_argument("--skeleton-txt", default=str(ROOT / "tmp" / "task2_answer_skeleton.txt"))
    parser.add_argument("--result2-xlsx", default=str(ROOT / "result_2.xlsx"))
    parser.add_argument("--preview-txt", default=str(ROOT / "tmp" / "result_2_preview.txt"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outcome = run_attachment4_pipeline(
        questions_xlsx=args.questions_xlsx,
        db_path=args.db_path,
        bucket_json=args.bucket_json,
        bucket_txt=args.bucket_txt,
        skeleton_json=args.skeleton_json,
        skeleton_txt=args.skeleton_txt,
        result2_xlsx=args.result2_xlsx,
        preview_txt=args.preview_txt,
    )
    print("== Task2 full pipeline complete ==")
    print(f"turns={len(outcome['turns'])}")
    print(f"bucket_rows={len(outcome['bucket_rows'])}")
    print(f"skeleton_rows={len(outcome['skeleton_rows'])}")
    print(f"result_rows={len(outcome['entries'])}")


if __name__ == "__main__":
    main()
