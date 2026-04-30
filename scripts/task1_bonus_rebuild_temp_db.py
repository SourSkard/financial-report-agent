import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task1_ingest import run_ingest
import app.services.task1_extractors as task1_extractors
from app.services.table_semantics import is_row_semantically_valid, normalize_item_text


FINANCIAL_PREFIXES = [
    "营业收入",
    "营业成本",
    "税金及附加",
    "销售费用",
    "管理费用",
    "研发费用",
    "财务费用",
    "营业利润",
    "营业外收入",
    "营业外支出",
    "利润总额",
    "所得税费用",
    "净利润",
    "归属于母公司股东的净利润",
    "基本每股收益",
    "稀释每股收益",
    "资产总计",
    "流动资产合计",
    "非流动资产合计",
    "流动负债合计",
    "非流动负债合计",
    "负债合计",
    "所有者权益合计",
    "股本",
    "资本公积",
    "盈余公积",
    "未分配利润",
    "应付账款",
    "应付职工薪酬",
    "固定资产",
    "无形资产",
    "经营活动产生的现金流量净额",
]

TAIL_MARKERS = [
    "详见",
    "附注",
    "说明",
    "情况",
    "原因",
    "其中：",
    "其中:",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Task1 bonus temp DB without touching db/app.db.")
    parser.add_argument("--pdf", action="append", required=True, help="PDF path (repeatable).")
    parser.add_argument("--out-db", default="tmp/app_task1_bonus.db", help="Temporary SQLite output path.")
    parser.add_argument("--report-json", default="tmp/task1_bonus_report.json", help="Bonus QA report JSON path.")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--no-ocr", action="store_true")
    return parser.parse_args()


def _looks_numeric(val: object) -> bool:
    return task1_extractors._looks_numeric(val)


def _score_item_candidate(text: str) -> int:
    score = len(text)
    if any(keyword in text for keyword in task1_extractors._ITEM_KEYWORDS):
        score += 45
    if re.search(r"[收益费用利润负债权益资产股本公积账款薪酬总计合计净额收入成本现金流量]", text):
        score += 20
    if 2 <= len(text) <= 36:
        score += 10
    if len(text) > 48:
        score -= 20
    if any(marker in text for marker in ["。", "；", "："]) and len(text) > 18:
        score -= 25
    return score


def _normalize_bonus_tail(text: str) -> str:
    cleaned = normalize_item_text(text)
    cleaned = re.sub(r"^(其中[:：]\s*)", "", cleaned).strip()
    cleaned = re.sub(r"\s*[-—–:：]\s*(说明|详见|附注).*$", "", cleaned).strip()
    cleaned = re.sub(r"[（(][^（）()]{1,24}(说明|附注|注|详情|原因)[^（）()]*[)）]$", "", cleaned).strip()
    cleaned = re.sub(r"\s*(说明|详见|附注|情况|原因).*$", "", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -—–:：;；,，")
    for prefix in FINANCIAL_PREFIXES:
        if cleaned.startswith(prefix):
            return prefix
    return cleaned


def _bonus_extract_item_text(row: List[str], item_col_idx: int) -> str:
    if not row:
        return ""
    window = [str(cell or "").strip() for cell in row[: min(12, len(row))]]

    def _is_item_text(text: str) -> bool:
        if not text:
            return False
        if re.fullmatch(r"[0-9一二三四五六七八九十]+", text):
            return False
        if re.fullmatch(r"20\d{2}", text):
            return False
        if re.fullmatch(r"[\d,\.\-%]+", text):
            return False
        return True

    candidates: List[str] = []
    if item_col_idx < len(window):
        candidates.append(window[item_col_idx])

    numeric_positions = [idx for idx, cell in enumerate(window) if _looks_numeric(cell)]
    first_numeric_idx = min(numeric_positions) if numeric_positions else None

    prefix_cells = [
        cell
        for idx, cell in enumerate(window)
        if cell and not _looks_numeric(cell) and (first_numeric_idx is None or idx < first_numeric_idx + 1)
    ]
    if prefix_cells:
        candidates.append("".join(prefix_cells))
        candidates.append(" ".join(prefix_cells))

    for width in (2, 3, 4):
        for start in range(0, max(len(window) - width + 1, 0)):
            segment = window[start : start + width]
            if not all(segment):
                continue
            if sum(1 for cell in segment if _looks_numeric(cell)) > 1:
                continue
            segment_text = " ".join(cell for cell in segment if not _looks_numeric(cell))
            if segment_text:
                candidates.append(segment_text)

    candidates.extend(window)

    best = ""
    best_score = -10**9
    seen = set()
    for raw in candidates:
        text = _normalize_bonus_tail(raw)
        if not _is_item_text(text):
            continue
        if text in seen:
            continue
        seen.add(text)
        score = _score_item_candidate(text)
        if score > best_score:
            best = text
            best_score = score
    return best


def _apply_bonus_item_cleanup(db_path: Path) -> Dict[str, Any]:
    conn = sqlite3.connect(str(db_path), timeout=60)
    summary: Dict[str, Any] = {"normalized": {}, "dropped": {}, "bad_rows": {}}
    tables = [
        "income_sheet",
        "balance_sheet",
        "cash_flow_sheet",
        "core_performance_indicators_sheet",
    ]

    try:
        cur = conn.cursor()
        for table in tables:
            rows = cur.execute(f"SELECT id, item FROM {table}").fetchall()
            normalized = 0
            dropped = 0
            for row_id, item in rows:
                new_item = _normalize_bonus_tail(str(item or ""))
                ok, _ = is_row_semantically_valid(table, new_item)
                if not new_item or not ok:
                    cur.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))
                    dropped += 1
                    continue
                if new_item != item:
                    cur.execute(f"UPDATE {table} SET item=? WHERE id=?", (new_item, row_id))
                    normalized += 1
            conn.commit()

            bad_rows = []
            for item, in cur.execute(f"SELECT item FROM {table}").fetchall():
                ok, reason = is_row_semantically_valid(table, str(item or ""))
                if not ok:
                    bad_rows.append({"item": item, "reason": reason})

            summary["normalized"][table] = normalized
            summary["dropped"][table] = dropped
            summary["bad_rows"][table] = bad_rows[:20]
    finally:
        conn.close()
    return summary


