from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def test_health_endpoint_ok():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
