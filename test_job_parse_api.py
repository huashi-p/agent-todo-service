from fastapi.testclient import TestClient

import main
from schemas import ParsedJob


client = TestClient(main.app)


def test_parse_job_api_returns_structured_fields(monkeypatch):
    async def fake_parse(description):
        return ParsedJob(
            company="解析测试公司",
            title="后端开发实习生",
            location="深圳",
            source_url=None,
            deadline=None,
            requirements=[
                "熟悉 Python",
                "了解 FastAPI",
            ],
        )

    monkeypatch.setenv("APP_AUTH_ENABLED", "true")
    monkeypatch.setenv("APP_USERNAME", "tester")
    monkeypatch.setenv("APP_PASSWORD", "secret")
    monkeypatch.setattr(
        main,
        "parse_job_description",
        fake_parse,
    )

    response = client.post(
        "/api/jobs/parse",
        auth=("tester", "secret"),
        json={
            "description": (
                "解析测试公司招聘后端开发实习生，"
                "要求熟悉 Python 并了解 FastAPI。"
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["company"] == "解析测试公司"
    assert data["title"] == "后端开发实习生"
    assert data["requirements"] == [
        "熟悉 Python",
        "了解 FastAPI",
    ]
