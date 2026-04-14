# GIT WORKFLOW — RAG Knowledge Chatbot

## Branch Strategy

- `main` is always stable and deployable
- All work happens on feature branches
- Merge to `main` only when the work is complete and tested

**Branch naming:**
```
phase/1-infra
phase/2-ingest
phase/3-query
phase/4-frontend
phase/5-observability
phase/6-integration
phase/7-polish
```

**How to create a branch:**
```bash
cd /mnt/c/Users/jimmy/Desktop/ClaudeCode/rag-chatbot
git checkout -b phase/1-infra
```

**How to merge back to main:**
```bash
git checkout main
git merge phase/1-infra
git push origin main
```

---

## Commit Message Format

Use conventional commits. Format: `type: description`

| Type | When to Use | Example |
|------|------------|---------|
| `feat:` | New functionality added | `feat: add cosine similarity retrieval to query Lambda` |
| `fix:` | Bug corrected | `fix: handle empty document chunks in ingest handler` |
| `chore:` | Setup, config, tooling | `chore: initial project scaffold` |
| `docs:` | Documentation only | `docs: add architecture decisions for retrieval layer` |
| `test:` | Tests added or updated | `test: add integration test for query endpoint` |
| `infra:` | CloudFormation or IaC changes | `infra: add CloudWatch dashboard to template` |

Keep the description short (under 72 characters). Use lowercase. No period at the end.

---

## When to Commit

Commit after each completed task within a phase. Do not bundle unrelated work into a single commit. Do not commit broken code.

Examples of good commit points:
- CloudFormation template written (before deploy)
- CloudFormation template validated (after `validate-template` passes)
- Ingest Lambda handler written
- Integration test written
- Frontend HTML written
- Session wrap-up written

---

## When to Push to GitHub

Push at each milestone — when a phase test gate passes and work is complete.

| Milestone | Event | Tag |
|-----------|-------|-----|
| Milestone 1 | Planning package complete (Phase 0 done) | `v0.1-planning` |
| Milestone 2 | CloudFormation template written and validated (Phase 1 complete) | `v0.2-infra` |
| Milestone 3 | Ingestion pipeline working end-to-end (Phase 2 test gate passes) | `v0.3-ingest` |
| Milestone 4 | Query pipeline returning answers (Phase 3 test gate passes) | `v0.4-query` |
| Milestone 5 | Frontend live on S3 (Phase 4 test gate passes) | `v0.5-frontend` |
| Milestone 6 | Full integration test passing (Phase 6 test gate passes) | `v0.6-tested` |
| Milestone 7 | Portfolio polish complete (Phase 7 test gate passes) | `v1.0-complete` |

**How to tag a milestone:**
```bash
git tag v0.1-planning
git push origin v0.1-planning
```

---

## What Never Gets Committed

The `.gitignore` enforces this, but understand what and why:

| What | Why |
|------|-----|
| `.env` files | May contain AWS credentials or API keys |
| `data/documents/` | Source documents may be personal/sensitive; large files not appropriate for git |
| `__pycache__/`, `*.pyc` | Python bytecode; generated automatically, not source |
| `venv/` | Python virtual environment; recreated from `requirements.txt` |
| `*.zip` | Lambda deployment packages; built artifacts, not source |
| `.DS_Store` | macOS metadata; irrelevant to the project |
| `node_modules/` | Not expected in this project, but included as a precaution |

**If you accidentally commit something that should not be committed:**
1. Stop. Do not push.
2. Run `git rm --cached <file>` to untrack it
3. Add it to `.gitignore`
4. Commit the removal
5. If it was already pushed, tell Claude Code — do not try to rewrite git history without guidance

---

## Quick Reference

```bash
# Check current status
git status
git log --oneline -10

# Create and switch to a new branch
git checkout -b phase/1-infra

# Stage and commit
git add <specific-files>
git commit -m "feat: description"

# Push current branch
git push origin phase/1-infra

# Merge to main and push
git checkout main
git merge phase/1-infra
git push origin main

# Tag a milestone
git tag v0.2-infra
git push origin v0.2-infra
```
