import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task3_rag import run_rag
from app.services.export_result3 import export_result3


def _resolve_columns(df: pd.DataFrame) -> tuple[str, str]:
    cols = list(df.columns)
    normalized = {str(column).strip().replace(" ", ""): str(column) for column in cols}
    id_col = normalized.get("编号") or cols[0]
    q_col = normalized.get("问题") or cols[-1]
    return id_col, q_col


def extract_turns(path: Path) -> List[Dict[str, Any]]:
    df = pd.read_excel(path)
    id_col, q_col = _resolve_columns(df)
    turns: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        session_id = str(row[id_col]).strip()
        raw = row[q_col]
        payload = json.loads(raw) if isinstance(raw, str) and raw.strip().startswith("[") else [{"Q": str(raw)}]
        for idx, item in enumerate(payload, start=1):
            turns.append(
                {
                    "qid": f"{session_id}-{idx}",
                    "session_id": session_id,
                    "question": str(item.get("Q", "")).strip(),
                }
            )
    return turns


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch validate Task3 with Attachment 6 questions.")
    parser.add_argument("--questions-xlsx", required=True, help="Path to Attachment 6 workbook.")
    parser.add_argument("--reports-dir", required=True, help="Path to Attachment 5 report directory.")
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--out-xlsx", default="result_3.xlsx")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    turns = extract_turns(Path(args.questions_xlsx))
    entries: List[Dict[str, Any]] = []
    prev_context_by_session: Dict[str, Dict[str, Any]] = {}

    for turn in turns:
        prev_context = prev_context_by_session.get(turn["session_id"])
        result = run_rag(
            turn["question"],
            reports_dir=args.reports_dir,
            db_path=args.db_path,
            qid=turn["qid"],
            prev_context=prev_context,
        )[0]
        new_context = result.get("internal", {}).get("context")
        if isinstance(new_context, dict):
            prev_context_by_session[turn["session_id"]] = new_context
        refs = result.get("A", {}).get("references", []) or []
        entries.append(
            {
                "id": turn["qid"],
                "question": turn["question"],
                "sql": result.get("internal", {}).get("sql", "") or "无",
                "answer": result.get("A", {}).get("content", ""),
                "references_json": json.dumps(refs, ensure_ascii=False),
            }
        )

    export_result3(entries, out_path=args.out_xlsx)
    print(f"Processed {len(entries)} turns. result_3={Path(args.out_xlsx).resolve()}")


if __name__ == "__main__":
    main()
