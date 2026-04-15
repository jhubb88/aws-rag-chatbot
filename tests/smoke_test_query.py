#!/usr/bin/env python3
"""
tests/smoke_test_query.py — Query Lambda local smoke test
Phase 3 | rag-chatbot project

Runs the query handler directly (no Lambda runtime needed).
Requires:
  - Bedrock Titan Embeddings v2 (live, unblocked)
  - Nebius API key in SSM at /rag-chatbot/nebius-api-key (live)
  - documents/index.json in S3 (built by ingest Lambda -- 15 chunks)

Bedrock generation path (selected_engine=bedrock) is code-complete but
untestable until AWS Support resolves the account-level block on
anthropic.claude-3-haiku-20240307-v1:0.

IMPORTANT: AWS_PROFILE must be set before handler is imported.
handler.py creates boto3 clients at module load time, so any profile
override must be in the environment before the import statement below.

Run from project root:
  python3 tests/smoke_test_query.py
"""

import os
import sys
import json

# Set profile before importing handler -- boto3 clients are created at import time.
os.environ.setdefault("AWS_PROFILE", "portfolio-user")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Add the lambda source to path so handler can be imported directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "lambdas", "query"))

import handler  # noqa: E402 -- must come after env vars are set

TEST_QUERY = "What projects has Jimmy built?"
TEST_ENGINE = "nebius"


def run():
    print("=" * 60)
    print("RAG Chatbot -- Query Lambda Smoke Test")
    print(f"Query:  {TEST_QUERY!r}")
    print(f"Engine: {TEST_ENGINE}")
    print("=" * 60)

    event = {
        "body": json.dumps({
            "query": TEST_QUERY,
            "selected_engine": TEST_ENGINE,
        })
    }

    response = handler.lambda_handler(event, context=None)

    print("\n--- Response Status ---")
    print(f"HTTP status: {response['statusCode']}")
    print(f"Headers:     {response.get('headers', {})}")

    # Guard: parse body before anything else so a raw error surfaces cleanly.
    try:
        body = json.loads(response["body"])
    except (KeyError, json.JSONDecodeError) as e:
        print(f"\n[FAIL] Could not parse response body: {e}")
        print(f"Raw response: {response}")
        sys.exit(1)

    print("\n--- Answer ---")
    print(body.get("answer", "(no answer)"))

    print("\n--- Sources ---")
    sources = body.get("sources", [])
    if not sources:
        print("(no sources returned)")
    for i, src in enumerate(sources, start=1):
        print(f"[{i}] {src['source_file']} (score: {src['score']})")
        preview = src["text"][:150] + ("..." if len(src["text"]) > 150 else "")
        print(f"    {preview}")

    print("\n--- Engine Used ---")
    print(body.get("engine_used", "(unknown)"))

    # Assertions
    failures = []

    if response["statusCode"] != 200:
        failures.append(f"Expected status 200, got {response['statusCode']}")

    answer = body.get("answer", "")
    if not answer or not answer.strip():
        failures.append("Answer is missing or empty")

    engine_used = body.get("engine_used", "")
    if engine_used != TEST_ENGINE:
        failures.append(f"Expected engine_used={TEST_ENGINE!r}, got {engine_used!r}")

    if failures:
        print("\n[FAIL] Smoke test failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n[PASS] Smoke test complete")


if __name__ == "__main__":
    run()
