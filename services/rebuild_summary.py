"""
Rebuild materialised-view tables (RatingSummary, ReviewSummary).
"""
from sqlalchemy import func
from datetime import datetime
from app.db import SessionLocal
from app.models import Review, Media, RatingSummary, ReviewSummary


def rebuild_all():
    db = SessionLocal()
    try:
        _rebuild_rating_summary(db)
        _rebuild_review_summary(db)
        print("")
        print("  Rebuild Complete")
        print("  " + "-" * 30)
        print("  Status : Rating and review summaries rebuilt successfully.")
        print("")
    finally:
        db.close()


def _rebuild_rating_summary(db):
    db.query(RatingSummary).delete()
    rows = (
        db.query(
            Review.media_id,
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .group_by(Review.media_id)
        .all()
    )
    for r in rows:
        db.add(RatingSummary(
            media_id=r.media_id,
            avg_rating=round(float(r.avg_rating), 2),
            review_count=r.review_count,
            last_updated=datetime.utcnow()
        ))
    db.commit()


def _rebuild_review_summary(db):
    db.query(ReviewSummary).delete()
    rows = (
        db.query(
            Review.media_id,
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .group_by(Review.media_id)
        .all()
    )
    for r in rows:
        db.add(ReviewSummary(
            media_id=r.media_id,
            avg_rating=round(float(r.avg_rating), 2),
            review_count=r.review_count,
            last_updated=datetime.utcnow()
        ))
    db.commit()
