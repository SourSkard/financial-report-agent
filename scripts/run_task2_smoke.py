import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_qa import run_qa


@dataclass(frozen=True)
class SmokeCase:
    question: str
    expected_behavior: str
    should_draw_chart: bool


DEFAULT_CASES_JSON = ROOT / "app" / "config" / "task2_smoke_cases.json"
DEGRADE_MARKERS = [
    "暂不支持",
    "仅支持单期单值查询",
    "暂无法生成趋势图",
    "不足以形成趋势图",
    "不足以生成",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Task2 fixed smoke regression set.")
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--cases-json", default=str(DEFAULT_CASES_JSON))
    return parser.parse_args()


def load_smoke_cases(path: str | Path) -> List[SmokeCase]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return [
        SmokeCase(
            question=str(row["question"]),
            expected_behavior=str(row["expected_behavior"]),
            should_draw_chart=bool(row["should_draw_chart"]),
        )
        for row in payload
    ]


def infer_behavior(record: Dict) -> str:
    if record.get("clarification"):
        return "clarify"
    content = str(record.get("A", {}).get("content", ""))
    if any(marker in content for marker in DEGRADE_MARKERS):
        return "degrade"
    return "direct_answer"


def build_actual_result(record: Dict, actual_behavior: str) -> str:
    answer = record.get("A", {})
    content = str(answer.get("content", "")).strip() or "(empty)"
    chart_flag = "yes" if answer.get("image") else "no"
    return f"behavior={actual_behavior}; chart={chart_flag}; answer={content}"


def run_case(case: SmokeCase, idx: int, db_path: str) -> Dict[str, object]:
    qid = f"T2SMOKE{idx:02d}"
    result = run_qa(case.question, db_path=db_path, question_id=qid, debug=False)
    record = result[0]
    actual_behavior = infer_behavior(record)
    actual_chart = bool(record.get("A", {}).get("image") or [])
    passed = actual_behavior == case.expected_behavior and actual_chart == case.should_draw_chart
    return {
        "question": case.question,
        "expected_behavior": case.expected_behavior,
        "should_draw_chart": case.should_draw_chart,
        "actual_result": build_actual_result(record, actual_behavior),
        "pass": passed,
    }


def print_summary(results: List[Dict[str, object]]) -> None:
    passed_count = sum(1 for row in results if row["pass"])
    total = len(results)

    print("== Task2 Smoke Regression ==")
    print(f"总通过数: {passed_count}/{total}")
    print("")
    print("每题结果摘要:")
    for idx, row in enumerate(results, start=1):
        status = "PASS" if row["pass"] else "FAIL"
        chart_expected = "true" if row["should_draw_chart"] else "false"
        print(
            f"[{status}] {idx}. {row['question']} | "
            f"expected_behavior={row['expected_behavior']} | "
            f"should_draw_chart={chart_expected}"
        )
        print(f"    actual_result={row['actual_result']}")

    failures = [row for row in results if not row["pass"]]
    print("")
    print("失败题清单:")
    if not failures:
        print("- (empty)")
        return
    for idx, row in enumerate(failures, start=1):
        print(
            f"- {idx}. {row['question']} | "
            f"expected_behavior={row['expected_behavior']} | "
            f"actual_result={row['actual_result']}"
        )


def main() -> None:
    args = parse_args()
    cases = load_smoke_cases(args.cases_json)
    results = [run_case(case, idx, args.db_path) for idx, case in enumerate(cases, start=1)]
    print_summary(results)


if __name__ == "__main__":
    main()
