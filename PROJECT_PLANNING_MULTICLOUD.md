# RAG Knowledge Chatbot — Project Planning Document
### Multi-Cloud Edition | Last Updated: 2026-04-17
**Phase 1 Status:** ✅ Complete — stack deployed, commit `68a92b6`, tag `v0.2-infra`
**Phase 2 Status:** ✅ Complete — ingest Lambda deployed, Titan Embeddings v2 unblocked, commit `61ee46e`, tag `v0.3-ingest`
**Phase 3 Status:** ✅ Complete — query Lambda deployed, smoke test + live API gate passed, commit `c428b22`, tag `v0.4-query`
**Phase 4 Status:** ✅ Complete — three-panel analyst console deployed to S3, commit `5ca1f31`, tag `v0.5-frontend`
**Retrieval Tuning Status:** ✅ Complete — chunk size 500→175 words, curated knowledge files added, all target queries above 0.40, commits `6ae65e2` + `fe98ee9`, tag `v0.6-retrieval-tuning`
**Phase 5 Status:** ✅ Complete — CloudWatch dashboard + alarms, SNS alerts, CloudFront HTTPS (`https://d1r1qv7io7k8vk.cloudfront.net`), model migration to `us.anthropic.claude-haiku-4-5-20251001-v1:0`, commit `beae846`, tag `v0.7-observability`. Bedrock smoke test PASSED — both providers fully operational.
**Phase 6 Status:** ✅ Complete — full stack integration tested, all providers passing, commit `d665d53`, tag `v0.8-integration`
**Phase 7 Status:** ✅ Complete — empty state, top bar subtitle, contrast fix, About modal, commit `2fba0f4`, tag `v0.9-polish`
**Phase 8 Status:** ✅ Complete — 2-KB expansion shipped, EventBridge warm-up live, Bedrock default, commit `f872fc0`, tag `v1.0-multikb`

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

### WA Query Latency — ✅ RESOLVED (2026-04-17)
Phase 8 WA queries were hitting the API Gateway 29s hard timeout due to: 256MB Lambda memory (insufficient CPU for 58MB index), no index caching, and max_tokens=512 allowing verbose Nebius responses. Three fixes applied:
- QueryLambda MemorySize 256MB → 1024MB (CloudFormation + direct update)
- Module-level index caching in query Lambda (warm containers skip S3 load)
- max_tokens 512 → 256 on both Nebius and Bedrock paths (matched, enforced — confirmed via Nebius `completion_tokens` usage log)

Cold worst-case dropped from 32,279ms → 14,860ms (~54%). Warm queries now 5–8s. All queries pass under 29s limit.

**Not fully resolved:** 19–20s warm on some verbose queries is still high for portfolio demo quality. Step 7 performance gate will decide whether to ship as-is or invest in parked levers (see Phase 9 Candidates).

### Query Vocabulary Gap (Deferred — Phase 9)
Open-ended recruiter queries like "what should I look at first" score below the 0.40 retrieval threshold because the curated content uses comparative vocabulary (impressive, flagship, best) rather than entry-point vocabulary (start with, first thing). The right fix is query rewriting at the query Lambda layer, not additional content patches. Candidate for Phase 9.

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
| Phase 7 | Portfolio polish + About modal | ✅ Complete — empty state UX, subtitle, contrast, About modal, tag `v0.9-polish` |
| Phase 7.5 | Portfolio site card update (lives in portfolio-site repo) | ⏳ Not started |
| Phase 8 | Multi-KB expansion: AWS Well-Architected Framework | ✅ Complete — commit `f872fc0`, tag `v1.0-multikb` |

---

## Retrieval Tuning — ✅ Complete (2026-04-16)

All target queries now score above 0.40. See Known Issues section for final scores and model migration note.

## Phase 6 — Integration Testing ✅ Complete (2026-04-16) | commit `d665d53` | tag `v0.8-integration`

