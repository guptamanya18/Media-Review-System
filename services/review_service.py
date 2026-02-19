"""
Review Service

Security: write operations require a validated token passed via --token flag.
Performance: skip_taste_rebuild during bulk; rebuild once at end.
"""
import asyncio, csv, statistics, time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Review, Media, RatingSummary, ReviewSummary
from app.cache import cache_get, cache_set, cache_delete, cache_delete_pattern
from services.review_summary_service import update_review_summary
from services.taste_profile import rebuild_user_summary
from services.notification_service import notify_subscribers

executor   = ThreadPoolExecutor(max_workers=20)
BATCH_SIZE = 50


def add_review(db: Session, user_id: int, media_id: int,
               rating: int, comment: str,
               skip_taste_rebuild: bool = False):
    """Add a single review. Returns True | 'duplicate' | False."""
    if not 1 <= rating <= 5:
        print(f"  ERROR: Rating must be between 1 and 5. Got: {rating}")
        return False

    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        print(f"  ERROR: Media ID {media_id} not found.")
        return False

    if db.query(Review).filter_by(user_id=user_id, media_id=media_id).first():
        if not skip_taste_rebuild:
            print(f"  WARNING: You have already reviewed '{media.title}'.")
        return "duplicate"

    db.add(Review(user_id=user_id, media_id=media_id,
                  rating=rating, comment=comment,
                  created_at=datetime.utcnow()))
    db.commit()

    update_review_summary(db, media_id)
    _update_rating_summary(db, media_id)

    if not skip_taste_rebuild:
        rebuild_user_summary(user_id)

    cache_delete(f"reviews:{media_id}")
    cache_delete_pattern("media:top_rated:*")
    cache_delete("media:list")
    cache_delete(f"recommend:{user_id}")

    if not skip_taste_rebuild:
        print("")
        print("  Review Added")
        print("  " + "-" * 40)
        print(f"  Media    : {media.title}")
        print(f"  Rating   : {rating} / 5")
        print(f"  Comment  : {comment}")
        print("")
        notify_subscribers(db, media_id,
                           f"New review on '{media.title}' - Rating: {rating}/5 - \"{comment}\"")
    return True


def _update_rating_summary(db, media_id):
    avg_r, cnt = db.query(
        func.avg(Review.rating), func.count(Review.id)
    ).filter(Review.media_id == media_id).first()
    s = db.query(RatingSummary).filter_by(media_id=media_id).first()
    if s:
        s.avg_rating   = float(avg_r)
        s.review_count = cnt
        s.last_updated = datetime.utcnow()
    else:
        db.add(RatingSummary(media_id=media_id, avg_rating=float(avg_r),
                             review_count=cnt, last_updated=datetime.utcnow()))
    db.commit()


def view_reviews(db: Session, media_id: int):
    cache_key = f"reviews:{media_id}"
    cached = cache_get(cache_key)
    if cached:
        _print_reviews(cached["reviews"], cached["stats"], media_id)
        return

    reviews = db.query(Review).filter(Review.media_id == media_id).all()
    if not reviews:
        print("")
        print(f"  No reviews found for Media ID {media_id}.")
        print("")
        return

    ratings = [r.rating for r in reviews]
    stats = {
        "avg":    round(statistics.mean(ratings), 2),
        "median": statistics.median(ratings),
        "stdev":  round(statistics.stdev(ratings), 2) if len(ratings) > 1 else 0,
        "min":    min(ratings),
        "max":    max(ratings),
        "total":  len(ratings),
    }
    dicts = [{"user_id": r.user_id, "rating": r.rating,
              "comment": r.comment, "created_at": str(r.created_at)}
             for r in reviews]
    cache_set(cache_key, {"reviews": dicts, "stats": stats})
    _print_reviews(dicts, stats, media_id)


def _print_reviews(reviews, stats, media_id):
    print("")
    print(f"  Reviews for Media ID {media_id}")
    print("  " + "=" * 60)
    print(f"  {'User ID':<10} {'Rating':<8} {'Date':<22} Comment")
    print("  " + "-" * 60)
    for r in reviews:
        print(f"  {str(r['user_id']):<10} {str(r['rating']) + '/5':<8} {str(r['created_at'])[:19]:<22} {r['comment']}")
    print("  " + "-" * 60)
    print(f"  Statistics")
    print(f"  {'Average':<15}: {stats['avg']}")
    print(f"  {'Median':<15}: {stats['median']}")
    print(f"  {'Std Deviation':<15}: {stats['stdev']}")
    print(f"  {'Min Rating':<15}: {stats['min']}")
    print(f"  {'Max Rating':<15}: {stats['max']}")
    print(f"  {'Total Reviews':<15}: {stats['total']}")
    print("")


# ── ASYNC BULK REVIEW ──────────────────────────────────────────────────

async def _one_task(user_id, media_id, rating, comment, row):
    from services.bulk_logger import log_success, log_skip, log_fail

    def sync_write():
        db = SessionLocal()
        try:
            return add_review(db, user_id, media_id, rating, comment,
                              skip_taste_rebuild=True)
        except Exception as e:
            return str(e)
        finally:
            db.close()

    result = await asyncio.get_event_loop().run_in_executor(executor, sync_write)

    if result is True:
        log_success(row, user_id, media_id, rating, comment)
        return "success"
    elif result == "duplicate":
        log_skip(row, media_id, "already reviewed")
        return "skip"
    else:
        log_fail(row, media_id, str(result))
        return "fail"


async def bulk_review_async(file_path: str, db: Session, user_id: int):
    from services.bulk_logger import log_bulk_start, log_bulk_done

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"  ERROR: File not found: {file_path}")
        return

    if not rows:
        print("  ERROR: CSV file is empty.")
        return

    log_bulk_start(file_path, len(rows), user_id)
    start   = time.time()
    success = skipped = failed = 0
    total   = len(rows)

    print("")
    print("  Bulk Review Processing")
    print("  " + "=" * 50)
    print(f"  File       : {file_path}")
    print(f"  Total Rows : {total}")
    print(f"  User ID    : {user_id}")
    print("")

    for batch_start in range(0, total, BATCH_SIZE):
        batch = rows[batch_start: batch_start + BATCH_SIZE]
        tasks = []
        for i, row in enumerate(batch, batch_start + 1):
            try:
                tasks.append(_one_task(
                    user_id, int(row["media_id"]),
                    int(row["rating"]), row.get("comment", ""), i
                ))
            except (KeyError, ValueError) as e:
                from services.bulk_logger import log_fail
                log_fail(i, row.get("media_id", "?"), f"bad row: {e}")
                failed += 1

        results  = await asyncio.gather(*tasks)
        success += results.count("success")
        skipped += results.count("skip")
        failed  += results.count("fail")

        done = batch_start + len(batch)
        pct  = round(done / total * 100)
        print(f"  Progress : {done}/{total} ({pct}%)  "
              f"Added: {success}  Skipped: {skipped}  Failed: {failed}")

    rebuild_user_summary(user_id)
    elapsed = time.time() - start
    log_bulk_done(file_path, total, success, skipped, failed, elapsed)

    print("")
    print("  Bulk Review Complete")
    print("  " + "-" * 40)
    print(f"  {'Total Rows':<15}: {total}")
    print(f"  {'Added':<15}: {success}")
    print(f"  {'Skipped':<15}: {skipped}")
    print(f"  {'Failed':<15}: {failed}")
    print(f"  {'Time Taken':<15}: {round(elapsed, 2)}s")
    print(f"  {'Log File':<15}: logs/bulk_reviews.log")
    print("")
