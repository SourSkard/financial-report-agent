import argparse
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task2_qa import run_qa
from app.services.export_result2 import export_result2


def extract_questions(path: Path):
    df = pd.read_excel(path)
    if "问题" in df.columns:
        return df["问题"].dropna().tolist()
    # fallback: first column
    return df.iloc[:, 0].dropna().tolist()


def main():
    parser = argparse.ArgumentParser(description="Batch validate Task 2 using an Attachment 4 style workbook")
    parser.add_argument("--questions-xlsx", required=True, help="Path to an Attachment 4 style workbook")
    parser.add_argument("--db-path", default="db/app.db")
    parser.add_argument("--qid-prefix", default="B2", help="Prefix for question id, will append index")
    args = parser.parse_args()

    questions = extract_questions(Path(args.questions_xlsx))
    entries = []
    for idx, q in enumerate(questions, start=1):
        qid = f"{args.qid_prefix}{idx:03d}"
        res = run_qa(q, db_path=args.db_path, question_id=qid)
        record = res[0]
        sql = record.get("internal", {}).get("sql", "")
        chart_path = (record["A"].get("image") or [None])[0]
        entries.append(
            {
                "id": idx,
                "question": q,
                "sql": sql,
                "chart_path": chart_path,
                "answer": record["A"]["content"],
            }
        )
    export_result2(entries)
    print(f"Processed {len(entries)} questions. result_2.xlsx updated.")


if __name__ == "__main__":
    main()
