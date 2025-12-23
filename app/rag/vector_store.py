from __future__ import annotations

import uuid
import json
from functools import lru_cache
from typing import Iterable

import requests

from app.rag.schema import EMBEDDING_DIM
from app.rag.settings import settings
from app.rag.chunking import ChunkedText


class WeaviateNotConfiguredError(RuntimeError):
    pass

class WeaviateHTTPError(RuntimeError):
    pass


def _base_url() -> str:
    if not settings.weaviate_host or not settings.weaviate_port:
        raise WeaviateNotConfiguredError("WEAVIATE_HOST/WEAVIATE_PORT not set")
    scheme = "https" if settings.weaviate_secure else "http"
    return f"{scheme}://{settings.weaviate_host}:{settings.weaviate_port}"


def _headers() -> dict:
    hdrs = {"Content-Type": "application/json"}
    if settings.weaviate_api_key:
        hdrs["Authorization"] = f"Bearer {settings.weaviate_api_key}"
    return hdrs


def _ensure_schema() -> None:
    url = f"{_base_url()}/v1/schema"
    resp = requests.get(url, headers=_headers(), timeout=10)
    if resp.status_code != 200:
        raise WeaviateHTTPError(f"Schema fetch failed: {resp.status_code} {resp.text}")
    existing = {cls["class"] for cls in resp.json().get("classes", [])}
    if settings.weaviate_class in existing:
        return

    payload = {
        "class": settings.weaviate_class,
        "vectorIndexType": "hnsw",
        "vectorIndexConfig": {"distance": "cosine"},
        "properties": [
            {"name": "content", "dataType": ["text"]},
            {"name": "source", "dataType": ["text"]},
            {"name": "chunk_index", "dataType": ["int"]},
        ],
        "vectorConfig": {"vectorLength": EMBEDDING_DIM},
    }
    resp = requests.post(url, headers=_headers(), data=json.dumps(payload), timeout=10)
    if resp.status_code not in (200, 201):
        raise WeaviateHTTPError(f"Schema create failed: {resp.status_code} {resp.text}")


def _chunk_id(source: str, chunk: ChunkedText) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}-{chunk.index}-{chunk.text}"))


def upsert_chunks(chunks: Iterable[ChunkedText], embeddings: list[list[float]], source: str, metadata: dict) -> int:
    _ensure_schema()
    count = 0
    for chunk, emb in zip(chunks, embeddings, strict=True):
        payload = {
            "class": settings.weaviate_class,
            "id": _chunk_id(source, chunk),
            "properties": {
                "content": chunk.text,
                "source": source,
                "chunk_index": chunk.index,
                **(metadata or {}),
            },
            "vector": emb,
        }
        resp = requests.post(f"{_base_url()}/v1/objects", headers=_headers(), data=json.dumps(payload), timeout=10)
        if resp.status_code not in (200, 201):
            raise WeaviateHTTPError(f"Upsert failed: {resp.status_code} {resp.text}")
        count += 1
    return count


def query_top_k(query_embedding: list[float], top_k: int) -> list[dict]:
    _ensure_schema()
    graphql_query = {
        "query": """
        {
          Get {
            %s(
              limit: %d
              nearVector: { vector: %s }
            ) {
              _additional { id distance }
              content
              source
              chunk_index
            }
          }
        }
        """
        % (settings.weaviate_class, top_k, json.dumps(query_embedding))
    }
    resp = requests.post(f"{_base_url()}/v1/graphql", headers=_headers(), data=json.dumps(graphql_query), timeout=10)
    if resp.status_code != 200:
        raise WeaviateHTTPError(f"Query failed: {resp.status_code} {resp.text}")
    data = resp.json()
    hits = data.get("data", {}).get("Get", {}).get(settings.weaviate_class, []) or []
    out: list[dict] = []
    for h in hits:
        meta = h.get("_additional", {}) or {}
        out.append(
            {
                "id": meta.get("id", ""),
                "content": h.get("content", ""),
                "source": h.get("source", "unknown"),
                "score": meta.get("distance"),
            }
        )
    return out
