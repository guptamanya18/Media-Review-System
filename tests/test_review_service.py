"""
Tests for review_service using an in-memory SQLite database.
"""
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, User, Media, Review, RatingSummary, ReviewSummary


def _make_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


class TestReviewService(unittest.TestCase):

    def setUp(self):
        self.db = _make_db()
        # seed a user + media
        self.user = User(id=1, username="alice", password_hash="x")
        self.media = Media(id=1, title="Test Movie", media_type="movie", genre="Action", year=2020)
        self.db.add_all([self.user, self.media])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def _add_review(self, user_id=1, media_id=1, rating=5, comment="Great"):
        from services.review_service import add_review
        add_review(self.db, user_id, media_id, rating, comment)

    def test_add_review_success(self):
        self._add_review()
        reviews = self.db.query(Review).all()
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].rating, 5)

    def test_duplicate_review_blocked(self):
        self._add_review()
        self._add_review()  # second attempt
        reviews = self.db.query(Review).all()
        self.assertEqual(len(reviews), 1)  # still only 1

    def test_invalid_rating(self):
        self._add_review(rating=10)  # should be blocked
        reviews = self.db.query(Review).all()
        self.assertEqual(len(reviews), 0)

    def test_media_not_found(self):
        self._add_review(media_id=999)
        reviews = self.db.query(Review).all()
        self.assertEqual(len(reviews), 0)


class TestSimilarity(unittest.TestCase):

    def test_identical_profiles(self):
        from services.similarity import cosine_similarity
        p = {"Action": 5.0, "Drama": 3.0}
        self.assertAlmostEqual(cosine_similarity(p, p), 1.0)

    def test_no_common_genres(self):
        from services.similarity import cosine_similarity
        p1 = {"Action": 5.0}
        p2 = {"Comedy": 4.0}
        self.assertEqual(cosine_similarity(p1, p2), 0)

    def test_partial_overlap(self):
        from services.similarity import cosine_similarity
        p1 = {"Action": 4.0, "Drama": 2.0}
        p2 = {"Action": 4.0, "Comedy": 3.0}
        score = cosine_similarity(p1, p2)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1.0)


class TestCacheModule(unittest.TestCase):

    def test_set_and_get(self):
        from app.cache import cache_set, cache_get
        cache_set("test:key", {"hello": "world"}, ttl=60)
        result = cache_get("test:key")
        self.assertIsNotNone(result)
        self.assertEqual(result["hello"], "world")

    def test_delete(self):
        from app.cache import cache_set, cache_get, cache_delete
        cache_set("test:del", 42)
        cache_delete("test:del")
        self.assertIsNone(cache_get("test:del"))

    def test_expired_key(self):
        import time
        from app.cache import cache_set, cache_get
        cache_set("test:ttl", "short-lived", ttl=1)
        time.sleep(1.1)
        self.assertIsNone(cache_get("test:ttl"))


if __name__ == "__main__":
    unittest.main()
