"""
ingest/handler.py — RAG Chatbot Document Ingestion Lambda
Phase 2 | rag-chatbot project

Triggers: S3 ObjectCreated event (documents/ prefix) or direct invoke with {"filename": "foo.txt"}
Reads documents from S3 (documents/ prefix), chunks text, embeds via Bedrock Titan Embeddings v2,
and writes a JSON vector index to S3 at documents/index.json.

Local testing: requires boto3 session using --profile portfolio-user.
Lambda execution: uses the IngestLambda IAM execution role (no profile needed).
"""

import json
import os
import boto3

# Optional: pypdf for PDF support
try:
    from pypdf import PdfReader
    import io
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# --- Config (from environment variables set by CloudFormation) ---
S3_BUCKET = os.environ.get("S3_BUCKET", "rag-chatbot-603509861186-dev")
EMBED_MODEL = "amazon.titan-embed-text-v2:0"
CHUNK_SIZE = 500       # tokens (approximated as words)
CHUNK_OVERLAP = 50     # tokens overlap between chunks
INDEX_KEY = "documents/index.json"

# --- AWS clients ---
s3 = boto3.client("s3", region_name="us-east-1")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


def lambda_handler(event, context):
    """
    Entry point for the ingest Lambda.
    Accepts S3 event or direct invoke: {"filename": "example.txt"}
    """
    print("[INFO] Ingest Lambda invoked")
    print(f"[INFO] Event: {json.dumps(event)}")

    filenames = _extract_filenames(event)
    if not filenames:
        print("[WARN] No filenames found in event — nothing to ingest")
        return {"statusCode": 200, "body": "No files to ingest"}

    # Load existing index from S3 (merge mode)
    existing_index = _load_existing_index()
    existing_sources = {entry["source_file"] for entry in existing_index}

    new_entries = []
    chunk_counter = len(existing_index)

    for filename in filenames:
        print(f"[INFO] Processing file: {filename}")
        s3_key = f"documents/{filename}"

        # Read document text from S3
        text = _read_document_from_s3(s3_key, filename)
        if text is None:
            print(f"[WARN] Skipping {filename} — could not read document")
            continue

        # Remove old entries for this file if re-ingesting
        if filename in existing_sources:
            print(f"[INFO] Re-ingesting {filename} — removing old entries")
            existing_index = [e for e in existing_index if e["source_file"] != filename]
            chunk_counter = len(existing_index)

        # Chunk the text
        chunks = _chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        print(f"[INFO] {filename} split into {len(chunks)} chunks")

        # Embed each chunk
        for chunk_text in chunks:
            embedding = _embed_text(chunk_text)
            if embedding is None:
                print(f"[WARN] Skipping chunk from {filename} — embedding failed")
                continue
            entry = {
                "chunk_id": chunk_counter,
                "text": chunk_text,
                "embedding": embedding,
                "source_file": filename,
            }
            new_entries.append(entry)
            chunk_counter += 1

        print(f"[INFO] {filename}: {len([e for e in new_entries if e['source_file'] == filename])} chunks embedded successfully")

    if not new_entries:
        print("[WARN] No new entries produced — index not updated")
        return {"statusCode": 200, "body": "No new entries to write"}

    # Merge and write updated index
    updated_index = existing_index + new_entries
    _write_index(updated_index)
    print(f"[INFO] Index updated: {len(updated_index)} total entries written to s3://{S3_BUCKET}/{INDEX_KEY}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "files_processed": filenames,
            "new_chunks": len(new_entries),
            "total_chunks": len(updated_index),
        }),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_filenames(event):
    """Extract filename(s) from S3 event or direct invoke payload."""
    filenames = []

    # S3 trigger event
    if "Records" in event:
        for record in event["Records"]:
            try:
                key = record["s3"]["object"]["key"]
                # Strip the documents/ prefix to get just the filename
                filename = key.split("/")[-1]
                if filename:
                    filenames.append(filename)
            except (KeyError, IndexError) as e:
                print(f"[WARN] Could not parse S3 record: {e}")

    # Direct invoke: {"filename": "foo.txt"} or {"filenames": ["a.txt", "b.txt"]}
    elif "filename" in event:
        filenames.append(event["filename"])
    elif "filenames" in event:
        filenames.extend(event["filenames"])

    return filenames


def _read_document_from_s3(s3_key, filename):
    """Download a document from S3 and return its text content."""
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
        raw = response["Body"].read()
    except Exception as e:
        print(f"[ERROR] Failed to read s3://{S3_BUCKET}/{s3_key}: {e}")
        return None

    ext = filename.lower().rsplit(".", 1)[-1]

    if ext == "txt":
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1")

    elif ext == "pdf":
        if not PDF_SUPPORT:
            print(f"[ERROR] pypdf not installed — cannot parse PDF: {filename}")
            return None
        try:
            reader = PdfReader(io.BytesIO(raw))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        except Exception as e:
            print(f"[ERROR] PDF parse failed for {filename}: {e}")
            return None

    else:
        print(f"[WARN] Unsupported file type: {filename} (ext={ext}) — skipping")
        return None


def _chunk_text(text, chunk_size, overlap):
    """
    Split text into chunks of approximately chunk_size words with overlap.
    Words are used as a proxy for tokens (approx 0.75 tokens/word average).
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap

    return chunks


def _embed_text(text):
    """
    Call Bedrock Titan Embeddings v2 to embed a single text chunk.
    Returns the embedding vector (list of floats), or None on failure.
    """
    payload = json.dumps({"inputText": text})
    try:
        response = bedrock.invoke_model(
            modelId=EMBED_MODEL,
            body=payload,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["embedding"]
    except Exception as e:
        print(f"[ERROR] Bedrock embedding failed: {e}")
        return None


def _load_existing_index():
    """Load the current vector index from S3. Returns empty list if none exists."""
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=INDEX_KEY)
        data = json.loads(response["Body"].read())
        print(f"[INFO] Loaded existing index: {len(data)} entries")
        return data
    except s3.exceptions.NoSuchKey:
        print("[INFO] No existing index found — starting fresh")
        return []
    except Exception as e:
        print(f"[WARN] Could not load existing index: {e} — starting fresh")
        return []


def _write_index(index):
    """Write the vector index to S3 as JSON."""
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=INDEX_KEY,
            Body=json.dumps(index, indent=2),
            ContentType="application/json",
        )
        print(f"[INFO] Index written to s3://{S3_BUCKET}/{INDEX_KEY}")
    except Exception as e:
        print(f"[ERROR] Failed to write index to S3: {e}")
        raise
