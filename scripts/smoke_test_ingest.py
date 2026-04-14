"""
scripts/smoke_test_ingest.py — Manual smoke test for the ingest Lambda handler
Phase 2 | rag-chatbot project

WARNING: This script mutates live S3 demo data. It uploads a test document to
s3://rag-chatbot-603509861186-dev/documents/ and overwrites documents/index.json.
Intended for manual validation only — not automated test coverage.

IMPORTANT: Requires Bedrock Titan Embeddings v2 access.
Will fail with AccessDeniedException if the account-level Bedrock block is still active.

Run with:
    python3 scripts/smoke_test_ingest.py

Requirements:
    - AWS credentials for portfolio-user must be active in your environment
    - The S3 bucket must be accessible (rag-chatbot-603509861186-dev)
    - data/documents/ directory must exist (gitignored)
"""

import os
import sys
import json

# Allow importing from src/lambdas/ingest/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "lambdas", "ingest"))

# Use portfolio-user profile for local testing.
# Override AWS_PROFILE in your shell if running from a different machine.
os.environ.setdefault("AWS_PROFILE", "portfolio-user")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Set the S3 bucket env var the handler reads
os.environ["S3_BUCKET"] = "rag-chatbot-603509861186-dev"

SAMPLE_FILENAME = "test_sample.txt"
SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "documents", SAMPLE_FILENAME)
S3_BUCKET = "rag-chatbot-603509861186-dev"
S3_KEY = f"documents/{SAMPLE_FILENAME}"

SAMPLE_TEXT = """
AWS Bedrock is a fully managed service that makes high-performing foundation models available
through a unified API. It supports models from Amazon, Anthropic, Cohere, Meta, and others.

Retrieval-Augmented Generation (RAG) is a pattern that combines a retrieval system with a
generative model. The retrieval system finds relevant documents from a knowledge base, and
the generative model uses those documents as context to produce a grounded response.

Titan Embeddings v2 is Amazon's embedding model available through Bedrock. It converts text
into dense vector representations that can be compared using cosine similarity to find
semantically related content.

This test document is used to validate the end-to-end ingest pipeline: chunking, embedding,
and index writing to S3.
"""


def upload_sample_to_s3():
    import boto3
    print(f"[SMOKE] Uploading sample file to s3://{S3_BUCKET}/{S3_KEY}")
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=S3_KEY,
        Body=SAMPLE_TEXT.encode("utf-8"),
        ContentType="text/plain",
    )
    print("[SMOKE] Upload complete")


def run():
    print("=" * 60)
    print("RAG Chatbot — Ingest Lambda Smoke Test")
    print("IMPORTANT: Requires Bedrock Titan Embeddings v2 access.")
    print("Will fail with AccessDeniedException if account block is active.")
    print("WARNING: Mutates live S3 demo data — manual validation only.")
    print("=" * 60)

    # Write sample file locally (for reference only — handler reads from S3)
    os.makedirs(os.path.dirname(SAMPLE_PATH), exist_ok=True)
    with open(SAMPLE_PATH, "w") as f:
        f.write(SAMPLE_TEXT)
    print(f"[SMOKE] Sample file written locally: {SAMPLE_PATH}")

    # Upload sample to S3 so the handler can read it
    upload_sample_to_s3()

    # Import handler after env vars are set
    import handler

    # Build a direct-invoke event
    event = {"filename": SAMPLE_FILENAME}

    print(f"\n[SMOKE] Invoking handler with event: {json.dumps(event)}")
    print("-" * 60)

    result = handler.lambda_handler(event, context=None)

    print("-" * 60)
    print(f"[SMOKE] Handler returned: {json.dumps(result, indent=2)}")

    # Pull the index back from S3 and show the first 2 entries
    import boto3
    s3 = boto3.client("s3", region_name="us-east-1")
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key="documents/index.json")
        index = json.loads(response["Body"].read())
        print(f"\n[SMOKE] Index contains {len(index)} total entries.")
        print("[SMOKE] First 2 entries (embedding truncated to 5 values):\n")
        for entry in index[:2]:
            display = dict(entry)
            if display.get("embedding"):
                display["embedding"] = display["embedding"][:5] + ["..."]
            print(json.dumps(display, indent=2))
    except Exception as e:
        print(f"[SMOKE ERROR] Could not read index from S3: {e}")


if __name__ == "__main__":
    run()
