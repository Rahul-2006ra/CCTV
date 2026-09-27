import hashlib
import threading
import uuid
from qdrant_client import QdrantClient, models
from backend.config import DATA, MODEL


class VectorStore:
    def __init__(self, path=None):
        self.lock = threading.RLock()
        self.client = QdrantClient(path=str(path or DATA / "qdrant"))
        self.collection = "visual_" + hashlib.sha256(MODEL.encode()).hexdigest()[:12]

    def ensure(self, dimension):
        with self.lock:
            if not self.client.collection_exists(self.collection):
                self.client.create_collection(
                    self.collection,
                    vectors_config=models.VectorParams(
                        size=dimension, distance=models.Distance.COSINE
                    ),
                )
            elif (
                self.client.get_collection(self.collection).config.params.vectors.size
                != dimension
            ):
                raise ValueError(
                    "Embedding dimension changed. Use a new data directory and re-index."
                )

    def upsert(self, vectors, payloads):
        with self.lock:
            self.client.upsert(
                self.collection,
                points=[
                    models.PointStruct(
                        id=str(uuid.uuid4()), vector=v.tolist(), payload=p
                    )
                    for v, p in zip(vectors, payloads)
                ],
                wait=True,
            )

    def count(self):
        with self.lock:
            return (
                self.client.count(self.collection, exact=True).count
                if self.client.collection_exists(self.collection)
                else 0
            )

    def search(self, vector, filters=None, limit=500, video_ids=None):
        with self.lock:
            if not self.client.collection_exists(self.collection):
                return []
            conditions = [
                models.FieldCondition(key=k, match=models.MatchValue(value=v))
                for k, v in (filters or {}).items()
                if v
            ]
            if video_ids is not None:
                if not video_ids:
                    return []
                conditions.append(
                    models.FieldCondition(
                        key="video_id", match=models.MatchAny(any=video_ids)
                    )
                )
            result = self.client.query_points(
                self.collection,
                query=vector.tolist(),
                query_filter=models.Filter(must=conditions) if conditions else None,
                limit=limit,
                with_payload=True,
                with_vectors=True,
            )
            return [
                dict(p.payload, cosine=float(p.score), vector=p.vector)
                for p in result.points
            ]

    def delete_video(self, video_id):
        with self.lock:
            if self.client.collection_exists(self.collection):
                self.client.delete(
                    self.collection,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="video_id",
                                    match=models.MatchValue(value=video_id),
                                )
                            ]
                        )
                    ),
                    wait=True,
                )

    def close(self):
        self.client.close()