All 9 test cases passed (11 checks including 7a/7b/7c sub-tests). Two issues found and fixed:

- **F1 (CRITICAL):** Bedrock engine dropdown showed "AWS Bedrock Claude (Coming Soon)" with `disabled` attribute. Fixed — now "AWS Bedrock — Claude Haiku 4.5", fully selectable, routes correctly to `selected_engine: bedrock`.
- **F2 (MINOR):** Missing `favicon.ico` caused HTTP 403 console error on every page load. Fixed with inline SVG data URI `<link rel="icon">` in `<head>` — no S3 upload required.
- **Alarm tuning:** `rag-chatbot-p95-duration-dev` threshold raised 10,000ms → 12,000ms based on Phase 6 cold start measurement. CloudFormation template updated and redeployed.

---

## Phase 7 — Portfolio Polish ✅ Complete (2026-04-16) | commit `2fba0f4` | tag `v0.9-polish`

- **Item 1 — Empty state:** Replaced blank center panel with headline, subhead naming both providers, and 3 starter prompt cards. Clicking a card auto-submits. Clear Session empties the thread without restoring cards.
- **Item 2 — Top bar subtitle:** Added "Multi-cloud retrieval · AWS Bedrock + Nebius AI Studio" below the app name in secondary text.
- **Item 3 — Contrast:** `--color-text-secondary` bumped from `#6B7280` to `#9CA3AF` for WCAG AA compliance on dark background.
- **Item 4 — About This Demo modal:** Sidebar button opens overlay modal explaining RAG and the full tech stack. Closes on ✕, backdrop click, or Escape. Bug fixed: close listeners use document-level event delegation to avoid script-before-DOM timing issue.

---

## Phase 7.5 — Portfolio Site Card Update (Parking Lot)

**Lives in the `portfolio-site` repo, NOT `aws-rag-chatbot`. Separate commit, separate planning doc if applicable.**

Update the RAG Knowledge Chatbot card on the advanced projects page to match the FieldIQ card exactly:
- Replace both "COMING SOON" buttons with:
  - Orange **LIVE DEMO** button → `https://d1r1qv7io7k8vk.cloudfront.net`
  - Blue **ARCHITECTURE** button → destination TBD (options: GitHub repo README, dedicated architecture page, or About modal anchor inside the demo)
- Same button styling, spacing, and hover behavior as FieldIQ card
- No other changes to the card content (title, description stay as-is unless they need a refresh)

Do this AFTER Phase 7 is complete and the demo is fully polished — the LIVE DEMO button should land on the finished version.

---

## Phase 8 — Multi-KB Expansion: AWS Well-Architected Framework

### Why
The current knowledge base is exclusively about Jimmy. A recruiter exhausts the meaningful questions in 30 seconds, the dual-provider toggle has no reason to be exercised twice, and the strong retrieval scores aren't visibly impressive because the questions are too easy. Adding a second knowledge base — AWS Well-Architected Framework — gives the demo range, gives the dual-provider feature a real reason to exist (technical questions where Claude and Llama phrase answers differently is the most interesting comparison), and turns the retrieval layer into a feature recruiters can actually test.

### Scope
- Add the AWS Well-Architected Framework as a second knowledge base alongside Jimmy's background
- Implement cross-KB search (Option B): a single query searches across all KBs at once, results are returned merged with each chunk tagged by its source KB
- Visually distinguish chunks from different KBs in the right panel (badge + color accent)
- No KB toggle on/off — it's always-on cross-KB search

### Source Documents
AWS Well-Architected Framework PDFs (publicly available, free):
- Framework whitepaper (~80 pages)
- Six pillar whitepapers: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability
- Source: https://aws.amazon.com/architecture/well-architected/
- Total source: ~500–800 pages of dense technical content
- Files live in `data/well-architected/` (gitignored, same pattern as `data/documents/`)

