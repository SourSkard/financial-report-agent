import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_batch_pipeline import bucket_questions, parse_questions, write_bucket_outputs


DEFAULT_OUT_JSON = ROOT / "tmp" / "task2_bucket.json"
DEFAULT_OUT_TXT = ROOT / "tmp" / "task2_bucket.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bucket Attachment 4 questions under Task2 phase-1 support rules.")
    parser.add_argument("--questions-xlsx", default=None, help="Attachment 4 style workbook path. If omitted, auto-discover the first matching .xlsx.")
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON))
    parser.add_argument("--out-txt", default=str(DEFAULT_OUT_TXT))
    return parser.parse_args()


def print_summary(rows) -> None:
    direct_rows = [row for row in rows if row["expected_behavior"] == "direct_answer"]
    clarify_rows = [row for row in rows if row["expected_behavior"] == "clarify_first"]
    degrade_rows = [row for row in rows if row["expected_behavior"] == "degrade"]

    print("== Task2 Bucket ==")
    print(f"total_turns={len(rows)}")
    print(f"direct_answer={len(direct_rows)}")
    print(f"clarify_first={len(clarify_rows)}")
    print(f"degrade={len(degrade_rows)}")
    print("")
    for row in rows:
        print(
            f"{row['qid']} | {row['expected_behavior']} | {row['question_type']} | "
            f"chart={str(row['allow_chart']).lower()} | {row['original_question']}"
        )


def main() -> None:
    args = parse_args()
    turns = parse_questions(questions_xlsx=args.questions_xlsx)
    rows = bucket_questions(turns)
    write_bucket_outputs(rows, args.out_json, args.out_txt)
    print_summary(rows)


if __name__ == "__main__":
    main()
