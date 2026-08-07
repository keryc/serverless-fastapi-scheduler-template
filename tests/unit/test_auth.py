import pytest
from fastapi.testclient import TestClient

from src.app.core import auth
from src.app.main import app

client = TestClient(app)


@pytest.fixture
def token(monkeypatch):
    monkeypatch.setattr(auth.settings, "API_BEARER_TOKEN", "s3cret")
    return "s3cret"


def test_protected_endpoint_requires_a_token(token):
    assert client.get("/api/v1/tasks").status_code == 401


def test_protected_endpoint_rejects_a_wrong_token(token):
    r = client.get("/api/v1/tasks", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


def test_protected_endpoint_accepts_the_configured_token(token):
    r = client.get("/api/v1/tasks", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    ids = [task["id"] for task in r.json()["tasks"]]
    assert "nightly-cleanup" in ids


def test_unconfigured_token_returns_503(monkeypatch):
    monkeypatch.setattr(auth.settings, "API_BEARER_TOKEN", "")
    r = client.get("/api/v1/tasks", headers={"Authorization": "Bearer anything"})
    assert r.status_code == 503
