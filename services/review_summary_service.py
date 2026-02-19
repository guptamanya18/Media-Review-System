from sqlalchemy import func
from app.models import Review, ReviewSummary


def update_review_summary(session, media_id):

    avg_rating, count = session.query(
        func.avg(Review.rating),
        func.count(Review.id)
    ).filter(Review.media_id == media_id).first()

    summary = session.get(ReviewSummary, media_id)

    if summary:
        summary.avg_rating = float(avg_rating)
        summary.review_count = count
    else:
        summary = ReviewSummary(
            media_id=media_id,
            avg_rating=float(avg_rating),
            review_count=count
        )
        session.add(summary)

    session.commit()
