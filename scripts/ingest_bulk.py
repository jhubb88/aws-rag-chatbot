"""
ingest_bulk.py — Bulk ingest for large corpus loads.

This script handles bulk ingest operations that exceed Lambda's 15-minute ceiling.
The ingest Lambda (rag-chatbot-ingest-dev) handles single-document, event-triggered
ingest. This script handles bulk corpus loads (e.g. a full 7-PDF knowledge base) where
per-document embedding loops would timeout inside Lambda.

Both this script and the Lambda use identical chunking and embedding logic via
src/lambdas/ingest/rag_utils.py. Chunking parameters must only be changed there.

Usage:
    python3 scripts/ingest_bulk.py
Requires:
    boto3 with portfolio-user profile, pypdf, AWS credentials configured.
"""

import json
import os
import sys
import boto3
from pypdf import PdfReader

# Import shared chunking + embedding logic from the Lambda package.
# This guarantees the script and Lambda always use identical logic.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "lambdas", "ingest"))
from rag_utils import chunk_text, embed_text

BUCKET = "rag-chatbot-603509861186-dev"
INDEX_KEY = "documents/index.json"
EMBED_MODEL = "amazon.titan-embed-text-v2:0"
SOURCE_KB = "aws_well_architected"
PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "well-architected")

PDFS = [
    "framework.pdf",
    "operational-excellence.pdf",
    "security.pdf",
    "reliability.pdf",
    "performance-efficiency.pdf",
    "cost-optimization.pdf",
    "sustainability.pdf",
]

session = boto3.Session(profile_name="portfolio-user")
s3 = session.client("s3", region_name="us-east-1")
bedrock = session.client("bedrock-runtime", region_name="us-east-1")


def load_index():
    try:
        r = s3.get_object(Bucket=BUCKET, Key=INDEX_KEY)
        data = json.loads(r["Body"].read())
        print(f"[INFO] Loaded existing index: {len(data)} entries")
        return data
    except Exception as e:
        print(f"[WARN] Could not load existing index: {e} — starting fresh")
        return []


# Load current index. Remove any existing aws_well_architected entries so this
# script is idempotent — safe to re-run if it fails partway through.
index = load_index()
before_count = len(index)
index = [e for e in index if e.get("source_kb") != SOURCE_KB]
if before_count != len(index):
    print(f"[INFO] Removed {before_count - len(index)} stale aws_well_architected entries")

chunk_counter = len(index)
total_new = 0

for pdf_name in PDFS:
    path = os.path.join(PDF_DIR, pdf_name)
    print(f"\n[INFO] Processing {pdf_name}...")
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    print(f"[INFO]   {len(reader.pages)} pages extracted")

    chunks = chunk_text(text)
    print(f"[INFO]   {len(chunks)} chunks")

    added = 0
    for chunk_val in chunks:
        embedding = embed_text(bedrock, chunk_val, EMBED_MODEL)
        if embedding is None:
            print(f"[WARN]   Skipping chunk — embedding failed")
            continue
        index.append({
            "chunk_id": chunk_counter,
            "text": chunk_val,
            "embedding": embedding,
            "source_file": pdf_name,
            "source_kb": SOURCE_KB,
        })
        chunk_counter += 1
        added += 1
        if added % 20 == 0:
            print(f"[INFO]   ...{added}/{len(chunks)} embedded")

    print(f"[INFO]   Done: {added} chunks added from {pdf_name}")
    total_new += added

print(f"\n[INFO] Ingestion complete: {total_new} new chunks added")
print(f"[INFO] Total index size: {len(index)} entries")

s3.put_object(
    Bucket=BUCKET,
    Key=INDEX_KEY,
    Body=json.dumps(index, indent=2),
    ContentType="application/json",
)
print(f"[INFO] Index written to s3://{BUCKET}/{INDEX_KEY}")
