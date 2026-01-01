from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "joyuri_images"

    # Storage paths
    images_dir: Path = Path("data/images")
    reference_dir: Path = Path("data/reference")

    # CLIP (multi-model support)
    default_clip_model: str = "openai/ViT-B-32"
    clip_models_cache_dir: Path = Path("data/models")
    max_loaded_models: int = 2

    # Face recognition
    face_recognition_tolerance: float = 0.6

    class Config:
        env_file = ".env"


settings = Settings()
