import json
from pathlib import Path
import sys
from typing import Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_batch_pipeline import (
    bucket_questions,
    build_answer_skeleton,
    export_result2_xlsx,
    parse_questions,
)
from app.services.task2_support import QUERY_RULES, TASK2_SUPPORT_MATRIX


TARGET_FILES = [
    ROOT / "app" / "services" / "task2_support.py",
    ROOT / "app" / "services" / "query_intent.py",
    ROOT / "app" / "pipelines" / "task2_qa.py",
    ROOT / "app" / "pipelines" / "task2_batch_pipeline.py",
    ROOT / "scripts" / "bucket_task2_attachment4.py",
    ROOT / "scripts" / "build_task2_attachment4_answer_skeleton.py",
    ROOT / "scripts" / "build_result2_from_task2_attachment4.py",
    ROOT / "scripts" / "run_task2.py",
    ROOT / "scripts" / "run_task2_smoke.py",
    ROOT / "tests" / "test_task2_smoke.py",
    ROOT / "tests" / "test_task2_degrade.py",
]
BANNED_TOKENS = [
    "华润三九",
    "金花股份",
    "B1001",
    "B1002",
    "附件4：问题汇总.xlsx",
]


def scan_for_sample_coupling() -> Dict[str, List[str]]:
    hits: Dict[str, List[str]] = {}
    for path in TARGET_FILES:
        text = path.read_text(encoding="utf-8-sig")
        matched = [token for token in BANNED_TOKENS if token in text]
        if matched:
            hits[str(path.relative_to(ROOT))] = matched
    return hits


def verify_support_configuration() -> None:
    required_metrics = {"revenue", "net_profit", "total_profit", "eps"}
    if not required_metrics.issubset(set(TASK2_SUPPORT_MATRIX.keys())):
        missing = sorted(required_metrics - set(TASK2_SUPPORT_MATRIX.keys()))
        raise AssertionError(f"support matrix missing metrics: {missing}")
    if "ranking_query_types" not in QUERY_RULES:
        raise AssertionError("support matrix query_rules must define ranking_query_types")
    if "allow_multi_company" not in QUERY_RULES:
        raise AssertionError("support matrix query_rules must define allow_multi_company")


def build_synthetic_workbook(out_path: Path) -> Path:
    rows = [
        {
            "编号": "CASE001",
            "问题类型": "财务问答",
            "问题": json.dumps(
                [
                    {"Q": "示例企业甲利润总额是多少？"},
                    {"Q": "2024年第三季度的"},
                ],
                ensure_ascii=False,
            ),
        },
        {
            "编号": "CASE002",
            "问题类型": "财务问答",
            "问题": json.dumps(
                [
                    {"Q": "示例企业甲近几年 EPS 趋势如何？"},
                ],
                ensure_ascii=False,
            ),
        },
        {
            "编号": "CASE003",
            "问题类型": "财务问答",
            "问题": json.dumps(
                [
                    {"Q": "2024 年利润最高的 top10 企业是哪些？"},
                ],
                ensure_ascii=False,
            ),
        },
        {
            "编号": "CASE004",
            "问题类型": "财务问答",
            "问题": json.dumps(
                [
                    {"Q": "示例企业甲和示例企业乙 2024 年营业收入哪个更高？"},
                ],
                ensure_ascii=False,
            ),
        },
    ]
    df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(out_path, index=False)
    return out_path


def run_synthetic_pipeline(base_dir: Path) -> Dict[str, object]:
    workbook = build_synthetic_workbook(base_dir / "task2_pipeline_generalization_input.xlsx")
    turns = parse_questions(questions_xlsx=workbook)
    bucket_rows = bucket_questions(turns)
    skeleton_rows, summary_rows = build_answer_skeleton(bucket_rows, "db/app.db")
    result2_xlsx = base_dir / "task2_pipeline_generalization_result_2.xlsx"
    preview_txt = base_dir / "task2_pipeline_generalization_preview.txt"
    entries, previews = export_result2_xlsx(
        bucket_rows=bucket_rows,
        skeleton_rows=skeleton_rows,
        db_path="db/app.db",
        out_xlsx=result2_xlsx,
        preview_txt=preview_txt,
    )

    expected = {
        "CASE001-1": "clarify_first",
        "CASE001-2": "direct_answer",
        "CASE002-1": "degrade",
        "CASE003-1": "degrade",
        "CASE004-1": "degrade",
    }
    actual = {row["qid"]: row["expected_behavior"] for row in bucket_rows}
    for qid, behavior in expected.items():
        if actual.get(qid) != behavior:
            raise AssertionError(f"{qid} expected {behavior}, got {actual.get(qid)}")

    if not result2_xlsx.exists():
        raise AssertionError("result_2 xlsx was not generated for synthetic pipeline")
    if not preview_txt.exists():
        raise AssertionError("preview txt was not generated for synthetic pipeline")

    return {
        "workbook": workbook,
        "turn_count": len(turns),
        "bucket_count": len(bucket_rows),
        "skeleton_count": len(skeleton_rows),
        "session_count": len(entries),
        "preview_count": len(previews),
        "result2_xlsx": result2_xlsx,
        "preview_txt": preview_txt,
    }


def main() -> None:
    coupling_hits = scan_for_sample_coupling()
    if coupling_hits:
        lines = ["Detected sample-coupled tokens:"]
        for path, tokens in coupling_hits.items():
            lines.append(f"- {path}: {', '.join(tokens)}")
        raise SystemExit("\n".join(lines))

    verify_support_configuration()
    outcome = run_synthetic_pipeline(ROOT / "tmp" / "pipeline_generalization_check")

    print("== Task2 pipeline generalization check ==")
    print("sample_coupling_check=pass")
    print("support_matrix_check=pass")
    print(f"turn_count={outcome['turn_count']}")
    print(f"bucket_count={outcome['bucket_count']}")
    print(f"skeleton_count={outcome['skeleton_count']}")
    print(f"session_count={outcome['session_count']}")
    print(f"result2={Path(outcome['result2_xlsx']).resolve()}")
    print(f"preview={Path(outcome['preview_txt']).resolve()}")


if __name__ == "__main__":
    main()
