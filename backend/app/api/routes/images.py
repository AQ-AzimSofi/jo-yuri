from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.models.schemas import ImageUploadResponse
from app.services.clip_service import clip_service
from app.services.vector_store import vector_store
from app.config import settings
import uuid
from pathlib import Path

router = APIRouter()


@router.get("/file/{filename}")
async def get_image(filename: str):
    """Serve an image file."""
    file_path = settings.images_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """Upload an image and index it with CLIP embeddings."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_id = str(uuid.uuid4())
    filename = f"{image_id}_{file.filename}"
    file_path = settings.images_dir / filename

    settings.images_dir.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    file_path.write_bytes(content)

    embedding = clip_service.get_image_embedding(file_path)
    vector_store.upsert(
        id=image_id,
        vector=embedding,
        payload={"filename": filename, "path": str(file_path)},
    )

    return ImageUploadResponse(
        id=image_id,
        filename=filename,
        message="Image uploaded and indexed successfully",
    )


@router.get("/")
async def list_images():
    """List all indexed images."""
    return vector_store.list_all()


@router.delete("/{image_id}")
async def delete_image(image_id: str):
    """Delete an image from the index."""
    vector_store.delete(image_id)
    return {"message": f"Image {image_id} deleted"}
