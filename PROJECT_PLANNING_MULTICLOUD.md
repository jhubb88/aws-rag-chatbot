# RAG Knowledge Chatbot — Project Planning Document
### Multi-Cloud Edition | Last Updated: 2026-04-19
**Phase 1 Status:** ✅ Complete — stack deployed, commit `68a92b6`, tag `v0.2-infra`
**Phase 2 Status:** ✅ Complete — ingest Lambda deployed, Titan Embeddings v2 unblocked, commit `61ee46e`, tag `v0.3-ingest`
**Phase 3 Status:** ✅ Complete — query Lambda deployed, smoke test + live API gate passed, commit `c428b22`, tag `v0.4-query`
**Phase 4 Status:** ✅ Complete — three-panel analyst console deployed to S3, commit `5ca1f31`, tag `v0.5-frontend`
**Retrieval Tuning Status:** ✅ Complete — chunk size 500→175 words, curated knowledge files added, all target queries above 0.40, commits `6ae65e2` + `fe98ee9`, tag `v0.6-retrieval-tuning`
**Phase 5 Status:** ✅ Complete — CloudWatch dashboard + alarms, SNS alerts, CloudFront HTTPS (`https://d1r1qv7io7k8vk.cloudfront.net`), model migration to `us.anthropic.claude-haiku-4-5-20251001-v1:0`, commit `beae846`, tag `v0.7-observability`. Bedrock smoke test PASSED — both providers fully operational.
**Phase 6 Status:** ✅ Complete — full stack integration tested, all providers passing, commit `d665d53`, tag `v0.8-integration`
**Phase 7 Status:** ✅ Complete — empty state, top bar subtitle, contrast fix, About modal, commit `2fba0f4`, tag `v0.9-polish`
**Phase 8 Status:** ✅ Complete — 2-KB expansion shipped, EventBridge warm-up live, Bedrock default, commit `f872fc0`, tag `v1.0-multikb`
**Phase 8.5 Status:** ✅ Complete — mobile responsive layout, iPhone Safari bugs resolved, commit `ba601b5` (no new tag — v1.0-multikb stands)

---

## What This Project Is

A serverless Retrieval-Augmented Generation (RAG) chatbot built on AWS, enhanced with a **Multi-Cloud Dual-Provider AI architecture**. Users ask plain English questions and get answers grounded in real documents — resume, project writeups, technical references. It uses a custom retrieval layer, not Bedrock Knowledge Bases. The live demo features a real-time UI toggle between AWS Bedrock (Claude) and SambaNova (Llama).

**Portfolio page:** http://jimmy-advanced-projects.s3-website-us-east-1.amazonaws.com  
**GitHub repo:** https://github.com/jhubb88/aws-rag-chatbot

---

## Project Goals

- Build a recruiter-friendly, advanced portfolio project on AWS
- Demonstrate end-to-end serverless architecture
- **Showcase Multi-Cloud API routing and AI provider abstraction (AWS Bedrock vs SambaNova)**
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
| **SambaNova — Llama 3.3-70B** | **Generation Provider B** | OpenAI-compatible, sub-1s TTFT, free tier 240 RPM/48K req/day |
| CloudFormation | Infrastructure as code | Recruiter value, prevents drift |
| CloudWatch | Logging and dashboards | Required for observability |
| CloudTrail | Audit logging | Shows ops maturity |
| AWS Budgets | Cost alerts | $15 alert ✅, $18 alert ✅, $20 hard cap |
| AWS Systems Manager (SSM) | Store SambaNova API Key | Secure secret management for external APIs |

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
- The frontend passes `selected_engine` (bedrock or sambanova)
- If bedrock: Lambda loads the Claude XML template and uses `boto3` to invoke Claude 3 Haiku
- If sambanova: Lambda loads the Llama Markdown template, fetches the SambaNova API key from SSM, and makes a standard HTTP request to SambaNova

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
Both AI providers (Bedrock Claude Haiku 4.5 + SambaNova Llama 3.3-70B) are now fully operational.

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

