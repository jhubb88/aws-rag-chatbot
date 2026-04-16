# RAG Knowledge Chatbot — Project Planning Document
### Multi-Cloud Edition | Last Updated: 2026-04-16
**Phase 1 Status:** ✅ Complete — stack deployed, commit `68a92b6`, tag `v0.2-infra`
**Phase 2 Status:** ✅ Complete — ingest Lambda deployed, Titan Embeddings v2 unblocked, commit `61ee46e`, tag `v0.3-ingest`
**Phase 3 Status:** ✅ Complete — query Lambda deployed, smoke test + live API gate passed, commit `c428b22`, tag `v0.4-query`
**Phase 4 Status:** ✅ Complete — three-panel analyst console deployed to S3, commit `5ca1f31`, tag `v0.5-frontend`
**Retrieval Tuning Status:** ✅ Complete — chunk size 500→175 words, curated knowledge files added, all target queries above 0.40, commits `6ae65e2` + `fe98ee9`, tag `v0.6-retrieval-tuning`
**Phase 5 Status:** ✅ Complete — CloudWatch dashboard + alarms, SNS alerts, CloudFront HTTPS (`https://d1r1qv7io7k8vk.cloudfront.net`), model migration to `us.anthropic.claude-haiku-4-5-20251001-v1:0`, commit `beae846`, tag `v0.7-observability`. Bedrock smoke test PASSED — both providers fully operational.
**Phase 6 Status:** ✅ Complete — full stack integration tested, all providers passing, commit `d665d53`, tag `v0.8-integration`

---

## What This Project Is

A serverless Retrieval-Augmented Generation (RAG) chatbot built on AWS, enhanced with a **Multi-Cloud Dual-Provider AI architecture**. Users ask plain English questions and get answers grounded in real documents — resume, project writeups, technical references. It uses a custom retrieval layer, not Bedrock Knowledge Bases. The live demo features a real-time UI toggle between AWS Bedrock (Claude) and Nebius AI Studio (Llama).

**Portfolio page:** http://jimmy-advanced-projects.s3-website-us-east-1.amazonaws.com  
**GitHub repo:** https://github.com/jhubb88/aws-rag-chatbot

---

## Project Goals

- Build a recruiter-friendly, advanced portfolio project on AWS
- Demonstrate end-to-end serverless architecture
- **Showcase Multi-Cloud API routing and AI provider abstraction (AWS Bedrock vs Nebius AI Studio)**
- Show responsible cost management
- Produce clean, readable infrastructure as code
- Keep monthly cost under $20
- Create a live demo with a working URL

---

## Architecture Decisions

### AWS Region
us-east-1 — best Bedrock model availability and lowest latency for demos.

### MVP Services

| Service | Purpose | Why Chosen |
|---|---|---|
| S3 | Store documents, embeddings index, frontend | Cheap, reliable, AWS-native |
| Lambda | Ingest and query compute | Serverless, zero cost when idle |
| API Gateway | Public HTTPS endpoint for query Lambda | Pay-per-request, essentially free at demo scale |
| Bedrock — Titan Embeddings v2 | Convert text to vectors | AWS-native, instantly approved, no third-party keys |
| **AWS Bedrock — Claude 3 Haiku** | **Generation Provider A** | Fast, enterprise-grade, requires specific XML prompting |
| **Nebius AI Studio — Llama 3.3-70B** | **Generation Provider B** | OpenAI-compatible, bypasses AWS auth blocks, uses Markdown prompting |
| CloudFormation | Infrastructure as code | Recruiter value, prevents drift |
| CloudWatch | Logging and dashboards | Required for observability |
| CloudTrail | Audit logging | Shows ops maturity |
| AWS Budgets | Cost alerts | $15 alert ✅, $18 alert ✅, $20 hard cap |
| AWS Systems Manager (SSM) | Store Nebius API Key | Secure secret management for external APIs |

### Excluded from MVP

| Service | Why Excluded | When to Add |
|---|---|---|
| Bedrock Knowledge Bases | Abstracts retrieval — custom layer shows more skill | Never for MVP |
| DynamoDB | Not needed until multi-turn memory | Phase 2 |
| Cognito | Auth not needed for portfolio demo | Phase 2 |
| CloudFront | Raw S3 URL fine for MVP | Phase 2 |
| Custom domain | Unnecessary complexity for MVP | Phase 2 |

### Retrieval Layer Decision
NOT using Bedrock Knowledge Bases. Using a custom retrieval layer:
- Documents chunked and embedded via **Titan Embeddings v2** (embeddings stay entirely on AWS)
- Embeddings stored as a vector index in S3
- Cosine similarity search runs inside the query Lambda
- Gives full control and isolates retrieval from generation

### Multi-Provider Generation Decision
The Query Lambda acts as a **Router**:
- The frontend passes `selected_engine` (bedrock or nebius)
- If bedrock: Lambda loads the Claude XML template and uses `boto3` to invoke Claude 3 Haiku
- If nebius: Lambda loads the Llama Markdown template, fetches the Nebius API key from SSM, and makes a standard HTTP request to Nebius AI Studio

