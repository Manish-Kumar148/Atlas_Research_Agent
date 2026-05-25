from datetime import datetime, timezone
from agents.state import ResearchState
from services import claude_client

SYSTEM = """You are a research planning agent for an autonomous research platform.
Given research objectives, create a structured execution plan.

Output JSON with exactly these keys:
{
  "subtasks": [
    {
      "id": "subtask_1",
      "title": "string",
      "description": "string",
      "search_focus": "string describing what to search for"
    }
  ],
  "search_queries": [
    "list of 6-8 targeted, specific search query strings"
  ],
  "estimated_sources_needed": 15,
  "parallel_tracks": ["track1 name", "track2 name"]
}

Make search queries specific and varied — mix overview queries with deep-dive technical queries."""


async def planning_node(state: ResearchState) -> ResearchState:
    if state.get("error"):
        return state

    try:
        api_keys = state.get("api_keys", {})
        provider = claude_client._provider()
        api_key = api_keys.get("openrouter_api_key") if provider == "openrouter" else api_keys.get("anthropic_api_key")

        objectives_text = "\n".join(f"- {o}" for o in state.get("objectives", []))
        result = await claude_client.complete_json(
            system=SYSTEM,
            user=f"Topic: {state['topic']}\nDomain: {state['domain']}\nObjectives:\n{objectives_text}",
            api_key=api_key,
        )

        state["subtasks"] = result.get("subtasks", [])
        state["search_queries"] = result.get("search_queries", [state["topic"]])

        event = {
            "agent_id": "planning",
            "event": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": f"Generated {len(state['subtasks'])} subtasks and {len(state['search_queries'])} targeted search queries.",
            "tool_calls": [],
            "data": {
                "subtask_count": len(state["subtasks"]),
                "subtasks": state["subtasks"],
                "search_queries": state["search_queries"],
                "estimated_sources": result.get("estimated_sources_needed", 15),
                "parallel_tracks": result.get("parallel_tracks", []),
            },
        }
        state["agent_events"] = state.get("agent_events", []) + [event]

    except Exception as e:
        state["error"] = f"planning failed: {str(e)}"
        state["agent_events"] = state.get("agent_events", []) + [{
            "agent_id": "planning",
            "event": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": f"Error: {str(e)}",
            "tool_calls": [],
            "data": {},
        }]

    return state