### Horizontal Scroll on Mobile — ✅ Resolved (Phase 8.6, 2026-04-19)
**Symptom:** Tapping the textarea on iPhone Safari zoomed the viewport horizontally; zoom persisted after keyboard dismiss, leaving horizontal scroll until user pinch-zoomed out.
**Root cause:** iOS Safari auto-zooms any `<input>`/`<textarea>`/`<select>` with `font-size < 16px` on focus. The `.query-input` textarea was `14px` and the `.mob-engine-row select` was `12px`.
**Fix:** Added `font-size: 16px` overrides for both elements inside the existing `@media (max-width: 767px)` block in `frontend/index.html`. Desktop sizes unchanged.
**Reproduced on:** real iPhone (Jimmy, 2026-04-19). Not user-scalable=no — accessibility-safe fix.
**Commit:** see `fix(mobile): prevent iOS Safari input zoom causing horizontal scroll`

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
| Phase 7.5 | Portfolio site card update (lives in advanced-projects repo) | ✅ Complete — commit `a863579` in advanced-projects |
| Phase 8 | Multi-KB expansion: AWS Well-Architected Framework | ✅ Complete — commit `f872fc0`, tag `v1.0-multikb` |
| Phase 8.5 | Mobile responsive layout (iPhone Safari fix) | ✅ Complete — slide-over panels, backdrop dismiss, clear session, placeholder optimization |

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

## Phase 7.5 — Portfolio Site Card Update ✅ Complete (2026-04-17) | commit `a863579` (advanced-projects repo)

**Lives in the `advanced-projects` repo, NOT `aws-rag-chatbot`.**

Updated the RAG Knowledge Chatbot card on `https://d2uisqfxjzeo6a.cloudfront.net` to match the FieldIQ card pattern exactly:
- Orange **LIVE DEMO** button → `https://d1r1qv7io7k8vk.cloudfront.net` (`target="_blank" rel="noopener"`)
- Blue **ARCHITECTURE** button → opens 6-section RAG architecture modal

Architecture modal sections: What It Is, Tech Stack, Data Layer, Key Decisions, Structure, What I Learned. Same `modal-overlay` / `modal-panel` structure, close button, backdrop dismiss, and Escape key handling as FieldIQ modal. No shared JS state — RAG modal functions are fully independent (`openRAGModal`, `closeRAGModal`, `handleRAGOverlayClick`, `handleRAGEscKey`).

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

## Phase 8.5 — Mobile Responsive Layout ✅ Complete (2026-04-17) | commit `ba601b5`

**Why:** The three-panel desktop layout was broken on iPhone Safari — center panel invisible, panels overlapping, text clipped. Added a `@media (max-width: 767px)` breakpoint with slide-over overlays for sidebar and right panel, matching the Claude.ai panel pattern.

**What shipped:**
- `body` uses `100dvh` for accurate iOS viewport height
- Sidebar + right panel become `position: fixed` slide-overs (`transform: translateX`), toggled by hamburger and info buttons in the top bar
- `mob-backdrop` div (z-index 150) dims content and dismisses overlays on tap
- Mobile engine dropdown in `.input-area` (bidirectionally synced with desktop dropdown)
- "Clear Session" button in sidebar for mobile
- Placeholder swap: JS swaps textarea placeholder at load + resize (≤767px: "Ask about Jimmy or AWS...", >767px: full desktop text)

**Bugs found and fixed across iterations:**

| Bug | Root cause | Fix |
|---|---|---|
| Backdrop tap ignored on iOS | `mob-backdrop` div was defined AFTER `</script>` — `getElementById` returned null at setup, `backdrop.addEventListener` never ran | Moved `mob-backdrop` div to before `<script>` tag |
| Mobile "Clear Session" did nothing | Same null throw caused `clearSidebar.addEventListener` to never execute (it came after the throw in `setupMobileOverlays`) | Fixed by moving backdrop element; `clearSession()` also updated to restore empty state HTML + re-wire prompt buttons |
| Portrait scroll hid input area | `position: sticky; bottom: 0` on `.input-area` inside a non-scrolling flex column → iOS Safari quirk | Removed sticky override; flex layout already pins input at the bottom |
| Input placeholder clipped on load | Long placeholder wrapped to two lines inside a 42px single-row textarea | JS placeholder swap at load + resize |

