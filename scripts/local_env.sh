#!/usr/bin/env bash
set -euo pipefail

export OPENAI_MODEL="${OPENAI_MODEL:-gpt-5}"
export OPENAI_EMBEDDING_MODEL="${OPENAI_EMBEDDING_MODEL:-text-embedding-3-small}"
export CHUNK_SIZE="${CHUNK_SIZE:-800}"
export CHUNK_OVERLAP="${CHUNK_OVERLAP:-120}"
export MILVUS_URI="${MILVUS_URI:-http://localhost:19530}"
export MILVUS_TOKEN="${MILVUS_TOKEN:-}"
export MILVUS_COLLECTION="${MILVUS_COLLECTION:-rag_demo}"

echo "MILVUS_URI=$MILVUS_URI"
echo "MILVUS_COLLECTION=$MILVUS_COLLECTION"
