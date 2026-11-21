import os
import hashlib
import threading
import uuid
import numpy as np

import json
from pathlib import Path

try:
    from qdrant_client import QdrantClient, models
except ImportError:
    QdrantClient = None
    models = None

from backend.config import DATA, MODEL


class VectorStore:
    def __init__(self, path=None):
        self.lock = threading.RLock()
        self.collection = "visual_" + hashlib.sha256(MODEL.encode()).hexdigest()[:12]
        self._path = Path(path or DATA / "qdrant")
        self._path.mkdir(parents=True, exist_ok=True)
        self._file = self._path / f"{self.collection}_fallback.json"
        self._fallback_points = []
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        if QdrantClient is not None:
            try:
                if qdrant_url:
                    self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
                else:
                    self.client = QdrantClient(path=str(self._path))
            except Exception:
                self.client = None
        else:
            self.client = None

        if self.client is None and self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    self._fallback_points = json.load(f)
            except Exception:
                self._fallback_points = []

    def _save_fallback(self):
        if self.client is None:
            try:
                with open(self._file, "w", encoding="utf-8") as f:
                    json.dump(self._fallback_points, f)
            except Exception:
                pass

    def ensure(self, dimension):
        with self.lock:
            if self.client is None:
                return
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
            if self.client is None:
                for v, p in zip(vectors, payloads):
                    self._fallback_points.append({
                        "id": str(uuid.uuid4()),
                        "vector": v.tolist() if hasattr(v, "tolist") else list(v),
                        "payload": p,
                    })
                self._save_fallback()
                return
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
            if self.client is None:
                return len(self._fallback_points)
            return (
                self.client.count(self.collection, exact=True).count
                if self.client.collection_exists(self.collection)
                else 0
            )

    def search(self, vector, filters=None, limit=500, video_ids=None):
        with self.lock:
            if self.client is None:
                q = np.array(vector, dtype=np.float32)
                q_norm = np.linalg.norm(q) or 1e-6
                results = []
                for pt in self._fallback_points:
                    p = pt["payload"]
                    if filters:
                        mismatch = False
                        for k, v in filters.items():
                            if v and p.get(k) != v:
                                mismatch = True
                                break
                        if mismatch:
                            continue
                    if video_ids and p.get("video_id") not in video_ids:
                        continue
                    v = np.array(pt["vector"], dtype=np.float32)
                    v_norm = np.linalg.norm(v) or 1e-6
                    score = float(np.dot(q, v) / (q_norm * v_norm))
                    results.append(dict(p, cosine=score, vector=pt["vector"]))
                results.sort(key=lambda x: x["cosine"], reverse=True)
                return results[:limit]

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
            if self.client is None:
                self._fallback_points = [
                    pt for pt in self._fallback_points
                    if pt["payload"].get("video_id") != video_id
                ]
                self._save_fallback()
                return
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
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
