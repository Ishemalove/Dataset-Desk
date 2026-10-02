#!/usr/bin/env python3
"""Bootstrap Postgres, seed data, and start the API.

    python scripts/run_local.py

Requires a local PostgreSQL instance (user postgres, password love).
Create the database once with:

    & "C:\\Program Files\\PostgreSQL\\17\\bin\\psql.exe" -U postgres -c "CREATE DATABASE dataset_desk;"

Then run the frontend separately: cd frontend && npm run dev
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_URL = "postgresql://postgres:love@localhost:5432/dataset_desk"

os.environ["DATABASE_URL"] = DATABASE_URL
os.environ.setdefault("SECRET_KEY", "dev-secret-change-in-production")
sys.path.insert(0, str(ROOT))


def ensure_database() -> None:
    import psycopg2

    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="love",
        dbname="postgres",
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'dataset_desk'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE dataset_desk")
        print("Created database dataset_desk")
    else:
        print("Database dataset_desk is ready")
    cur.close()
    conn.close()


def migrate_and_seed() -> None:
    from app.auth import hash_password
    from app.database import Base, SessionLocal, engine
    from app.models import User, UserRole
    from app.services.import_episodes import import_episodes_csv
    import json

    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.exec_driver_sql(
            "ALTER TABLE assignments ADD COLUMN IF NOT EXISTS export_status VARCHAR(32) NOT NULL DEFAULT 'pending'"
        )
        conn.exec_driver_sql(
            "ALTER TABLE assignments ADD COLUMN IF NOT EXISTS export_attempts INTEGER NOT NULL DEFAULT 0"
        )

    db = SessionLocal()
    seed_dir = ROOT.parent / "candidate-pack" / "seed"
    users_path = seed_dir / "users.json"
    if users_path.exists():
        for u in json.loads(users_path.read_text()):
            if db.query(User).filter(User.email == u["email"]).first():
                continue
            db.add(
                User(
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    role=UserRole(u["role"]),
                    name=u["name"],
                    organisation=u.get("organisation"),
                )
            )
        db.commit()
        print("Seeded users")

    csv_path = seed_dir / "episodes.csv"
    if csv_path.exists():
        from app.models import Episode

        if db.query(Episode).count() == 0:
            result = import_episodes_csv(db, csv_path.read_text(encoding="utf-8-sig"))
            print(
                f"Episodes: imported={result['imported']} updated={result['updated']} "
                f"skipped={result['skipped']}"
            )
        else:
            print(f"Episodes already present ({db.query(Episode).count()})")
    db.close()


if __name__ == "__main__":
    print("Connecting to PostgreSQL as postgres@localhost/dataset_desk")
    ensure_database()
    migrate_and_seed()
    print("API starting at http://localhost:8000")
    print("Open frontend with: cd frontend && npm run dev")
    (ROOT / ".env").write_text(
        f"DATABASE_URL={DATABASE_URL}\nSECRET_KEY={os.environ['SECRET_KEY']}\nENABLE_EXPORT_JOBS=true\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(ROOT),
        env=os.environ.copy(),
    )
