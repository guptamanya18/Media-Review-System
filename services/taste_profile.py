from app.db import SessionLocal
from app.models import Review, Media, UserTaste
from sqlalchemy import func


def rebuild_user_summary(user_id):

    db = SessionLocal()

    # find avg rating per genre by user
    genre_scores = (
        db.query(Media.genre, func.avg(Review.rating))
        .join(Media, Review.media_id == Media.id)
        .filter(Review.user_id == user_id)
        .group_by(Media.genre)
        .all()
    )

    # clear old taste
    db.query(UserTaste).filter(UserTaste.user_id == user_id).delete()

    # insert new taste weights
    for genre, score in genre_scores:
        db.add(UserTaste(user_id=user_id, genre=genre, weight=score))

    db.commit()
    db.close()


def get_user_taste(user_id):

    db = SessionLocal()

    tastes = (
        db.query(UserTaste.genre)
        .filter(UserTaste.user_id == user_id)
        .order_by(UserTaste.weight.desc())
        .limit(3)
        .all()
    )

    db.close()

    return [t[0] for t in tastes]
