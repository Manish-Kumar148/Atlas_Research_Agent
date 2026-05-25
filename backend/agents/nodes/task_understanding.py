from datetime import datetime, timezone
from agents.state import ResearchState
from services import claude_client

SYSTEM = """You are a research intent classifier for an autonomous research platform.
Given a research topic, analyze and classify it.

Output JSON with exactly these keys:
{
  "domain": "string (e.g. AI / Machine Learning, Biotechnology, Finance, etc.)",
  "objectives": ["list", "of", "3-5", "specific", "research", "objectives"],
  "output_types": ["technical analysis", "market landscape", "recommendations"],
  "complexity": "low | medium | high",
  "key_entities": ["list of main entities, companies, technologies to research"]
}"""


async def task_understanding_node(state: ResearchState) -> ResearchState:
    try:
        api_keys = state.get("api_keys", {})
        provider = claude_client._provider()
        api_key = api_keys.get("openrouter_api_key") if provider == "openrouter" else api_keys.get("anthropic_api_key")

        result = await claude_client.complete_json(
            system=SYSTEM,
            user=f"Research topic: {state['topic']}",
            api_key=api_key,
        )

        state["domain"] = result.get("domain", "Technology Research")
        state["objectives"] = result.get("objectives", [state["topic"]])

        event = {
            "agent_id": "task_understanding",
            "event": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": f"Classified as {state['domain']} research with {len(state['objectives'])} objectives identified.",
            "tool_calls": [],
            "data": {
                "domain": state["domain"],
                "objectives": state["objectives"],
                "output_types": result.get("output_types", []),
                "complexity": result.get("complexity", "medium"),
                "key_entities": result.get("key_entities", []),
            },
        }
        state["agent_events"] = state.get("agent_events", []) + [event]

    except Exception as e:
        state["error"] = f"task_understanding failed: {str(e)}"
        state["agent_events"] = state.get("agent_events", []) + [{
            "agent_id": "task_understanding",
            "event": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": f"Error: {str(e)}",
            "tool_calls": [],
            "data": {},
        }]

    return state
