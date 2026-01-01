import torch
from PIL import Image
from pathlib import Path
from typing import Optional, Callable
from collections import OrderedDict
from abc import ABC, abstractmethod
import threading

from app.config import settings
from app.models.clip_models import (
    MODEL_REGISTRY,
    CLIPModelConfig,
    ModelFamily,
    get_model_config,
)


class ModelLoader(ABC):
    @abstractmethod
    def load(self, config: CLIPModelConfig, device: str) -> None:
        pass

    @abstractmethod
    def encode_image(self, image: Image.Image) -> list[float]:
        pass

    @abstractmethod
    def encode_text(self, text: str) -> list[float]:
        pass

    def unload(self) -> None:
        pass


class OpenAICLIPLoader(ModelLoader):
    def __init__(self):
        self.model = None
        self.preprocess = None
        self.device = None

    def load(self, config: CLIPModelConfig, device: str) -> None:
        import clip

        self.device = device
        self.model, self.preprocess = clip.load(
            config.model_name,
            device=device,
            download_root=str(settings.clip_models_cache_dir),
        )
        self.model.eval()

    def encode_image(self, image: Image.Image) -> list[float]:
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding = self.model.encode_image(image_input)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy().flatten().tolist()

    def encode_text(self, text: str) -> list[float]:
        import clip

        text_input = clip.tokenize([text], truncate=True).to(self.device)
        with torch.no_grad():
            embedding = self.model.encode_text(text_input)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy().flatten().tolist()

    def unload(self) -> None:
        self.model = None
        self.preprocess = None


class OpenCLIPLoader(ModelLoader):
    def __init__(self):
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self.device = None

    def load(self, config: CLIPModelConfig, device: str) -> None:
        import open_clip

        self.device = device
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            config.model_name,
            pretrained=config.pretrained,
            cache_dir=str(settings.clip_models_cache_dir),
        )
        self.tokenizer = open_clip.get_tokenizer(config.model_name)
        self.model = self.model.to(device)
        self.model.eval()

    def encode_image(self, image: Image.Image) -> list[float]:
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            embedding = self.model.encode_image(image_input)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy().flatten().tolist()

    def encode_text(self, text: str) -> list[float]:
        text_input = self.tokenizer([text]).to(self.device)
        with torch.no_grad():
            embedding = self.model.encode_text(text_input)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy().flatten().tolist()

    def unload(self) -> None:
        self.model = None
        self.preprocess = None
        self.tokenizer = None


class SigLIPLoader(ModelLoader):
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = None

    def load(self, config: CLIPModelConfig, device: str) -> None:
        from transformers import AutoProcessor, AutoModel

        self.device = device
        self.processor = AutoProcessor.from_pretrained(
            config.model_name,
            cache_dir=str(settings.clip_models_cache_dir),
        )
        self.model = AutoModel.from_pretrained(
            config.model_name,
            cache_dir=str(settings.clip_models_cache_dir),
        ).to(device)
        self.model.eval()

    def encode_image(self, image: Image.Image) -> list[float]:
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            embedding = self.model.get_image_features(**inputs)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy().flatten().tolist()

    def encode_text(self, text: str) -> list[float]:
        inputs = self.processor(
            text=[text], return_tensors="pt", padding=True, truncation=True
        ).to(self.device)
        with torch.no_grad():
            embedding = self.model.get_text_features(**inputs)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)
        return embedding.cpu().numpy().flatten().tolist()

    def unload(self) -> None:
        self.model = None
        self.processor = None


class MultiModelCLIPService:
    def __init__(self):
        self._loaded_models: OrderedDict[str, ModelLoader] = OrderedDict()
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._lock = threading.Lock()
        self._current_model_id: str = settings.default_clip_model

    def _get_loader_class(self, family: ModelFamily) -> type[ModelLoader]:
        loaders = {
            ModelFamily.OPENAI_CLIP: OpenAICLIPLoader,
            ModelFamily.OPENCLIP: OpenCLIPLoader,
            ModelFamily.SIGLIP: SigLIPLoader,
        }
        return loaders[family]

    def _evict_if_needed(self) -> None:
        while len(self._loaded_models) >= settings.max_loaded_models:
            evicted_id, evicted_loader = self._loaded_models.popitem(last=False)
            evicted_loader.unload()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def load_model(
        self, model_id: str, progress_callback: Optional[Callable[[float], None]] = None
    ) -> ModelLoader:
        if model_id not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {model_id}")

        with self._lock:
            if model_id in self._loaded_models:
                self._loaded_models.move_to_end(model_id)
                return self._loaded_models[model_id]

            self._evict_if_needed()

            config = get_model_config(model_id)
            loader_class = self._get_loader_class(config.family)
            loader = loader_class()

            if progress_callback:
                progress_callback(10)

            loader.load(config, self._device)

            if progress_callback:
                progress_callback(100)

            self._loaded_models[model_id] = loader
            return loader

    def set_current_model(self, model_id: str) -> None:
        if model_id not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {model_id}")
        self._current_model_id = model_id

    def get_current_model_id(self) -> str:
        return self._current_model_id

    def get_image_embedding(
        self, image_path: Path, model_id: Optional[str] = None
    ) -> list[float]:
        model_id = model_id or self._current_model_id
        loader = self.load_model(model_id)
        image = Image.open(image_path).convert("RGB")
        return loader.encode_image(image)

    def get_text_embedding(
        self, text: str, model_id: Optional[str] = None
    ) -> list[float]:
        model_id = model_id or self._current_model_id
        loader = self.load_model(model_id)
        return loader.encode_text(text)

    def is_model_loaded(self, model_id: str) -> bool:
        return model_id in self._loaded_models

    def get_loaded_models(self) -> list[str]:
        return list(self._loaded_models.keys())


clip_service = MultiModelCLIPService()
