import argparse
import os
import sys
import time
from pathlib import Path
import sqlite3
import shutil
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.pipelines.task1_ingest import run_ingest


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Rebuild Task1 SQLite db/app.db from one or more PDFs.")
    ap.add_argument("--db-path", default="db/app.db", help="Target SQLite path (default db/app.db).")
    ap.add_argument("--pdf", action="append", required=True, help="PDF path (repeatable).")
    ap.add_argument("--max-pages", type=int, default=None, help="Only parse first N pages (debug).")
    ap.add_argument("--timeout", type=int, default=240, help="Parser timeout seconds.")
    ap.add_argument("--no-ocr", action="store_true", help="Disable OCR if backend supports it.")
    return ap.parse_args()


def _safe_unlink(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:
        # Best-effort cleanup; rebuild will still run and may overwrite.
        pass


def _sqlite_sidecars(db_path: Path) -> list[Path]:
    return [
        db_path,
        Path(str(db_path) + "-journal"),
        Path(str(db_path) + "-wal"),
        Path(str(db_path) + "-shm"),
        db_path.parent / f"{db_path.name}.__rebuild__",
        db_path.parent / f"{db_path.name}.__rebuild__-journal",
    ]


def _safe_unlink_with_retries(path: Path, retries: int = 8, delay: float = 0.25) -> None:
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            if path.exists():
                path.unlink()
            return
        except Exception as exc:  # pragma: no cover - best effort on Windows
            last_error = exc
            time.sleep(delay)
    if path.exists() and last_error is not None:
        raise last_error


def _cleanup_sidecars(db_path: Path) -> None:
    for sidecar in _sqlite_sidecars(db_path)[1:]:
        _safe_unlink_with_retries(sidecar)


def _neutralize_sidecars(db_path: Path) -> None:
    for sidecar in _sqlite_sidecars(db_path)[1:]:
        if not sidecar.exists():
            continue
        try:
            with sidecar.open("r+b") as fh:
                fh.truncate(0)
                fh.flush()
                os.fsync(fh.fileno())
        except FileNotFoundError:
            continue


def _integrity_check(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path), timeout=60)
    try:
        cur = conn.cursor()
        result = cur.execute("PRAGMA integrity_check;").fetchone()
        if not result or result[0] != "ok":
            raise RuntimeError(f"integrity_check failed for {db_path}: {result}")
    finally:
        conn.close()


def _copy_into_place(src: Path, dst: Path) -> None:
    src_size = src.stat().st_size
    with src.open("rb") as rf, dst.open("r+b") as wf:
        wf.seek(0)
        shutil.copyfileobj(rf, wf, length=1024 * 1024)
        if dst.stat().st_size > src_size:
            try:
                wf.truncate(src_size)
            except PermissionError:
                # Some Windows handles allow overwrite but reject truncate.
                # For the current Task1 rebuild target the file size is stable,
                # so leave the existing size unchanged in that edge case.
                pass
        wf.flush()
        os.fsync(wf.fileno())


def main() -> None:
    args = parse_args()
    final_db_path = Path(args.db_path)
    tmp_db_dir = Path("tmp")
    tmp_db_path = tmp_db_dir / f"{final_db_path.stem}.tmp.{uuid4().hex[:8]}{final_db_path.suffix}"
    backup_dir = final_db_path.parent / "bak"
    backup_path = backup_dir / f"{final_db_path.stem}.before_task1_rebuild{final_db_path.suffix}"
    os.environ["TEDDY_DB_PATH"] = str(tmp_db_path)

    tmp_db_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    for sidecar in _sqlite_sidecars(tmp_db_path):
        _safe_unlink(sidecar)

    total = {}
    try:
        for pdf in args.pdf:
            counts = run_ingest(
                pdf_path=pdf,
                raw_tables=None,
                use_fake_parser=False,
                db_path=str(tmp_db_path),
                max_pages=args.max_pages,
                timeout=args.timeout,
                use_ocr=not args.no_ocr,
            )
            total = counts
            print("Ingest done:", counts, "pdf=", pdf)

        _integrity_check(tmp_db_path)

        final_db_path.parent.mkdir(parents=True, exist_ok=True)
        if final_db_path.exists():
            shutil.copy2(final_db_path, backup_path)
            print("Backup written:", backup_path)
        try:
            _cleanup_sidecars(final_db_path)
            os.replace(str(tmp_db_path), str(final_db_path))
        except PermissionError:
            print("[WARN] replace target denied; falling back to in-place overwrite:", final_db_path)
            _neutralize_sidecars(final_db_path)
            if final_db_path.exists():
                _copy_into_place(tmp_db_path, final_db_path)
                _safe_unlink_with_retries(tmp_db_path)
            else:
                raise
        _neutralize_sidecars(final_db_path)
        _integrity_check(final_db_path)
        print("Rebuild finished. Replaced target db:", final_db_path)
        print("Last counts:", total)
    except Exception as exc:
        print("[FAIL] Could not replace target db. Likely open handle on db/app.db.")
        print("tmp_db_path:", tmp_db_path)
        print("final_db_path:", final_db_path)
        print("error:", repr(exc))


if __name__ == "__main__":
    main()
