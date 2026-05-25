import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

from tavily import AsyncTavilyClient

from agents.state import ResearchState
from config import get_settings

settings = get_settings()
_tavily: AsyncTavilyClient | None = None

MAX_CONCURRENT = 3
MAX_SEARCH_QUERIES = 4
MAX_RESULTS_PER_QUERY = 3


def get_tavily(api_key: str | None = None) -> AsyncTavilyClient:
    global _tavily
    if api_key:
        return AsyncTavilyClient(api_key=api_key)
    if _tavily is None:
        _tavily = AsyncTavilyClient(api_key=settings.tavily_api_key)
    return _tavily


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return url


async def _search_one(query: str, semaphore: asyncio.Semaphore, tavily_key: str | None = None) -> list[dict]:
    async with semaphore:
        try:
            client = get_tavily(tavily_key)
            resp = await client.search(
                query=query,
                max_results=MAX_RESULTS_PER_QUERY,
                search_depth="advanced",
                include_raw_content=True,
                include_answer=True,
            )
            results = []
            for r in resp.get("results", []):
                results.append({
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "content": r.get("raw_content") or r.get("content", ""),
                    "score": round(r.get("score", 0.0), 4),
                    "domain": _extract_domain(r.get("url", "")),
                    "query": query,
                })
            return results
        except Exception as e:
            return []


async def web_research_node(state: ResearchState) -> ResearchState:
    if state.get("error"):
        return state

    api_keys = state.get("api_keys", {})
    tavily_key = api_keys.get("tavily_api_key")

    queries = state.get("search_queries", [state["topic"]])[:MAX_SEARCH_QUERIES]
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    tasks = [_search_one(q, semaphore, tavily_key) for q in queries]
    all_results = await asyncio.gather(*tasks)

    # Flatten and deduplicate by URL
    seen_urls: set[str] = set()
    raw_sources: list[dict] = []
    for batch in all_results:
        for source in batch:
            if source["url"] and source["url"] not in seen_urls:
                seen_urls.add(source["url"])
                raw_sources.append(source)

    state["raw_sources"] = raw_sources

    per_query_counts = [len(b) for b in all_results]
    event = {
        "agent_id": "web_research",
        "event": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": f"Executed {len(queries)} searches, collected {len(raw_sources)} unique sources across {len(set(s['domain'] for s in raw_sources))} domains.",
        "tool_calls": [f"tavily.search({q[:40]}…)" for q in queries],
        "data": {
            "query_count": len(queries),
            "source_count": len(raw_sources),
            "queries": queries,
            "sources": [{"url": s["url"], "title": s["title"], "domain": s["domain"], "score": s["score"]} for s in raw_sources],
        },
    }
    state["agent_events"] = state.get("agent_events", []) + [event]
    return state
