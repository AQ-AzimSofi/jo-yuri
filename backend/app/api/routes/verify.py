from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import VerifyResponse
from app.services.face_service import face_service
import tempfile
from pathlib import Path

router = APIRouter()


@router.post("/", response_model=VerifyResponse)
async def verify_joyuri(
    file: UploadFile = File(...),
    threshold: float = 0.6,
):
    """Verify if an uploaded image contains Jo Yuri."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Save to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        result = face_service.verify(tmp_path, threshold=threshold)
        return VerifyResponse(**result)
    finally:
        tmp_path.unlink()  # Cleanup


@router.post("/add-reference")
async def add_reference_image(file: UploadFile = File(...)):
    """Add a reference image of Jo Yuri for face matching."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    result = await face_service.add_reference(file)
    return result
