import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_qa_bonus import run_qa_bonus


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Task2 bonus QA without touching formal outputs.")
    parser.add_argument("question", help="Question text.")
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--qid", default="T2BONUS001")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--out-json", default="", help="Optional JSON output path under tmp/.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_qa_bonus(args.question, db_path=args.db_path, question_id=args.qid, debug=args.debug)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
