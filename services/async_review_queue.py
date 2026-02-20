
import asyncio, json, os, time, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

QUEUE_FILE = "review_queue.jsonl"
_lock      = threading.Lock()
_executor  = ThreadPoolExecutor(max_workers=20)


def enqueue_review(user_id: int, media_id: int, rating: int, comment: str):
    job = {
        "job_id":    f"job_{int(time.time()*1000)}_{os.getpid()}",
        "user_id":   user_id,
        "media_id":  media_id,
        "rating":    rating,
        "comment":   comment,
        "status":    "pending",
        "queued_at": datetime.utcnow().isoformat(),
    }
    with _lock:
        with open(QUEUE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(job) + "\n")
    print("")
    print("  Review Queued")
    print("  " + "-" * 40)
    print(f"  Job ID   : {job['job_id']}")
    print(f"  Media ID : {media_id}")
    print(f"  Rating   : {rating} / 5")
    print(f"  Status   : Pending")
    print("")
    print("  Run --process-queue to submit all queued reviews.")
    print("")


def _load_pending():
    if not Path(QUEUE_FILE).exists():
        return []
    jobs = []
    with open(QUEUE_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                jobs.append(json.loads(line))
    return [j for j in jobs if j["status"] == "pending"]


def _update_status(job_id: str, status: str, error: str = ""):
    with _lock:
        if not Path(QUEUE_FILE).exists():
            return
        lines = Path(QUEUE_FILE).read_text(encoding="utf-8").splitlines()
        updated = []
        for line in lines:
            if not line.strip():
                continue
            job = json.loads(line)
            if job["job_id"] == job_id:
                job["status"]       = status
                job["processed_at"] = datetime.utcnow().isoformat()
                if error:
                    job["error"] = error
            updated.append(json.dumps(job))
        Path(QUEUE_FILE).write_text("\n".join(updated) + "\n", encoding="utf-8")


async def _process_one(job: dict, sem: asyncio.Semaphore):
    async with sem:
        def write():
            from app.db import SessionLocal
            from services.review_service import add_review
            db = SessionLocal()
            try:
                return add_review(db, job["user_id"], job["media_id"],
                                  job["rating"], job["comment"],
                                  skip_taste_rebuild=True)
            except Exception as e:
                return str(e)
            finally:
                db.close()

        result = await asyncio.get_event_loop().run_in_executor(_executor, write)

        if result is True:
            _update_status(job["job_id"], "done")
            print(f"  Added    : {job['job_id']}  media={job['media_id']}  rating={job['rating']}/5")
        elif result == "duplicate":
            _update_status(job["job_id"], "skipped")
            print(f"  Skipped  : {job['job_id']}  (already reviewed)")
        else:
            _update_status(job["job_id"], "failed", str(result))
            print(f"  Failed   : {job['job_id']}  error: {result}")


async def _run_queue():
    jobs = _load_pending()
    if not jobs:
        print("")
        print("  Queue Status : No pending reviews.")
        print("")
        return

    print("")
    print("  Processing Queue")
    print("  " + "=" * 50)
    print(f"  Pending Jobs : {len(jobs)}")
    print("")
    sem = asyncio.Semaphore(5)
    await asyncio.gather(*[_process_one(j, sem) for j in jobs])
    print("")
    print(f"  Done. {len(jobs)} jobs processed.")
    print("")


def process_queue():
    asyncio.run(_run_queue())


def show_queue_status():
    if not Path(QUEUE_FILE).exists():
        print("")
        print("  Queue Status : No queue file found. Nothing queued yet.")
        print("")
        return
    jobs = []
    with open(QUEUE_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                jobs.append(json.loads(line))
    if not jobs:
        print("")
        print("  Queue Status : Queue is empty.")
        print("")
        return

    pending = sum(1 for j in jobs if j["status"] == "pending")
    done    = sum(1 for j in jobs if j["status"] == "done")
    skipped = sum(1 for j in jobs if j["status"] == "skipped")
    failed  = sum(1 for j in jobs if j["status"] == "failed")

    print("")
    print("  Queue Status")
    print("  " + "=" * 30)
    print(f"  {'Pending':<12}: {pending}")
    print(f"  {'Done':<12}: {done}")
    print(f"  {'Skipped':<12}: {skipped}")
    print(f"  {'Failed':<12}: {failed}")
    print(f"  {'Total':<12}: {len(jobs)}")
    print("")
