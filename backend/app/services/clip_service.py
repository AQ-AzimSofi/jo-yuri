import torch
import clip
from PIL import Image
from pathlib import Path
from app.config import settings


class CLIPService:
    def __init__(self):
        self._model = None
        self._preprocess = None
        self._device = None

    def _load_model(self):
        if self._model is None:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model, self._preprocess = clip.load(
                settings.clip_model, device=self._device
            )
            self._model.eval()

    def get_image_embedding(self, image_path: Path) -> list[float]:
        """Generate CLIP embedding for an image."""
        self._load_model()

        image = Image.open(image_path).convert("RGB")
        image_input = self._preprocess(image).unsqueeze(0).to(self._device)

        with torch.no_grad():
            embedding = self._model.encode_image(image_input)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)

        return embedding.cpu().numpy().flatten().tolist()

    def get_text_embedding(self, text: str) -> list[float]:
        """Generate CLIP embedding for text query."""
        self._load_model()

        text_input = clip.tokenize([text]).to(self._device)

        with torch.no_grad():
            embedding = self._model.encode_text(text_input)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)

        return embedding.cpu().numpy().flatten().tolist()


clip_service = CLIPService()
