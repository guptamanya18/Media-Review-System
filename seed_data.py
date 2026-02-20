"""
Seed the database with fake data.
Safe to re-run — clears all existing data first.

Password rule: every seeded user password = username + "_password"
Example: username = john42  ->  password = john42_password
"""
from faker import Faker
import random
from sqlalchemy import func
from passlib.context import CryptContext
from app.db import SessionLocal
from app.models import (User, Media, Review, RatingSummary,
                        ReviewSummary, UserTaste, Subscription)

fake        = Faker()
db          = SessionLocal()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

GENRES      = ["Action", "Drama", "Comedy", "Sci-Fi", "Horror",
               "Romance", "Thriller", "Documentary"]
MEDIA_TYPES = ["movie", "webshow", "song"]
COMMENTS    = [
    "Absolutely loved it", "Total waste of time", "Mind blowing experience",
    "Great storyline and acting", "Boring and slow paced", "Must watch",
    "Decent but could be better", "One of the best I have seen",
    "Very disappointing", "Highly recommended", "Overrated in my opinion",
    "Brilliant direction", "Average at best", "Masterpiece",
    "Not worth the hype", "Kept me hooked throughout", "Predictable but fun",
    "Stunning visuals", "Poor character development", "Exceeded my expectations",
]

print("")
print("  Seeding Database")
print("  " + "=" * 40)
#print("  Clearing existing data...")

db.query(Subscription).delete()
db.query(UserTaste).delete()
db.query(ReviewSummary).delete()
db.query(RatingSummary).delete()
db.query(Review).delete()
db.query(Media).delete()
db.query(User).delete()
db.commit()

#print("  Creating users...")
users     = []
usernames = []
for _ in range(50):
    username = fake.unique.user_name()
    password = f"{username}_password"
    usernames.append(username)
    u = User(username=username, password_hash=pwd_context.hash(password))
    db.add(u)
    users.append(u)
db.commit()
print(f"  Users created    : {len(users)}")


print("  Creating media...")
media_list = []
for _ in range(100):
    m = Media(
        title=fake.catch_phrase(),
        media_type=random.choice(MEDIA_TYPES),
        genre=random.choice(GENRES),
        year=random.randint(1990, 2024)
    )
    db.add(m)
    media_list.append(m)
db.commit()
print(f"  Media created    : {len(media_list)}")


print("  Creating reviews...")
seen, count, attempts = set(), 0, 0
while count < 500 and attempts < 5000:
    attempts += 1
    u   = random.choice(users)
    m   = random.choice(media_list)
    key = (u.id, m.id)
    if key in seen:
        continue
    seen.add(key)
    db.add(Review(
        user_id=u.id, media_id=m.id,
        rating=random.randint(1, 5),
        comment=random.choice(COMMENTS)
    ))
    count += 1
db.commit()
print(f"  Reviews created  : {count}")


print("  Building rating summaries...")
for media_id, avg_r, cnt in (
    db.query(Review.media_id, func.avg(Review.rating), func.count(Review.id))
    .group_by(Review.media_id).all()
):
    db.add(RatingSummary(media_id=media_id,
                         avg_rating=round(float(avg_r), 2), review_count=cnt))
    db.add(ReviewSummary(media_id=media_id,
                         avg_rating=round(float(avg_r), 2), review_count=cnt))
db.commit()
print("  Summaries built  : Done")


print("  Building taste profiles...")
from services.taste_profile import rebuild_user_summary
for u in users:
    rebuild_user_summary(u.id)
print("  Taste profiles   : Done")

db.close()

print("")
print("  Seed Complete")
