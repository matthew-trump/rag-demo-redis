# Design decisions

## Why Weaviate?
- Purpose-built vector DB with HNSW ANN, metadata filters, and optional hybrid search.
- Easy local run (Docker) and managed cloud option; you can self-host or use Weaviate Cloud.
- Simple upsert/search API; supports custom vectors (no built-in vectorizer in this demo).

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
