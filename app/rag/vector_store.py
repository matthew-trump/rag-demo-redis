from __future__ import annotations

import uuid
from typing import Iterable

# Ensure marshmallow exposes __version_info__ for environs (used by pymilvus)
# Ensure marshmallow/environs are patched even if sitecustomize is bypassed
import marshmallow as _mm  # type: ignore
import marshmallow.fields as _mm_fields  # type: ignore

# environs (pulled in by pymilvus) expects marshmallow __version_info__ and
# Field to accept a "missing" kwarg. Newer marshmallow drops both, so we
# patch them here before pymilvus is imported.
ver = getattr(_mm, "__version__", None)
parts = (0, 0, 0)
if isinstance(ver, str):
    try:
        parts = tuple(int(p) for p in ver.split(".") if p.split(".")[0].isdigit())
    except Exception:
        parts = (0, 0, 0)
if not isinstance(getattr(_mm, "__version_info__", None), tuple):
    _mm.__version_info__ = parts  # type: ignore[attr-defined]

_orig_field_init = _mm_fields.Field.__init__
if "missing" not in _orig_field_init.__code__.co_varnames:
    def _patched_field_init(self, *args, **kwargs):  # type: ignore
        if "missing" in kwargs and "load_default" not in kwargs:
            kwargs["load_default"] = kwargs.pop("missing")
        return _orig_field_init(self, *args, **kwargs)
    _mm_fields.Field.__init__ = _patched_field_init  # type: ignore

# Tell environs to rely on load_default instead of missing
import environs as _env  # type: ignore
_env._SUPPORTS_LOAD_DEFAULT = True  # type: ignore[attr-defined]

from app.rag.schema import EMBEDDING_DIM
from app.rag.settings import settings
from app.rag.chunking import ChunkedText


class MilvusNotConfiguredError(RuntimeError):
    pass


def _load_milvus():
    from pymilvus import MilvusClient, DataType, FieldSchema, CollectionSchema  # type: ignore
    return MilvusClient, DataType, FieldSchema, CollectionSchema


def _client():
    MilvusClient, *_ = _load_milvus()
    if not settings.milvus_uri:
        raise MilvusNotConfiguredError("MILVUS_URI is not set")
    return MilvusClient(uri=settings.milvus_uri, token=settings.milvus_token)


def _ensure_collection() -> None:
    MilvusClient, DataType, FieldSchema, CollectionSchema = _load_milvus()
    client = _client()
    if client.has_collection(settings.milvus_collection):
        return
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
        FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=512),
    ]
    schema = CollectionSchema(fields=fields, description="RAG chunks")
    client.create_collection(
        collection_name=settings.milvus_collection,
        schema=schema,
        index_params=[
            {
                "index_type": "AUTOINDEX",
                "metric_type": "COSINE",
                "field_name": "embedding",
            }
        ],
    )


def _chunk_id(source: str, chunk: ChunkedText) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}-{chunk.index}-{chunk.text}"))


def upsert_chunks(chunks: Iterable[ChunkedText], embeddings: list[list[float]], source: str, metadata: dict) -> int:
    _ensure_collection()
    client = _client()
    rows = []
    for chunk, emb in zip(chunks, embeddings, strict=True):
        rows.append(
            {
                "id": _chunk_id(source, chunk),
                "content": chunk.text,
                "source": source,
                "chunk_index": chunk.index,
                "embedding": emb,
                **(metadata or {}),
            }
        )
    if not rows:
        return 0
    client.insert(collection_name=settings.milvus_collection, data=rows)
    return len(rows)


def query_top_k(query_embedding: list[float], top_k: int) -> list[dict]:
    _ensure_collection()
    client = _client()
    search_res = client.search(
        collection_name=settings.milvus_collection,
        data=[query_embedding],
        limit=top_k,
        search_params={"metric_type": "COSINE"},
        output_fields=["content", "source", "chunk_index", "filename"],
    )
    if not search_res or not search_res[0]:
        return []

    # Collect ids from the search to fetch full metadata via query (more reliable).
    hit_ids = []
    hit_scores = {}
    for h in search_res[0]:
        hid = getattr(h, "id", None) or h.get("id")  # type: ignore
        if hid:
            hit_ids.append(hid)
            hit_scores[hid] = getattr(h, "distance", None) or h.get("distance")  # type: ignore

    rows_by_id: dict[str, dict] = {}
    if hit_ids:
        quoted_ids = ", ".join(repr(str(hid)) for hid in hit_ids)
        filter_expr = f"id in [{quoted_ids}]"
        rows = client.query(
            collection_name=settings.milvus_collection,
            filter=filter_expr,
            output_fields=["id", "source", "filename", "chunk_index", "content"],
        )
        for r in rows:
            rows_by_id[str(r.get("id"))] = r

    hits: list[dict] = []
    for h in search_res[0]:
        hid = getattr(h, "id", None) or h.get("id")  # type: ignore
        row = rows_by_id.get(str(hid), {}) if hid is not None else {}
        src = row.get("source") or row.get("filename") or getattr(h, "source", None) or "unknown"
        hits.append(
            {
                "id": str(hid) if hid is not None else "",
                "content": row.get("content") or getattr(h, "content", None) or "",
                "source": src,
                "filename": row.get("filename") or getattr(h, "filename", None) or "",
                "score": hit_scores.get(hid),
            }
        )
    return hits
