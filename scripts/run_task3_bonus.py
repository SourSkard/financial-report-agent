import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task3_rag_bonus import run_rag_bonus


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single Task3 bonus query.")
    parser.add_argument("question")
    parser.add_argument("--reports-dir", required=True)
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--qid", default="T3BONUS001")
    parser.add_argument("--out-json", default="tmp/run_task3_bonus.json")
    return parser.parse_args()


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = parse_args()
    result = run_rag_bonus(
        args.question,
        reports_dir=args.reports_dir,
        db_path=args.db_path,
        qid=args.qid,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
    print(rendered)
    print(f"Saved: {out_path.resolve()}")


if __name__ == "__main__":
    main()
