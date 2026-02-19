"""
Tests for authentication service using in-memory DB.
"""
import unittest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch


# Patch the SessionLocal used inside auth_service to use in-memory DB
import app.db as app_db

_engine = create_engine("sqlite:///:memory:", echo=False)
from app.models import Base, User, Session as DBSession

Base.metadata.create_all(bind=_engine)
_Session = sessionmaker(bind=_engine)

# Monkey-patch
app_db.engine = _engine
app_db.SessionLocal = _Session


class TestAuth(unittest.TestCase):

    def setUp(self):
        # clean slate
        db = _Session()
        db.query(DBSession).delete()
        db.query(User).delete()
        db.commit()
        db.close()
        # clean up .session file
        if os.path.exists(".session"):
            os.remove(".session")

    def test_register_new_user(self):
        from services.auth_service import register
        register("testuser", "password123")
        db = _Session()
        user = db.query(User).filter_by(username="testuser").first()
        self.assertIsNotNone(user)
        db.close()

    def test_duplicate_register(self):
        from services.auth_service import register
        register("dupeuser", "pass")
        register("dupeuser", "pass")
        db = _Session()
        count = db.query(User).filter_by(username="dupeuser").count()
        self.assertEqual(count, 1)
        db.close()

    def test_login_success(self):
        from services.auth_service import register, login
        register("loginuser", "secure123")
        token = login("loginuser", "secure123")
        self.assertIsNotNone(token)

    def test_login_wrong_password(self):
        from services.auth_service import register, login
        register("badpass", "correct")
        result = login("badpass", "wrong")
        self.assertIsNone(result)

    def test_session_file_created_on_login(self):
        from services.auth_service import register, login
        register("sessuser", "pass")
        login("sessuser", "pass")
        self.assertTrue(os.path.exists(".session"))


if __name__ == "__main__":
    unittest.main()
