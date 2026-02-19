from sqlalchemy import func
from app.models import Review, Media
from collections import Counter
import re

POSITIVE = ["good", "great", "amazing", "masterpiece", "excellent", "love", "best"]
NEGATIVE = ["bad", "boring", "waste", "poor", "slow", "worst"]


def analyze_media(media_id, db):
    reviews = db.query(Review).filter(Review.media_id == media_id).all()
    if not reviews:
        return None

    avg_rating = db.query(func.avg(Review.rating)).filter(Review.media_id == media_id).scalar()
    positive   = 0
    negative   = 0
    words      = []

    for r in reviews:
        text = r.comment.lower()
        if any(w in text for w in POSITIVE):
            positive += 1
        if any(w in text for w in NEGATIVE):
            negative += 1
        words += re.findall(r'\b[a-z]{4,}\b', text)

    top_words = Counter(words).most_common(5)

    return {
        "avg":       round(avg_rating, 2),
        "total":     len(reviews),
        "positive":  positive,
        "negative":  negative,
        "top_words": [w for w, _ in top_words],
    }
