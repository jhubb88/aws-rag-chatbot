# RAG Knowledge Chatbot — Project Planning Document
### Multi-Cloud Edition | Last Updated: 2026-04-14
**Phase 1 Status:** ✅ Complete — stack deployed, commit `68a92b6`, tag `v0.2-infra`

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
| **Nebius AI Studio — Llama 3.1** | **Generation Provider B** | OpenAI-compatible, bypasses AWS auth blocks, uses Markdown prompting |
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

### Bedrock Access — ACTIVE BLOCKER (Mitigated by Nebius)
AWS account cannot submit Anthropic use case details form.  
Error: "Your account is not authorized to perform this action."

**Mitigation Plan:**  
Because the architecture now includes Nebius as a dual-provider, Phase 1 and the Query Pipeline (Phase 3) are **NO LONGER BLOCKED**. The build will proceed using Nebius for text generation. Bedrock integration will be built in code, but tested live only once AWS Support resolves the account-level block.

Test command to verify Bedrock when resolved:
```bash
cat > /tmp/bt.json << 'EOF'
{"anthropic_version":"bedrock-2023-05-31","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}
EOF

aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --body fileb:///tmp/bt.json \
  --profile portfolio-user \
  --region us-east-1 \
  /tmp/bo.json && cat /tmp/bo.json
```

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
| Phase 2 | Document ingestion pipeline | ⏳ Not started |
| Phase 3 | Query pipeline (Router Logic) | ⏳ Not started |
| Phase 4 | Frontend (Dual-Provider UI) | ⏳ Not started |
| Phase 5 | Observability | ⏳ Not started |
| Phase 6 | Integration testing | ⏳ Not started |
| Phase 7 | Portfolio polish | ⏳ Not started |
| Phase 8 | Phase 2 features | ⏳ Future |

---

## Next Session — Phase 2: Document Ingestion Pipeline

- Create `data/documents/` directory (gitignored — add source docs here)
- Write `src/lambdas/ingest/handler.py`:
  - Accept PDF/text from `data/documents/`
  - Chunk into ~500 token segments with overlap
  - Call Titan Embeddings v2 via Bedrock to embed each chunk
  - Store chunks + embeddings as JSON vector index in S3 (`documents/` prefix)
- Package and deploy ingest Lambda via CloudFormation update
- Note: Bedrock still blocked at account level — code path will be built but live-testable only after AWS Support resolves

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
- Milestone tags: `v0.1-planning` ✅, `v0.2-infra` (next), `v0.3-ingest`, etc.
- Never commit: `.env`, credentials, `data/documents/`

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
