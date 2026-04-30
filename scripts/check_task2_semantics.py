"""Check Task2 metric semantic coverage and diagnose explainability gaps."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.metric_semantics import METRIC_STANDARDS, explain_item_classification
from app.storage.db import session_scope

TASK2_SCAN_TABLES = [
    "income_sheet",
    "core_performance_indicators_sheet",
    "balance_sheet",
    "cash_flow_sheet",
]


@dataclass
class Row:
    table: str
    company: str
    report_period: str
    item: str


def _existing_tables(session) -> set[str]:
    rows = session.exec(text("SELECT name FROM sqlite_master WHERE type='table'"))
    return {str(r[0]) for r in rows}


def load_rows(session) -> List[Row]:
    existing = _existing_tables(session)
    out: List[Row] = []
    for table in TASK2_SCAN_TABLES:
        if table not in existing:
            continue
        sql = text(f"SELECT company, report_period, item FROM {table}")
        for company, report_period, item in session.exec(sql):
            out.append(
                Row(
                    table=table,
                    company=str(company or "").strip(),
                    report_period=str(report_period or "").strip(),
                    item=str(item or "").strip(),
                )
            )
    return out


def build_semantic_report(rows: Iterable[Row], top_n: int = 20) -> Dict[str, Any]:
    metric_item_counter: Dict[str, Counter[str]] = {k: Counter() for k in METRIC_STANDARDS.keys()}
    metric_companies: Dict[str, set[str]] = {k: set() for k in METRIC_STANDARDS.keys()}
    metric_periods: Dict[str, set[str]] = {k: set() for k in METRIC_STANDARDS.keys()}

    metric_company_periods: Dict[str, Dict[str, set[str]]] = {
        k: defaultdict(set) for k in METRIC_STANDARDS.keys()
    }
    metric_period_companies: Dict[str, Dict[str, set[str]]] = {
        k: defaultdict(set) for k in METRIC_STANDARDS.keys()
    }

    excluded_negative_items: Counter[str] = Counter()

    for row in rows:
        detail = explain_item_classification(row.item)
        if detail["should_exclude"]:
            if detail["matched_negative_patterns"]:
                excluded_negative_items[row.item] += 1
            continue

        metric_key = detail["metric_key"]
        if not metric_key:
            continue

        metric_item_counter[metric_key][row.item] += 1
        if row.company:
            metric_companies[metric_key].add(row.company)
        if row.report_period:
            metric_periods[metric_key].add(row.report_period)

        if row.company and row.report_period:
            metric_company_periods[metric_key][row.company].add(row.report_period)
            metric_period_companies[metric_key][row.report_period].add(row.company)

    trend_renderability: Dict[str, Dict[str, Any]] = {}
    topk_renderability: Dict[str, Dict[str, Any]] = {}

    for metric_key in METRIC_STANDARDS.keys():
        company_periods = metric_company_periods[metric_key]
        total_companies = len(company_periods)
        trend_ready_companies = sum(1 for periods in company_periods.values() if len(periods) >= 2)
        trend_rate = (trend_ready_companies / total_companies) if total_companies else 0.0
        trend_renderability[metric_key] = {
            "ready": trend_ready_companies,
            "total": total_companies,
            "rate": round(trend_rate, 4),
        }

        period_companies = metric_period_companies[metric_key]
        total_periods = len(period_companies)
        topk_ready_periods = sum(1 for companies in period_companies.values() if len(companies) >= 2)
        topk_rate = (topk_ready_periods / total_periods) if total_periods else 0.0
        topk_renderability[metric_key] = {
            "ready": topk_ready_periods,
            "total": total_periods,
            "rate": round(topk_rate, 4),
        }

    return {
        "metric_item_frequency": {
            k: metric_item_counter[k].most_common() for k in METRIC_STANDARDS.keys()
        },
        "metric_company_coverage": {
            k: len(metric_companies[k]) for k in METRIC_STANDARDS.keys()
        },
        "metric_report_period_coverage": {
            k: len(metric_periods[k]) for k in METRIC_STANDARDS.keys()
        },
        "excluded_high_frequency_items": excluded_negative_items.most_common(top_n),
        "trend_renderability": trend_renderability,
        "topk_renderability": topk_renderability,
    }


def _print_report(report: Dict[str, Any]) -> None:
    print("== Task2 Semantic Coverage Check ==")
    print("\n[1] metric_key -> item 命中频次")
    for metric_key, pairs in report["metric_item_frequency"].items():
        shown = ", ".join([f"{item}:{freq}" for item, freq in pairs[:10]]) or "(empty)"
        print(f"- {metric_key}: {shown}")

    print("\n[2] metric_key 覆盖 company 数")
    for metric_key, count in report["metric_company_coverage"].items():
        print(f"- {metric_key}: {count}")

    print("\n[3] metric_key 覆盖 report_period 数")
    for metric_key, count in report["metric_report_period_coverage"].items():
        print(f"- {metric_key}: {count}")

    print("\n[4] 被 negative/global 排除的高频 item")
    excluded = report["excluded_high_frequency_items"]
    if not excluded:
        print("- (empty)")
    else:
        for item, freq in excluded:
            print(f"- {item}: {freq}")

    print("\n[5] trend 可画图率（>=2 个 report_period）")
    for metric_key, row in report["trend_renderability"].items():
        print(f"- {metric_key}: {row['ready']}/{row['total']} ({row['rate']:.2%})")

    print("\n[6] topk 可排名率（>=2 家 company）")
    for metric_key, row in report["topk_renderability"].items():
        print(f"- {metric_key}: {row['ready']}/{row['total']} ({row['rate']:.2%})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Task2 semantic coverage and diagnosis.")
    parser.add_argument("--db-path", default=None, help="SQLite DB path, default uses TEDDY_DB_PATH or db/app.db")
    parser.add_argument("--top-n", type=int, default=20, help="Top-N excluded items to display")
    args = parser.parse_args()

    db_path = str(Path(args.db_path)) if args.db_path else None

    with session_scope(db_path=db_path) as session:
        rows = load_rows(session)

    report = build_semantic_report(rows, top_n=args.top_n)
    _print_report(report)


if __name__ == "__main__":
    main()
