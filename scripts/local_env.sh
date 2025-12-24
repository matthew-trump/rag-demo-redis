#!/usr/bin/env bash
set -euo pipefail

export OPENAI_MODEL="${OPENAI_MODEL:-gpt-5}"
export OPENAI_EMBEDDING_MODEL="${OPENAI_EMBEDDING_MODEL:-text-embedding-3-small}"
export CHUNK_SIZE="${CHUNK_SIZE:-800}"
export CHUNK_OVERLAP="${CHUNK_OVERLAP:-120}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
export REDIS_INDEX="${REDIS_INDEX:-rag:chunks}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-}"

echo "REDIS_URL=$REDIS_URL"
echo "REDIS_INDEX=$REDIS_INDEX"
