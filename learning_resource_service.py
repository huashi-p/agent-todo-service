from datetime import datetime, timezone

from application_service import normalize_text
from evidence_service import requirement_terms
from resource_fetcher import fetch_sources
from search_client import search_learning_resources


MAX_SEARCH_RESULTS = 5
MAX_FETCH_SOURCES = 3
MAX_EXCERPTS_PER_SOURCE = 2
MAX_EXCERPT_CHARS = 800

def select_resource_urls(results, limit=MAX_FETCH_SOURCES):
    selected = []
    seen = set()

    for item in results:
        url = str(item.get("url", "")).strip()
        if not url or url in seen:
            continue

        selected.append(url)
        seen.add(url)

        if len(selected) >= limit:
            break

    return selected

def select_excerpts(requirement, text):
    paragraphs = [
        part.strip()
        for part in (text or "").split("\n\n")
        if part.strip()
    ]
    terms = requirement_terms(requirement)
    scored = []

    for paragraph in paragraphs:
        searchable = normalize_text(paragraph)
        score = sum(
            searchable.count(term)
            for term in terms
        )
        scored.append((score, paragraph))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [
        paragraph[:MAX_EXCERPT_CHARS]
        for score, paragraph in scored
        if score > 0
    ][:MAX_EXCERPTS_PER_SOURCE]

    if not selected and paragraphs:
        selected = [
            paragraphs[0][:MAX_EXCERPT_CHARS]
        ]

    return "\n\n".join(selected)

async def collect_learning_resources(
    requirement,
    target_level="L3",
    search_topics=None,
):
    search_query = (
        " ".join(
            str(topic).strip()
            for topic in (search_topics or [])
            if str(topic).strip()
        )
        or requirement
    )

    try:
        results = await search_learning_resources(
            search_query,
            target_level=target_level,
            max_results=MAX_SEARCH_RESULTS,
        )
    except Exception as error:
        return {
            "ok": False,
            "status": "search_failed",
            "error": f"{type(error).__name__}: {error}",
            "sources": [],
            "failed": [],
        }

    if not results:
        return {
            "ok": False,
            "status": "no_search_results",
            "error": "",
            "sources": [],
            "failed": [],
        }

    urls = select_resource_urls(results)
    sources = await fetch_sources(requirement, urls)
    successful = [source for source in sources if source.ok]

    if not successful:
        return {
            "ok": False,
            "status": "fetch_failed",
            "error": "",
            "sources": [],
            "failed": [
                {
                    "url": source.url,
                    "error": source.error,
                }
                for source in sources
            ],
        }

    fetched_at = datetime.now(timezone.utc).isoformat()
    score_by_url = {
        item["url"]: item.get("score")
        for item in results
    }
    snapshots = []

    for index, source in enumerate(successful, start=1):
        excerpt = select_excerpts(
            search_query,
            source.text,
        )
        if not excerpt:
            continue

        snapshots.append(
            {
                "source_id": f"RESOURCE_{index}",
                "title": source.title,
                "url": source.url,
                "final_url": source.final_url or source.url,
                "fetched_at": fetched_at,
                "excerpt": excerpt,
                "search_score": score_by_url.get(source.url),
            }
        )

    return {
        "ok": bool(snapshots),
        "status": "grounded" if snapshots else "no_relevant_content",
        "error": "",
        "sources": snapshots,
        "failed": [
            {
                "url": source.url,
                "error": source.error,
            }
            for source in sources
            if not source.ok
        ],
    }
