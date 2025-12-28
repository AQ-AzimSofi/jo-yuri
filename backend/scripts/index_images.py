"""
Batch index images with CLIP embeddings into Qdrant.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.clip_service import clip_service
from app.services.vector_store import vector_store
from app.config import settings
import uuid


def index_all_images(images_dir: Path = None):
    """Index all images in the directory."""
    images_dir = images_dir or settings.images_dir

    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    print(f"Found {len(image_files)} images to index")

    for i, img_path in enumerate(image_files, 1):
        try:
            image_id = str(uuid.uuid4())
            embedding = clip_service.get_image_embedding(img_path)

            vector_store.upsert(
                id=image_id,
                vector=embedding,
                payload={
                    "filename": img_path.name,
                    "path": str(img_path),
                },
            )
            print(f"[{i}/{len(image_files)}] Indexed: {img_path.name}")

        except Exception as e:
            print(f"[{i}/{len(image_files)}] Failed: {img_path.name} - {e}")

    print(f"\nDone! Indexed {len(image_files)} images.")


if __name__ == "__main__":
    index_all_images()
