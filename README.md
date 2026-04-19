# RAG Knowledge Chatbot

A serverless Retrieval-Augmented Generation chatbot on AWS with multi-cloud dual-provider routing. Ask questions about my engineering background or the AWS Well-Architected Framework — the same query runs through either AWS Bedrock (Claude Haiku 4.5) or SambaNova (Llama 3.3-70B) based on the provider you select, so you can compare answers and latency side-by-side.

**Live Demo:** https://d1r1qv7io7k8vk.cloudfront.net
**Portfolio:** https://d2uisqfxjzeo6a.cloudfront.net

---

## What This Project Is

A production-style RAG system that demonstrates:

- **Multi-cloud AI routing** — a single Lambda router calls either AWS Bedrock or SambaNova based on the user's selected provider, with matching retrieved context and intentionally different prompt formats per provider.
- **Custom retrieval layer** — no Bedrock Knowledge Bases, no managed vector service. Documents are chunked, embedded via Bedrock Titan Embeddings v2, and stored as a combined vector index in S3. Cosine similarity runs inside the query Lambda.
- **Two knowledge bases in one index** — Jimmy's engineering background (resume, project writeups, curated Q&A) and the full AWS Well-Architected Framework pillars. Every chunk carries a `source_kb` tag so the frontend can visually distinguish sources in the evidence panel.
- **Real observability** — CloudWatch dashboard, alarms on error rate and p95 duration, SNS alerts, EventBridge warm-up pings against both Lambda and the SambaNova inference endpoint.
- **Hard cost cap** — $20/month enforced via AWS Budgets alerts at $15 and $18. Actual run cost sits in single-digit dollars.

---

## Architecture

**Ingestion (one-time per corpus load):**
Documents land in `data/documents/` or `data/well-architected/` → `scripts/ingest_bulk.py` chunks them (175 words, 20-word overlap) → each chunk is embedded via Bedrock Titan Embeddings v2 (1536-dim vectors) → the combined index is written to S3 as `documents/index.json`.

**Query (every user request):**
`POST /query` hits API Gateway → query Lambda embeds the question → cosine similarity returns top-5 chunks across both KBs → router branches on `selected_engine`: Bedrock path builds an Anthropic Messages API request to Claude Haiku 4.5 (via cross-region inference profile), SambaNova path fetches the API key from SSM and builds an OpenAI-compatible request to Llama 3.3-70B → answer streams back through CloudFront → frontend renders the answer plus the retrieved chunks in an evidence panel with relevance scores and KB badges.

**Warm-up:**
EventBridge fires every 5 minutes with `{"warmup": true}`. The Lambda handler short-circuits on that payload, makes a 1-token synthetic call to SambaNova to keep their inference endpoint warm, then returns in under 2 seconds. The prior Nebius warmup was prone to 20-second timeouts that triggered p95 alarms — the SambaNova warmup completes in ~631ms. Runs about $0.03/month.

---

## Tech Stack

| Service | Purpose |
|---|---|
| Amazon S3 | Document storage, vector index, static frontend hosting |
| AWS Lambda (×2) | Ingest pipeline (Python 3.12, 512MB) and query router (Python 3.12, 1024MB) |
| Amazon API Gateway | HTTPS endpoint for the query Lambda |
| Amazon Bedrock — Titan Embeddings v2 | Text-to-vector for documents and queries |
| Amazon Bedrock — Claude Haiku 4.5 | Generation Provider A (via cross-region inference profile, ~3–8s warm) |
| SambaNova — Llama 3.3-70B | Generation Provider B (OpenAI-compatible API, ~2.5–5s warm, ~5–6s first-call-after-idle) |
| Amazon CloudFront | HTTPS edge distribution for the frontend |
| AWS CloudFormation | All infrastructure as code — 665-line single template |
| Amazon CloudWatch | Logs, dashboard, alarms on error rate and p95 duration |
| Amazon EventBridge | 5-minute warm-up ping |
| AWS Systems Manager (SSM) | Secure storage for the SambaNova API key |
| Amazon SNS | Alarm delivery |
| AWS Budgets | Cost alerts at $15 and $18 against a $20/month hard cap |

**Frontend:** plain HTML, CSS, and vanilla JavaScript hosted on S3 behind CloudFront. No framework, no build step. Three-panel analyst console layout with mobile slide-over responsive design below 768px.

