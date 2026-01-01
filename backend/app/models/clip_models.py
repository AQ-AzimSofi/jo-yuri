from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ModelFamily(str, Enum):
    OPENAI_CLIP = "openai_clip"
    OPENCLIP = "openclip"
    SIGLIP = "siglip"


@dataclass
class CLIPModelConfig:
    id: str
    name: str
    family: ModelFamily
    vector_dim: int
    model_name: str
    pretrained: Optional[str]
    description: str


MODEL_REGISTRY: dict[str, CLIPModelConfig] = {
    "openai/ViT-B-32": CLIPModelConfig(
        id="openai/ViT-B-32",
        name="CLIP ViT-B/32",
        family=ModelFamily.OPENAI_CLIP,
        vector_dim=512,
        model_name="ViT-B/32",
        pretrained=None,
        description="Fast, good balance of speed and quality",
    ),
    "openai/ViT-B-16": CLIPModelConfig(
        id="openai/ViT-B-16",
        name="CLIP ViT-B/16",
        family=ModelFamily.OPENAI_CLIP,
        vector_dim=512,
        model_name="ViT-B/16",
        pretrained=None,
        description="Higher quality, slower than B/32",
    ),
    "openai/ViT-L-14": CLIPModelConfig(
        id="openai/ViT-L-14",
        name="CLIP ViT-L/14",
        family=ModelFamily.OPENAI_CLIP,
        vector_dim=768,
        model_name="ViT-L/14",
        pretrained=None,
        description="Highest quality OpenAI model",
    ),
    "openclip/ViT-B-32-laion2b": CLIPModelConfig(
        id="openclip/ViT-B-32-laion2b",
        name="OpenCLIP ViT-B/32",
        family=ModelFamily.OPENCLIP,
        vector_dim=512,
        model_name="ViT-B-32",
        pretrained="laion2b_s34b_b79k",
        description="Trained on LAION-2B dataset",
    ),
    "openclip/ViT-L-14-laion2b": CLIPModelConfig(
        id="openclip/ViT-L-14-laion2b",
        name="OpenCLIP ViT-L/14",
        family=ModelFamily.OPENCLIP,
        vector_dim=768,
        model_name="ViT-L-14",
        pretrained="laion2b_s32b_b82k",
        description="Large model trained on LAION-2B",
    ),
    "siglip/base-patch16-224": CLIPModelConfig(
        id="siglip/base-patch16-224",
        name="SigLIP Base",
        family=ModelFamily.SIGLIP,
        vector_dim=768,
        model_name="google/siglip-base-patch16-224",
        pretrained=None,
        description="Google SigLIP with sigmoid loss",
    ),
    "siglip/large-patch16-384": CLIPModelConfig(
        id="siglip/large-patch16-384",
        name="SigLIP Large",
        family=ModelFamily.SIGLIP,
        vector_dim=1024,
        model_name="google/siglip-large-patch16-384",
        pretrained=None,
        description="High-res SigLIP model",
    ),
}


def get_collection_name(model_id: str, base_name: str = "joyuri_images") -> str:
    safe_id = model_id.replace("/", "_").replace("-", "_").lower()
    return f"{base_name}_{safe_id}"


def get_model_config(model_id: str) -> CLIPModelConfig:
    if model_id not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_id}")
    return MODEL_REGISTRY[model_id]
