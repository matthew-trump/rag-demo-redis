from __future__ import annotations

import uuid
from typing import Iterable

import numpy as np
import redis
from redis.commands.search.field import TextField, NumericField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from app.rag.schema import EMBEDDING_DIM
from app.rag.settings import settings
from app.rag.chunking import ChunkedText


class RedisNotConfiguredError(RuntimeError):
    pass


def _client() -> redis.Redis:
    if not settings.redis_url:
        raise RedisNotConfiguredError("REDIS_URL is not set")
    return redis.Redis.from_url(settings.redis_url, password=settings.redis_password)


def _ensure_index() -> None:
    client = _client()
    try:
        # If index exists, INFO will succeed
        client.ft(settings.redis_index).info()
        return
    except Exception:
        pass

    schema = [
        TextField("id"),
        TextField("content"),
        TextField("source"),
        TextField("filename"),
        NumericField("chunk_index"),
        VectorField(
            "embedding",
            "HNSW",
            {
                "TYPE": "FLOAT32",
                "DIM": EMBEDDING_DIM,
                "DISTANCE_METRIC": "COSINE",
            },
        ),
    ]
    definition = IndexDefinition(prefix=[f"{settings.redis_index}:chunk:"], index_type=IndexType.HASH)
    client.ft(settings.redis_index).create_index(schema, definition=definition)


def _chunk_id(source: str, chunk: ChunkedText) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}-{chunk.index}-{chunk.text}"))


def _vec_to_bytes(vec: list[float]) -> bytes:
    return np.array(vec, dtype=np.float32).tobytes()


def upsert_chunks(chunks: Iterable[ChunkedText], embeddings: list[list[float]], source: str, metadata: dict) -> int:
    _ensure_index()
    client = _client()
    pipe = client.pipeline(transaction=False)

    count = 0
    for chunk, emb in zip(chunks, embeddings, strict=True):
        key = f"{settings.redis_index}:chunk:{_chunk_id(source, chunk)}"
        doc = {
            "id": _chunk_id(source, chunk),
            "content": chunk.text,
            "source": source,
            "filename": metadata.get("filename", ""),
            "chunk_index": chunk.index,
            "embedding": _vec_to_bytes(emb),
        }
        pipe.hset(key, mapping=doc)
        count += 1
    if count:
        pipe.execute()
    return count


def query_top_k(query_embedding: list[float], top_k: int) -> list[dict]:
    _ensure_index()
    client = _client()
    q = (
        Query(f"*=>[KNN {top_k} @embedding $vec AS score]")
        .sort_by("score")
        .return_fields("id", "content", "source", "filename", "chunk_index", "score")
        .dialect(2)
    )
    params = {"vec": _vec_to_bytes(query_embedding)}
    res = client.ft(settings.redis_index).search(q, query_params=params)

    hits: list[dict] = []
    for d in res.docs:
        # redis-py returns attributes on the doc; also accessible via __dict__
        source = getattr(d, "source", None) or getattr(d, "filename", None) or "unknown"
        hits.append(
            {
                "id": getattr(d, "id", ""),
                "content": getattr(d, "content", ""),
                "source": source,
                "filename": getattr(d, "filename", ""),
                "score": getattr(d, "score", None),
            }
        )
    return hits
