from collections import defaultdict
from app.models import Review, Media

def build_user_profile(user_id, db):
    

    reviews = (
        db.query(Review, Media.genre)
        .join(Media, Media.id == Review.media_id)
        .filter(Review.user_id == user_id)
        .all()
    )

    genre_scores = defaultdict(list)

    for review, genre in reviews:
        genre_scores[genre].append(review.rating)

    profile = {}
    for genre in genre_scores:
        profile[genre] = sum(genre_scores[genre]) / len(genre_scores[genre])

    return profile