def _build_anchor_report(db_path: Path) -> Dict[str, Any]:
    anchor_items = {
        "balance_sheet": ["资产总计", "负债合计", "所有者权益合计", "流动资产合计", "流动负债合计"],
        "income_sheet": ["营业收入", "利润总额", "归属于母公司股东的净利润"],
    }
    conn = sqlite3.connect(str(db_path), timeout=60)
    report: Dict[str, Any] = {}
    try:
        cur = conn.cursor()
        for table, items in anchor_items.items():
            report[table] = {}
            for item in items:
                count = cur.execute(f"SELECT COUNT(*) FROM {table} WHERE item=?", (item,)).fetchone()[0]
                report[table][item] = count
    finally:
        conn.close()
    return report


def main() -> None:
    args = parse_args()
    out_db = Path(args.out_db)
    out_db.parent.mkdir(parents=True, exist_ok=True)
    report_json = Path(args.report_json)
    report_json.parent.mkdir(parents=True, exist_ok=True)

    for suffix in ("", "-journal", "-wal", "-shm"):
        path = Path(str(out_db) + suffix) if suffix else out_db
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass

    task1_extractors._extract_item_text = _bonus_extract_item_text

    counts: Dict[str, int] = {}
    for pdf in args.pdf:
        counts = run_ingest(
            pdf_path=pdf,
            db_path=str(out_db),
            timeout=args.timeout,
            use_ocr=not args.no_ocr,
        )

    cleanup_summary = _apply_bonus_item_cleanup(out_db)
    payload = {
        "out_db": str(out_db),
        "counts": counts,
        "cleanup_summary": cleanup_summary,
        "anchor_report": _build_anchor_report(out_db),
    }
    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Bonus temp DB ready: {out_db.resolve()}")
    print(f"Bonus report: {report_json.resolve()}")


if __name__ == "__main__":
    main()
