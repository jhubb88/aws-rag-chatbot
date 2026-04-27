# CLAUDE.md — RAG Chatbot Global Rules
Last updated: 2026-04-27

These rules apply to every Claude Code session in this project without exception.

---

## Identity and Profile
- Always use --profile portfolio-user for every AWS CLI command
- Verify the profile exists at the start of every session before doing anything else:
  aws configure list --profile portfolio-user
- If the profile is missing, stop and tell Jimmy immediately — do not proceed
- Never use the default AWS profile under any circumstances

## GitHub Auth (Recurring Issue)
- gh CLI requires a classic PAT (ghp_) with repo and read:org scopes
- If any gh command fails with an auth error, tell Jimmy to run:
  echo "TOKEN" | gh auth login --hostname github.com --git-protocol https --with-token

## Execution Rules
- Explain what you will do before every major action and wait for explicit "go" confirmation
- One file at a time — stop after each file and confirm before moving to the next
- If a file is under 700 lines, print it in full before writing to disk
- If a file is 700+ lines, write directly to disk
- Flag problems before they become problems
- Never force push without explicit confirmation from Jimmy
- Never batch or deliver CC prompts ahead of time — one at a time, only when needed
- When retrieval returns an answer that contradicts known source content, the first diagnostic step is to inspect top-K retrieved chunks AND their full ranking in CloudWatch logs or via direct index query — not to rewrite the source file. Source rewrites are a downstream fix; retrieval diagnosis comes first.
- Warmup branch in the query Lambda primes the index cache only — no synthetic provider ping. Bedrock has no cold endpoint to keep warm. Ground-truth log line `[INFO] Warmup: index cache primed (N chunks)` is permanent. Do not add provider warmup pings without explicit approval.
- To force Lambda index cache refresh after ingest, bump the `INDEX_CACHE_VERSION` env var (e.g., 1→2) via `aws lambda update-function-configuration`. No code change needed. Keep this env var permanently — do not remove it.
- Flag any approach to autonomous edits (even small ones) before applying — stop and confirm between steps, no exceptions.

## Lesson — SambaNova Free-Tier Trap (permanent)
SambaNova's free tier was 20 RPD on Llama 3.3-70B (verified via API response headers, not docs). The Developer Tier upgrade documented as 48K RPD requires a card on file — but the auto-upgrade is broken in SambaNova's billing migration as of 2026-04-27. Community forum threads confirm widespread issue; staff response was "manually @ Coby in the forum and I'll move you over." Lesson: never depend on a third-party AI provider whose tier-upgrade path requires a forum @-mention to function. SambaNova was removed from this project in v1.2 (Phase 11). Rule for any future provider integration: curl the live endpoint with a real key BEFORE writing integration code. Verify rate-limit headers match documented limits. Test the upgrade/billing flow on a throwaway account before committing architecture.

## Portfolio Context
- The portfolio-wide infrastructure reference lives at:
  /mnt/c/Users/jimmy/Desktop/Projects/portfolio-context/CONTEXT.md
  GitHub: https://github.com/jhubb88/portfolio-context
- At the end of every session, check if any of the following changed:
  - Project status or phase
  - AWS infrastructure (new resources, URLs, stack outputs)
  - CloudFront URLs
  - GitHub repos
  - Known issues or blockers
- If anything changed, update CONTEXT.md and commit with:
  chore: update portfolio context — [brief description of what changed]
- Push to origin main

## Session Wrap-Up
- Write a session wrap-up to sessions/YYYY-MM-DD-wrap.md at the end of every session
- Never end a session without a wrap-up file
- Wrap-up must include: what was completed, what was skipped, errors hit, and exact next steps

## Bedrock (sole generation provider as of v1.2)
- Bedrock is the only generation path. Claude Haiku 4.5 is the active model.
- Model ID: `us.anthropic.claude-haiku-4-5-20251001-v1:0` (cross-region inference profile)
- Bedrock Titan Embeddings v2 is active for all query and ingest embeddings.

## Local Paths
- This project: /mnt/c/Users/jimmy/Desktop/Projects/rag-chatbot/
- Portfolio context: /mnt/c/Users/jimmy/Desktop/Projects/portfolio-context/
- All projects: /mnt/c/Users/jimmy/Desktop/Projects/

## Key AWS Config
- Region: us-east-1
- Account ID: 603509861186
- AWS CLI profile: portfolio-user
- SSM SambaNova API key path: /rag-chatbot/sambanova-api-key (DORMANT post-v1.2 — kept for rollback only, no live code reads it)
- SSM Nebius API key path: /rag-chatbot/nebius-api-key (DORMANT — do not delete before 2026-05-19)

