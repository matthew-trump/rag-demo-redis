from __future__ import annotations

import hashlib
import uuid
from functools import lru_cache
from typing import Iterable

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.rag.schema import EMBEDDING_DIM
from app.rag.settings import settings
from app.rag.chunking import ChunkedText


class QdrantNotConfiguredError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _client() -> QdrantClient:
    if not settings.qdrant_url:
        raise QdrantNotConfiguredError("QDRANT_URL is not set")
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


@lru_cache(maxsize=1)
def _ensure_collection() -> None:
    client = _client()
    collections = {c.name for c in client.get_collections().collections}
    if settings.qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qm.VectorParams(size=EMBEDDING_DIM, distance=qm.Distance.COSINE),
        )


def _chunk_id(source: str, chunk: ChunkedText) -> str:
    # Qdrant expects UUID or integer IDs by default; use deterministic UUID5 for stability.
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}-{chunk.index}-{chunk.text}"))


def upsert_chunks(chunks: Iterable[ChunkedText], embeddings: list[list[float]], source: str, metadata: dict) -> int:
    _ensure_collection()
    client = _client()
    points: list[qm.PointStruct] = []
    for chunk, emb in zip(chunks, embeddings, strict=True):
        points.append(
            qm.PointStruct(
                id=_chunk_id(source, chunk),
                vector=emb,
                payload={
                    "content": chunk.text,
                    "source": source,
                    "chunk_index": chunk.index,
                    **(metadata or {}),
                },
            )
        )
    if not points:
        return 0
    client.upsert(collection_name=settings.qdrant_collection, points=points)
    return len(points)


def query_top_k(query_embedding: list[float], top_k: int) -> list[dict]:
    _ensure_collection()
    client = _client()
    res = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_embedding,
        limit=top_k,
        with_payload=True,
    )
    hits: list[dict] = []
    for match in res or []:
        md = match.payload or {}
        hits.append(
            {
                "id": str(match.id),
                "content": md.get("content", ""),
                "source": md.get("source", "unknown"),
                "score": match.score,
            }
        )
    return hits
