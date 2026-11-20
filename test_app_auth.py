import base64

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


def test_non_ascii_credentials_do_not_crash(monkeypatch):
    monkeypatch.setenv("APP_AUTH_ENABLED", "true")
    monkeypatch.setenv("APP_USERNAME", "测试用户")
    monkeypatch.setenv("APP_PASSWORD", "测试密码")

    raw = "测试用户:测试密码".encode("utf-8")
    token = base64.b64encode(raw).decode("ascii")

    response = client.get(
        "/static/applications.html",
        headers={
            "Authorization": f"Basic {token}",
        },
    )

    assert response.status_code == 200
