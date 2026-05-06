# RAG Knowledge Chatbot

A serverless Retrieval-Augmented Generation chatbot on AWS. Ask questions about my engineering background or the AWS Well-Architected Framework — answers are retrieval-grounded across both knowledge bases and generated via AWS Bedrock (Claude Haiku 4.5).

**Live Demo:** https://d1r1qv7io7k8vk.cloudfront.net
**Portfolio:** https://d2uisqfxjzeo6a.cloudfront.net

---

## What This Project Is

A production-style RAG system that demonstrates:

- **Custom retrieval layer** — no Bedrock Knowledge Bases, no managed vector service. Documents are chunked, embedded via Bedrock Titan Embeddings v2, and stored as a combined vector index in S3. Cosine similarity runs inside the query Lambda.
- **Two knowledge bases in one index** — Jimmy's engineering background (resume, project writeups, curated Q&A) and the full AWS Well-Architected Framework pillars. Every chunk carries a `source_kb` tag so the frontend can visually distinguish sources in the evidence panel.
- **Real observability** — CloudWatch dashboard, alarms on error rate and p95 duration, SNS alerts, EventBridge warm-up pings that prime the Lambda container and pre-populate the in-memory index cache.
- **Hard cost cap** — $20/month enforced via AWS Budgets alerts at $15 and $18. Actual run cost sits in single-digit dollars.

---

## Architecture

**Ingestion (one-time per corpus load):**
Documents land in `data/documents/` or `data/well-architected/` → `scripts/ingest_bulk.py` chunks them (175 words, 20-word overlap) → each chunk is embedded via Bedrock Titan Embeddings v2 (1536-dim vectors) → the combined index is written to S3 as `documents/index.json`.

**Query (every user request):**
`POST /query` hits API Gateway → query Lambda embeds the question → cosine similarity returns top-5 chunks across both KBs → Lambda builds an Anthropic Messages API request to Claude Haiku 4.5 (via cross-region inference profile) and invokes Bedrock → answer streams back through CloudFront → frontend renders the answer plus the retrieved chunks in an evidence panel with relevance scores and KB badges.

