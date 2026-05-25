import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.schemas import ResearchStartRequest, ResearchStartResponse, ResearchSessionOut, ResearchReportOut
from services import postgres_service
from agents.graph import run_research

router = APIRouter(prefix="/research", tags=["research"])

HEARTBEAT_INTERVAL = 15  # seconds


@router.post("/start", response_model=ResearchStartResponse)
async def start_research(
    body: ResearchStartRequest,
    db: AsyncSession = Depends(get_db),
):
    api_keys = {}
    if body.openrouter_api_key:
        api_keys["openrouter_api_key"] = body.openrouter_api_key.strip()
    if body.tavily_api_key:
        api_keys["tavily_api_key"] = body.tavily_api_key.strip()
    if body.anthropic_api_key:
        api_keys["anthropic_api_key"] = body.anthropic_api_key.strip()

    session = await postgres_service.create_session(
        db=db,
        topic=body.topic,
        workspace_id=body.workspace_id,
        api_keys=api_keys if api_keys else None
    )
    return ResearchStartResponse(session_id=str(session.id))


@router.get("/stream/{session_id}")
async def stream_research(session_id: str, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        # Heartbeat task
        last_event_time = datetime.now(timezone.utc)

        try:
            session = await postgres_service.get_session(db, uuid.UUID(session_id))
            if not session:
                yield f"data: {json.dumps({'event': 'error', 'message': 'Session not found'})}\n\n"
                return

            topic = session.topic
            api_keys = getattr(session, "agent_states", {}).get("api_keys", {}) if session else {}

            async for event in run_research(topic=topic, session_id=session_id, api_keys=api_keys):
                yield f"data: {json.dumps(event, default=str)}\n\n"
                last_event_time = datetime.now(timezone.utc)

                if event.get("event") == "error":
                    await postgres_service.update_session_status(db, uuid.UUID(session_id), "failed")
                    await db.commit()
                    return

                # Heartbeat if needed
                elapsed = (datetime.now(timezone.utc) - last_event_time).seconds
                if elapsed > HEARTBEAT_INTERVAL:
                    yield f"data: {json.dumps({'event': 'heartbeat', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

            # Update DB session to completed
            await postgres_service.update_session_status(db, uuid.UUID(session_id), "completed")
            await db.commit()

            # Save report if available
            # (report is retrieved via separate endpoint)

            yield f"data: {json.dumps({'event': 'done', 'session_id': session_id, 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

        except Exception as e:
            await postgres_service.update_session_status(db, uuid.UUID(session_id), "failed")
            await db.commit()
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/sessions/{workspace_id}", response_model=list[ResearchSessionOut])
async def get_sessions(workspace_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    sessions = await postgres_service.get_sessions_by_workspace(db, workspace_id)
    return sessions


@router.get("/report/{session_id}", response_model=ResearchReportOut)
async def get_report(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    report = await postgres_service.get_report_by_session(db, session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
