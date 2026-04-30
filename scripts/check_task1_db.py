import argparse
import sqlite3
from pathlib import Path


TABLES = [
    "income_sheet",
    "balance_sheet",
    "cash_flow_sheet",
    "core_performance_indicators_sheet",
]


def table_exists(conn, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    )
    return cur.fetchone() is not None


def count_rows(conn, name: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) FROM {name}")
    return cur.fetchone()[0]


def null_issues(conn, name: str):
    cur = conn.execute(
        f"SELECT COUNT(*) FROM {name} WHERE company IS NULL OR company='' OR source_path IS NULL OR source_path=''"
    )
    return cur.fetchone()[0]


def invalid_report_period(conn, name: str):
    cur = conn.execute(
        f"SELECT COUNT(*) FROM {name} WHERE report_period IS NULL OR report_period = ''"
    )
    return cur.fetchone()[0]


def non_numeric_value(conn, name: str):
    cur = conn.execute(
        f"SELECT COUNT(*) FROM {name} WHERE typeof(value) NOT IN ('real','integer')"
    )
    return cur.fetchone()[0]


def duplicate_rows(conn, name: str):
    cur = conn.execute(
        f"""
        SELECT COUNT(*) FROM (
            SELECT company, report_period, item, COUNT(*) c
            FROM {name}
            GROUP BY company, report_period, item
            HAVING c > 1
        )
        """
    )
    return cur.fetchone()[0]


def main():
    parser = argparse.ArgumentParser(description="Health check for Task1 SQLite output.")
    parser.add_argument("--db-path", default="db/app.db", help="Path to SQLite db (default db/app.db)")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"[FAIL] DB not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    overall_fail = False
    for t in TABLES:
        if not table_exists(conn, t):
            print(f"[FAIL] Table missing: {t}")
            overall_fail = True
            continue
        rows = count_rows(conn, t)
        if rows == 0:
            print(f"[FAIL] Table {t} is empty")
            overall_fail = True
        nulls = null_issues(conn, t)
        invalid_period = invalid_report_period(conn, t)
        non_numeric = non_numeric_value(conn, t)
        dups = duplicate_rows(conn, t)
        print(
            f"[OK] {t}: rows={rows}, null_company/source={nulls}, invalid_period={invalid_period}, non_numeric={non_numeric}, duplicates={dups}"
        )
    conn.close()
    if overall_fail:
        print("[RESULT] Issues found. See logs above.")
    else:
        print("[RESULT] Task1 DB health check passed.")


if __name__ == "__main__":
    main()