**Files changed:** `frontend/index.html` only.

---

## SambaNova Provider Swap ✅ Complete (2026-04-19) | commit `<hash-pending>`

**Decision rationale:** Nebius Base tier (Llama 3.3-70B) was the latency bottleneck — warm 3–9s, first-call-after-idle 5.5s median despite warmup pings. The p95 alarm (`rag-chatbot-p95-duration-dev`) was firing repeatedly, confirmed on 2026-04-19 12:30 UTC: the 20,299ms breach was 100% Nebius warmup timeout (20s read timeout), zero Bedrock involvement. Alarm log: `[WARNING] Nebius warmup failed: The read operation timed out`.

**Provider selected: SambaNova.** Model: `Meta-Llama-3.3-70B-Instruct` (exact casing required — Nebius used `meta-llama/Llama-3.3-70B-Instruct`, different casing and org prefix). Endpoint: `https://api.sambanova.ai/v1/chat/completions`. Auth: bearer token in SSM at `/rag-chatbot/sambanova-api-key`.

**Groq rejected:** 12K TPM free tier cap would trigger 429s during a recruiter demo at ~1,050 tokens/query average (~11 queries before rate limit). Not viable for demo use.

**Cost delta:** Nebius Base $0.13/$0.40 per M tokens → SambaNova $0.60/$1.20. Monthly impact ~$0.30–0.50 at demo volume, within $20 cap. Free tier: 240 RPM, 48K requests/day, no credit card required.

**Dormant Nebius key:** `/rag-chatbot/nebius-api-key` left in SSM as rollback asset. Do not delete before 2026-05-19.

**Warm performance (Step 7 validation, 2026-04-19):**

| Query | Engine | Wall time | Lambda duration | completion_tokens | finish_reason |
|---|---|---|---|---|---|
| Why should I hire Jimmy? | Bedrock | 8,311ms | 8,034ms | 274 output | end_turn |
| Why should I hire Jimmy? | SambaNova | 4,845ms | 4,439ms | 97 | stop |
| What is the NTCIP simulator? | SambaNova | 3,582ms | 3,095ms | 149 | stop |
| Six pillars of Well-Architected? | SambaNova | 2,784ms | 2,517ms | 31 | stop |

**First-call-after-idle (Steps 8 + 8b, with warmup pings running):**

| Provider | Wall time | Lambda duration |
|---|---|---|
| SambaNova | 5,656ms | 5,259ms |
| Bedrock | 4,858ms | 4,438ms |

SambaNova warm: 2.5–4.4s Lambda — **clear improvement over Nebius 3–9s**. First-call matches Nebius post-warmup median (5.52s) — warmup ping equally effective for both providers.

**Warmup ping:** Cycle 1 post-deploy returned HTTP 500 (transient — SambaNova free-tier spin-up on first hit). Cycle 2: `duration_ms=631 status=ok`. 631ms vs Nebius 2,146ms on a healthy cycle; Nebius was timing out at 20s on unhealthy cycles. No more p95 alarm breaches expected from warmup path.

**Answer quality finding:** SambaNova handles technical/factual queries well (NTCIP, six pillars, AWS services). Biographical synthesis (Why hire Jimmy?) defaults to category descriptions rather than proper nouns (Air Force appears; Kapsch, Secret clearance, specific AWS services do not) despite two system prompt instruction attempts. Retrieval confirmed correct — all 5 top chunks from `about_jimmy.txt`, which contains all specific facts. Structural ceiling of Llama 3.3-70B for biographical tasks. **Bedrock stays default provider permanently.** SambaNova's value is speed on factual queries; the provider toggle remains meaningful as a speed-vs-depth tradeoff demo.

