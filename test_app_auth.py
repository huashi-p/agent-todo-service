from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_is_public(monkeypatch):
    monkeypatch.setenv("APP_AUTH_ENABLED", "true")

    response = client.get("/health")

    assert response.status_code == 200


def test_api_requires_auth(monkeypatch):
    monkeypatch.setenv("APP_AUTH_ENABLED", "true")
    monkeypatch.setenv("APP_USERNAME", "tester")
    monkeypatch.setenv("APP_PASSWORD", "secret")

    response = client.get("/api/applications")

    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith(
        "Basic"
    )


def test_protected_route_accepts_valid_auth(monkeypatch):
    monkeypatch.setenv("APP_AUTH_ENABLED", "true")
    monkeypatch.setenv("APP_USERNAME", "tester")
    monkeypatch.setenv("APP_PASSWORD", "secret")

    response = client.get(
        "/static/applications.html",
        auth=("tester", "secret"),
    )

    assert response.status_code == 200


def test_missing_credentials_fail_closed(monkeypatch):
    monkeypatch.setenv("APP_AUTH_ENABLED", "true")
    monkeypatch.delenv("APP_USERNAME", raising=False)
    monkeypatch.delenv("APP_PASSWORD", raising=False)

    response = client.get("/api/applications")

    assert response.status_code == 503
