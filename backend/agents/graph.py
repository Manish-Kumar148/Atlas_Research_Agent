import asyncio
from datetime import datetime, timezone
from typing import AsyncIterator

from langgraph.graph import StateGraph, END

from agents.state import ResearchState
from agents.nodes.task_understanding import task_understanding_node
from agents.nodes.planning import planning_node
from agents.nodes.web_research import web_research_node
from agents.nodes.knowledge_extraction import knowledge_extraction_node
from agents.nodes.memory_agent import memory_agent_node
from agents.nodes.reflection import reflection_node
from agents.nodes.report_generation import report_generation_node


def _should_continue(state: ResearchState) -> str:
    if state.get("error"):
        return END
    return "continue"


# Build and compile the graph once at module level
_builder = StateGraph(ResearchState)

_builder.add_node("task_understanding", task_understanding_node)
_builder.add_node("planning", planning_node)
_builder.add_node("web_research", web_research_node)
_builder.add_node("knowledge_extraction", knowledge_extraction_node)
_builder.add_node("memory_agent", memory_agent_node)
_builder.add_node("reflection", reflection_node)
_builder.add_node("report_generation", report_generation_node)

_builder.set_entry_point("task_understanding")

_builder.add_edge("task_understanding", "planning")
_builder.add_edge("planning", "web_research")
_builder.add_edge("web_research", "knowledge_extraction")
_builder.add_edge("knowledge_extraction", "memory_agent")
_builder.add_edge("memory_agent", "reflection")
_builder.add_edge("reflection", "report_generation")
_builder.add_edge("report_generation", END)

research_graph = _builder.compile()


async def run_research(topic: str, session_id: str, api_keys: dict | None = None) -> AsyncIterator[dict]:
    """
    Run the full research pipeline and yield agent events as they complete.
    Uses an asyncio.Queue to bridge LangGraph's synchronous-ish execution
    with async streaming.
    """
    initial_state: ResearchState = {
        "session_id": session_id,
        "topic": topic,
        "domain": "",
        "objectives": [],
        "subtasks": [],
        "search_queries": [],
        "raw_sources": [],
        "extracted_findings": [],
        "memory_ids": [],
        "reflection_score": 0.0,
        "reflection_gaps": [],
        "report_markdown": "",
        "agent_events": [],
        "error": None,
        "api_keys": api_keys or {},
    }

    queue: asyncio.Queue[dict | None] = asyncio.Queue()
    seen_events: set[int] = set()

    async def _run_and_enqueue() -> None:
        prev_count = 0
        try:
            async for chunk in research_graph.astream(initial_state):
                # chunk is {node_name: state_update}
                for node_name, state_update in chunk.items():
                    events = state_update.get("agent_events", [])
                    new_events = events[prev_count:]
                    prev_count = len(events)
                    for event in new_events:
                        await queue.put(event)
        except Exception as exc:
            await queue.put({
                "agent_id": "pipeline",
                "event": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": f"Pipeline failed: {str(exc)}",
                "tool_calls": [],
                "data": {},
            })
        finally:
            await queue.put(None)  # sentinel

    task = asyncio.create_task(_run_and_enqueue())

    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
    finally:
        if not task.done():
            task.cancel()