### Architecture Decision: Single Combined Index
All chunks from all KBs go into a single S3 vector index. Each chunk carries a `source_kb` field:
- `jimmy_background` — existing 43 chunks from `data/documents/` and `data/curated/`
- `aws_well_architected` — new chunks from `data/well-architected/`

**Why single index over separate-per-KB:**
- One cosine similarity pass per query — faster, simpler code
- Merge logic is just sorting by score, no cross-index reconciliation
- The `source_kb` tag is what enables UI differentiation, not separate indexes
- If a future KB needs to be removed or refreshed, ingest pipeline filters by `source_kb` field

**Index size impact:** Current 43 chunks → estimated 800–1,200 chunks after Well-Architected ingest. Cosine search across 1,200 1,536-dim vectors in Lambda is still well under 100ms.

### Ingest Pipeline Changes
- `data/well-architected/` directory created, gitignored
- Ingest Lambda updated to accept a `source_kb` parameter when processing files
- Two ingest runs: one for `jimmy_background` (re-ingest existing), one for `aws_well_architected`
- Combined index written to `s3://rag-chatbot-{account}-dev/documents/index.json`
- Each chunk record includes: `chunk_id`, `text`, `embedding`, `source_doc`, `source_kb`

### Query Pipeline Changes
- Cosine search returns top-K across the entire combined index, no KB filtering
- Response includes `source_kb` for each retrieved chunk
- Generation prompt template (Claude XML and Llama Markdown both) updated to label each chunk with its source KB so the LLM knows when it's blending sources