**System prompt change:** One instruction added: *"When answering questions about Jimmy's background, cite specific proper nouns from the context — employer names, specific technologies, certifications, and credentials by name — do not paraphrase them into generic descriptions."* Partially effective (Air Force name appeared), not sufficient to force Kapsch/clearance/AWS specifics. This is the final system prompt iteration per hard gate — no further tuning.

**KB re-ingest (Step 8.5):** `data/curated/about_jimmy.txt` and `data/curated/project_summary.txt` updated — Nebius → SambaNova references. Re-ingest revealed an ingest pipeline path normalization bug: curated files were indexed under `curated/<name>` prefix but re-ingested as `<name>`, so old stale entries were not removed. Fixed by manual index surgery (filter + re-upload). Index restored to 2,027 chunks. Backup at `documents/index.json.bak-sambanova-swap`. `INDEX_CACHE_VERSION=1` Lambda env var added to force container cache invalidation after re-ingest — bump this value any time re-ingest is run.

---

## Phase 9 Candidates

### Parked Latency Levers (ranked by impact)

~~1. **EventBridge warm-up ping**~~ — ✅ Complete (2026-04-18, commit `b36c69c`). See Nebius Warmup Ping below.

1. **Index format change: 58MB JSON → ~12MB NumPy binary** — Float32 embeddings stored as binary instead of JSON strings. Cuts S3 transfer + parse time significantly. Requires ingest pipeline change.
2. **Response streaming to frontend** — Cuts perceived latency without reducing total time. Requires API Gateway + Lambda streaming setup.

### Bedrock Completion Tokens Logging Symmetry ✅ Complete (2026-04-17) | commit `92fc076`
Added `[DEBUG] Bedrock request: model=... max_tokens=256` before `invoke_model` and `[INFO] Bedrock usage: input_tokens=N output_tokens=N stop_reason=X` after response parse. Uses Bedrock-native field names (`input_tokens` / `output_tokens` / `stop_reason`) matching Anthropic's response shape. Confirmed in CloudWatch: `input_tokens=926 output_tokens=255 stop_reason=end_turn` on first post-deploy query.

### Bedrock Prompt Tuning + Asymmetric max_tokens ✅ Complete (2026-04-17) | commit `4768755`
**Problem:** Bedrock Claude was producing section-heavy markdown answers that truncated at the 256-token ceiling. 3 of 4 test queries returned `stop_reason=max_tokens`. Nebius finished naturally at 256 because its system prompt already included "Be concise and accurate."

**Fix 1 — Prompt tuning:** Added concision instruction to the Bedrock user message: *"Be concise. Answer in 2-3 short paragraphs. Use markdown headers only if the question genuinely requires distinct sections."* Kept role definition, dual-KB binding, and context injection unchanged.

**Fix 2 — Safety-net cap raise:** Bedrock `max_tokens` raised from 256 → 384. Nebius left at 256 (already producing natural stops). Providers are now intentionally asymmetric: Bedrock 384, Nebius 256.

**Validation (4-query test post-deploy):**

| Query | output_tokens | stop_reason | Wall time |
|---|---|---|---|
| What are the six pillars? | 146 | end_turn | 7.1s |
| What is the NTCIP simulator? | 221 | end_turn | 8.5s |
| Why should I hire Jimmy? | 197 | end_turn | 8.1s |
| How do I optimize cost on AWS? | 255 | end_turn | 8.1s |

4/4 end_turn. Zero max_tokens hits at 384. Wall times above were cold containers post-deploy.

**Confirmed warm baseline (sequential test after EventBridge warm-up, commit `4768755`):**

| Query | output_tokens | stop_reason | Wall time (warm) |
|---|---|---|---|
| Why should I hire Jimmy? | 231 | end_turn | 4.3s |
| What is the NTCIP simulator? | 275 | end_turn | 4.9s |
| How do I optimize cost on AWS? | 222 | end_turn | 4.0s |
| What are the six pillars? | 131 | end_turn | 2.8s |

