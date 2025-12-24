# Architecture

## Components (minimal RAG)

1. **FastAPI service** (single container)
   - Ingest: chunk → embed → store (Milvus)
   - Ask: embed question → retrieve top-k from Milvus → generate answer → return citations

2. **Milvus**
   - Stores chunks + embeddings as vectors with properties (`content`, `source`, `chunk_index`, optional metadata).
   - Retrieval is a vector similarity query (cosine).

## Data flow

### Ingest
1. `POST /ingest` (text + optional metadata)
2. Chunking (fixed-size + overlap)
3. Embeddings
4. Upsert N vectors to Milvus with properties/metadata

### Ask
1. `POST /ask` (question)
2. Embed question
3. Retrieve top-k similar chunks from Milvus
4. Build prompt with:
   - instructions
   - retrieved context (with citations)
   - question
5. Call the LLM
6. Return answer + citations (chunk ids + sources)

## Storage

Milvus collection:
- Vectors sized to embedding dimension (1536) with cosine metric (AUTOINDEX).
- Properties: `id` (UUID primary key), `content`, `source`, `chunk_index`, plus user-supplied metadata.

## Deployments

### Local dev
- API via `uvicorn`
- Milvus locally (e.g., `docker run -p 19530:19530 milvusdb/milvus:v2.4.6`) or a managed Milvus endpoint (update URI/token accordingly).

### Cloud
- Containerize the FastAPI service (e.g., ECS/Fargate or your platform of choice).
- Use a managed Milvus offering or your own Milvus deployment; configure URI/token/collection via env vars.