### Frontend Changes
- Right panel: each retrieved chunk card shows a KB badge in the top-right corner
  - "Jimmy" badge — existing accent color (#E8622A orange)
  - "Well-Architected" badge — new accent color, suggested #4F8AE8 (blue, matches AWS branding) — final color TBD at build
- Empty state on center panel: replace 3 starter prompts with 6 (3 per KB) to immediately signal that two knowledge bases exist:
  - Jimmy: existing 3 prompts
  - Well-Architected: 3 new prompts, suggested:
    - "What are the six pillars of the Well-Architected Framework?"
    - "How does AWS recommend handling cost optimization for serverless workloads?"
    - "What does Well-Architected say about disaster recovery patterns?"
- Subtitle update: "Multi-cloud retrieval · 2 knowledge bases · AWS Bedrock + Nebius AI Studio"
- About modal updated: add "Knowledge Bases" section listing the two KBs and their contents

### Retrieval Quality Gate
After ingest, run cosine score test on representative queries from both KBs. Targets:
- Jimmy queries: maintain existing scores (>0.40 on all 5 from Retrieval Tuning phase)
- Well-Architected queries: >0.40 on each of the 3 starter prompts plus 2 random spot-checks
- If any query drops below threshold, investigate before declaring Phase 8 complete

### Cost Impact
- One-time ingest cost: ~800 additional chunks × Titan Embeddings v2 pricing ≈ negligible (well under $1)
- Ongoing query cost: same as current (one embedding per query, one generation call)
- No new AWS services added
- $20/mo budget cap unchanged

### What's NOT in Phase 8
- KB on/off toggle (always-on cross-KB is the demo)
- Per-KB query routing (one combined index, not multiple)
- Multi-turn memory / DynamoDB
- Cognito auth
- Custom domain
- Additional KBs beyond Well-Architected (those are Phase 9+)

### Phase 8 Progress

**Steps 1–4 — Ingest pipeline + source_kb tagging**
- Ingest Lambda and `rag_utils.py` shared library updated to accept and stamp `source_kb` on every chunk
- `scripts/ingest_bulk.py` added as permanent repo tool for corpus loads exceeding Lambda's 15-min ceiling
- `scripts/migrate_index_add_source_kb.py` ran once to tag all 43 original Jimmy chunks as `jimmy_background`
- 1,974 Well-Architected chunks ingested from 6 pillar PDFs (`framework.pdf` removed — umbrella doc duplicating pillar content); curated files `about_jimmy.txt` and `highlight_index.txt` added and ingested
- Total index: **2,027 chunks** (1,974 WA + 43 Jimmy background + 10 curated) at `documents/index.json` (~58MB)

**Step 5 — Frontend**
- Sidebar restructured into 2 KB groups (JIMMY'S BACKGROUND / AWS WELL-ARCHITECTED); SVG document icons via CSS `::before`; `.sidebar__kb-scroll` with `overflow-y: auto`
- Empty state: 6 grouped prompts (3 per KB) replacing original 3
- Top bar subtitle updated to "Multi-cloud retrieval · 2 knowledge bases · AWS Bedrock + Nebius AI Studio"
- Top bar status updated to "Knowledge Bases Online" (plural)
- KB badges deployed on source cards: orange `#E8622A` for Jimmy, blue `#4F8AE8` for Well-Architected
- About modal updated with Knowledge Bases section
- Bottom pill bar refreshed: 6 mixed-KB chips

**Step 6 — Retrieval quality gate: ✅ 10/10 PASS**

| Query | KB | Top Score |
|---|---|---|
| Why should I hire Jimmy? | jimmy_background | 0.5968 |
| What technologies does Jimmy know? | jimmy_background | 0.5870 |
| What is Jimmy's work experience? | jimmy_background | 0.6660 |
| What projects has Jimmy built? | jimmy_background | 0.4857 |
| What makes Jimmy a strong candidate? | jimmy_background | 0.5577 |
| What are the six pillars? | aws_well_architected | 0.8188 |
| How do I optimize cost on AWS? | aws_well_architected | 0.8367 |
| What is operational excellence? | aws_well_architected | 0.8149 |
| How do I improve security? | aws_well_architected | 0.6609 |
| What is the reliability pillar? | aws_well_architected | 0.8132 |

All queries above 0.40 threshold. Cross-KB routing clean — every query landed in correct KB. WA scores 0.66–0.84, Jimmy scores 0.49–0.67.

### Phase 8 Performance Fix

**Problem:** WA queries hit API Gateway 29s hard timeout. Root cause: 58MB index + 256MB Lambda memory (CPU bottleneck on S3 load + cosine over 2,027 vectors) + max_tokens=512 allowing verbose Nebius responses. Cold worst-case was 32,279ms — 3,279ms over the limit.

**Fix 1:** QueryLambda MemorySize 256MB → 1024MB (CloudFormation template + direct Lambda update)

**Fix 2:** Module-level index caching in `src/lambdas/query/handler.py` — `_index_cache` global populated on first invocation, reused on warm containers. Confirmed working: CloudWatch log showed "Using cached vector index" on subsequent calls.

**Fix 3:** max_tokens 512 → 256 on both Nebius and Bedrock generation paths (matched across providers). Ground truth confirmed via Nebius usage log: `completion_tokens=230, finish_reason=stop` at 1,155 chars — model answered naturally within the 256-token budget. Llama 3.3-70B effective ~5 chars/token on technical AWS content.

**Fix 4 (permanent observability):** Added to Nebius generation path in `_generate_nebius`:
- `[DEBUG] Nebius request body: {model, max_tokens, temperature}` — confirms serialized payload before send
- `[INFO] Nebius usage: prompt_tokens=N completion_tokens=N finish_reason=X` — Nebius ground truth after response
These logs are permanent. Do not remove in future changes.

**Result:** Cold worst-case 32,279ms → 14,860ms (~54% reduction). Warm queries 5–8s. All queries pass under 29s API GW limit.

**Step 7 — Performance gate: ✅ PASS.** EventBridge warm-up ping deployed (`rate(5 minutes)`, payload `{"warmup": true}`). Warmup branch confirmed: 2.56ms duration, no Bedrock/Nebius calls. All 8 warm queries under 12s:

| Query | Provider | Wall time | Lambda duration | completion_tokens | Chars |
|---|---|---|---|---|---|
| Why hire Jimmy? | Bedrock | 4.55s | ~4,171ms | — | 1,243 |
| Optimize cost on AWS? | Bedrock | 4.61s | ~4,175ms | — | 1,105 |
| Six pillars? | Bedrock | 3.05s | ~2,583ms | — | 616 |
| Operational excellence? | Bedrock | 4.71s | ~4,400ms | — | 1,413 |
| Why hire Jimmy? | Nebius | 4.16s | 3,799ms | 98 (stop) | 595 |
| Optimize cost on AWS? | Nebius | 8.62s | 8,261ms | 241 (stop) | 1,217 |
| Six pillars? | Nebius | 3.13s | 2,821ms | 64 (stop) | 307 |
| Operational excellence? | Nebius | 6.00s | 5,760ms | 98 (stop) | 602 |

Speed delta Bedrock (3–5s) vs Nebius (3–9s) is intentional — visible contrast makes the provider toggle meaningful as a demo feature.

**Step 8 — Deployment:**
- EventBridge rule `rag-chatbot-warmup-dev` created via CLI (CFN early-validation error on this stack is a recurring blocker — resources are correct in template for future full deploys)
- `lambda:AddPermission` granted to `events.amazonaws.com` (`EventBridgeWarmupPermission`)
- Frontend default switched to Bedrock (`selected` attribute on bedrock option)
- Query Lambda deployed with warmup branch + max_tokens=256 + index caching
- Frontend deployed to S3 + CloudFront invalidation `I27FTAYSL2YZ7ICI07W5TGD70V`
- Smoke test: CloudFront 200, bedrock selected in served HTML, both providers returning real answers with correct KB routing

---

## Phase 9 Candidates

### Parked Latency Levers (ranked by impact)

1. **EventBridge warm-up ping** — Scheduled rule pings query Lambda every 5 min to keep container warm. Eliminates cold starts entirely. Cost: ~$0.01/mo. No answer quality impact. Highest leverage per effort.
2. **Index format change: 58MB JSON → ~12MB NumPy binary** — Float32 embeddings stored as binary instead of JSON strings. Cuts S3 transfer + parse time significantly. Requires ingest pipeline change.
3. **Nebius Fast tier** — Higher per-token cost but faster streaming. Reduces Nebius generation wall time.
4. **Response streaming to frontend** — Cuts perceived latency without reducing total time. Requires API Gateway + Lambda streaming setup.

### Bedrock Completion Tokens Logging Symmetry
Nebius path logs `completion_tokens` and `finish_reason` via the permanent usage log. Bedrock path has no equivalent — CloudWatch shows Lambda duration but not token usage. Add a usage log to `_generate_bedrock` mirroring the Nebius pattern for consistent observability across both providers.

### Query Vocabulary Gap
Open-ended recruiter queries like "what should I look at first" score below 0.40 because curated content uses comparative vocabulary (impressive, flagship) rather than entry-point vocabulary (start with, look at first). Fix: query rewriting at the Lambda layer, not content patches.

---

## Phase 8 — Multi-KB Expansion ✅ Complete (2026-04-17) | commit `TBD` | tag `v1.0-multikb`

All 8 steps complete. See Phase 8 Progress and Phase 8 Performance Fix subsections above for full details.

**Final state:**
- 2,027-chunk combined index: `jimmy_background` (43 + curated) + `aws_well_architected` (1,974)
- EventBridge warm-up ping every 5 min — cold starts eliminated for demo use
- Bedrock selected by default on page load
- Warm baseline: Bedrock 3–5s, Nebius 3–9s
- CloudFront URL: `https://d1r1qv7io7k8vk.cloudfront.net`

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

**Phase 8 addition:** AWS Well-Architected Framework PDFs to `data/well-architected/` (also gitignored).

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
| Text Secondary | #9CA3AF (raised from #6B7280 — WCAG AA compliance) |
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
- Never commit: `.env`, credentials, `data/documents/`, `data/well-architected/`
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
