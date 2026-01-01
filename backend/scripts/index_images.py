"""
Batch index images with CLIP embeddings into Qdrant.
Supports multiple CLIP model variants.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.clip_service import clip_service
from app.services.vector_store import vector_store
from app.models.clip_models import MODEL_REGISTRY, get_collection_name
from app.config import settings
import uuid


def index_all_images(model_id: str, images_dir: Path = None):
    images_dir = images_dir or settings.images_dir

    if model_id not in MODEL_REGISTRY:
        print(f"Error: Unknown model '{model_id}'")
        print(f"Available models: {', '.join(MODEL_REGISTRY.keys())}")
        return

    config = MODEL_REGISTRY[model_id]
    collection_name = get_collection_name(model_id)

    print(f"Model: {config.name}")
    print(f"Collection: {collection_name}")
    print(f"Vector dimension: {config.vector_dim}")
    print()

    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    print(f"Found {len(image_files)} images to index")

    print("Loading model...")
    clip_service.load_model(model_id)
    print("Model loaded!")
    print()

    for i, img_path in enumerate(image_files, 1):
        try:
            image_id = str(uuid.uuid4())
            embedding = clip_service.get_image_embedding(img_path, model_id)

            vector_store.upsert(
                model_id=model_id,
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

    print(f"\nDone! Indexed {len(image_files)} images with {config.name}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index images with CLIP models")
    parser.add_argument(
        "--model",
        default=settings.default_clip_model,
        help=f"Model ID to use (default: {settings.default_clip_model})",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models",
    )
    args = parser.parse_args()

    if args.list_models:
        print("Available models:")
        for model_id, config in MODEL_REGISTRY.items():
            print(f"  {model_id}")
            print(f"    Name: {config.name}")
            print(f"    Family: {config.family.value}")
            print(f"    Dimensions: {config.vector_dim}")
            print()
    else:
        index_all_images(args.model)
