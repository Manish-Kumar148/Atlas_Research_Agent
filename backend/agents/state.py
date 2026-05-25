from typing import TypedDict, Any


class ResearchState(TypedDict):
    session_id: str
    topic: str
    domain: str
    objectives: list[str]
    subtasks: list[dict[str, Any]]
    search_queries: list[str]
    raw_sources: list[dict[str, Any]]       # {url, title, content, score}
    extracted_findings: list[dict[str, Any]] # {type, title, text, source_url, confidence}
    memory_ids: list[str]                    # ChromaDB doc IDs
    reflection_score: float                  # 0.0 - 1.0
    reflection_gaps: list[str]
    report_markdown: str
    agent_events: list[dict[str, Any]]       # streaming event log
    error: str | None
    api_keys: dict[str, Any]                 # custom API keys from user