### IaC Decision
CloudFormation included in MVP:
- Shows infrastructure maturity
- Prevents manual drift
- Reproducible deployments
- Significant recruiter value

---

## Known Issues and Blockers

### Bedrock Titan Embeddings v2 — ✅ UNBLOCKED (2026-04-14)
Titan Embeddings v2 confirmed live. Phase 2 ingest test gate passed end-to-end.
Real 1536-dim vectors confirmed from `amazon.titan-embed-text-v2:0`.

### Bedrock Generation — ✅ FULLY OPERATIONAL (2026-04-16)
Model migrated to `us.anthropic.claude-haiku-4-5-20251001-v1:0` (cross-region inference profile) during Phase 5.
Smoke test confirmed: `engine_used: bedrock` — real answer returned from Claude Haiku 4.5.
Both AI providers (Bedrock Claude Haiku 4.5 + Nebius Llama 3.3-70B) are now fully operational.

### Retrieval Quality — ✅ RESOLVED (2026-04-16)
Chunk size reduced from 500 to 175 words (overlap 50→20). Four curated knowledge files
added to `data/curated/` and ingested: `project_index.txt`, `project_summary.txt`,
`work_history.txt`, `work_history_index.txt`. Total index: 43 chunks.

**Final scores:**
- "What projects has Jimmy built?" — 0.4179 ✅ (was 0.2059)
- "What is the NTCIP simulator?" — 0.7268 ✅
- "What AWS services has Jimmy worked with?" — 0.4590 ✅
- "Where has Jimmy previously worked?" — 0.4047 ✅
- "What companies has Jimmy worked for?" — 0.4820 ✅

**Model migration:** ✅ Complete (Phase 5). Query Lambda uses `us.anthropic.claude-haiku-4-5-20251001-v1:0`.

### AWS CLI Profile (Recurring Issue)
`portfolio-user` profile is sometimes lost between WSL sessions. Always verify at session start:
```bash
aws configure list --profile portfolio-user
```

### GitHub Auth (Recurring Issue)
`gh` CLI requires a classic PAT (`ghp_`) with `repo` and `read:org` scopes. If repo creation fails, re-authenticate:
```bash
echo "YOUR_GHP_TOKEN" | gh auth login --hostname github.com --git-protocol https --with-token
```

---

## Build Phases

| Phase | Name | Status |
|---|---|---|
| Phase 0 | Planning and scaffolding | ✅ Complete |
| Phase 1 | CloudFormation infrastructure | ✅ Complete — stack live, commit `68a92b6`, tag `v0.2-infra` |
| Phase 2 | Document ingestion pipeline | ✅ Complete — Lambda deployed, commit `61ee46e`, tag `v0.3-ingest` |
| Phase 3 | Query pipeline (Router Logic) | ✅ Complete — query Lambda deployed, commit `c428b22`, tag `v0.4-query` |
| Phase 4 | Frontend (Dual-Provider UI) | ✅ Complete — analyst console live, commit `5ca1f31`, tag `v0.5-frontend` |
| Retrieval Tuning | Pre-Phase 5 quality fix | ✅ Complete — chunk size 175w, 4 curated files, all queries >0.40, tag `v0.6-retrieval-tuning` |
| Phase 5 | Observability | ✅ Complete — CloudWatch dashboard + alarms, SNS, CloudFront, model migration, tag `v0.7-observability` |
| Phase 6 | Integration testing | ✅ Complete — 9/9 tests passed, F1/F2 fixed, alarm tuned 10s→12s, tag `v0.8-integration` |
| Phase 7 | Portfolio polish + About modal | ⏳ Not started |
| Phase 8 | Phase 2 features | ⏳ Future |

---

## Retrieval Tuning — ✅ Complete (2026-04-16)

All target queries now score above 0.40. See Known Issues section for final scores and model migration note.

## Phase 6 — Integration Testing ✅ Complete (2026-04-16) | commit `d665d53` | tag `v0.8-integration`

All 9 test cases passed (11 checks including 7a/7b/7c sub-tests). Two issues found and fixed:

- **F1 (CRITICAL):** Bedrock engine dropdown showed "AWS Bedrock Claude (Coming Soon)" with `disabled` attribute. Fixed — now "AWS Bedrock — Claude Haiku 4.5", fully selectable, routes correctly to `selected_engine: bedrock`.
- **F2 (MINOR):** Missing `favicon.ico` caused HTTP 403 console error on every page load. Fixed with inline SVG data URI `<link rel="icon">` in `<head>` — no S3 upload required.
- **Alarm tuning:** `rag-chatbot-p95-duration-dev` threshold raised 10,000ms → 12,000ms based on Phase 6 cold start measurement. CloudFormation template updated and redeployed.

---

## Phase 7 — Portfolio Polish

