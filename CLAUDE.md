# CLAUDE.md — RAG Chatbot Global Rules
Last updated: 2026-04-18

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
- Nebius warmup ping in query Lambda's warmup branch is permanent. Do not remove or alter without explicit approval. Ground truth log lines `[INFO] Nebius warmup: duration_ms=X status=ok` and `[WARNING] Nebius warmup failed: <error>` are also permanent.
- Nebius Fast tier not available for Llama 3.3-70B as of 2026-04-18.

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

## Bedrock (Active Blocker)
- Bedrock model access is blocked at the account level — AWS Support case is open
- Do not attempt to invoke any Bedrock generation model (Claude 3 Haiku) until Jimmy confirms it is unblocked
- Bedrock Titan Embeddings v2 may be used for embeddings once Phase 2 begins
- Test command when Bedrock is resolved:
  cat > /tmp/bt.json << 'EOF'
  {"anthropic_version":"bedrock-2023-05-31","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}
  EOF
  aws bedrock-runtime invoke-model \
    --model-id anthropic.claude-3-haiku-20240307-v1:0 \
    --body fileb:///tmp/bt.json \
    --profile portfolio-user \
    --region us-east-1 \
    /tmp/bo.json && cat /tmp/bo.json

## Local Paths
- This project: /mnt/c/Users/jimmy/Desktop/Projects/rag-chatbot/
- Portfolio context: /mnt/c/Users/jimmy/Desktop/Projects/portfolio-context/
- All projects: /mnt/c/Users/jimmy/Desktop/Projects/

## Key AWS Config
- Region: us-east-1
- Account ID: 603509861186
- AWS CLI profile: portfolio-user
- SSM Nebius API key path: /rag-chatbot/nebius-api-key (already exists — do not overwrite)

## Known Retrieval Issues

### "What projects has Jimmy built?" — retrieval miss (2026-04-18)
**Query:** "What projects has Jimmy built?"
**Symptom:** Both providers hedge with "context doesn't provide details about other specific projects" despite the answer existing in three index chunks. The cleanest chunk (project_index.txt, 345 chars) scored 0.4179 and ranked 5th overall — missing the top-3 cutoff by 0.0329.
**Root cause:** top_k=3 is too aggressive for a 2,027-chunk index. Narrative career chunks outrank enumeration chunks due to vocabulary overlap with "built / projects / Jimmy." The index content is correct; the cutoff is too tight.
**Status:** resolved 2026-04-18 commit b30b6ab — TOP_K raised 3→5, both providers now name all 7 projects. Nebius first-call-after-idle latency (true baseline: min 3.10s, median 8.25s, max 14.86s from CloudWatch REPORT — prior "10–18s" estimate was eyeball, not data) is a Nebius-side characteristic, not related to this fix. Warmup ping (commit b36c69c) reduces first-call median by ~33%, worst-case by ~58%.

## README Maintenance Rule

README.md is a living document and must be kept current as code and infrastructure change. Every Claude Code session that makes significant changes to this project MUST update README.md as part of the same work, not as a separate cleanup pass.

Triggers that require README.md updates:
- Model change (either provider) — update Tech Stack table, Architecture section, Engineering Decisions if the change is load-bearing
- Provider change (switching Nebius to Groq/Together/etc., or adding a third provider) — update all references including the opening paragraph
- New AWS service added or removed from the stack — update Tech Stack table
- New KB added or KB scope changed — update What This Project Is, Architecture, Engineering Decisions
- New latency lever shipped (streaming, index format change, etc.) — update Engineering Decisions
- Cost structure changes materially — update Cost Guardrails numbers
- New tag (v1.1, v2.0, etc.) — update Current Status
- Phase 9 items completed — move relevant lines out of the "active work" mention

README.md updates should be committed in the SAME commit as the code change that triggered them, not as a separate docs commit. This keeps the history honest — the README shows what was true at each tag, not what was aspirational.

A full README polish pass should happen before Jimmy actively shares the GitHub link with recruiters. Do not skip that pass assuming incremental updates have kept it clean.
