import uuid
from datetime import datetime, timezone

from agents.state import ResearchState
from services import chroma_service, redis_service

async def memory_agent_node(state: ResearchState) -> ResearchState:
    if state.get("error"):
        return state

    session_id = state["session_id"]
    findings = state.get("extracted_findings", [])
    memory_ids: list[str] = []

    # Store each finding in ChromaDB
    for i, finding in enumerate(findings):
        doc_id = f"{session_id}_{i}"
        content = f"{finding.get('title', '')}: {finding.get('text', '')}"
        metadata = {
            "session_id": session_id,
            "agent_id": "memory_agent",
            "type": finding.get("type", "finding"),
            "source_url": finding.get("source_url", ""),
            "confidence": str(finding.get("confidence", 0.0)),
            "tags": f"{state['domain']},{finding.get('type','finding')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await chroma_service.upsert(doc_id=doc_id, content=content, metadata=metadata)
            memory_ids.append(doc_id)
        except Exception:
            pass

    state["memory_ids"] = memory_ids

    # Query for related prior research
    related: list[dict] = []
    try:
        related = await chroma_service.query(
            text=state["topic"],
            top_k=3,
            filter_metadata={"session_id": {"$ne": session_id}},
        )
    except Exception:
        related = []

    # Cache full state snapshot in Redis
    try:
        snapshot = {
            "session_id": session_id,
            "topic": state["topic"],
            "domain": state["domain"],
            "source_count": len(state.get("raw_sources", [])),
            "finding_count": len(findings),
            "memory_ids": memory_ids,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await redis_service.set_session_state(session_id, snapshot)
    except Exception:
        pass

    event = {
        "agent_id": "memory_agent",
        "event": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": f"Stored {len(memory_ids)} documents in ChromaDB vector store. Found {len(related)} related prior research entries.",
        "tool_calls": ["ChromaDB.upsert()", "Redis.setex()", "ChromaDB.query()"],
        "data": {
            "stored_count": len(memory_ids),
            "memory_ids": memory_ids[:5],
            "related_sessions": len(related),
            "related_previews": [r["content"][:100] for r in related[:2]],
        },
    }
    state["agent_events"] = state.get("agent_events", []) + [event]
    return state
