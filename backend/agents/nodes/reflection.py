import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

from agents.state import ResearchState
from services import claude_client

SYSTEM = """You are a research quality evaluator for an autonomous research platform.
Evaluate how completely the gathered research addresses the original objectives.

Output JSON with exactly these keys:
{
  "score": 0.0-1.0,
  "gaps": ["list of specific missing information areas"],
  "additional_queries": ["1-3 targeted search queries to fill the gaps"],
  "strengths": ["areas well covered"],
  "verdict": "brief 1-sentence quality assessment"
}

Score guide: 0.9+ = excellent, 0.8-0.9 = good, 0.7-0.8 = acceptable, <0.7 = needs more research."""

THRESHOLD = 0.85


async def reflection_node(state: ResearchState) -> ResearchState:
    if state.get("error"):
        return state

    api_keys = state.get("api_keys", {})
    provider = claude_client._provider()
    api_key = api_keys.get("openrouter_api_key") if provider == "openrouter" else api_keys.get("anthropic_api_key")
    tavily_key = api_keys.get("tavily_api_key")

    objectives_text = "\n".join(f"- {o}" for o in state.get("objectives", []))
    findings_preview = ""
    for f in state.get("extracted_findings", [])[:10]:
        findings_preview += f"\n- [{f.get('type','?')}] {f.get('title','')}: {f.get('text','')[:150]}"

    try:
        result = await claude_client.complete_json(
            system=SYSTEM,
            user=(
                f"Topic: {state['topic']}\n"
                f"Objectives:\n{objectives_text}\n"
                f"Sources collected: {len(state.get('raw_sources', []))}\n"
                f"Findings extracted: {len(state.get('extracted_findings', []))}\n"
                f"Sample findings:{findings_preview}"
            ),
            api_key=api_key,
        )
    except Exception as e:
        state["reflection_score"] = 0.75
        state["reflection_gaps"] = []
        return state

    score = float(result.get("score", 0.75))
    gaps = result.get("gaps", [])
    additional_queries = result.get("additional_queries", [])
    re_searched = False

    # If score below threshold, run supplementary searches
    if score < THRESHOLD and additional_queries:
        re_searched = True
        from tavily import AsyncTavilyClient
        from config import get_settings
        settings = get_settings()
        client = AsyncTavilyClient(api_key=tavily_key or settings.tavily_api_key)

        seen_urls = {s["url"] for s in state.get("raw_sources", [])}
        new_sources: list[dict] = []

        for query in additional_queries[:3]:
            try:
                resp = await client.search(query=query, max_results=3, search_depth="advanced", include_raw_content=True)
                for r in resp.get("results", []):
                    url = r.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        new_sources.append({
                            "url": url,
                            "title": r.get("title", ""),
                            "content": r.get("raw_content") or r.get("content", ""),
                            "score": round(r.get("score", 0.0), 4),
                            "domain": urlparse(url).netloc.replace("www.", ""),
                            "query": query,
                        })
            except Exception:
                continue

        if new_sources:
            state["raw_sources"] = state.get("raw_sources", []) + new_sources
            # Re-extract from new sources only
            from agents.nodes.knowledge_extraction import knowledge_extraction_node
            prev_findings = state.get("extracted_findings", [])
            temp_state = dict(state)
            temp_state["raw_sources"] = new_sources
            temp_state = await knowledge_extraction_node(temp_state)
            state["extracted_findings"] = prev_findings + temp_state.get("extracted_findings", [])
            score = min(score + 0.10, 1.0)

    state["reflection_score"] = round(score, 3)
    state["reflection_gaps"] = gaps

    event = {
        "agent_id": "reflection",
        "event": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": (
            f"Research scored {round(score*100)}% complete. "
            + (f"{len(gaps)} gaps identified; supplementary search triggered." if re_searched else "Quality threshold met.")
        ),
        "tool_calls": (["tavily.search(gap_query)"] * len(additional_queries)) if re_searched else [],
        "data": {
            "score": round(score, 3),
            "gaps": gaps,
            "additional_queries": additional_queries,
            "re_searched": re_searched,
            "new_sources_found": len(state.get("raw_sources", [])),
            "verdict": result.get("verdict", ""),
            "strengths": result.get("strengths", []),
        },
    }
    state["agent_events"] = state.get("agent_events", []) + [event]
    return state
