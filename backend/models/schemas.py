import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


# ── Workspace ─────────────────────────────────────────────

class WorkspaceCreate(BaseModel):
    name: str
    description: str | None = None


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


# ── Research Session ──────────────────────────────────────

class ResearchStartRequest(BaseModel):
    topic: str
    workspace_id: uuid.UUID | None = None
    openrouter_api_key: str | None = None
    tavily_api_key: str | None = None
    anthropic_api_key: str | None = None


class ResearchStartResponse(BaseModel):
    session_id: str


class ResearchSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    topic: str
    status: str
    agent_states: dict[str, Any]
    created_at: datetime
    completed_at: datetime | None


# ── Report ────────────────────────────────────────────────

class ResearchReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    content_markdown: str
    sources: list[dict[str, Any]]
    findings: list[dict[str, Any]]
    confidence_score: float
    created_at: datetime


# ── Memory ────────────────────────────────────────────────

class MemoryQueryRequest(BaseModel):
    query: str
    session_id: str | None = None
    top_k: int = 5


class MemoryQueryResult(BaseModel):
    content: str
    tags: list[str]
    similarity_score: float
    session_id: str


# ── Agent Events (SSE payloads) ───────────────────────────

class AgentEvent(BaseModel):
    agent_id: str
    event: str  # started | completed | tool_call | error | done
    timestamp: str
    summary: str
    tool_calls: list[str] = []
    data: dict[str, Any] = {}


# ── Source ────────────────────────────────────────────────

class Source(BaseModel):
    url: str
    title: str
    content: str
    score: float
    domain: str = ""


# ── Finding ───────────────────────────────────────────────

class Finding(BaseModel):
    type: str  # finding | trend | limitation | metric | quote
    title: str
    text: str
    source_url: str
    confidence: float
