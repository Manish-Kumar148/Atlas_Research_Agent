import asyncio
from datetime import datetime, timezone
from services import claude_client
from agents.state import ResearchState

SYSTEM = """You are a knowledge extraction specialist. Given web research content, extract structured findings.

Output a JSON array of findings. Each finding must have:
{
  "type": "finding | trend | limitation | metric | quote",
  "title": "short descriptive title (max 8 words)",
  "text": "2-4 sentence explanation with specific details",
  "source_url": "the URL this came from",
  "confidence": 0.0-1.0
}

Extract 3-6 findings per batch. Focus on: specific data points, emerging trends,
technical limitations, market metrics, and expert statements. Be specific — avoid vague generalities."""

BATCH_SIZE = 3
MAX_EXTRACTION_CONCURRENT = 3


async def _extract_batch(state: ResearchState, batch: list[dict], semaphore: asyncio.Semaphore, api_key: str | None = None) -> list[dict]:
    async with semaphore:
        batch_text = ""
        for source in batch:
            content_snippet = (source.get("content") or "")[:1500]
            batch_text += f"\n\n---\nURL: {source['url']}\nTitle: {source['title']}\nContent: {content_snippet}"

        try:
            result = await claude_client.complete_json(
                system=SYSTEM,
                user=f"Topic: {state['topic']}\n\nSources:{batch_text}",
                max_tokens=1500,
                api_key=api_key,
            )
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "findings" in result:
                return result["findings"]
        except Exception:
            return []

    return []


async def knowledge_extraction_node(state: ResearchState) -> ResearchState:
    if state.get("error"):
        return state

    sources = state.get("raw_sources", [])
    if not sources:
        state["extracted_findings"] = []
        return state

    api_keys = state.get("api_keys", {})
    provider = claude_client._provider()
    api_key = api_keys.get("openrouter_api_key") if provider == "openrouter" else api_keys.get("anthropic_api_key")

    batches = [sources[i: i + BATCH_SIZE] for i in range(0, len(sources), BATCH_SIZE)]
    semaphore = asyncio.Semaphore(MAX_EXTRACTION_CONCURRENT)
    batch_results = await asyncio.gather(*(_extract_batch(state, batch, semaphore, api_key) for batch in batches))
    all_findings = [finding for findings in batch_results for finding in findings]

    state["extracted_findings"] = all_findings

    type_counts: dict[str, int] = {}
    for f in all_findings:
        t = f.get("type", "finding")
        type_counts[t] = type_counts.get(t, 0) + 1

    event = {
        "agent_id": "knowledge_extraction",
        "event": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": f"Extracted {len(all_findings)} findings from {len(sources)} sources across {len(type_counts)} finding types.",
        "tool_calls": [f"extract_batch({index + 1})" for index in range(len(batches))],
        "data": {
            "finding_count": len(all_findings),
            "type_breakdown": type_counts,
            "findings": all_findings[:5],  # preview first 5
        },
    }
    state["agent_events"] = state.get("agent_events", []) + [event]
    return state