Bedrock warm baseline: **2.8–4.9s**. Nebius warm baseline: **3–9s** (unchanged from Phase 8). Frontend end-to-end test (8 queries, both providers via CloudFront): all pass, no truncation, no errors.

### SambaNova/Llama System Prompt Tuning ✅ Complete (2026-04-17) | commit `25d4c7d`
**Problem:** Post-content-rewrite testing revealed two Llama answer quality issues (originally on Nebius, prompt carries over to SambaNova — same model): (1) Llama was leading answers with "According to the context" or "Based on the provided information" — a robotic tic that reads poorly in a recruiter-facing demo. (2) Answers closely echoed the source text verbatim rather than synthesizing across chunks.

**Fix — two instructions added to SambaNova system prompt:**
1. *"Never say 'according to the context', 'based on the provided information', or similar phrases — answer directly as if the information is your own knowledge."*
2. *"Write in your own words and voice, combining facts from multiple context chunks into a flowing answer. Do not structure your answer as bullet points or sectioned lists unless the question genuinely requires them."*

Note: "Do not closely paraphrase the source text" was explicitly rejected — risks Llama dropping specific facts (8 years, Air Force, Staff Engineer level) that feel like direct quotes but are factual grounding we want preserved.

Both providers now have instruction-tuned system prompts. Bedrock tuned for concision and structure (2026-04-17, commit `4768755`); SambaNova (Llama) tuned for natural voice and synthesis (2026-04-17, commit `25d4c7d`).

**Validation (2 queries post-deploy, warm container):**

| Query | completion_tokens | finish_reason | Wall time | Tic present? |
|---|---|---|---|---|
| Why should I hire Jimmy? | 113 | stop | 8.3s | No ✅ |
| What is the NTCIP simulator? | 143 | stop | 4.6s | No ✅ |

"According to the context" tic gone. Both answers read as natural prose. No regression on NTCIP query.

### Curated Content Rewrite Pattern — Phase 9 Candidate
**Observation:** The "Why hire Jimmy?" section in `data/curated/about_jimmy.txt` was rewritten from a generic two-paragraph summary to a focused 3-sentence pitch. The new text produced immediately better Nebius answers — Nebius echoed the source closely, but the source was now good enough that close echo = good answer.

**Pattern:** Source structure drives answer structure. When Nebius retrieves a well-structured, recruiter-facing chunk, it produces recruiter-facing output without needing synthesis instructions. Prompt tuning helps but content quality is the upstream lever.

**Phase 9 candidate:** Audit remaining `jimmy_background` sections in `data/curated/about_jimmy.txt` using the same pattern — rewrite sections that produce mediocre answers by improving the source text, not just tuning prompts. High-leverage sections to review: "How Jimmy Works With Code and AI Tools", "Role Interests and Career Goals", "Which Project Is Most Impressive".

### Query Vocabulary Gap
Open-ended recruiter queries like "what should I look at first" score below 0.40 because curated content uses comparative vocabulary (impressive, flagship) rather than entry-point vocabulary (start with, look at first). Fix: query rewriting at the Lambda layer, not content patches.

### Ingest Pipeline Path Normalization — Phase 9 Candidate
Curated files have inconsistent `source_file` prefixes in the index (`curated/<name>` vs `<name>`), causing re-ingest replacement to miss existing entries — old stale chunks remain and new chunks are added on top. Incident: 2026-04-19 SambaNova swap re-ingest produced 2,036 chunks instead of 2,027; required manual index surgery. Fix: normalize all `source_file` values to a single convention (basename only, no path prefix) in the ingest Lambda before write. Low priority — only triggers on curated file re-ingest.

### Curated Content: SambaNova Swap Narrative — Phase 9 Candidate
Rewrite the Nebius→SambaNova swap narrative in `data/curated/about_jimmy.txt` with the actual decision rationale (latency alarm breaches, 20s timeouts, SambaNova free-tier selection, Groq rejection) rather than a mechanical name swap. Follows the Curated Content Rewrite Pattern from Phase 9. Source quality drives answer quality — a well-structured rationale chunk would let the model produce a recruiter-facing narrative about provider decisions without prompt gymnastics.

