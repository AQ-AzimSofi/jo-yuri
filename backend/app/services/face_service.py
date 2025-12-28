import face_recognition
import numpy as np
from pathlib import Path
from fastapi import UploadFile
from app.config import settings
import pickle


class FaceService:
    def __init__(self):
        self._reference_encodings: list[np.ndarray] = []
        self._encodings_file = settings.reference_dir / "encodings.pkl"
        self._load_encodings()

    def _load_encodings(self):
        """Load saved reference encodings."""
        if self._encodings_file.exists():
            with open(self._encodings_file, "rb") as f:
                self._reference_encodings = pickle.load(f)

    def _save_encodings(self):
        """Save reference encodings to disk."""
        settings.reference_dir.mkdir(parents=True, exist_ok=True)
        with open(self._encodings_file, "wb") as f:
            pickle.dump(self._reference_encodings, f)

    async def add_reference(self, file: UploadFile) -> dict:
        """Add a reference image of Jo Yuri."""
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            image = face_recognition.load_image_file(tmp_path)
            encodings = face_recognition.face_encodings(image)

            if not encodings:
                return {"success": False, "message": "No face detected in image"}

            self._reference_encodings.append(encodings[0])
            self._save_encodings()

            settings.reference_dir.mkdir(parents=True, exist_ok=True)
            ref_path = settings.reference_dir / f"ref_{len(self._reference_encodings)}.jpg"
            ref_path.write_bytes(content)

            return {
                "success": True,
                "message": f"Reference added. Total references: {len(self._reference_encodings)}",
            }
        finally:
            tmp_path.unlink()

    def verify(self, image_path: Path, threshold: float = 0.6) -> dict:
        """Verify if image contains Jo Yuri."""
        if not self._reference_encodings:
            return {
                "is_joyuri": False,
                "confidence": 0.0,
                "faces_detected": 0,
                "message": "No reference images loaded. Add reference images first.",
            }

        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        if not face_encodings:
            return {
                "is_joyuri": False,
                "confidence": 0.0,
                "faces_detected": 0,
                "message": "No faces detected in image",
            }

        best_confidence = 0.0
        is_joyuri = False

        for encoding in face_encodings:
            distances = face_recognition.face_distance(
                self._reference_encodings, encoding
            )
            min_distance = min(distances)
            confidence = 1 - min_distance

            if confidence > best_confidence:
                best_confidence = confidence

            if min_distance <= threshold:
                is_joyuri = True

        return {
            "is_joyuri": is_joyuri,
            "confidence": round(best_confidence, 4),
            "faces_detected": len(face_encodings),
            "message": "Match found!" if is_joyuri else "No match found",
        }


face_service = FaceService()
