# Design decisions

## Why Redis (RediSearch)?
- Ubiquitous, simple to run locally via Redis Stack; also available as managed services.
- RediSearch provides HNSW vector search alongside text/numeric fields for citations/filters.
- Minimal client surface (redis-py) and straightforward deployment story for small demos.

## Setup experience (relative)
- Postgres + pgvector: solid but heavier to configure; indexing/tuning is manual.
- Weaviate/Milvus: feature-rich but local setup can be finicky (extra deps like MinIO/etcd, gRPC ports).
- Redis/RediSearch: quickest to stand up locally (single container) with minimal tuning for a small RAG demo.

## Why a single FastAPI container?
- Minimizes moving parts for a demo.
- Keeps local + cloud parity high.
- You can add a worker/queue later if needed.

## Why “mock mode”?
- Lets you run end-to-end without an API key.
- Enables deterministic CI tests (hash-based embeddings).

## Why not LangChain?
For a demo repo meant to showcase fundamentals, it's valuable to:
- control chunking explicitly
- see embeddings + retrieval SQL plainly
- avoid framework magic that can obscure the basics

You can always wrap this later with LangChain or an agent framework.