### Bedrock Graceful Rate-Limit Handling — Phase 10 Candidate
`_generate_bedrock` returns generic 500 on `ThrottlingException`. Add the same sentinel-value pattern used for SambaNova: catch `ThrottlingException` specifically, return `(None, "bedrock_throttled")`, and have `lambda_handler` return HTTP 200 with `{"error_type": "rate_limit", "message": "Bedrock is temporarily throttled. Try SambaNova instead, or retry in a moment."}`. Low priority — Bedrock rarely throttles at portfolio demo volume. Front-end `appendRateLimitCard` already handles `error_type: "rate_limit"` generically, so no frontend change required.

### Retrieval Miss on Projects List Query — Diagnosis (2026-04-18)
**Status: ✅ Resolved 2026-04-18, commit `b30b6ab` — TOP_K raised 3→5. See "Retrieval Fix + Content Drift" below.**

**Symptom:** Both providers return incomplete answers to "What projects has Jimmy built?" — Bedrock hedges with "context doesn't provide details about other specific projects," Nebius with "no other projects are mentioned in the provided context."

**Retrieval data (query: "What projects has Jimmy built?", top_k=3, 2,027-chunk index):**

| Rank | Source | Score |
|---|---|---|
| 1 | highlight_index.txt | 0.4857 |
| 2 | about_jimmy.txt — Experience/Seniority | 0.4547 |
| 3 | about_jimmy.txt — hiring pitch | 0.4508 |
| 5 | project_index.txt (345 chars, all 7 projects) | 0.4179 |
| 7 | project_summary.txt (1,283 chars, all 7 projects) | 0.3858 |
| 8 | about_jimmy.txt — projects section (contaminated RAG preamble) | 0.3601 |

**Root cause:** top_k=3 is too aggressive for a 2,027-chunk index with overlapping narrative content. The projects-list content IS present in the index — three chunks contain it, the cleanest one (project_index.txt, position 39) scored 0.4179 and ranked 5th overall, 0.0329 below the rank-3 cutoff. Narrative chunks about Jimmy's career outrank enumeration chunks because the query shares vocabulary with career accomplishment language. The retrieval ordering is correct; the cutoff is too tight.

**Proposed fix:** Raise top_k from 3 to 5 in the query Lambda. This places project_index.txt (0.4179) and project_summary.txt (0.3858) into the generator's context alongside the current top-3, giving both providers the full projects list.

**Secondary observation:** Shorter dense enumeration chunks (project_index.txt, 345 chars, score 0.4179) outscored longer verbose versions (project_summary.txt, 1,283 chars, score 0.3858) on this list-style query. Useful signal for curated content structure decisions.

### Retrieval Fix + Content Drift ✅ Complete (2026-04-18) | commits `b30b6ab`, `f0dd24d`

**b30b6ab — TOP_K 3→5 in `src/lambdas/query/handler.py`**

Root cause: `project_index.txt` (clean 7-project enumeration, 345 chars) scored 0.4179 and ranked 5th of 2,027 chunks — excluded by `top_k=3`. Narrative career chunks outranked the clean list by 0.05–0.07 points (`highlight_index` 0.4857, Experience/Seniority 0.4547) because they share vocabulary with "built / projects / Jimmy." The retrieval ordering was correct; the cutoff was too tight for a 2,027-chunk index. Fix: raise `top_k` to 5 so the retrieval window includes the list chunk. Both providers now correctly name all 7 projects on "What projects has Jimmy built?"

**f0dd24d — Committed working tree drift on `data/curated/about_jimmy.txt`**

The "Why hire Jimmy" 3-sentence pitch rewrite from 2026-04-17 was live in the ingested index but never committed to git. HEAD was stale relative to production. No behavior change — purely git hygiene.

