from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import settings
from app.models.clip_models import MODEL_REGISTRY, get_collection_name


class VectorStore:
    def __init__(self):
        self._client: Optional[QdrantClient] = None

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
        return self._client

    def ensure_collection(self, model_id: str) -> str:
        client = self._get_client()
        collection_name = get_collection_name(model_id)
        vector_size = MODEL_REGISTRY[model_id].vector_dim

        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
        return collection_name

    def get_collection_info(self, model_id: str) -> Optional[dict]:
        client = self._get_client()
        collection_name = get_collection_name(model_id)
        try:
            info = client.get_collection(collection_name)
            return {
                "name": collection_name,
                "points_count": info.points_count,
                "vector_dim": MODEL_REGISTRY[model_id].vector_dim,
            }
        except Exception:
            return None

    def list_indexed_models(self) -> list[dict]:
        client = self._get_client()
        collections = client.get_collections().collections
        collection_names = {c.name for c in collections}

        indexed = []
        for model_id in MODEL_REGISTRY:
            collection_name = get_collection_name(model_id)
            if collection_name in collection_names:
                try:
                    info = client.get_collection(collection_name)
                    indexed.append({
                        "model_id": model_id,
                        "collection": collection_name,
                        "points_count": info.points_count,
                        "vector_dim": MODEL_REGISTRY[model_id].vector_dim,
                    })
                except Exception:
                    pass
        return indexed

    def upsert(self, model_id: str, id: str, vector: list[float], payload: dict) -> None:
        client = self._get_client()
        collection_name = self.ensure_collection(model_id)
        client.upsert(
            collection_name=collection_name,
            points=[PointStruct(id=id, vector=vector, payload=payload)],
        )

    def search(self, model_id: str, vector: list[float], limit: int = 10) -> list[dict]:
        client = self._get_client()
        collection_name = get_collection_name(model_id)

        try:
            results = client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=limit,
            )
            return [
                {"id": str(r.id), "score": r.score, "payload": r.payload}
                for r in results.points
            ]
        except Exception:
            return []

    def list_all(self, model_id: str) -> list[dict]:
        client = self._get_client()
        collection_name = get_collection_name(model_id)

        try:
            results = client.scroll(collection_name=collection_name, limit=1000)
            return [{"id": str(r.id), "payload": r.payload} for r in results[0]]
        except Exception:
            return []

    def delete(self, model_id: str, id: str) -> None:
        client = self._get_client()
        collection_name = get_collection_name(model_id)
        client.delete(
            collection_name=collection_name,
            points_selector=[id],
        )

    def delete_collection(self, model_id: str) -> None:
        client = self._get_client()
        collection_name = get_collection_name(model_id)
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass


vector_store = VectorStore()
