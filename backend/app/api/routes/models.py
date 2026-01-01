import asyncio
import json
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models.clip_models import MODEL_REGISTRY
from app.services.clip_service import clip_service
from app.services.vector_store import vector_store
from app.config import settings

router = APIRouter()


class ModelInfo(BaseModel):
    id: str
    name: str
    family: str
    vector_dim: int
    description: str
    is_loaded: bool
    is_indexed: bool
    indexed_count: int


class SetModelRequest(BaseModel):
    model_id: str


@router.get("/", response_model=list[ModelInfo])
async def list_models():
    indexed_models = {m["model_id"]: m for m in vector_store.list_indexed_models()}

    models = []
    for model_id, config in MODEL_REGISTRY.items():
        indexed_info = indexed_models.get(model_id)
        models.append(
            ModelInfo(
                id=model_id,
                name=config.name,
                family=config.family.value,
                vector_dim=config.vector_dim,
                description=config.description,
                is_loaded=clip_service.is_model_loaded(model_id),
                is_indexed=indexed_info is not None,
                indexed_count=indexed_info["points_count"] if indexed_info else 0,
            )
        )
    return models


@router.get("/current")
async def get_current_model():
    model_id = clip_service.get_current_model_id()
    config = MODEL_REGISTRY[model_id]
    indexed = vector_store.get_collection_info(model_id)

    return {
        "model_id": model_id,
        "name": config.name,
        "is_loaded": clip_service.is_model_loaded(model_id),
        "is_indexed": indexed is not None,
        "indexed_count": indexed["points_count"] if indexed else 0,
    }


@router.post("/current")
async def set_current_model(request: SetModelRequest):
    if request.model_id not in MODEL_REGISTRY:
        raise HTTPException(status_code=400, detail="Unknown model")

    clip_service.set_current_model(request.model_id)
    return {"model_id": request.model_id, "status": "set"}


@router.get("/load/{model_id}/stream")
async def load_model_stream(model_id: str):
    if model_id not in MODEL_REGISTRY:
        raise HTTPException(status_code=400, detail="Unknown model")

    async def event_generator():
        yield f"data: {json.dumps({'status': 'starting', 'progress': 0})}\n\n"

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: clip_service.load_model(model_id))
            yield f"data: {json.dumps({'status': 'complete', 'progress': 100})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/index/{model_id}/stream")
async def index_with_model_stream(model_id: str):
    if model_id not in MODEL_REGISTRY:
        raise HTTPException(status_code=400, detail="Unknown model")

    async def event_generator():
        images_dir = settings.images_dir
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
        total = len(image_files)

        yield f"data: {json.dumps({'status': 'loading_model', 'total': total, 'current': 0})}\n\n"

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: clip_service.load_model(model_id))
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': f'Failed to load model: {e}'})}\n\n"
            return

        yield f"data: {json.dumps({'status': 'starting', 'total': total, 'current': 0})}\n\n"

        for i, img_path in enumerate(image_files):
            try:
                image_id = str(uuid.uuid4())

                def process_image():
                    embedding = clip_service.get_image_embedding(img_path, model_id)
                    vector_store.upsert(
                        model_id=model_id,
                        id=image_id,
                        vector=embedding,
                        payload={"filename": img_path.name, "path": str(img_path)},
                    )

                await loop.run_in_executor(None, process_image)

                yield f"data: {json.dumps({'status': 'indexing', 'current': i + 1, 'total': total, 'file': img_path.name})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'status': 'file_error', 'file': img_path.name, 'error': str(e), 'current': i + 1, 'total': total})}\n\n"

        yield f"data: {json.dumps({'status': 'complete', 'total': total})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
