import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_batch_pipeline import build_answer_skeleton, write_answer_skeleton_outputs


DEFAULT_BUCKET_JSON = ROOT / "tmp" / "task2_bucket.json"
DEFAULT_OUT_JSON = ROOT / "tmp" / "task2_answer_skeleton.json"
DEFAULT_OUT_TXT = ROOT / "tmp" / "task2_answer_skeleton.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Task2 answer skeleton from bucket results.")
    parser.add_argument("--bucket-json", default=str(DEFAULT_BUCKET_JSON))
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON))
    parser.add_argument("--out-txt", default=str(DEFAULT_OUT_TXT))
    return parser.parse_args()


def load_bucket_rows(path: Path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))


build_skeleton_rows = build_answer_skeleton


def print_summary(summary_rows, out_json: Path, out_txt: Path) -> None:
    print("== Task2 Answer Skeleton ==")
    print(f"generated_json={out_json}")
    print(f"generated_txt={out_txt}")
    print(f"total={len(summary_rows)}")
    print("")
    for row in summary_rows:
        print(
            f"{row['qid']} | {row['bucket']} | chart={str(row['has_chart']).lower()} | "
            f"{row['content']}"
        )


def main() -> None:
    args = parse_args()
    bucket_rows = load_bucket_rows(Path(args.bucket_json))
    skeleton_rows, summary_rows = build_answer_skeleton(bucket_rows, args.db_path)
    out_json = Path(args.out_json)
    out_txt = Path(args.out_txt)
    write_answer_skeleton_outputs(skeleton_rows, summary_rows, out_json, out_txt)
    print_summary(summary_rows, out_json, out_txt)


if __name__ == "__main__":
    main()
