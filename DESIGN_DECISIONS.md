# Design decisions

## Why Milvus?
- Mature vector database with robust ANN indexes (HNSW, AUTOINDEX) and cosine metric support.
- Easy local run via a single container; also offered as managed services.
- Simple insert/search APIs via the Python client; we supply our own embeddings.

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
