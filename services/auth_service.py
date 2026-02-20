
import uuid
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models import User, Session as DBSession

SESSION_TTL_MINUTES = 30


def register(username: str, password: str):
    from passlib.context import CryptContext
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            print("")
            print("  ERROR: Registration Failed")
            print("  " + "-" * 30)
            print("  Reason : Username already exists")
            print("")
            return
        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user = User(username=username, password_hash=pwd.hash(password))
        db.add(user)
        db.commit()
        print("")
        print("  Registration Successful")
        print("  " + "-" * 30)
        print(f"  Username : {username}")
        print("  Status   : Account created")
        print("")
    finally:
        db.close()


def login(username: str, password: str):
    from passlib.context import CryptContext

    existing_token = _read_session_file()
    if existing_token:
        uid = _validate_token(existing_token)
        if uid:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == uid).first()
                logged_in_as = user.username if user else f"user {uid}"
            finally:
                db.close()
            print("")
            print("  WARNING: Already Logged In")
            print("  " + "-" * 30)
            print(f"  Logged in as : {logged_in_as}")
            print("  Action       : Run --logout first")
            print("")
            return None

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print("")
            print("  ERROR: Login Failed")
            print("  " + "-" * 30)
            print("  Reason : Username not found")
            print("")
            return None

        pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not pwd.verify(password, user.password_hash):
            print("")
            print("  ERROR: Login Failed")
            print("  " + "-" * 30)
            print("  Reason : Incorrect password")
            print("")
            return None

        token  = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(minutes=SESSION_TTL_MINUTES)
        db.add(DBSession(user_id=user.id, token=token, expires_at=expiry))
        db.commit()
        _write_session_file(token)

        print("")
        print("  Login Successful")
        print("  " + "=" * 50)
        print(f"  Username   : {username}")
        #print(f"  Token      : {token}")
        print(f"  Expires in : {SESSION_TTL_MINUTES} minutes")
        print("  " + "=" * 50)
        
        return token
    finally:
        db.close()


def logout():
    token = _read_session_file()
    if not token:
        print("")
        print("  WARNING: Not currently logged in.")
        print("")
        return

    db = SessionLocal()
    try:
        db.query(DBSession).filter(DBSession.token == token).delete()
        db.commit()
    finally:
        db.close()

    import os
    try:
        os.remove(".session")
    except FileNotFoundError:
        pass

    print("")
    print("  Logout Successful")
    print("  " + "-" * 30)
    print("  Status : Token invalidated. Session ended.")
    print("")


def validate_session() -> int | None:
    
    token = _read_session_file()
    if not token:
        return None
    return _validate_token(token)


def validate_token_arg(token: str) -> int | None:
    
    if not token:
        return None
    return _validate_token(token)


def _validate_token(token: str) -> int | None:
    db = SessionLocal()
    try:
        s = db.query(DBSession).filter(DBSession.token == token).first()
        if not s:
            return None
        if s.expires_at < datetime.utcnow():
            db.delete(s)
            db.commit()
            return None
        return s.user_id
    finally:
        db.close()


def _read_session_file() -> str | None:
    try:
        with open(".session", "r") as f:
            t = f.read().strip()
            return t if t else None
    except FileNotFoundError:
        return None


def _write_session_file(token: str):
    with open(".session", "w") as f:
        f.write(token)


def get_current_user_id() -> int | None:
    
    return validate_session()
