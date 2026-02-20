
from sqlalchemy.orm import Session
from app.models import Subscription, User, Media
from app.db import SessionLocal


def subscribe(db: Session, user_id: int, media_id: int):
    existing = db.query(Subscription).filter_by(
        user_id=user_id, media_id=media_id
    ).first()
    if existing:
        print(f"  Already subscribed to Media ID {media_id}.")
        return
    db.add(Subscription(user_id=user_id, media_id=media_id))
    db.commit()
    print("")
    print("  Subscription Added")
    print("  " + "-" * 30)
    print(f"  User ID  : {user_id}")
    print(f"  Media ID : {media_id}")
    print(f"  Status   : Subscribed to review notifications")
    print("")


def unsubscribe(db: Session, user_id: int, media_id: int):
    db.query(Subscription).filter_by(user_id=user_id, media_id=media_id).delete()
    db.commit()
    print(f"  Unsubscribed from Media ID {media_id}.")


def notify_subscribers(db: Session, media_id: int, message: str):
    """Print CLI notifications to all subscribers of this media."""
    subs = db.query(Subscription).filter_by(media_id=media_id).all()
    if subs:
        print("  Notifications Sent")
        for sub in subs:
            print(f"  Notification -> User {sub.user_id}: {message}")


def show_notifications(user_id: int, media_id: int = None):
    from app.models import Review
    db = SessionLocal()

    if media_id:
        media_ids = [media_id]
        subscribe(db, user_id, media_id)
    else:
        subs      = db.query(Subscription).filter_by(user_id=user_id).all()
        media_ids = [s.media_id for s in subs]

    if not media_ids:
        print("")
        print("  No subscriptions found.")
        print("  Use --notification <media_id> to subscribe.")
        print("")
        db.close()
        return

    print("")
    print(f"  Notifications for User {user_id}")
    print("  " + "=" * 55)

    found_any = False
    for mid in media_ids:
        media   = db.query(Media).filter_by(id=mid).first()
        reviews = (
            db.query(Review)
            .filter(Review.media_id == mid)
            .order_by(Review.created_at.desc())
            .limit(5)
            .all()
        )
        if reviews:
            found_any = True
            title = media.title if media else f"Media {mid}"
            print(f"  {title}")
            print("  " + "-" * 40)
            print(f"  {'User ID':<10} {'Rating':<8} Comment")
            print("  " + "-" * 40)
            for r in reviews:
                print(f"  {str(r.user_id):<10} {str(r.rating) + '/5':<8} {r.comment}")
            print("")

    if not found_any:
        print("  No reviews yet on your subscribed media.")
        print("")
    db.close()
