# Architecture

## Components (minimal RAG)

1. **FastAPI service** (single container)
   - Ingest: chunk → embed → store (Weaviate)
   - Ask: embed question → retrieve top-k from Weaviate → generate answer → return citations

2. **Weaviate**
   - Stores chunks + embeddings as vectors with properties (`content`, `source`, `chunk_index`, optional metadata).
   - Retrieval is a vector similarity query (cosine).

## Data flow

### Ingest
1. `POST /ingest` (text + optional metadata)
2. Chunking (fixed-size + overlap)
3. Embeddings
4. Upsert N vectors to Weaviate with properties/metadata

### Ask
1. `POST /ask` (question)
2. Embed question
3. Retrieve top-k similar chunks from Weaviate
4. Build prompt with:
   - instructions
   - retrieved context (with citations)
   - question
5. Call the LLM
6. Return answer + citations (chunk ids + sources)

## Storage

Weaviate class:
- Vectors sized to embedding dimension (1536) with cosine metric.
- Properties: `content`, `source`, `chunk_index`, plus user-supplied metadata.

## Deployments

### Local dev
- API via `uvicorn`
- Weaviate locally (e.g., `docker run -p 8091:8080 semitechnologies/weaviate`) or managed Weaviate Cloud (update host/port accordingly).

### Cloud
- Containerize the FastAPI service (e.g., ECS/Fargate or your platform of choice).
- Use Weaviate Cloud or your own Weaviate deployment; configure URL/API key/class via env vars.
