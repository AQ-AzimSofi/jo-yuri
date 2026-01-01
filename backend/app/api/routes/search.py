from typing import Optional
from fastapi import APIRouter, Query
from app.models.schemas import SearchResponse, SearchResult
from app.models.clip_models import MODEL_REGISTRY
from app.services.clip_service import clip_service
from app.services.vector_store import vector_store

router = APIRouter()


@router.get("/", response_model=SearchResponse)
async def semantic_search(
    q: str = Query(..., description="Search query (e.g., 'smiling', 'concert')"),
    limit: int = Query(12, ge=1, le=50),
    model: Optional[str] = Query(None, description="Model ID to use (defaults to current)"),
):
    model_id = model if model and model in MODEL_REGISTRY else clip_service.get_current_model_id()

    text_embedding = clip_service.get_text_embedding(q, model_id)
    results = vector_store.search(model_id=model_id, vector=text_embedding, limit=limit)

    return SearchResponse(
        query=q,
        results=[
            SearchResult(
                id=r["id"],
                filename=r["payload"].get("filename", ""),
                score=r["score"],
                url=f"/api/images/file/{r['payload'].get('filename', '')}",
            )
            for r in results
        ],
    )
