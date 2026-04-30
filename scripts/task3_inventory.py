import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _count_files(base: Path) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for path in base.rglob("*"):
        if path.is_file():
            ext = path.suffix.lower() or "<no_ext>"
            counts[ext] = counts.get(ext, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def _list_reports(base: Path) -> Dict[str, List[str]]:
    stock_dir = next((p for p in base.rglob("*") if p.is_dir() and "个股研报" in p.name), None)
    industry_dir = next((p for p in base.rglob("*") if p.is_dir() and "行业研报" in p.name), None)

    stock_reports = sorted([p.name for p in stock_dir.rglob("*.pdf")]) if stock_dir else []
    industry_reports = sorted([p.name for p in industry_dir.rglob("*.pdf")]) if industry_dir else []
    return {"stock_reports": stock_reports, "industry_reports": industry_reports}


def _xlsx_rows(path: Path) -> int:
    try:
        return int(pd.read_excel(path).shape[0])
    except Exception:
        return 0


def build_inventory(data_root: Path) -> Dict[str, object]:
    attachment5 = next((p for p in data_root.rglob("*") if p.is_dir() and "附件5" in p.name), None)
    attachment6 = next((p for p in data_root.rglob("*") if p.is_file() and "附件6" in p.name and p.suffix.lower() == ".xlsx"), None)
    if not attachment5:
        raise FileNotFoundError("Attachment 5 directory was not found.")

    reports = _list_reports(attachment5)
    first_batch = reports["stock_reports"] + reports["industry_reports"]

    return {
        "attachment5_dir": str(attachment5),
        "attachment6_file": str(attachment6) if attachment6 else None,
        "file_type_counts": _count_files(attachment5),
        "stock_report_count": len(reports["stock_reports"]),
        "industry_report_count": len(reports["industry_reports"]),
        "stock_reports": reports["stock_reports"],
        "industry_reports": reports["industry_reports"],
        "stock_metadata_rows": _xlsx_rows(attachment5 / "个股_研报信息.xlsx"),
        "industry_metadata_rows": _xlsx_rows(attachment5 / "行业_研报信息.xlsx"),
        "first_batch_index_set": first_batch,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory Task3 inputs from Attachment 5/6.")
    parser.add_argument("--data-root", default="B题-示例数据/示例数据")
    parser.add_argument("--out-json", default="tmp/task3_inventory.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inventory = build_inventory(Path(args.data_root))
    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"task3_inventory={out_path.resolve()}")
    print(f"attachment5_dir={inventory['attachment5_dir']}")
    print(f"attachment6_file={inventory['attachment6_file']}")
    print(f"stock_report_count={inventory['stock_report_count']}")
    print(f"industry_report_count={inventory['industry_report_count']}")


if __name__ == "__main__":
    main()
