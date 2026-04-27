"""
query/handler.py — RAG Chatbot Query Lambda

Accepts POST /query with body: {"query": "..."}
Embeds the query via Bedrock Titan Embeddings v2, retrieves top-k chunks by cosine
similarity from the S3 vector index, and generates an answer via AWS Bedrock
(Claude Haiku 4.5 cross-region inference profile).

CORS: Every response includes Access-Control-Allow-Origin: '*' so browser
      requests are not blocked even when the OPTIONS preflight succeeds. The OPTIONS
      preflight alone is not sufficient — the actual POST response must also carry
      this header or the browser will block the response body.

"""

import json
import os
import math
import boto3
from botocore.exceptions import ClientError

# --- Config ---
S3_BUCKET = os.environ.get("S3_BUCKET", "rag-chatbot-603509861186-dev")
INDEX_KEY = "documents/index.json"
EMBED_MODEL = "amazon.titan-embed-text-v2:0"
HAIKU_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"  # cross-region inference profile
TOP_K = 5
CHUNK_CHAR_CAP = 2000  # max chars per chunk sent to the model

# --- AWS clients ---
s3 = boto3.client("s3", region_name="us-east-1")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

# --- Module-level cache — populated on first invocation, reused on warm containers ---
_index_cache = None


def lambda_handler(event, context):
    """Entry point for the Query Lambda."""

    # Warm-up ping from EventBridge
    if event.get("warmup"):
        print("[INFO] Warm-up ping received — container is warm")
        try:
            idx = _load_index()
            if idx is not None:
                print(f"[INFO] Warmup: index cache primed ({len(idx)} chunks)")
            else:
                print("[WARNING] Warmup: index load failed, first user query will pay cold cost")
        except Exception as e:
            print(f"[WARNING] Warmup: index load failed, first user query will pay cold cost")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"status": "warm"}',
        }

    print("[INFO] Query Lambda invoked")

    # Parse request body
    try:
        body = json.loads(event.get("body") or "{}")
        query = body.get("query", "").strip()
    except Exception as e:
        print(f"[ERROR] Failed to parse request body: {e}")
        return _build_response(400, {"error": "Invalid request body — must be JSON with 'query' field"})

    if not query:
        return _build_response(400, {"error": "'query' field is required and cannot be empty"})

    # Log only the fields we control — not the full event (which includes headers and auth context).
    # Query is truncated to 200 chars to keep logs useful without dumping arbitrary user input verbatim.
    query_preview = query[:200] + ("…" if len(query) > 200 else "")
    print(f"[INFO] Query: {query_preview!r}")

    # Step 1: Embed the query
    query_embedding = _embed_query(query)
    if query_embedding is None:
        return _build_response(500, {"error": "Failed to embed query — Bedrock Titan Embeddings unavailable"})

    # Step 2: Load the vector index
    index = _load_index()
    if index is None:
        return _build_response(500, {"error": "Failed to load vector index from S3"})
    if len(index) == 0:
        return _build_response(500, {"error": "Vector index is empty — run ingest first"})

    # Step 3: Retrieve top-k chunks
    top_chunks = _retrieve_top_k(query_embedding, index, k=TOP_K)
    if not top_chunks:
        print("[ERROR] Retrieval returned no chunks — all index entries may be malformed")
        return _build_response(500, {"error": "Retrieval failed — no valid chunks could be scored"})

    print(f"[INFO] Retrieved {len(top_chunks)} chunks. Top score: {top_chunks[0]['score']:.4f}")

    # Step 4: Generate answer
    answer = _generate_bedrock(query, top_chunks)
    if answer is None:
        return _build_response(500, {"error": "Generation failed"})

    # Step 5: Build and return response
    sources = [
        {
            "text": chunk["text"],
            "source_file": chunk["source_file"],
            "source_kb": chunk["source_kb"],
            "score": round(chunk["score"], 4),
        }
        for chunk in top_chunks
    ]

    return _build_response(200, {
        "answer": answer,
        "sources": sources,
    })


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def _embed_query(text):
    """Embed query text using Bedrock Titan Embeddings v2. Returns list of floats or None."""
    payload = json.dumps({"inputText": text})
    try:
        response = bedrock.invoke_model(
            modelId=EMBED_MODEL,
            body=payload,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        embedding = result["embedding"]
        print(f"[INFO] Query embedded successfully ({len(embedding)} dimensions)")
        return embedding
    except Exception as e:
        print(f"[ERROR] Bedrock embedding failed: {e}")
        return None


def _load_index():
    """Load vector index from S3. Returns list of chunk dicts or None on hard failure.
    On warm containers the module-level _index_cache is returned directly, skipping S3.
    """
    global _index_cache
    if _index_cache is not None:
        print(f"[INFO] Using cached vector index: {len(_index_cache)} chunks")
        return _index_cache
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=INDEX_KEY)
        data = json.loads(response["Body"].read())
        print(f"[INFO] Loaded vector index from S3: {len(data)} chunks")
        _index_cache = data
        return _index_cache
    except s3.exceptions.NoSuchKey:
        print(f"[ERROR] Index not found at s3://{S3_BUCKET}/{INDEX_KEY} — run ingest first")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to load index from S3: {e}")
        return None


