"""Tests for api-gateway service."""
from __future__ import annotations

import sys
import os

# Add service root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db
from models import Base

# ---- in-memory SQLite test DB with shared connection ----
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


def get_token():
    resp = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_login_valid_credentials():
    resp = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_invalid_credentials():
    resp = client.post("/auth/login", data={"username": "admin", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_list_repositories_without_auth():
    resp = client.get("/repositories")
    assert resp.status_code == 401


def test_connect_repository_with_auth():
    token = get_token()
    resp = client.post(
        "/repositories/connect",
        json={"name": "company/backend", "provider": "github"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "company/backend"
    assert data["provider"] == "github"
    assert "id" in data


def test_get_review_not_found():
    resp = client.get("/reviews/9999")
    assert resp.status_code == 404


def test_get_alerts_requires_auth():
    resp = client.get("/alerts")
    assert resp.status_code == 401


def test_get_alerts_with_auth():
    token = get_token()
    resp = client.get("/alerts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
