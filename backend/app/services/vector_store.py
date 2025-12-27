from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import settings


class VectorStore:
    def __init__(self):
        self._client = None
        self._collection = settings.qdrant_collection
        self._vector_size = 512  # CLIP ViT-B/32 embedding size

    def _get_client(self) -> QdrantClient:
        if self._client is None:
            self._client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
            self._ensure_collection()
        return self._client

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self._client.get_collections().collections
        if not any(c.name == self._collection for c in collections):
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=self._vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def upsert(self, id: str, vector: list[float], payload: dict):
        """Insert or update a vector."""
        client = self._get_client()
        client.upsert(
            collection_name=self._collection,
            points=[
                PointStruct(
                    id=id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    def search(self, vector: list[float], limit: int = 10) -> list[dict]:
        """Search for similar vectors."""
        client = self._get_client()
        results = client.search(
            collection_name=self._collection,
            query_vector=vector,
            limit=limit,
        )
        return [
            {
                "id": str(r.id),
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]

    def list_all(self) -> list[dict]:
        """List all indexed images."""
        client = self._get_client()
        results = client.scroll(
            collection_name=self._collection,
            limit=1000,
        )
        return [
            {
                "id": str(r.id),
                "payload": r.payload,
            }
            for r in results[0]
        ]

    def delete(self, id: str):
        """Delete a vector by ID."""
        client = self._get_client()
        client.delete(
            collection_name=self._collection,
            points_selector=[id],
        )


vector_store = VectorStore()
