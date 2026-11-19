import asyncio

import pytest

from resource_fetcher import fetch_sources
from resource_guard import SourceReadError
from resource_guard import validate_public_url
import learning_resource_service as resource_service
import resource_fetcher
from schemas import ResourceSourceStatus

def run(coro):
    return asyncio.run(coro)


def test_private_url_is_blocked():
    with pytest.raises(SourceReadError):
        run(validate_public_url("http://127.0.0.1/"))


def test_non_http_port_is_blocked():
    with pytest.raises(SourceReadError):
        run(validate_public_url("http://example.com:6379/"))


def test_partial_fetch_failure_is_kept(monkeypatch):
    async def fake_fetch_with_retry(client, url):
        if "blocked" in url:
            raise SourceReadError(
                "blocked_address",
                "模拟抓取失败",
            )

        return url, (
            "<html><head><title>Example</title></head>"
            "<body><p>有效正文</p></body></html>"
        )

    monkeypatch.setattr(
        resource_fetcher,
        "fetch_with_retry",
        fake_fetch_with_retry,
    )

    sources = run(
        resource_fetcher.fetch_sources(
            "测试部分失败",
            [
                "https://example.com/guide",
                "https://blocked.example/",
            ],
        )
    )

    assert any(source.ok for source in sources)
    assert any(not source.ok for source in sources)

def test_collect_returns_no_search_results(monkeypatch):
    async def fake_search(*args, **kwargs):
        return []

    monkeypatch.setattr(
        resource_service,
        "search_learning_resources",
        fake_search,
    )

    result = run(
        resource_service.collect_learning_resources("Docker")
    )

    assert result["status"] == "no_search_results"
    assert result["sources"] == []


def test_collect_handles_search_error(monkeypatch):
    async def fake_search(*args, **kwargs):
        raise RuntimeError("搜索失败")

    monkeypatch.setattr(
        resource_service,
        "search_learning_resources",
        fake_search,
    )

    result = run(
        resource_service.collect_learning_resources("Docker")
    )

    assert result["status"] == "search_failed"
    assert result["sources"] == []

def test_collect_returns_fetch_failed(monkeypatch):
    async def fake_search(*args, **kwargs):
        return [
            {"url": f"https://example.com/{index}", "score": 0.8}
            for index in range(5)
        ]

    async def fake_fetch(requirement, urls):
        return [
            ResourceSourceStatus(
                url=url,
                ok=False,
                error="timeout",
            )
            for url in urls
        ]

    monkeypatch.setattr(
        resource_service,
        "search_learning_resources",
        fake_search,
    )
    monkeypatch.setattr(
        resource_service,
        "fetch_sources",
        fake_fetch,
    )

    result = run(
        resource_service.collect_learning_resources("Docker")
    )

    assert result["status"] == "fetch_failed"
    assert result["sources"] == []
    assert len(result["failed"]) == 3


def test_collect_keeps_success_and_builds_snapshot(monkeypatch):
    captured_queries = []

    async def fake_search(query, *args, **kwargs):
        captured_queries.append(query)
        return [
            {
                "url": "https://example.com/docker",
                "score": 0.91,
            },
            {
                "url": "https://example.com/failed",
                "score": 0.70,
            },
        ]

    async def fake_fetch(requirement, urls):
        return [
            ResourceSourceStatus(
                url="https://example.com/docker",
                final_url="https://example.com/docker",
                ok=True,
                title="Docker Guide",
                text="Docker 容器部署需要编写镜像。\n\n无关段落。",
            ),
            ResourceSourceStatus(
                url="https://example.com/failed",
                ok=False,
                error="timeout",
            ),
        ]

    monkeypatch.setattr(
        resource_service,
        "search_learning_resources",
        fake_search,
    )
    monkeypatch.setattr(
        resource_service,
        "fetch_sources",
        fake_fetch,
    )

    result = run(
        resource_service.collect_learning_resources(
            "Docker 容器部署",
            target_level="L2",
            search_topics=[
                "Docker 镜像构建",
                "Docker Compose",
            ],
        )
    )

    assert captured_queries == [
        "Docker 镜像构建 Docker Compose"
    ]
    assert result["status"] == "grounded"
    assert len(result["sources"]) == 1
    assert len(result["failed"]) == 1

    source = result["sources"][0]
    assert source["url"]
    assert source["fetched_at"]
    assert source["excerpt"]
    assert source["search_score"] == 0.91