### Provider Warmup Ping ✅ Complete (2026-04-18, Nebius) | Updated 2026-04-19 (SambaNova) | commit `b36c69c`

**Problem:** External provider first-call-after-idle penalty. The Lambda container stayed warm via the existing EventBridge ping (2–3ms early return), but the inference endpoint itself was going cold between real user queries. The container being warm doesn't mean the external provider's endpoint is warm.

**Fix:** Synthetic provider call added to the warmup branch in `src/lambdas/query/handler.py` via `_warmup_sambanova()` (originally `_warmup_nebius()`, renamed 2026-04-19 during SambaNova swap), called on every EventBridge warmup cycle (every 5 min). Payload: `model=Meta-Llama-3.3-70B-Instruct`, `messages=[{role:user, content:ping}]`, `max_tokens=1`, `temperature=0`. Wrapped in `try/except`, 20s timeout (lowered to 3s on 2026-04-19 — see Warmup Hardening section), never fails the Lambda invocation. Bedrock has no equivalent penalty; no Bedrock warmup call was added.

**Before/After (Lambda REPORT duration, first-call-after-idle):**

| Metric | Pre-warmup (n=10, CloudWatch historical) | Post-warmup (n=3, controlled test) |
|--------|------------------------------------------|-------------------------------------|
| Min | 3.10s | 4.80s |
| Median | 8.25s | — |
| Avg | — | 5.52s |
| Max | 14.86s | 6.26s |
| Spread | 11.76s | 1.46s |

The "10–18s baseline" referenced in earlier session notes was an eyeball estimate, not real data. True pre-warmup baseline from CloudWatch REPORT durations (10 qualifying invocations over 7 days): min 3.10s, median 8.25s, max 14.86s.

Key improvement: variance collapsed from 11.76s to 1.46s. The 10–15s tail is gone — every measured first-call post-warmup was between 4.8s and 6.3s. The warmup ping reduces first-call median by ~33%, worst-case by ~58%, collapses variance from 11.76s to 1.46s. User-perceived wall time on CloudFront is roughly Lambda REPORT + 500–1500ms for edge hops and frontend render, so real first-call UX was approximately 6–8s. Updated 2026-04-19: index cache priming in the warmup branch (Warmup Hardening, commit `87e1e21`) eliminated the ~6s S3-load penalty on first touch — first-call Lambda is now ~4.7s, wall time ~5–6s.

Caveat: one pre-warmup result at 3.10s suggests Nebius's endpoint is occasionally warm from other customer traffic. The ping doesn't create warmth that didn't exist — it makes reliable what was previously lucky.

**Cost:** ~8,640 pings/month × ~11 tokens/ping ≈ 95K tokens/month. Well under $0.05/month at Nebius pricing.

**Ground truth logging (permanent — do not remove):**
- `[INFO] SambaNova warmup: duration_ms=X status=ok` on success
- `[WARNING] SambaNova warmup failed: <error>` on failure (includes HTTP status code for HTTPError)

### Nebius Provider Swap → SambaNova ✅ Complete (2026-04-19)

Decision made 2026-04-18, implemented 2026-04-19. See **SambaNova Provider Swap** section below for full results, metrics, and decision rationale.

---

## Phase 8 — Multi-KB Expansion ✅ Complete (2026-04-17) | commit `TBD` | tag `v1.0-multikb`

All 8 steps complete. See Phase 8 Progress and Phase 8 Performance Fix subsections above for full details.

**Final state:**
- 2,027-chunk combined index: `jimmy_background` (43 + curated) + `aws_well_architected` (1,974)
- EventBridge warm-up ping every 5 min — cold starts eliminated for demo use
- Bedrock selected by default on page load
- Warm baseline at v1.0: Bedrock 3–5s, Nebius 3–9s (Nebius replaced by SambaNova 2026-04-19 — see SambaNova Provider Swap section)
- CloudFront URL: `https://d1r1qv7io7k8vk.cloudfront.net`

---

## Post-v1.0 Bug Fixes (2026-04-17)

