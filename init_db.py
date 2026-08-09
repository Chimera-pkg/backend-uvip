"""
UVIP Database Initialization Script
====================================
Jalankan sekali setelah container pertama kali start untuk membuat semua tabel.
Cara pakai:
    docker compose exec app python init_db.py
"""
from app.db.database import engine, Base

# Import SEMUA models agar Base.metadata tahu semua tabel
from app.db import models  # noqa: F401

def init():
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")

    # List tables that were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📋 Tables in database ({len(tables)}):")
    for t in tables:
        print(f"   - {t}")

if __name__ == "__main__":
    init()
