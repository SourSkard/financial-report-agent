import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_qa_bonus import run_qa_bonus


@dataclass(frozen=True)
class SmokeCase:
    question: str
    expected_behavior: str
    should_draw_chart: bool


DEFAULT_CASES_JSON = ROOT / "app" / "config" / "task2_smoke_cases.json"
DEGRADE_MARKERS = [
    "暂不支持",
    "仅支持单期单值查询",
    "暂时无法形成趋势结论",
    "当前数据不足",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Task2 bonus smoke regression set.")
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--cases-json", default=str(DEFAULT_CASES_JSON))
    parser.add_argument("--out-json", default="tmp/task2_bonus_smoke_results.json")
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


def main() -> None:
    args = parse_args()
    cases = load_smoke_cases(args.cases_json)
    results = []

    for idx, case in enumerate(cases, start=1):
        record = run_qa_bonus(
            case.question,
            db_path=args.db_path,
            prev_intent=None,
            prev_state=None,
            question_id=f"T2BONUSSMOKE{idx:02d}",
            debug=True,
        )[0]
        actual_behavior = infer_behavior(record)
        actual_chart = bool(record.get("A", {}).get("image") or [])
        results.append(
            {
                "question": case.question,
                "expected_behavior": case.expected_behavior,
                "should_draw_chart": case.should_draw_chart,
                "actual_behavior": actual_behavior,
                "actual_chart": actual_chart,
                "answer": record.get("A", {}).get("content", ""),
                "pass": actual_behavior == case.expected_behavior and actual_chart == case.should_draw_chart,
                "bonus_meta": record.get("internal", {}).get("bonus_meta", {}),
            }
        )

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    passed = sum(1 for row in results if row["pass"])
    print(f"Task2 bonus smoke passed: {passed}/{len(results)}")
    print(f"Details: {out_path.resolve()}")


if __name__ == "__main__":
    main()
