import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_batch_pipeline import export_result2_xlsx, group_result2_rows


DEFAULT_BUCKET_JSON = ROOT / "tmp" / "task2_bucket.json"
DEFAULT_SKELETON_JSON = ROOT / "tmp" / "task2_answer_skeleton.json"
DEFAULT_OUT_XLSX = ROOT / "result_2.xlsx"
DEFAULT_PREVIEW_TXT = ROOT / "tmp" / "result_2_preview.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build final result_2.xlsx from Task2 bucket and answer skeleton.")
    parser.add_argument("--bucket-json", default=str(DEFAULT_BUCKET_JSON))
    parser.add_argument("--skeleton-json", default=str(DEFAULT_SKELETON_JSON))
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--out-xlsx", default=str(DEFAULT_OUT_XLSX))
    parser.add_argument("--preview-txt", default=str(DEFAULT_PREVIEW_TXT))
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    bucket_rows = load_json(Path(args.bucket_json))
    skeleton_rows = load_json(Path(args.skeleton_json))
    entries, previews = export_result2_xlsx(
        bucket_rows=bucket_rows,
        skeleton_rows=skeleton_rows,
        db_path=args.db_path,
        out_xlsx=args.out_xlsx,
        preview_txt=args.preview_txt,
    )
    print("== result_2 build complete ==")
    print(f"result_2={Path(args.out_xlsx).resolve()}")
    print(f"preview={Path(args.preview_txt).resolve()}")
    print(f"rows={len(entries)}")
    for row in previews:
        print(f"{row['编号']} | SQL={row['SQL查询语句']} | 图形={row['图形格式']}")


group_session_rows = group_result2_rows


__all__ = ["group_result2_rows", "group_session_rows"]


if __name__ == "__main__":
    main()
