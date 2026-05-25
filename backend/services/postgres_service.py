import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import (
    Workspace,
    ResearchSession,
    ResearchReport,
    MemoryEntry,
)


# ── Workspace ─────────────────────────────────────────────

async def create_workspace(db: AsyncSession, name: str, description: str | None = None) -> Workspace:
    ws = Workspace(name=name, description=description)
    db.add(ws)
    await db.flush()
    await db.refresh(ws)
    return ws


async def get_workspaces(db: AsyncSession) -> list[Workspace]:
    result = await db.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    return list(result.scalars().all())


async def get_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace | None:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def delete_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> bool:
    ws = await get_workspace(db, workspace_id)
    if not ws:
        return False
    await db.delete(ws)
    return True


# ── Research Session ──────────────────────────────────────

async def create_session(
    db: AsyncSession, topic: str, workspace_id: uuid.UUID | None = None, api_keys: dict | None = None
) -> ResearchSession:
    session = ResearchSession(
        topic=topic,
        workspace_id=workspace_id,
        status="running",
        agent_states={"api_keys": api_keys} if api_keys else {},
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> ResearchSession | None:
    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def get_sessions_by_workspace(
    db: AsyncSession, workspace_id: uuid.UUID
) -> list[ResearchSession]:
    result = await db.execute(
        select(ResearchSession)
        .where(ResearchSession.workspace_id == workspace_id)
        .order_by(ResearchSession.created_at.desc())
    )
    return list(result.scalars().all())


async def update_session_status(
    db: AsyncSession, session_id: uuid.UUID, status: str
) -> None:
    values: dict = {"status": status}
    if status in ("completed", "failed"):
        values["completed_at"] = datetime.now(timezone.utc)
    await db.execute(
        update(ResearchSession)
        .where(ResearchSession.id == session_id)
        .values(**values)
    )


# ── Report ────────────────────────────────────────────────

async def create_report(
    db: AsyncSession,
    session_id: uuid.UUID,
    content_markdown: str,
    sources: list,
    findings: list,
    confidence_score: float,
) -> ResearchReport:
    report = ResearchReport(
        session_id=session_id,
        content_markdown=content_markdown,
        sources=sources,
        findings=findings,
        confidence_score=confidence_score,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


async def get_report_by_session(
    db: AsyncSession, session_id: uuid.UUID
) -> ResearchReport | None:
    result = await db.execute(
        select(ResearchReport).where(ResearchReport.session_id == session_id)
    )
    return result.scalar_one_or_none()


# ── Memory ────────────────────────────────────────────────

async def create_memory_entry(
    db: AsyncSession,
    session_id: uuid.UUID,
    agent_id: str,
    content: str,
    embedding_id: str,
    tags: list[str],
) -> MemoryEntry:
    entry = MemoryEntry(
        session_id=session_id,
        agent_id=agent_id,
        content=content,
        embedding_id=embedding_id,
        tags=tags,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry
