# SESSION WORKFLOW — RAG Knowledge Chatbot

## At the Start of Every Session

Run these steps before opening Claude Code or writing any code.

### Step 1 — Navigate to the project

```bash
cd /mnt/c/Users/jimmy/Desktop/ClaudeCode/rag-chatbot/
```

### Step 2 — Check current state

```bash
git status
git log --oneline -5
```

This tells you what branch you are on, whether there are uncommitted changes, and what was last committed.

### Step 3 — Read the most recent session wrap-up

```bash
ls sessions/
cat sessions/<most-recent-date>-wrap.md
```

This tells you exactly where work stopped and what the next step is.

### Step 4 — Tell Claude Code your starting point

When you open a new Claude Code session, paste or say:

> "I am working on the RAG chatbot project at `/mnt/c/Users/jimmy/Desktop/ClaudeCode/rag-chatbot/`. I am in **[Phase X — Name]**. The last completed step was **[paste from wrap-up]**. The next step is **[paste from wrap-up]**."

This gives Claude Code the context it needs without re-reading the entire planning package.

---

## At the End of Every Session

**Rule: Never end a session without a wrap-up file.**

### Step 1 — Claude Code writes the wrap-up

The wrap-up goes in `sessions/YYYY-MM-DD-wrap.md`.

If multiple sessions happen on the same day, append a suffix: `sessions/2026-04-02-wrap-a.md`, `sessions/2026-04-02-wrap-b.md`.

### Wrap-Up File Format

```markdown
# Session Wrap-Up — YYYY-MM-DD

## Phase
Phase X — Name

## What Was Completed This Session
- [bullet list of completed tasks]

## What Was NOT Finished and Why
- [bullet list of incomplete tasks and the reason — blocked, ran out of time, deferred decision, etc.]

## Errors Hit and How They Were Resolved
- [describe any errors encountered and what fixed them, or that they are still open]

## Exact Next Step
[One clear sentence: what to do first in the next session. Be specific enough that no context is needed.]

## Decisions Made This Session
- [any architecture, naming, or approach decisions made — enough detail to reconstruct the reasoning]
```

### Step 2 — Commit the wrap-up

```bash
git add sessions/YYYY-MM-DD-wrap.md
git commit -m "docs: session wrap-up YYYY-MM-DD"
```

### Step 3 — Push if a milestone was reached

If the session completed a phase and the test gate passed, push and tag per `GIT_WORKFLOW.md`.

---

## Ground Rules for All Sessions

These apply in every session, not just the first one:

- Before doing anything, Claude Code tells you what it is about to do and waits for "go"
- After completing each major step, Claude Code summarizes what was done and what comes next, then waits for "go"
- If Claude Code hits the same error twice, it stops and summarizes what failed and why — it does not try a third approach without your input
- No destructive commands (`rm -rf`, deleting S3 buckets, dropping stacks) without explicit confirmation
- Always specify whether a command should run in WSL terminal or somewhere else
- Every file Claude Code writes must be reviewed before the final commit in a phase