Two silent frontend bugs found and fixed after v1.0 shipped. No new phase number — these are follow-up polish.

### Fix 1 — Center starter prompts threw silent ReferenceError (commit `e14b447`)
`wireEmptyStatePrompts()` called `handleSubmit()` which was never defined. Result: tapping a center prompt filled the input field but the query never fired and the empty-state DOM was never removed. User had to press Ask manually (two-tap flow). The bottom pill row called `submitQuery()` directly and worked correctly — one-tap flow. Fixed by replacing `handleSubmit()` with `submitQuery(btn.textContent)` plus `isProcessing` guard and `autoResize()` call, matching the chip handler exactly. Bug was present since Phase 7.

### Fix 2 — Clear Session mid-flight left `isProcessing` stuck true (commit `04e88d6`)
`clearSession()` reset the DOM but did not reset `isProcessing` or abort the in-flight fetch. Any chip or starter prompt tap during the ~2.6s animation + fetch window was silently dropped by `if (isProcessing) return`. Tapping Clear then tapping a new prompt appeared to do nothing for 3–4 taps until the original fetch resolved. Fixed with AbortController pattern: `submitQuery()` creates a controller per call and passes `signal` to `fetch()`; `AbortError` is caught and returns silently. `clearSession()` calls `abort()`, sets `isProcessing = false`, re-enables the submit button, and nulls the controller reference before restoring the DOM.

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
- **SambaNova:** Pay-per-token ($0.60/$1.20 per M input/output tokens — ~$0.30–0.50/month at demo volume)
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

## Warmup Hardening ✅ Complete (2026-04-19) | commit `87e1e21`

### Root Cause (discovered via CloudWatch diagnosis, 2026-04-19)

**Problem 1 — Index cache not primed by warmup:** The warmup branch short-circuited before `_load_index()` was called. Every Lambda container spawned by a warmup ping had `_index_cache = None`. The first real user query on that container paid a ~6s S3 load penalty (58MB JSON parse). Warmup kept the container alive but did not populate the index. Measured: first-touch cold was 8.3s Lambda before fix; `[INFO] Loaded vector index from S3: 2027 chunks` confirmed in that invocation's logs.

**Problem 2 — SambaNova TLS hang at 20s timeout:** SambaNova's endpoint was hanging at the TCP/TLS layer on ~50% of warmup cycles (alternating with fast 429s from rate-limit exhaustion). With `timeout=20`, these warmup invocations produced ~20s REPORT durations — breaching the 12s p95 alarm threshold. Log evidence: `[WARNING] SambaNova warmup failed: <urlopen error _ssl.c:993: The handshake operation timed out>`.

### Fixes (`src/lambdas/query/handler.py`, warmup branch)

**Fix 1 — Index cache priming:** Added `_load_index()` call in the warmup branch, before `_warmup_sambanova()`. Populates `_index_cache` on the container serving the warmup ping. Subsequent warmup pings on the same container hit the cache instantly. New log markers: `[INFO] Warmup: index cache primed (2027 chunks)` on success, `[WARNING] Warmup: index load failed, first user query will pay cold cost` on failure.

**Fix 2 — 3s SambaNova timeout:** Lowered `urllib.request.urlopen(req, timeout=20)` → `timeout=3`. Catches TLS hangs, slow 429s, and any TCP-layer stall. A warmup ping that can't respond in 3s provides no endpoint-warming value.

### Measured Results (4-cycle post-deploy CloudWatch window)

| Warmup failure type | Pre-fix REPORT | Post-fix REPORT |
|---|---|---|
| TLS handshake timeout | ~20,000ms | ~3,079ms |
| Cold container + 429 | ~18,000ms | ~3,976ms |
| Fast 429 (warm, cached index) | ~250ms | ~250ms |

No warmup exceeded 12s. p95 alarm remained OK throughout.

**First-touch cold (incognito browser test):** 4.7s Lambda REPORT, `[INFO] Using cached vector index: 2027 chunks` confirmed — cache hit, no S3 load. Down from 8.3s before fix.

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
