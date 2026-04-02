# STEP PLAN — RAG Knowledge Chatbot

## Overview

| Phase | Name | Goal |
|-------|------|------|
| 0 | Planning and Scaffolding | Project structure, documentation, GitHub repo |
| 1 | Infrastructure as Code | CloudFormation template for all MVP services |
| 2 | Document Ingestion Pipeline | Lambda reads docs, creates embeddings, stores vectors |
| 3 | Query Pipeline | Lambda retrieves chunks, calls Bedrock, returns answers |
| 4 | Frontend | Static chat UI on S3 |
| 5 | Observability | CloudWatch dashboards, CloudTrail, Budgets |
| 6 | Integration Testing and Cleanup | End-to-end tests, dead code removal |
| 7 | Portfolio Polish | README, architecture diagram, demo recording |
| 8 | Phase 2 Features | DynamoDB, Cognito, CloudFront — future |

---

## Phase 0 — Planning and Scaffolding

**Goal:** Establish the project foundation before any build work begins.

**Tasks:**
- Create folder structure
- Initialize git and create GitHub repo
- Write all planning documents (PROJECT_BRIEF, ARCHITECTURE_DECISIONS, STEP_PLAN, TEST_GATES, COST_GUARDRAILS, GIT_WORKFLOW, SESSION_WORKFLOW, README)
- Write session wrap-up
- Tag and push milestone commit

**Claude Code does:**
- Creates all folders and .gitkeep files
- Writes all planning documents
- Writes session wrap-up
- Commits and pushes

**Jimmy does:**
- Reviews all planning documents before final push
- Confirms GitHub repo is live and looks correct
- Completes pre-build checklist (see TEST_GATES.md) before Phase 1

**Test gate:** All 8 planning documents written and committed. GitHub repo live. Pre-build checklist complete.

---

## Phase 1 — Infrastructure as Code

**Goal:** Write a CloudFormation template that defines every MVP AWS resource. No resources deployed yet — template written and validated only.

**Tasks:**
- Write `infra/template.yaml` (CloudFormation)
- Define: S3 buckets (documents, vector store, frontend), Lambda functions (ingest, query), API Gateway (REST API with POST /chat), IAM roles (least privilege), CloudWatch log groups
- Validate template with `aws cloudformation validate-template`
- Deploy stack to us-east-1 with `aws cloudformation deploy`
- Confirm all resources created successfully in AWS console

**Claude Code does:**
- Writes `infra/template.yaml`
- Runs validation command and reports result
- Runs deploy command and reports result
- Writes decisions log entry if any architecture changes were made

**Jimmy does:**
- Confirms AWS CLI is configured and working before this phase starts
- Confirms Bedrock model access is enabled (see TEST_GATES.md pre-build checklist)
- Reviews `infra/template.yaml` before deploy
- Confirms stack in AWS console after deploy

**Test gate:** `aws cloudformation describe-stacks` returns `CREATE_COMPLETE`. All resources visible in AWS console.

---

## Phase 2 — Document Ingestion Pipeline

**Goal:** A Lambda function that reads source documents from S3, generates embeddings via Titan Embeddings v2, and stores vector JSON files in S3.

**Prerequisites:** Source documents must be placed in `data/documents/` before this phase begins. Do not start Phase 2 without them.

**Tasks:**
- Write `backend/ingest/handler.py`
- Implement: read document from S3, chunk text, call Titan Embeddings v2, write chunk+vector JSON to vector store S3 bucket
- Write `backend/ingest/requirements.txt`
- Write `scripts/upload_documents.sh` — uploads files from `data/documents/` to the documents S3 bucket
- Write `scripts/run_ingest.sh` — manually triggers the ingest Lambda
- Test ingestion end-to-end: upload a document, trigger Lambda, confirm vector files appear in S3

**Claude Code does:**
- Writes all ingest Lambda code
- Writes upload and trigger scripts
- Reports test results

**Jimmy does:**
- Places source documents in `data/documents/` before this phase
- Runs upload script to push documents to S3
- Runs ingest trigger script
- Confirms vector files appear in S3 console

**Test gate:** At least one document ingested successfully. Vector JSON files visible in S3 vector store bucket. CloudWatch logs show no errors.

---

## Phase 3 — Query Pipeline

**Goal:** A Lambda function behind API Gateway that accepts a question, retrieves relevant chunks from S3, calls Claude 3 Haiku, and returns an answer.

**Tasks:**
- Write `backend/query/handler.py`
- Implement: receive POST request, embed question with Titan, load vectors from S3, compute cosine similarity, select top N chunks, build prompt, call Claude 3 Haiku, return answer
- Write `backend/query/requirements.txt`
- Write `tests/integration/test_query.py` — sends a test question and validates the response format
- Test the API endpoint with curl