---

## Repository Layout

```
src/lambdas/
  ingest/          Ingest Lambda + shared rag_utils
  query/           Query Lambda with multi-provider router
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
CLAUDE.md          Working rules for Claude Code sessions on this repo
PROJECT_PLANNING_MULTICLOUD.md   Full phase-by-phase build log
```

---

## Engineering Decisions

A handful of trade-offs worth calling out. Full phase log lives in `PROJECT_PLANNING_MULTICLOUD.md`.

**Custom retrieval over Bedrock Knowledge Bases.**
Managed KBs abstract away the retrieval layer and hide the interesting engineering. Writing the chunker, embedding pipeline, and cosine search from scratch forced real decisions about chunk size, overlap, and index format, and it's what makes the provider router possible at all — the same retrieved context goes to both providers.

**Single combined index, not one per KB.**
Every chunk carries a `source_kb` tag. One cosine pass per query, merge logic is just sorting by score. Cleaner code and faster than running two indexes and reconciling them. The UI differentiation (orange badges for Jimmy, blue for Well-Architected) is driven by the tag, not by separate retrievals.

**Chunk size tuned from 500 words to 175.**
Initial retrieval scores for open-ended queries were under 0.30. Shrinking chunks to 175 words with 20-word overlap and adding four curated index files (project summaries, work history, highlight index) pushed all target queries above 0.40. Quality jump was immediate and dramatic.

**Provider-specific prompts, not a unified prompt.**
Claude Haiku responds to Anthropic's XML-style system/user structure; Llama responds better to Markdown-style instructions. Both system prompts are independently tuned — Bedrock for concision and structure (`max_tokens=384`), SambaNova (Llama) for natural voice and synthesis (`max_tokens=256`). Same context, different wrapping.

**Top-k = 5, not 3.**
Running top-k=3 against a 2,027-chunk index missed enumeration chunks that scored 0.40+ but got outranked by narrative chunks sharing query vocabulary. Raising to 5 added ~650ms of context processing and fixed the "What projects has Jimmy built?" incomplete-answer problem on both providers.

**Provider B swap: Nebius → SambaNova.**
Nebius AI Studio (Llama 3.3-70B) was the original Provider B. A 1-token synthetic warmup ping reduced first-call median from ~8s to ~5.5s, but p95 alarms kept firing because the Nebius warmup itself timed out at 20 seconds — breaching the 12s p95 alarm threshold. Groq was evaluated but rejected (Llama 3.3-70B not available on free tier without waitlist). SambaNova runs the same model, warmup completes in ~631ms, and first-call latency matches Bedrock at ~5s. The swap fixed the reliability problem; Bedrock remains the default provider because it produces ~2-3x longer biographical answers with more specific citations from retrieved context. Runs about $0.03/month.

**$20/month budget cap, hard.**
Budgets alarms at $15 and $18. Actual monthly cost at portfolio traffic runs in single-digit dollars. Every latency lever is sized against this ceiling — no provisioned throughput, no dedicated endpoints, no premium inference tiers that can't justify their delta at demo volume.

---

## Cost Guardrails

Monthly cost breakdown at portfolio demo volume (~500 queries/month):

- Bedrock embeddings (Titan v2): ~$0.02
- Bedrock generation (Claude Haiku 4.5): ~$0.95
- SambaNova generation (Llama 3.3-70B): ~$0.30–0.50 (free tier, usage-based)
- Lambda compute: under free tier
- API Gateway: under free tier
- S3 / CloudFront / CloudWatch: ~$0.50
- **Total: under $2/month at steady state**

Hard cap enforced at $20 via AWS Budgets. See `docs/COST_GUARDRAILS.md`.

---

## Current Status

`v1.0-multikb` tagged. Both providers live. Dual-KB retrieval operational. Mobile responsive. EventBridge and SambaNova warm-up pings running. Full deployment history in `PROJECT_PLANNING_MULTICLOUD.md`.

Active work is tracked in the "Phase 9 Candidates" section of the planning doc — current items include index format optimization (JSON→NumPy binary), ingest pipeline path normalization, and response streaming to the frontend.

---

## License

Portfolio project. Code available for reference; no redistribution license granted.