def _cosine_similarity(a, b):
    """Compute cosine similarity between two equal-length float lists."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _retrieve_top_k(query_embedding, index, k=3):
    """
    Score all chunks against the query embedding and return the top-k by cosine similarity.
    Returns list of dicts: {chunk_id, text, source_file, score}
    Returns empty list if all entries are malformed.
    """
    scored = []
    for entry in index:
        try:
            score = _cosine_similarity(query_embedding, entry["embedding"])
            scored.append({
                "chunk_id": entry.get("chunk_id"),
                "text": entry["text"],
                "source_file": entry["source_file"],
                "source_kb": entry.get("source_kb", "unknown"),
                "score": score,
            })
        except Exception as e:
            print(f"[WARN] Skipping chunk {entry.get('chunk_id')} — scoring error: {e}")

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


# ---------------------------------------------------------------------------
# Generation — Bedrock Claude Haiku
# ---------------------------------------------------------------------------

def _generate_bedrock(query, chunks):
    """
    Call Bedrock Claude Haiku with retrieved chunks as context.
    On AccessDeniedException: returns a user-readable message so the frontend
    can display a meaningful status rather than a generic 500.
    Returns answer text (str) or None on hard failure.
    """
    print("[INFO] Generating answer via AWS Bedrock (Claude Haiku)")

    context_block = _format_context(chunks)

    messages = [
        {
            "role": "user",
            "content": (
                "You are a helpful assistant with access to two knowledge bases: "
                "(1) Jimmy Hubbard's background as a systems engineer and software developer, "
                "and (2) the AWS Well-Architected Framework. "
                "Use only the provided context. Context chunks are labeled with their "
                "source knowledge base (jimmy_background or aws_well_architected). "
                "Be concise. Answer in 2-3 short paragraphs. Use markdown headers only "
                "if the question genuinely requires distinct sections.\n\n"
                f"Context:\n{context_block}\n\n"
                f"Question: {query}"
            ),
        }
    ]

    payload = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 384,
        "messages": messages,
    })
    print(f"[DEBUG] Bedrock request: model={HAIKU_MODEL} max_tokens=384")

    try:
        response = bedrock.invoke_model(
            modelId=HAIKU_MODEL,
            body=payload,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        answer = result["content"][0]["text"].strip()
        usage = result.get("usage", {})
        stop_reason = result.get("stop_reason")
        print(f"[INFO] Bedrock usage: input_tokens={usage.get('input_tokens')} output_tokens={usage.get('output_tokens')} stop_reason={stop_reason}")
        print(f"[INFO] Bedrock generation successful ({len(answer)} chars)")
        return answer
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "AccessDeniedException":
            aws_msg = e.response["Error"].get("Message", "(no message)")
            print(f"[ERROR] Bedrock AccessDeniedException — AWS: {aws_msg}")
            return "The AI provider is temporarily unavailable. Please try again in a moment."
        print(f"[ERROR] Bedrock ClientError ({code}): {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Bedrock generation failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _format_context(chunks):
    """
    Format retrieved chunks into a numbered context block for the prompt.
    Each chunk is capped at CHUNK_CHAR_CAP characters to prevent prompt overflow.
    """
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        text = chunk["text"]
        if len(text) > CHUNK_CHAR_CAP:
            text = text[:CHUNK_CHAR_CAP] + "…"
        lines.append(f"[{i}] (source: {chunk['source_file']}, kb: {chunk['source_kb']}, score: {chunk['score']:.4f})")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def _build_response(status_code, body_dict):
    """
    Build an API Gateway proxy response.
    ALWAYS includes Access-Control-Allow-Origin: '*' on every response path.
    The OPTIONS preflight (handled as a MOCK in API Gateway) is not sufficient —
    the actual POST response must also carry this header or the browser will block
    the response body even after a successful preflight.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body_dict),
    }
