import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_qa import run_qa


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Task2 phase-1 QA pipeline for a single question.")
    parser.add_argument("question", type=str)
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--qid", default="T2CLI001", help="Question id for chart naming")
    parser.add_argument("--debug", action="store_true", help="Include internal debug fields in output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_qa(args.question, db_path=args.db_path, question_id=args.qid, debug=args.debug)
    print(result)


if __name__ == "__main__":
    main()
