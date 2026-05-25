from fastapi import APIRouter
from models.schemas import MemoryQueryRequest, MemoryQueryResult
from services import chroma_service

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/query", response_model=list[MemoryQueryResult])
async def query_memory(body: MemoryQueryRequest):
    filter_meta = None
    if body.session_id:
        filter_meta = {"session_id": body.session_id}

    results = await chroma_service.query(
        text=body.query,
        top_k=body.top_k,
        filter_metadata=filter_meta,
    )

    return [
        MemoryQueryResult(
            content=r["content"],
            tags=r.get("tags", "").split(",") if isinstance(r.get("tags"), str) else r.get("tags", []),
            similarity_score=r["similarity_score"],
            session_id=r.get("session_id", ""),
        )
        for r in results
    ]
