import json
import re
import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import anthropic

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_anthropic_client: anthropic.AsyncAnthropic | None = None
_http_client: httpx.AsyncClient | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=120)
    return _http_client


def _provider() -> str:
    return settings.ai_provider.strip().lower()


async def _complete_anthropic(system: str, user: str, max_tokens: int, api_key: str | None = None) -> str:
    if api_key:
        client = anthropic.AsyncAnthropic(api_key=api_key)
    else:
        client = get_client()
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


async def _complete_openrouter(system: str, user: str, max_tokens: int, api_key: str | None = None) -> str:
    key = api_key or settings.openrouter_api_key
    if not key:
        raise ValueError("OPENROUTER_API_KEY is required when AI_PROVIDER=openrouter")

    client = get_http_client()
    response = await client.post(
        f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Atlas Research Agent",
        },
        json={
            "model": settings.openrouter_model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    return data["choices"][0]["message"]["content"]


@retry(
    retry=retry_if_exception_type(anthropic.RateLimitError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
)
async def complete(system: str, user: str, max_tokens: int = 2000, api_key: str | None = None) -> str:
    if _provider() == "openrouter":
        return await _complete_openrouter(system, user, max_tokens, api_key)
    return await _complete_anthropic(system, user, max_tokens, api_key)


@retry(
    retry=retry_if_exception_type(anthropic.RateLimitError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=30),
)
async def complete_json(system: str, user: str, max_tokens: int = 2000, api_key: str | None = None) -> dict:
    raw = await complete(
        system=system + "\n\nIMPORTANT: Respond with valid JSON only. No markdown fences, no preamble.",
        user=user,
        max_tokens=max_tokens,
        api_key=api_key,
    )
    # Strip markdown fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from AI provider: {e}\nRaw: {raw[:500]}")
        raise ValueError(f"AI provider returned invalid JSON: {e}") from e
