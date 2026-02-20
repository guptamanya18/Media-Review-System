
import json
from datetime import datetime
from pathlib import Path

LOG_DIR  = Path("logs")
LOG_FILE = LOG_DIR / "bulk_reviews.log"
LOG_DIR.mkdir(exist_ok=True)

# Ensure log file exists empty on first run
if not LOG_FILE.exists():
    LOG_FILE.write_text("", encoding="utf-8")


def _append(record: dict):
    record["ts"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    # flush immediately so every entry is visible in the file in real time


def log_bulk_start(file_path: str, total: int, user_id: int):
    _append({
        "event":   "BULK_START",
        "file":    file_path,
        "total":   total,
        "user_id": user_id,
    })


def log_success(row: int, user_id: int, media_id: int, rating: int, comment: str):
    _append({
        "event":    "SUCCESS",
        "row":      row,
        "user_id":  user_id,
        "media_id": media_id,
        "rating":   rating,
        "comment":  comment[:60],
    })


def log_skip(row: int, media_id, reason: str):
    _append({
        "event":    "SKIP",
        "row":      row,
        "media_id": media_id,
        "reason":   reason,
    })


def log_fail(row: int, media_id, error: str):
    _append({
        "event":    "FAIL",
        "row":      row,
        "media_id": media_id,
        "error":    str(error)[:80],
    })


def log_bulk_done(file_path: str, total: int, success: int,
                  skipped: int, failed: int, elapsed: float):
    _append({
        "event":       "BULK_DONE",
        "file":        file_path,
        "total":       total,
        "success":     success,
        "skipped":     skipped,
        "failed":      failed,
        "elapsed_sec": round(elapsed, 2),
    })


def show_recent_logs(n: int = 50):
    """Display last n entries from bulk_reviews.log in a clean table format."""
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        print("")
        print("  Bulk Review Log")
        print("  " + "-" * 40)
        print("  Log is empty. Run --bulk-review first.")
        print("")
        return

    lines = [l for l in LOG_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        print("")
        print("  Bulk Review Log")
        print("  " + "-" * 40)
        print("  Log is empty. Run --bulk-review first.")
        print("")
        return

    recent = lines[-n:]
    records = []
    for line in recent:
        try:
            records.append(json.loads(line))
        except Exception:
            pass

    print("")
    print("  Bulk Review Log")
    print("  Log file : " + str(LOG_FILE))
    print("  Entries  : " + str(len(records)) + " (showing last " + str(n) + ")")
    print("")

    # Separate summary records from row-level records
    summaries = [r for r in records if r.get("event") in ("BULK_START", "BULK_DONE")]
    rows      = [r for r in records if r.get("event") in ("SUCCESS", "SKIP", "FAIL")]

    # Print session summaries
    if summaries:
        print("  Session Summary")
        print("  " + "-" * 60)
        print(f"  {'Timestamp':<22} {'Event':<12} {'Detail'}")
        print("  " + "-" * 60)
        for r in summaries:
            ts = r.get("ts", "")
            ev = r.get("event", "")
            if ev == "BULK_START":
                detail = f"File: {r.get('file','')}  Rows: {r.get('total','')}  User: {r.get('user_id','')}"
            elif ev == "BULK_DONE":
                detail = (f"Total: {r.get('total','')}  "
                          f"Added: {r.get('success','')}  "
                          f"Skipped: {r.get('skipped','')}  "
                          f"Failed: {r.get('failed','')}  "
                          f"Time: {r.get('elapsed_sec','')}s")
            else:
                detail = ""
            print(f"  {ts:<22} {ev:<12} {detail}")
        print("")

    # Print row-level results
    if rows:
        print("  Row Details")
        print("  " + "-" * 70)
        print(f"  {'Timestamp':<22} {'Event':<10} {'Row':<6} {'Media ID':<10} {'Rating':<8} {'Comment / Reason'}")
        print("  " + "-" * 70)
        for r in rows:
            ts       = r.get("ts", "")
            ev       = r.get("event", "")
            row_num  = str(r.get("row", ""))
            media_id = str(r.get("media_id", ""))
            rating   = str(r.get("rating", "-"))
            if ev == "SUCCESS":
                detail = r.get("comment", "")
            elif ev == "SKIP":
                detail = r.get("reason", "")
            else:
                detail = r.get("error", "")
            print(f"  {ts:<22} {ev:<10} {row_num:<6} {media_id:<10} {rating:<8} {detail[:40]}")
        print("")
