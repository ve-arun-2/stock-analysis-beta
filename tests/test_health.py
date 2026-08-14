"""Smoke test proving the app boots and the router is wired up correctly."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