**Claude Code does:**
- Writes all query Lambda code
- Writes integration test
- Reports curl test results

**Jimmy does:**
- Reviews the prompt template before deploy
- Runs the curl test against the live endpoint
- Confirms answers look reasonable given the source documents

**Test gate:** `curl -X POST <api-endpoint>/chat -d '{"question":"test"}'` returns a JSON response with an `answer` field. Integration test passes. CloudWatch logs show no errors.

---

## Phase 4 — Frontend

**Goal:** A clean, static chat UI hosted on S3 that lets users type questions and see answers.

**Tasks:**
- Write `frontend/index.html`
- Write `frontend/style.css`
- Write `frontend/app.js` — handles form submit, calls API Gateway endpoint, displays answer
- Write `scripts/deploy_frontend.sh` — syncs frontend files to the S3 website bucket
- Enable S3 static website hosting (already configured in CloudFormation)
- Deploy and confirm the page loads in a browser

**Claude Code does:**
- Writes all frontend files
- Writes deploy script
- Reports deploy result and S3 website URL

**Jimmy does:**
- Opens the URL in a browser
- Types a test question and confirms the answer displays correctly
- Reports any visual or functional issues

**Test gate:** Frontend URL loads in a browser with no console errors. A question typed in the UI returns an answer from the API within 10 seconds.

---

## Phase 5 — Observability

**Goal:** CloudWatch dashboard showing key metrics, CloudTrail enabled, AWS Budget configured.

**Tasks:**
- Add CloudWatch dashboard to CloudFormation template: Lambda invocations, errors, duration; API Gateway 4xx/5xx errors
- Confirm CloudTrail is enabled in us-east-1 (trail already required in pre-build checklist)
- Create AWS Budget: $20/month cap, alerts at $15 and $18
- Write `docs/decisions/observability-setup.md` confirming what was configured

**Claude Code does:**
- Updates `infra/template.yaml` with dashboard resource
- Deploys updated stack
- Writes observability decisions doc

**Jimmy does:**
- Creates the AWS Budget manually in the console (Budget API requires special permissions)
- Confirms the CloudWatch dashboard is visible in the console
- Confirms CloudTrail trail is active

**Test gate:** CloudWatch dashboard visible and showing data after a test query. CloudTrail trail active. Budget alert configured at $15 and $18.

---

## Phase 6 — Integration Testing and Cleanup

**Goal:** Run a full end-to-end test, remove any dead code, confirm the system is clean.

**Tasks:**
- Run `tests/integration/test_query.py` against the live stack
- Send 5 different test questions and manually review answers for accuracy
- Remove any commented-out code, unused imports, or debug logging
- Confirm `.gitignore` is catching everything it should
- Confirm all CloudWatch log groups have retention policies set

**Claude Code does:**
- Runs integration tests and reports results
- Reviews all source files for cleanup
- Reports any issues found

**Jimmy does:**
- Reviews the 5 test answers for quality
- Signs off on the system before portfolio polish begins

**Test gate:** All integration tests pass. No errors in CloudWatch logs during test run. Jimmy signs off on answer quality.

---

## Phase 7 — Portfolio Polish

**Goal:** The GitHub repo and live demo are ready for a recruiter to review.

**Tasks:**
- Update `README.md` with final content: architecture diagram, live demo link, What I Learned section
- Create architecture diagram (draw.io or similar) and add to `docs/`
- Record a short demo video (optional but recommended)
- Write `docs/decisions/` entries for any decisions not yet documented
- Final review of all docs for accuracy and plain English
- Tag milestone: `v1.0-complete`

**Claude Code does:**
- Updates README with final content
- Reviews all docs for gaps or inaccuracies
- Prepares final commit

**Jimmy does:**
- Creates architecture diagram (tool of his choice)
- Records demo video if desired
- Does final review of README
- Pushes final tag

**Test gate:** README is complete and accurate. Live demo URL works. GitHub repo is clean and professional.

---

## Phase 8 — Phase 2 Features (Future)

**Goal:** Add user auth, conversation history, and CDN. Not part of MVP.

**Planned features:**
- DynamoDB table for conversation history (session ID → messages)
- Cognito user pool for authentication
- CloudFront distribution with custom domain
- Lambda authorizer to validate Cognito tokens

**Prerequisites before starting Phase 8:**
- Phase 7 complete and tagged
- Custom domain registered (not included in this project)
- Decision made on whether to keep the demo open-access or require login
