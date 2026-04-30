import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.data_cleaner import clean_records
from app.services.document_understanding import classify_page
from app.services.pdf_parser import PdfParser
from app.services.table_mapper import map_tables
from app.services.table_semantics import normalize_item_text
from app.services.task1_extractors import _read_camelot_tables
from app.services.mineru_backend import MinerUBackend


def _norm_contains(needle: str, hay: str) -> bool:
    n = normalize_item_text(needle)
    h = normalize_item_text(hay)
    return bool(n and h and n in h)


def _scan_page_text(pages, targets: Dict[str, List[str]]) -> Dict[str, Dict[str, bool]]:
    hit = {t: {item: False for item in items} for t, items in targets.items()}
    for p in pages:
        text = p.get("text") or ""
        for table, items in targets.items():
            for item in items:
                if _norm_contains(item, text):
                    hit[table][item] = True
    return hit


def _scan_extracted_tables(pdf_path: str, pages, targets: Dict[str, List[str]]) -> Dict[str, Dict[str, bool]]:
    mineru = MinerUBackend()
    hit = {t: {item: False for item in items} for t, items in targets.items()}

    for p in pages:
        page_type, _ = classify_page(p)
        if page_type not in {"financial_statement", "kpi_table"}:
            continue

        page_num = p["page_num"]
        tables: List[List[List[str]]] = []
        tables.extend(_read_camelot_tables(pdf_path, page_num))
        try:
            tables.extend(mineru.extract_page_tables(Path(pdf_path), page_num) or [])
        except Exception:
            pass
        # pdfplumber tables attached by PdfParser.get_page_text()
        page_tables = p.get("tables") or []
        if isinstance(page_tables, list):
            for t2d in page_tables:
                if isinstance(t2d, list) and t2d:
                    tables.append(t2d)

        for t2d in tables:
            for row in t2d:
                if not isinstance(row, list):
                    continue
                for cell in row:
                    s = str(cell or "")
                    for table, items in targets.items():
                        for item in items:
                            if _norm_contains(item, s):
                                hit[table][item] = True
    return hit


def _scan_rows_before_cleaner(parsed_rows, targets: Dict[str, List[str]]) -> Dict[str, Dict[str, bool]]:
    hit = {t: {item: False for item in items} for t, items in targets.items()}
    for r in parsed_rows:
        table = r.get("table")
        if table not in targets:
            continue
        item_text = normalize_item_text(str(r.get("item", "")))
        for target in targets[table]:
            if _norm_contains(target, item_text):
                hit[table][target] = True
    return hit


def _scan_rows_after_cleaner(cleaned, targets: Dict[str, List[str]]) -> Dict[str, Dict[str, bool]]:
    hit = {t: {item: False for item in items} for t, items in targets.items()}
    for table, rows in cleaned.items():
        if table not in targets:
            continue
        for r in rows:
            item_text = normalize_item_text(str(r.get("item", "")))
            for target in targets[table]:
                if _norm_contains(target, item_text):
                    hit[table][target] = True
    return hit


def build_layer_report(pdf_paths: List[str], max_pages: int | None, timeout: int) -> Dict:
    targets = {
        "income_sheet": [
            "营业收入",
            "营业成本",
            "税金及附加",
            "销售费用",
            "财务费用",
            "归属于母公司股东的净利润",
            "少数股东损益",
            "基本每股收益",
            "稀释每股收益",
        ],
        "balance_sheet": [
            "资产总计",
            "流动资产合计",
            "流动负债合计",
            "负债合计",
            "股本",
            "资本公积",
            "盈余公积",
            "未分配利润",
            "应付账款",
            "应付职工薪酬",
            "固定资产",
            "所有者权益合计",
        ],
        "core_performance_indicators_sheet": [
            "营业收入",
            "净利润",
            "归属于母公司股东的净利润",
            "基本每股收益",
            "稀释每股收益",
            "总资产",
            "经营活动产生的现金流量净额",
        ],
    }

    parser = PdfParser(use_fake=False)

    aggregated = []
    for pdf in pdf_paths:
        pages = parser.parse_pages(pdf, max_pages=max_pages)
        page_text_hit = _scan_page_text(pages, targets)
        extracted_table_hit = _scan_extracted_tables(pdf, pages, targets)

        parsed_rows = parser.parse_tables(pdf, max_pages=max_pages, timeout=timeout, use_ocr=True)
        before_clean_hit = _scan_rows_before_cleaner(parsed_rows, targets)

        mapped = map_tables(parsed_rows)
        cleaned = clean_records(mapped)
        after_clean_hit = _scan_rows_after_cleaner(cleaned, targets)

        for table, items in targets.items():
            for item in items:
                p = page_text_hit[table][item]
                e = extracted_table_hit[table][item]
                b = before_clean_hit[table][item]
                a = after_clean_hit[table][item]
                filtered = b and not a

                # final_reason must be one of:
                # not_found_in_pdf_text / table_not_extracted / row_not_mapped
                # normalized_away / filtered_as_noise / mapped_to_other_table / other
                if not p and not e and not b and not a:
                    reason = "not_found_in_pdf_text"
                elif p and not e:
                    reason = "table_not_extracted"
                elif e and not b:
                    reason = "row_not_mapped"
                elif filtered:
                    reason = "filtered_as_noise"
                elif a:
                    reason = "other"  # present end-to-end (no longer missing)
                else:
                    reason = "other"

                aggregated.append(
                    {
                        "pdf": pdf,
                        "table": table,
                        "item": item,
                        "found_in_page_text": "yes" if p else "no",
                        "found_in_extracted_table": "yes" if e else "no",
                        "found_before_cleaner": "yes" if b else "no",
                        "filtered_by_cleaner": "yes" if filtered else "no",
                        "final_reason": reason,
                    }
                )

    return {"targets": targets, "results": aggregated}


def main() -> None:
    ap = argparse.ArgumentParser(description="Trace Task1 item recall across layers.")
    ap.add_argument("--pdf", action="append", required=True, help="PDF path (repeatable).")
    ap.add_argument("--max-pages", type=int, default=None)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--out", default="tmp/task1_item_recall_trace.json")
    args = ap.parse_args()

    out = build_layer_report(args.pdf, max_pages=args.max_pages, timeout=args.timeout)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # Also print a compact table for quick inspection.
    for r in out["results"]:
        print(
            "\t".join(
                [
                    r["table"],
                    r["item"],
                    r["found_in_page_text"],
                    r["found_in_extracted_table"],
                    r["found_before_cleaner"],
                    r["filtered_by_cleaner"],
                    r["final_reason"],
                    Path(r["pdf"]).name,
                ]
            )
        )


if __name__ == "__main__":
    main()
