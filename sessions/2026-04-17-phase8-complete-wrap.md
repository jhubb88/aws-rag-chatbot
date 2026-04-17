# Session Wrap-Up — 2026-04-17 (Phase 8 Complete)

## Phase 8 Complete

Phase 8 (Multi-KB Expansion: AWS Well-Architected Framework) is fully shipped.

Tag: `v1.0-multikb`

---

## What Was Completed This Session

### Step 7 — Performance Gate ✅ PASS

EventBridge warm-up ping deployed: `rate(5 minutes)`, payload `{"warmup": true}`.

Warmup branch confirmed in CloudWatch:
- `[INFO] Warm-up ping received — container is warm`
- Duration: 2.56ms, Init Duration: 815ms (cold container spun up by EventBridge, now warm)
- No `[DEBUG] Nebius request body` on warmup invocations — Bedrock/Nebius paths never touched

Final warm baseline (8-query test suite):

| Query | Provider | Wall | Lambda | completion_tokens | Chars |
|---|---|---|---|---|---|
| Why hire Jimmy? | Bedrock | 4.55s | ~4,171ms | — | 1,243 |
| Optimize cost? | Bedrock | 4.61s | ~4,175ms | — | 1,105 |
| Six pillars? | Bedrock | 3.05s | ~2,583ms | — | 616 |
| Op excellence? | Bedrock | 4.71s | ~4,400ms | — | 1,413 |
| Why hire Jimmy? | Nebius | 4.16s | 3,799ms | 98 (stop) | 595 |
| Optimize cost? | Nebius | 8.62s | 8,261ms | 241 (stop) | 1,217 |
| Six pillars? | Nebius | 3.13s | 2,821ms | 64 (stop) | 307 |
| Op excellence? | Nebius | 6.00s | 5,760ms | 98 (stop) | 602 |

### Step 8 — Deployment

**Change 1 — EventBridge warm-up:**
- Rule `rag-chatbot-warmup-dev` created via CLI (`events:PutRule`, `events:PutTargets`)
- Lambda permission granted (`lambda:AddPermission` to `events.amazonaws.com`)
- IAM gap resolved: added `events:PutRule/PutTargets/DescribeRule/ListTargetsByRule/DeleteRule/RemoveTargets` and `lambda:AddPermission/RemovePermission` to `portfolio-user` `RagChatbotDeployPolicy`
- CloudFormation template updated with `QueryLambdaWarmupRule` + `QueryLambdaWarmupPermission` resources (CFN early-validation error continues to block direct CFN deploys on this stack — resources correct in template for future full deploys)

**Change 2 — Bedrock as default:**
- `frontend/index.html` line 748: added `selected` attribute to bedrock option, moved it first in dropdown
- Confirmed in CloudFront-served HTML: `value="bedrock" selected`

**Change 3 (dropped):** Nebius Fast tier model — no `-fast` variant exists for `meta-llama/Llama-3.3-70B-Instruct` in Nebius model catalog. Speed delta Bedrock vs Nebius is a feature, not a bug.

**Smoke test (curl-based — Playwright MCP unavailable this session):**
- CloudFront 200 ✓
- `value="bedrock" selected` in served HTML ✓
- Bedrock → jimmy_background routing ✓
- Nebius → aws_well_architected routing ✓
- KB badge CSS confirmed in deployed HTML ✓
- Console errors: not verified (Playwright down)

## Architecture Decisions Made

**EventBridge warm-up pattern:** Scheduled ping every 5 min with `{"warmup": true}` payload. Warmup branch returns before ANY Bedrock or Nebius call — zero generation cost per ping. Handler checks `event.get("warmup")` as first line before all other logic.

**Bedrock as default:** UX decision. Bedrock is faster and AWS-native — better first impression. Nebius is the "compare" option, not the default experience. The speed contrast (3–5s vs 3–9s) is visible and makes the toggle interesting.

**Nebius observability logs are permanent:** `[DEBUG] Nebius request body` and `[INFO] Nebius usage` lines stay in all future versions. They resolved the max_tokens enforcement ambiguity this session and are the only source of ground-truth token counts on the Nebius path.

## Known Issues Closed This Session
- WA Query Latency: MITIGATED → RESOLVED

## Permanent Infrastructure Added
- EventBridge rule `rag-chatbot-warmup-dev` (live, us-east-1)
- Lambda permission `EventBridgeWarmupPermission`
- IAM inline policy additions to `portfolio-user` for EventBridge

## Next Up: Phase 7.5 — Portfolio Site Card Update

**Lives in the `portfolio-site` repo — separate session, separate repo.**

Update the RAG Knowledge Chatbot card on the advanced projects page:
- Replace both "COMING SOON" buttons with:
  - Orange **LIVE DEMO** → `https://d1r1qv7io7k8vk.cloudfront.net`
  - Blue **ARCHITECTURE** → destination TBD
- Match FieldIQ card styling exactly

## Files Changed This Session
- `src/lambdas/query/handler.py` — warmup branch at top of `lambda_handler`
- `frontend/index.html` — Bedrock default (`selected` + first in dropdown)
- `infrastructure/cloudformation/template.yaml` — `QueryLambdaWarmupRule` + `QueryLambdaWarmupPermission`
- `PROJECT_PLANNING_MULTICLOUD.md` — Phase 8 complete, Step 7 results, Step 8 deployment summary, Phase 9 candidates updated, Known Issues resolved
- `sessions/2026-04-17-phase8-complete-wrap.md` — this file
