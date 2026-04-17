"""
rag_utils.py — Shared chunking and embedding helpers for the RAG ingest pipeline.

Used by:
  - src/lambdas/ingest/handler.py  (single-doc, event-triggered Lambda ingest)
  - scripts/ingest_bulk.py         (bulk corpus loads that exceed Lambda's 15-min ceiling)

Keep chunk_text and embed_text in sync. Do not duplicate these functions elsewhere.
"""
import json


def chunk_text(text, chunk_size=175, overlap=20):
    """
    Split text into overlapping word-count chunks.
    Words are used as a proxy for tokens (~0.75 tokens/word average).
    """
    words = text.split()
    if not words:
        return []
    chunks, start = [], 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def embed_text(bedrock_client, text, model_id="amazon.titan-embed-text-v2:0"):
    """
    Embed a single text chunk using Bedrock Titan Embeddings v2.
    Returns the embedding vector (list of floats), or None on failure.
    """
    payload = json.dumps({"inputText": text})
    try:
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=payload,
            contentType="application/json",
            accept="application/json",
        )
        return json.loads(response["body"].read())["embedding"]
    except Exception as e:
        print(f"[ERROR] Bedrock embedding failed: {e}")
        return None
