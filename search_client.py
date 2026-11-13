import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent / ".env")

MAX_RESULTS = 5


def build_search_query(requirement, target_level="L3"):
    return (
        f"{requirement} 官方文档 教程 "
        f"{target_level} 可运行项目"
    )


async def search_learning_resources(
    requirement,
    max_results=5,
):
    provider = os.getenv("SEARCH_PROVIDER", "tavily")
    api_key = os.getenv("SEARCH_API_KEY")

    if provider != "tavily":
        raise RuntimeError(
            f"不支持的搜索服务：{provider}"
        )
    if not api_key:
        raise RuntimeError("缺少 SEARCH_API_KEY")

    max_results = max(1, min(int(max_results), MAX_RESULTS))
    base_url = os.getenv(
        "SEARCH_BASE_URL",
        "https://api.tavily.com",
    ).rstrip("/")

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{base_url}/search",
            json={
                "api_key": api_key,
                "query": build_search_query(requirement),
                "max_results": max_results,
                "search_depth": "basic",
            },
        )
        response.raise_for_status()
        data = response.json()

    results = data.get("results", [])

    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
            "score": item.get("score"),
        }
        for item in results[:max_results]
        if item.get("url")
    ]