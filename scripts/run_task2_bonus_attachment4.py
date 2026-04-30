import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_batch_pipeline import parse_questions
from app.pipelines.task2_qa_bonus import run_qa_bonus
from app.services.export_result2 import export_result2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Attachment 4 through the Task2 bonus pipeline.")
    parser.add_argument("--questions-xlsx", required=True)
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--out-xlsx", default="tmp/result_2_bonus.xlsx")
    parser.add_argument("--out-json", default="tmp/task2_bonus_attachment4.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    turns = parse_questions(questions_xlsx=args.questions_xlsx)

    grouped_entries: List[Dict[str, Any]] = []
    detailed_rows: List[Dict[str, Any]] = []
    current_session = None
    question_payload: List[Dict[str, Any]] = []
    answer_payload: List[Dict[str, Any]] = []
    sql_payload: List[str] = []
    chart_payload: List[str] = []
    prev_intent = None
    prev_state = None

    def flush_session(session_id: str | None) -> None:
        if session_id is None:
            return
        grouped_entries.append(
            {
                "id": session_id,
                "question": json.dumps(question_payload, ensure_ascii=False),
                "sql": json.dumps(sql_payload, ensure_ascii=False) if sql_payload else "无",
                "chart_path": json.dumps(chart_payload, ensure_ascii=False) if chart_payload else "无",
                "answer": json.dumps(answer_payload, ensure_ascii=False),
            }
        )

    for turn in turns:
        if current_session != turn.session_id:
            flush_session(current_session)
            current_session = turn.session_id
            question_payload = []
            answer_payload = []
            sql_payload = []
            chart_payload = []
            prev_intent = None
            prev_state = None

        result = run_qa_bonus(
            turn.original_question,
            db_path=args.db_path,
            prev_intent=prev_intent,
            prev_state=prev_state,
            question_id=turn.qid,
            debug=True,
        )[0]
        answer = result.get("A", {})
        question_payload.append({"Q": turn.original_question})
        answer_payload.append({"Q": turn.original_question, "A": {"content": answer.get("content", ""), "image": answer.get("image") or []}})
        sql_payload.append(str(result.get("internal", {}).get("sql") or "无"))
        chart_payload.append((answer.get("image") or ["无"])[0] if answer.get("image") else "无")
        detailed_rows.append(
            {
                "qid": turn.qid,
                "question": turn.original_question,
                "answer": answer.get("content", ""),
                "bonus_meta": result.get("internal", {}).get("bonus_meta", {}),
            }
        )
        prev_intent = result.get("internal", {}).get("intent")
        prev_state = result.get("internal", {}).get("bonus_state")

    flush_session(current_session)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(detailed_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    export_result2(grouped_entries, out_path=args.out_xlsx)

    print(f"Task2 bonus Attachment4 rows: {len(detailed_rows)}")
    print(f"Bonus JSON: {out_json.resolve()}")
    print(f"Bonus XLSX: {Path(args.out_xlsx).resolve()}")


if __name__ == "__main__":
    main()