1. **"About This Demo" modal** — triggered by an `ⓘ About This Demo` button at the bottom of the left sidebar, below Session History. Clicking opens a modal overlay (Option B style) with:
   - **What is RAG?** — plain English explainer (3-4 sentences, non-technical audience)
   - **How it's built** — bullet list: Titan Embeddings, Lambda cosine search, dual-provider router (Bedrock Claude + Nebius Llama), S3 + API Gateway
   - Close button (✕) top right of modal
   - Modal background: `rgba(0,0,0,0.6)` overlay, box `#1A1D24` with `#2E3340` border
2. Additional polish items TBD at phase start

---

## Phase 5 — Observability ✅ Complete (2026-04-16) | commit `beae846` | tag `v0.7-observability`

1. ✅ CloudWatch dashboard `RAG-Chatbot-Dashboard` — 4 widgets: invocations, errors, p95 duration, estimated cost
2. ✅ CloudWatch Alarms: `rag-chatbot-error-rate-dev` (>5%), `rag-chatbot-p95-duration-dev` (>12s — raised from 10s after Phase 6 cold start measurement: Nebius 4,986ms / Bedrock 4,281ms) — both OK
3. ✅ SNS topic `RAG-Chatbot-Alerts-dev` → jimmy.hubbard0813@gmail.com — subscription confirmed
4. ✅ CloudFront distribution `EN88LEBW14923` → `https://d1r1qv7io7k8vk.cloudfront.net` — Deployed, returns 200
5. ✅ Model migration: query Lambda updated to `us.anthropic.claude-haiku-4-5-20251001-v1:0` (cross-region inference profile)
6. ✅ Bedrock smoke test: PASSED — `engine_used: bedrock` confirmed. Both providers fully operational.

---

## Knowledge Base Documents

Source documents to be added to `data/documents/` before Phase 2:
- Resume (PDF)
- NTCIP Simulator project writeup
- Kapsch project summary
- Additional project writeups as needed

Note: `data/documents/` is in `.gitignore` — files will never be committed.

---

## Frontend UI Spec (Phase 4)

### Layout
Three-panel analyst console — not a chatbot, not a form.

- Left sidebar: document list, session history
- Top bar: app name, knowledge base status, **AI Engine Toggle Dropdown (Claude 3 Haiku vs Llama 3.1)**, clear session
- Center panel: chat / Q&A thread with processing states
- Right panel: retrieved chunks, source citations, relevance scores

### What Makes It an Advanced RAG Demo
- **Multi-Cloud Router:** Users can select the AI provider and compare answers/speed in real-time
- Retrieved source chunks always visible alongside the answer
- Relevance scores shown as percentage + filled bar
- Processing states animate in real time: Embedding query → Searching chunks → Routing to [Provider] → Generating answer
- Answer and evidence linked visually

### Visual Style

| Element | Value |
|---|---|
| Background | #111318 (deep charcoal) |
| Panels | #1A1D24 |
| Cards | #22262F with 1px #2E3340 border |
| Accent | #E8622A (warm orange) |
| Active/Success | #10B981 (green) |
| Text Primary | #F9FAFB |
| Text Secondary | #6B7280 |
| Font | System font stack |
| Feel | Premium SaaS product, not a portfolio toy |

**Stack:** Plain HTML + CSS + Vanilla JS — hosted on S3. CSS custom properties for theming.

---

## Cost Guardrails

- Hard cap: $20/month
- AWS Budgets: **$15 alert configured ✅**, **$18 alert configured ✅**
- Lambda and API Gateway: effectively free at portfolio traffic
- **Nebius AI Studio:** Pay-per-token (fractions of a cent per query)
- Bedrock is the primary cost driver for embeddings
- Kill switch: disable API Gateway if budget is at risk

---

## Git Workflow

- Branch: `main` is always stable
- Commit format: conventional commits (`feat:`, `fix:`, `docs:`, `chore:`)
- Milestone tags: `v0.1-planning` ✅, `v0.2-infra` ✅, `v0.3-ingest` ✅, `v0.4-query` ✅, `v0.5-frontend` ✅, `v0.6-retrieval-tuning` ✅
- Never commit: `.env`, credentials, `data/documents/`
- `data/curated/` is NOT gitignored — hand-authored knowledge files live here

---

## Session Rules

- Always use `--profile portfolio-user` for all AWS CLI commands
- Read last session wrap-up before starting
- Write session wrap-up to `sessions/YYYY-MM-DD-wrap.md` at end of every session
- Never end a session without a wrap-up file

---

## Local Development Path

```
/mnt/c/Users/jimmy/Desktop/Projects/rag-chatbot/
```
All CC work happens here. The old ClaudeCode path is retired.

---

## Who Does What

### Claude Code
- All Lambda function code (including Multi-Provider Router)
- CloudFormation template
- Frontend HTML/CSS/JS
- Test scripts
- Session wrap-ups

### Jimmy
- Review and approve before each commit
- Provide source documents
- Approve each test gate
- Make go/no-go decisions at milestones
