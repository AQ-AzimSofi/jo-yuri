from pydantic import BaseModel
from typing import Optional


class ImageUploadResponse(BaseModel):
    id: str
    filename: str
    message: str


class SearchQuery(BaseModel):
    query: str
    limit: int = 10


class SearchResult(BaseModel):
    id: str
    filename: str
    score: float
    url: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class VerifyRequest(BaseModel):
    threshold: float = 0.6


class VerifyResponse(BaseModel):
    is_joyuri: bool
    confidence: float
    faces_detected: int
    message: str


class ScrapeRequest(BaseModel):
    pinterest_url: str
    max_images: int = 50


class ScrapeResponse(BaseModel):
    images_downloaded: int
    message: str
