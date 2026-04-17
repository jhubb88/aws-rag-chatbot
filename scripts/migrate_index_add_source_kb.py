"""
migrate_index_add_source_kb.py
One-time migration: tags all existing index entries with source_kb=jimmy_background.
Run locally with: python3 scripts/migrate_index_add_source_kb.py
"""
import json
import boto3

BUCKET = "rag-chatbot-603509861186-dev"
INDEX_KEY = "documents/index.json"

session = boto3.Session(profile_name="portfolio-user")
s3 = session.client("s3", region_name="us-east-1")

response = s3.get_object(Bucket=BUCKET, Key=INDEX_KEY)
index = json.loads(response["Body"].read())
print(f"Loaded {len(index)} entries")

updated = 0
for entry in index:
    if "source_kb" not in entry:
        entry["source_kb"] = "jimmy_background"
        updated += 1

print(f"Tagged {updated} entries with source_kb=jimmy_background")

s3.put_object(
    Bucket=BUCKET,
    Key=INDEX_KEY,
    Body=json.dumps(index, indent=2),
    ContentType="application/json",
)
print("Index written back to S3.")
