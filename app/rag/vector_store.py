from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Iterable

import weaviate
from weaviate.classes.config import Configure, VectorDistances, Property, DataType
from weaviate.classes.data import DataObject
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter

from app.rag.schema import EMBEDDING_DIM
from app.rag.settings import settings
from app.rag.chunking import ChunkedText


class WeaviateNotConfiguredError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _client() -> weaviate.WeaviateClient:
    if not settings.weaviate_host:
        raise WeaviateNotConfiguredError("WEAVIATE_HOST is not set")
    auth = Auth.api_key(settings.weaviate_api_key) if settings.weaviate_api_key else None
    return weaviate.connect_to_custom(
        http_host=settings.weaviate_host,
        http_port=settings.weaviate_port,
        http_secure=settings.weaviate_secure,
        grpc_host=settings.weaviate_host,
        grpc_port=settings.weaviate_port + 1,  # default gRPC is http_port+1 in local docker
        grpc_secure=settings.weaviate_secure,
        auth_credentials=auth,
        skip_init_checks=True,
    )


def _ensure_schema() -> None:
    client = _client()
    existing = {c.name for c in client.collections.list_all()}
    if settings.weaviate_class not in existing:
        client.collections.create(
            settings.weaviate_class,
            vectorizer_config=Configure.Vectorizer.none(),
            vector_index_config=Configure.VectorIndex.hnsw(distance_metric=VectorDistances.COSINE),
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="source", data_type=DataType.TEXT),
                Property(name="chunk_index", data_type=DataType.NUMBER),
            ],
        )


def _chunk_id(source: str, chunk: ChunkedText) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}-{chunk.index}-{chunk.text}"))


def upsert_chunks(chunks: Iterable[ChunkedText], embeddings: list[list[float]], source: str, metadata: dict) -> int:
    _ensure_schema()
    client = _client()
    coll = client.collections.get(settings.weaviate_class)

    objs: list[DataObject] = []
    for chunk, emb in zip(chunks, embeddings, strict=True):
        objs.append(
            DataObject(
                uuid=_chunk_id(source, chunk),
                properties={
                    "content": chunk.text,
                    "source": source,
                    "chunk_index": chunk.index,
                    **(metadata or {}),
                },
                vector=emb,
            )
        )
    if not objs:
        return 0
    coll.data.insert_many(objs)
    return len(objs)


def query_top_k(query_embedding: list[float], top_k: int) -> list[dict]:
    _ensure_schema()
    client = _client()
    coll = client.collections.get(settings.weaviate_class)
    res = coll.query.near_vector(query_embedding, limit=top_k, return_metadata=["distance"])

    hits: list[dict] = []
    for obj in res.objects:
        props = obj.properties or {}
        hits.append(
            {
                "id": obj.uuid,
                "content": props.get("content", ""),
                "source": props.get("source", "unknown"),
                "score": obj.metadata.get("distance") if obj.metadata else None,
            }
        )
    return hits
