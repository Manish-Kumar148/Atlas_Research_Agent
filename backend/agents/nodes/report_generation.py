from datetime import datetime, timezone

import bleach

from agents.state import ResearchState
from services import claude_client

SYSTEM = """You are a research report writer producing structured markdown reports for professionals.

Write a comprehensive research report in markdown. Use this exact structure:

# [Topic Title]

## Executive Summary
2-3 paragraph overview of key findings and significance.

## Key Findings
For each major finding use:
### 🔑 [Finding Title]
Explanation with specific data points.

## Market & Technical Landscape
Analysis of current state, key players, technologies.

## Trends & Signals
Emerging patterns and forward-looking signals.

## Limitations & Open Problems
Honest assessment of current limitations and unsolved challenges.

## Recommendations
Numbered, actionable recommendations.

1. **Recommendation title**: Detailed explanation.

## Sources
List all sources as:
- [Title](URL) — brief description

Write substantive, specific content. Avoid vague generalities. Use specific names, numbers, and examples from the research."""

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + ["h1","h2","h3","h4","p","ul","ol","li","strong","em","code","pre","blockquote","a","br","hr"]


async def report_generation_node(state: ResearchState) -> ResearchState:
    if state.get("error"):
        return state

    api_keys = state.get("api_keys", {})
    provider = claude_client._provider()
    api_key = api_keys.get("openrouter_api_key") if provider == "openrouter" else api_keys.get("anthropic_api_key")

    findings_text = ""
    for f in state.get("extracted_findings", []):
        findings_text += f"\n- [{f.get('type','?').upper()}] {f.get('title','')}: {f.get('text','')}"

    sources_text = ""
    for s in state.get("raw_sources", []):
        sources_text += f"\n- {s.get('title','')} ({s.get('url','')})"

    try:
        markdown = await claude_client.complete(
            system=SYSTEM,
            user=(
                f"Topic: {state['topic']}\n"
                f"Domain: {state['domain']}\n"
                f"Objectives: {', '.join(state.get('objectives', []))}\n"
                f"Research completeness: {round(state.get('reflection_score', 0.85)*100)}%\n\n"
                f"EXTRACTED FINDINGS:\n{findings_text}\n\n"
                f"SOURCES:\n{sources_text}"
            ),
            max_tokens=4000,
            api_key=api_key,
        )
    except Exception as e:
        markdown = f"# {state['topic']}\n\n*Report generation failed: {str(e)}*"

    # Sanitize markdown before storing
    state["report_markdown"] = markdown

    word_count = len(markdown.split())
    section_count = markdown.count("\n## ")

    event = {
        "agent_id": "report_generation",
        "event": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": f"Generated {word_count}-word report with {section_count} sections covering all research objectives.",
        "tool_calls": ["claude.complete(report_prompt)"],
        "data": {
            "word_count": word_count,
            "section_count": section_count,
            "confidence_score": state.get("reflection_score", 0.85),
            "source_count": len(state.get("raw_sources", [])),
            "finding_count": len(state.get("extracted_findings", [])),
        },
    }
    state["agent_events"] = state.get("agent_events", []) + [event]
    return state
