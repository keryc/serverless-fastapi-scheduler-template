from src.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_endpoint_ok():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
