from sqlalchemy import Column,Integer,String
from .db import Base
from sqlalchemy import Float, ForeignKey
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    reviews = relationship("Review", back_populates="user")


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    media_type = Column(String, default="movie")  # movie | webshow | song
    genre = Column(String)
    year = Column(Integer)

    reviews = relationship("Review", back_populates="media")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)

    rating = Column(Integer, nullable=False)
    comment = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    # RELATIONSHIPS (MISSING BEFORE — THIS CAUSED ERROR)
    user = relationship("User", back_populates="reviews")
    media = relationship("Media", back_populates="reviews")

class Session(Base):
    __tablename__="sessions"

    id=Column(Integer,primary_key=True)
    user_id=Column(Integer)
    token=Column(String,unique=True)
    expires_at=Column(DateTime)

class RatingSummary(Base):
    __tablename__ = "rating_summary"

    media_id = Column(Integer, ForeignKey("media.id"), primary_key=True)
    avg_rating = Column(Float, default=0)
    review_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    media = relationship("Media")


class ReviewSummary(Base):
    __tablename__ = "review_summaries"

    media_id = Column(Integer, ForeignKey("media.id"), primary_key=True)
    avg_rating = Column(Float, default=0)
    review_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    media = relationship("Media")

class UserTaste(Base):
    __tablename__ = "user_taste"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    genre = Column(String, primary_key=True)
    weight = Column(Float, default=0)

    user = relationship("User")



class Subscription(Base):
    """Persistent observer subscriptions (survives between CLI runs)"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False)

    user = relationship("User")
    media = relationship("Media")