**Warm-up:**
EventBridge fires every 5 minutes with `{"warmup": true}`. The warmup ping does two things: keeps the Lambda container alive and pre-populates the S3 vector index into the module-level `_index_cache` (eliminating a ~6s S3-load penalty on the container's first real query). Warmup REPORT duration: 1–4ms on warm containers with a cached index, up to ~4s on cold containers. Runs about $0.03/month.

---

## Tech Stack

| Service | Purpose |
|---|---|
| Amazon S3 | Document storage, vector index, static frontend hosting |
| AWS Lambda (×2) | Ingest pipeline (Python 3.12, 512MB) and query Lambda (Python 3.12, 1024MB) |
| Amazon API Gateway | HTTPS endpoint for the query Lambda |
| Amazon Bedrock — Titan Embeddings v2 | Text-to-vector for documents and queries |
| Amazon Bedrock — Claude Haiku 4.5 | Answer generation (via cross-region inference profile, ~5–6s warm) |
| Amazon CloudFront | HTTPS edge distribution for the frontend |
| AWS CloudFormation | Infrastructure as code |
| Amazon CloudWatch | Logs, dashboard, alarms on error rate and p95 duration |
| Amazon EventBridge | 5-minute warm-up ping |
| Amazon SNS | Alarm delivery |
| AWS Budgets | Cost alerts at $15 and $18 against a $20/month hard cap |

**Frontend:** plain HTML, CSS, and vanilla JavaScript hosted on S3 behind CloudFront. No framework, no build step. Three-panel analyst console layout with mobile slide-over responsive design below 768px.

---

## Repository Layout

```
src/lambdas/
  ingest/          Ingest Lambda + shared rag_utils
  query/           Query Lambda
infrastructure/
  cloudformation/  Single-template IaC for the entire stack
frontend/
  index.html       Full frontend, single file
scripts/
  ingest_bulk.py   Long-form corpus loader (bypasses 15-min Lambda limit)
  ...
data/
  documents/       Source documents for Jimmy KB (gitignored)
  well-architected/  Source PDFs for AWS WA KB (gitignored)
  curated/         Hand-authored Q&A chunks (tracked)
docs/              Planning docs, architecture decisions, cost guardrails
tests/             Smoke tests
```

---

## Deployment

Frontend deploys via push-triggered CI/CD. Pushing to `main` with changes under `frontend/**` triggers `.github/workflows/deploy.yml`, which syncs `frontend/` to the project S3 bucket and invalidates the CloudFront distribution.

**Pipeline:**
- Trigger: push to `main` modifying `frontend/**` or the workflow file (also `workflow_dispatch` for manual runs)
- Auth: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` GitHub secrets on `jhubb88/aws-rag-chatbot`
- Sync: `aws s3 sync frontend/ s3://rag-chatbot-603509861186-dev/` (no `--delete`)
- Invalidate: `aws cloudfront create-invalidation --paths "/*"` against distribution `EN88LEBW14923`

**Why no `--delete`:** the S3 bucket is shared with RAG infrastructure — `documents/` holds the 61MB vector index, `lambda/` holds Lambda deployment packages, `cloudtrail/` holds audit logs. A `--delete`-flagged sync would wipe the knowledge base and break the query Lambda. The workflow file carries an explicit warning above the sync step.

**Why `/*` invalidation:** verified 2026-04-19 that `/index.html`-only invalidations on this distribution do not reliably clear the cache; `/*` does. Documented quirk; do not narrow.

Backend Lambda code and CloudFormation infra are not touched by this pipeline — IaC realignment is on the backlog.

---

## Engineering Decisions

A handful of trade-offs worth calling out.

**Custom retrieval over Bedrock Knowledge Bases.**
Managed KBs abstract away the retrieval layer and hide the interesting engineering. Writing the chunker, embedding pipeline, and cosine search from scratch forced real decisions about chunk size, overlap, and index format.

**Single combined index, not one per KB.**
Every chunk carries a `source_kb` tag. One cosine pass per query, merge logic is just sorting by score. Cleaner code and faster than running two indexes and reconciling them. The UI differentiation (orange badges for Jimmy, blue for Well-Architected) is driven by the tag, not by separate retrievals.

**Chunk size tuned from 500 words to 175.**
Initial retrieval scores for open-ended queries were under 0.30. Shrinking chunks to 175 words with 20-word overlap and adding four curated index files (project summaries, work history, highlight index) pushed all target queries above 0.40. Quality jump was immediate and dramatic.

**Top-k = 5, not 3.**
Running top-k=3 against a 2,027-chunk index missed enumeration chunks that scored 0.40+ but got outranked by narrative chunks sharing query vocabulary. Raising to 5 added ~650ms of context processing and fixed the "What projects has Jimmy built?" incomplete-answer problem.

**Warmup does two things, not one.**
The EventBridge ping keeps the Lambda container alive — that's the obvious function. The second function was added after diagnosing real failure modes in production: the warmup branch calls `_load_index()` to pre-populate the module-level `_index_cache` — every container spawned by a warmup ping has the 58MB index ready before the first real user query, eliminating the ~6s S3-load penalty that previously hit every container's first touch. Measured impact: first-touch cold dropped from ~8.3s Lambda (6s S3 load + ~2s Bedrock) to ~4.7s Lambda (cache hit + ~4s Bedrock).

**$20/month budget cap, hard.**
Budgets alarms at $15 and $18. Actual monthly cost at portfolio traffic runs in single-digit dollars. Every latency lever is sized against this ceiling — no provisioned throughput, no dedicated endpoints, no premium inference tiers that can't justify their delta at demo volume.

---

## Cost Guardrails

Monthly cost breakdown at portfolio demo volume (~500 queries/month):

- Bedrock embeddings (Titan v2): ~$0.02
- Bedrock generation (Claude Haiku 4.5): ~$0.95
- Lambda compute: under free tier
- API Gateway: under free tier
- S3 / CloudFront / CloudWatch: ~$0.50
- **Total: under $2/month at steady state**

Hard cap enforced at $20 via AWS Budgets. See `docs/COST_GUARDRAILS.md`.

---

## Current Status

`v1.2-bedrock-only` tagged. Bedrock-only generation. Dual-KB retrieval operational. Mobile responsive. EventBridge warmup running with index cache priming — first-touch cold ~4.7s Lambda, warm queries 5–6s.

Deferred candidates (no active work): index format optimization, response streaming, IaC drift realignment.

## Supported Platforms

**Fully supported:** desktop browsers (Chrome, Firefox, Safari, Edge), iPhone Safari.

**Known issue — iPad Safari:** After using Clear Session and running a second query, the top bar and panel controls may become unresponsive. The chat input and center panel remain functional. Workaround: reload the page. Deferred as low-priority — the demo audience is primarily desktop and iPhone.

---

## License

MIT — see [LICENSE](LICENSE)

## Author

Jimmy Hubbard — [github.com/jhubb88](https://github.com/jhubb88)

---

*Part of [jhubb88's portfolio](https://jimmyhubbard2.cc)*
