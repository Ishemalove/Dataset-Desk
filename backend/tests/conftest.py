import os
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ENABLE_EXPORT_JOBS"] = "false"

from app.auth import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Episode, EpisodeQuality, User, UserRole

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    client_user = User(
        email="client@test.com",
        password_hash=hash_password("pass123"),
        role=UserRole.client,
        name="Test Client",
        organisation="Test Co",
    )
    operator = User(
        email="ops@test.com",
        password_hash=hash_password("pass123"),
        role=UserRole.operator,
        name="Test Operator",
    )
    admin = User(
        email="admin@test.com",
        password_hash=hash_password("pass123"),
        role=UserRole.admin,
        name="Test Admin",
    )
    db.add_all([client_user, operator, admin])
    db.commit()

    good_ep = Episode(
        episode_id="EP-TEST-001",
        robot_id="arm-01",
        task_name="pick cup",
        recorded_at=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
        duration_seconds=30,
        operator_name="Alice",
        quality=EpisodeQuality.good,
    )
    bad_ep = Episode(
        episode_id="EP-TEST-002",
        robot_id="arm-02",
        task_name="pick cup",
        recorded_at=datetime(2026, 8, 1, 11, 0, tzinfo=timezone.utc),
        duration_seconds=30,
        operator_name="Bob",
        quality=EpisodeQuality.bad,
    )
    db.add_all([good_ep, bad_ep])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def login(client, email: str, password: str = "pass123") -> str:
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def client_token(client):
    return login(client, "client@test.com")


@pytest.fixture
def operator_token(client):
    return login(client, "ops@test.com")


@pytest.fixture
def admin_token(client):
    return login(client, "admin@test.com")
