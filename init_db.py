"""Initialize the database — create all tables."""
from app.db import engine
from app.models import Base

Base.metadata.create_all(engine)

print("")
print("  Database Initialized")
print("  " + "-" * 30)
print("  Status : All tables created in media.db")
print("")
print("  Next: python seed_data.py")
print("")