## CloudFormation Stack — DRIFT WARNING (added v1.2)
The `rag-knowledge-chatbot` CFN stack has drifted from the local template. Until Phase 12 realignment is complete, do NOT run `aws cloudformation update-stack` against this stack — the update will fail (`AlreadyExistsException` on warmup resources) or revert Lambda code (template's `Code.S3Key` points to stale zip). All infra changes must use direct CLI until realignment ships. Live stack name is `rag-knowledge-chatbot`, NOT `rag-chatbot-dev` (which is an abandoned `REVIEW_IN_PROGRESS` shell). Full drift inventory in `PROJECT_PLANNING_MULTICLOUD.md` Phase 12 candidate.

## iOS / Mobile CSS Rules

- **Always use `height: 100dvh` with `height: 100vh` as a fallback for full-height layouts.** `100vh` on iOS Safari includes browser chrome (address bar) in some states and excludes it in others — this causes the body to overflow and viewport touch coordinates to shift, especially after programmatic scroll operations or rapid DOM swaps. Confirmed bug on this project (2026-04-19). Apply `dvh` globally, not just inside a mobile media query.
- **All `<input>`, `<textarea>`, and `<select>` elements must have `font-size: 16px` minimum on mobile.** iOS Safari auto-zooms any focusable form element with `font-size < 16px`, causing horizontal viewport zoom that persists after blur. Apply via mobile breakpoint or globally if desktop size doesn't matter. Confirmed bug and fix on this project (2026-04-19, commit `77c7c82`).
- **iPad portrait (768–820px CSS viewport) is an unsupported middle-ground for this project.** It falls above the `max-width: 767px` mobile breakpoint (gets desktop layout) but below typical desktop usage patterns. The mobile slide-over overlays are JS-wired but CSS-hidden at this width. A known iPad Safari freeze after Clear Session is deferred as low-priority. Do not attempt iPad-specific layout fixes without explicit approval.

## Known Infrastructure Quirks

### CloudFront Invalidation — Distribution EN88LEBW14923 (RAG Chatbot)
Always use `/*` as the invalidation path on this distribution. Invalidating `/index.html` alone does not reliably clear the cache — the live URL resolves through a different internal path. Verified 2026-04-19: `/index.html` invalidation completed successfully but the live site continued serving stale HTML; `/*` cleared it immediately.

## Known Retrieval Issues

### "What projects has Jimmy built?" — retrieval miss (2026-04-18)
**Query:** "What projects has Jimmy built?"
**Symptom:** Provider hedged with "context doesn't provide details about other specific projects" despite the answer existing in three index chunks. The cleanest chunk (project_index.txt, 345 chars) scored 0.4179 and ranked 5th overall — missing the top-3 cutoff by 0.0329.
**Root cause:** top_k=3 is too aggressive for a 2,027-chunk index. Narrative career chunks outrank enumeration chunks due to vocabulary overlap with "built / projects / Jimmy." The index content is correct; the cutoff is too tight.
**Status:** resolved 2026-04-18 commit b30b6ab — TOP_K raised 3→5, all 7 projects now named. First-touch cold (post warmup hardening, commit `87e1e21`): ~4.7s Lambda, cache hit confirmed. Warmup primes index cache — p95 alarm stable.

## README Maintenance Rule

README.md is a living document and must be kept current as code and infrastructure change. Every Claude Code session that makes significant changes to this project MUST update README.md as part of the same work, not as a separate cleanup pass.

Triggers that require README.md updates:
- Model change — update Tech Stack table, Architecture section, Engineering Decisions if the change is load-bearing
- Provider change — update all references including the opening paragraph
- New AWS service added or removed from the stack — update Tech Stack table
- New KB added or KB scope changed — update What This Project Is, Architecture, Engineering Decisions
- New latency lever shipped (streaming, index format change, etc.) — update Engineering Decisions
- Cost structure changes materially — update Cost Guardrails numbers
- New tag (v1.1, v1.2, v2.0, etc.) — update Current Status

README.md updates should be committed in the SAME commit as the code change that triggered them, not as a separate docs commit. This keeps the history honest — the README shows what was true at each tag, not what was aspirational.

A full README polish pass should happen before Jimmy actively shares the GitHub link with recruiters. Do not skip that pass assuming incremental updates have kept it clean.
