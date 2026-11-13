import asyncio

import httpx
import pytest

import search_client


def run(coro):
    return asyncio.run(coro)


class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self.data = data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request(
                "POST",
                "https://api.tavily.com/search",
            )
            response = httpx.Response(
                self.status_code,
                request=request,
            )
            raise httpx.HTTPStatusError(
                "search failed",
                request=request,
                response=response,
            )

    def json(self):
        return self.data


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, *args, **kwargs):
        if self.error is not None:
            raise self.error
        return self.response


def patch_client(monkeypatch, response=None, error=None):
    monkeypatch.setattr(
        search_client.httpx,
        "AsyncClient",
        lambda **kwargs: FakeClient(response, error),
    )


def test_search_requires_api_key(monkeypatch):
    monkeypatch.delenv("SEARCH_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SEARCH_API_KEY"):
        run(search_client.search_learning_resources("RAG"))


def test_search_handles_timeout(monkeypatch):
    monkeypatch.setenv("SEARCH_API_KEY", "test-key")
    patch_client(
        monkeypatch,
        error=httpx.TimeoutException("timeout"),
    )

    with pytest.raises(httpx.TimeoutException):
        run(search_client.search_learning_resources("RAG"))


def test_search_handles_rate_limit(monkeypatch):
    monkeypatch.setenv("SEARCH_API_KEY", "test-key")
    patch_client(
        monkeypatch,
        response=FakeResponse(status_code=429),
    )

    with pytest.raises(httpx.HTTPStatusError):
        run(search_client.search_learning_resources("RAG"))


def test_search_returns_empty_list(monkeypatch):
    monkeypatch.setenv("SEARCH_API_KEY", "test-key")
    patch_client(
        monkeypatch,
        response=FakeResponse(data={"results": []}),
    )

    results = run(
        search_client.search_learning_resources("RAG")
    )

    assert results == []


def test_search_filters_results_without_url(monkeypatch):
    monkeypatch.setenv("SEARCH_API_KEY", "test-key")
    patch_client(
        monkeypatch,
        response=FakeResponse(
            data={
                "results": [
                    {
                        "title": "没有 URL 的结果",
                        "content": "应被过滤",
                    },
                    {
                        "title": "有效结果",
                        "url": "https://example.com/guide",
                        "content": "有效摘要",
                        "score": 0.9,
                    },
                ]
            }
        ),
    )

    results = run(
        search_client.search_learning_resources("RAG")
    )

    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/guide"