import argparse
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.table_semantics import is_row_semantically_valid

TABLES = [
    "income_sheet",
    "balance_sheet",
    "cash_flow_sheet",
    "core_performance_indicators_sheet",
]


def _connect_db(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    journal = Path(str(path) + "-journal")
    if journal.exists() and journal.stat().st_size > 0:
        return sqlite3.connect(f"file:{path.as_posix()}?mode=ro&immutable=1", uri=True)
    return sqlite3.connect(path)


def scan_db(db_path: str, top_n: int = 20):
    conn = _connect_db(db_path)
    cur = conn.cursor()

    summary = {}
    for table in TABLES:
        try:
            rows = cur.execute(f"SELECT item FROM {table}").fetchall()
        except Exception:
            continue
        bad = Counter()
        reasons = defaultdict(Counter)
        for (item,) in rows:
            text = str(item or "").strip()
            ok, reason = is_row_semantically_valid(table, text)
            if not ok:
                bad[text] += 1
                reasons[reason][text] += 1
        summary[table] = {
            "rows": len(rows),
            "bad_total": sum(bad.values()),
            "bad_top": bad.most_common(top_n),
            "reason_top": {r: c.most_common(10) for r, c in reasons.items()},
        }

    conn.close()
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default="db/app.db")
    ap.add_argument("--top-n", type=int, default=20)
    args = ap.parse_args()

    report = scan_db(args.db_path, top_n=args.top_n)
    for table, payload in report.items():
        print(f"\n== {table} ==")
        print(f"rows={payload['rows']} bad_total={payload['bad_total']}")
        for item, c in payload["bad_top"]:
            print(f"{c:4d} | {item}")


if __name__ == "__main__":
    main()
