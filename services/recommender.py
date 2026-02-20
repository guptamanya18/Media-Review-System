
from app.models import User, Review, Media
from app.cache import cache_get, cache_set
from services.user_profile import build_user_profile
from services.similarity import cosine_similarity


def recommend_media(user_id: int, db, limit: int = 5):
    cache_key = f"recommend:{user_id}"
    cached = cache_get(cache_key)
    if cached:
        _print_recommendations(cached, user_id)
        return []

    target_profile = build_user_profile(user_id, db)
    if not target_profile:
        print("")
        print(f"  Recommendations for User {user_id}")
        print("  " + "-" * 40)
        print("  No taste profile found. Showing top-rated instead.")
        print("")
        from services.media_service import get_top_rated
        get_top_rated()
        return []

    users = db.query(User).filter(User.id != user_id).all()
    similarity_scores = []
    for u in users:
        profile = build_user_profile(u.id, db)
        score   = cosine_similarity(target_profile, profile)
        if score > 0:
            similarity_scores.append((u.id, score))

    similarity_scores.sort(key=lambda x: x[1], reverse=True)
    similar_users = [uid for uid, _ in similarity_scores[:3]]

    watched = {r.media_id for r in db.query(Review).filter_by(user_id=user_id)}

    recommendations: dict[int, int] = {}
    for sim_user in similar_users:
        reviews = db.query(Review).filter_by(user_id=sim_user).all()
        for r in reviews:
            if r.media_id not in watched and r.rating >= 4:
                recommendations[r.media_id] = recommendations.get(r.media_id, 0) + 1

    if not recommendations:
        print("")
        print(f"  Recommendations for User {user_id}")
        print("  " + "-" * 40)
        print("  No recommendations found at this time.")
        print("")
        return []

    top_ids    = sorted(recommendations, key=recommendations.get, reverse=True)[:limit]
    media_list = db.query(Media).filter(Media.id.in_(top_ids)).all()

    serialised = [{"title": m.title, "media_type": m.media_type, "genre": m.genre}
                  for m in media_list]
    cache_set(cache_key, serialised, ttl=300)

    _print_recommendations(serialised, user_id)
    return media_list


def _print_recommendations(items, user_id):
    print("")
    print(f"  Recommendations for User {user_id}")
    print("  " + "=" * 50)
    print(f"  {'Title':<30} {'Type':<12} Genre")
    print("  " + "-" * 50)
    for m in items:
        print(f"  {m['title'][:29]:<30} {m['media_type']:<12} {m['genre']}")
    print("")
