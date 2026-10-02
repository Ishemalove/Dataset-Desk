#!/usr/bin/env python3
"""Seed users and import episodes from candidate-pack/seed."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth import hash_password
from app.database import SessionLocal
from app.models import User, UserRole
from app.services.import_episodes import import_episodes_csv

def _find_seed_dir() -> Path:
    candidates = [
        Path("/candidate-pack/seed"),
        Path(__file__).resolve().parents[2] / "candidate-pack" / "seed",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Could not locate candidate-pack/seed directory")


SEED_DIR = _find_seed_dir()


def main():
    db = SessionLocal()
    users_path = SEED_DIR / "users.json"
    if users_path.exists():
        users = json.loads(users_path.read_text())
        for u in users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
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
        print(f"Seeded {len(users)} users")

    csv_path = SEED_DIR / "episodes.csv"
    if csv_path.exists():
        result = import_episodes_csv(db, csv_path.read_text(encoding="utf-8-sig"))
        print(
            f"Episodes: imported={result['imported']} updated={result['updated']} "
            f"skipped={result['skipped']} errors={len(result['errors'])}"
        )
    db.close()


if __name__ == "__main__":
    main()
