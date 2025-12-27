from fastapi import APIRouter, Query
from app.models.schemas import SearchResponse, SearchResult
from app.services.clip_service import clip_service
from app.services.vector_store import vector_store

router = APIRouter()


@router.get("/", response_model=SearchResponse)
async def semantic_search(
    q: str = Query(..., description="Search query (e.g., 'smiling', 'concert')"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search images by semantic description using CLIP."""
    text_embedding = clip_service.get_text_embedding(q)
    results = vector_store.search(vector=text_embedding, limit=limit)

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
