from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import SessionLocal
from app.models import Media, RatingSummary
from app.cache import cache_get, cache_set


def add_media(db: Session, title: str, genre: str, year: int, media_type: str = "movie"):
    m = Media(title=title, genre=genre, year=year, media_type=media_type)
    db.add(m)
    db.commit()
    cache_set("media:list", None, ttl=1)
    print("")
    print("  Media Added")
    print("  " + "-" * 30)
    print(f"  ID    : {m.id}")
    print(f"  Title : {title}")
    print(f"  Type  : {media_type}")
    print(f"  Genre : {genre}")
    print(f"  Year  : {year}")
    print("")


def list_media(db: Session):
    
    cached = cache_get("media:list")
    if cached:
        _print_media_table(cached)
        return

    media = db.query(Media).all()
    if not media:
        print("")
        print("  No media found.")
        print("")
        return

    result = []
    for m in media:
        result.append({"id": m.id, "title": m.title,
                        "media_type": m.media_type, "genre": m.genre, "year": m.year})
    cache_set("media:list", result)
    _print_media_table(result)


def _print_media_table(items):
    print("")
    print("  Media List")
    print("  " + "=" * 65)
    print(f"  {'ID':<6} {'Title':<30} {'Type':<10} {'Genre':<12} {'Year'}")
    print("  " + "-" * 65)
    for m in items:
        print(f"  {str(m['id']):<6} {m['title'][:29]:<30} {m['media_type']:<10} {m['genre']:<12} {m['year']}")
    print("")


def search_media(title: str):
    cache_key = f"media:search:{title.lower()}"
    cached = cache_get(cache_key)
    if cached:
        _print_media_table(cached)
        return []

    db = SessionLocal()
    results = db.query(Media).filter(
        func.lower(Media.title).like(f"%{title.lower()}%")
    ).all()
    db.close()

    if not results:
        print("")
        print(f"  No results found for: {title}")
        print("")
        return []

    serialised = [{"id": m.id, "title": m.title, "media_type": m.media_type,
                   "genre": m.genre, "year": m.year} for m in results]
    cache_set(cache_key, serialised, ttl=120)
    _print_media_table(serialised)
    return results


def get_top_rated(limit: int = 5):
    cache_key = f"media:top_rated:{limit}"
    cached = cache_get(cache_key)
    if cached:
        _print_top_rated(cached)
        return []

    db = SessionLocal()
    top = (
        db.query(Media, RatingSummary.avg_rating, RatingSummary.review_count)
        .join(RatingSummary, Media.id == RatingSummary.media_id)
        .order_by(RatingSummary.avg_rating.desc())
        .limit(limit)
        .all()
    )
    db.close()

    if not top:
        print("")
        print("  No rated media found yet.")
        print("")
        return []

    serialised = [{"title": m.title, "media_type": m.media_type,
                   "avg_rating": round(avg, 2), "review_count": cnt}
                  for m, avg, cnt in top]
    cache_set(cache_key, serialised, ttl=60)
    _print_top_rated(serialised)
    return top


def _print_top_rated(items):
    print("")
    print("  Top Rated Media")
    print("  " + "=" * 55)
    print(f"  {'Title':<30} {'Type':<10} {'Avg Rating':<12} Reviews")
    print("  " + "-" * 55)
    for m in items:
        print(f"  {m['title'][:29]:<30} {m['media_type']:<10} {str(m['avg_rating']):<12} {m['review_count']}")
    print("")
