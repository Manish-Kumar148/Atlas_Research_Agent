import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client: Any | None = None


async def get_chroma_client() -> Any:
    global _client
    if _client is None:
        _client = await chromadb.AsyncHttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _collection_name(workspace_id: str | None = None) -> str:
    base = settings.chroma_collection
    if workspace_id:
        safe = workspace_id.replace("-", "_")
        return f"{base}_{safe}"
    return base


async def upsert(
    doc_id: str,
    content: str,
    metadata: dict,
    workspace_id: str | None = None,
) -> None:
    client = await get_chroma_client()
    col = await client.get_or_create_collection(
        name=_collection_name(workspace_id),
        metadata={"hnsw:space": "cosine"},
    )
    await col.upsert(
        ids=[doc_id],
        documents=[content],
        metadatas=[metadata],
    )
    logger.debug(f"Upserted doc {doc_id} to ChromaDB")


async def query(
    text: str,
    top_k: int = 5,
    filter_metadata: dict | None = None,
    workspace_id: str | None = None,
) -> list[dict]:
    client = await get_chroma_client()
    try:
        col = await client.get_collection(name=_collection_name(workspace_id))
    except Exception:
        return []

    kwargs: dict = {"query_texts": [text], "n_results": top_k, "include": ["documents", "metadatas", "distances"]}
    if filter_metadata:
        kwargs["where"] = filter_metadata

    results = await col.query(**kwargs)
    output = []
    if results and results["documents"]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({
                "content": doc,
                "metadata": meta,
                "similarity_score": round(1 - dist, 4),
                "session_id": meta.get("session_id", ""),
                "tags": meta.get("tags", []),
            })
    return output


async def delete_collection(workspace_id: str | None = None) -> None:
    client = await get_chroma_client()
    name = _collection_name(workspace_id)
    try:
        await client.delete_collection(name=name)
        logger.info(f"Deleted ChromaDB collection: {name}")
    except Exception as e:
        logger.warning(f"Could not delete collection {name}: {e}")
