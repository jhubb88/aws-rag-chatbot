# TEST GATES — RAG Knowledge Chatbot

## Pre-Build Checklist (Complete Before Phase 1)

Run through this checklist before writing any infrastructure code. Every item must pass.

| # | Check | How to Verify | Pass | Fail / Action |
|---|-------|--------------|------|--------------|
| 1 | Bedrock model access — Claude 3 Haiku | AWS Console → Bedrock → Model access → confirm `anthropic.claude-3-haiku-20240307-v1:0` is enabled | "Access granted" shown | Request access; wait for approval (can take minutes to hours) |
| 2 | Bedrock model access — Titan Embeddings v2 | AWS Console → Bedrock → Model access → confirm `amazon.titan-embed-text-v2:0` is enabled | "Access granted" shown | Request access |
| 3 | AWS CLI configured in WSL | Run: `aws sts get-caller-identity` | Returns account ID and ARN | Run `aws configure` and enter credentials |
| 4 | AWS region set to us-east-1 | Run: `aws configure get region` | Returns `us-east-1` | Run `aws configure set region us-east-1` |
| 5 | GitHub CLI authenticated | Run: `gh auth status` | Shows `jhubb88` logged in | Run `gh auth login` |
| 6 | AWS Budget set at $20/month | AWS Console → Billing → Budgets | Budget exists with $15 and $18 alerts | Create manually in console (see COST_GUARDRAILS.md) |
| 7 | CloudTrail enabled in us-east-1 | AWS Console → CloudTrail → Trails | At least one trail active in us-east-1 | Create a trail; first trail is free |
| 8 | IAM permissions review | Confirm the IAM user/role used by CLI has permissions for: S3, Lambda, API Gateway, CloudFormation, Bedrock, CloudWatch, CloudTrail | No access denied errors on `aws sts get-caller-identity` | Check IAM policies; add missing permissions |

---

## Phase 0 — Planning and Scaffolding

**What to test:** All planning documents exist and are committed to GitHub.

**How to test:**
```
cd /mnt/c/Users/jimmy/Desktop/ClaudeCode/rag-chatbot
git log --oneline
ls docs/
ls docs/plans/
ls sessions/
```

**Pass:** All 8 documents present. Git log shows planning commit. GitHub repo shows files at `https://github.com/jhubb88/aws-rag-chatbot`.

**Fail:** Missing files. Action: re-run the document creation step for any missing file.

---

## Phase 1 — Infrastructure as Code

**What to test:** CloudFormation template is valid and stack deploys successfully.

**How to test:**
```
# Validate template
aws cloudformation validate-template --template-body file://infra/template.yaml

# Deploy stack
aws cloudformation deploy \
  --template-file infra/template.yaml \
  --stack-name rag-chatbot \
  --capabilities CAPABILITY_IAM \
  --region us-east-1

# Confirm stack status
aws cloudformation describe-stacks \
  --stack-name rag-chatbot \
  --query 'Stacks[0].StackStatus'
```

**Pass:** `validate-template` returns no errors. `describe-stacks` returns `"CREATE_COMPLETE"`. All expected resources (S3 buckets, Lambda functions, API Gateway) visible in AWS console.

**Fail:** Template validation error — fix the template, do not deploy. Stack status is `ROLLBACK_COMPLETE` — check CloudFormation Events tab for the specific resource that failed, fix it, delete the failed stack, and re-deploy.

---

## Phase 2 — Document Ingestion Pipeline

**What to test:** Ingestion Lambda runs successfully and produces vector files in S3.

**Pre-condition:** Source documents must be in `data/documents/` and uploaded to S3 before testing.

**How to test:**
```
# Upload source documents to S3
bash scripts/upload_documents.sh

# Trigger ingestion Lambda
bash scripts/run_ingest.sh

# Confirm vector files exist in S3
aws s3 ls s3://<vector-store-bucket-name>/vectors/ --recursive
```

**Check CloudWatch logs:**
```
aws logs tail /aws/lambda/rag-chatbot-ingest --follow
```

**Pass:** At least one vector JSON file appears in the S3 vector store bucket. CloudWatch logs show no errors. Each vector file contains `chunk_text` and `embedding` fields.

**Fail:** Lambda errors in CloudWatch — read the full error message, identify the cause (permissions, Bedrock access, malformed document), fix one thing at a time. If the same error occurs twice, stop and report.

---

## Phase 3 — Query Pipeline

**What to test:** API endpoint accepts a question and returns an answer.

**How to test:**
```
# Get the API endpoint URL from CloudFormation outputs
API_URL=$(aws cloudformation describe-stacks \
  --stack-name rag-chatbot \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

# Send a test question
curl -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What projects has Jimmy worked on?"}'
```

**Run integration test:**
```
python tests/integration/test_query.py
```

**Pass:** curl returns a JSON object with an `answer` field containing a non-empty string. Integration test passes (exit code 0). CloudWatch logs show no errors.

**Fail:** 500 error from API Gateway — check Lambda CloudWatch logs for the specific error. Empty or garbled answer — check the prompt template and retrieved chunks. If the same failure occurs twice, stop and report.

---

## Phase 4 — Frontend

**What to test:** Static frontend loads in a browser and successfully sends a question to the API.

**How to test:**
```
# Deploy frontend files to S3
bash scripts/deploy_frontend.sh

# Get the S3 website URL from CloudFormation outputs
aws cloudformation describe-stacks \
  --stack-name rag-chatbot \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendUrl`].OutputValue' \
  --output text
```

Open the URL in a browser. Open browser developer tools (F12) and check the Console tab for errors. Type a test question and submit.

**Pass:** Page loads with no console errors. Question submitted. Answer displayed within 10 seconds. Network tab shows a successful POST to the API Gateway endpoint.

**Fail:** Page does not load — check S3 bucket policy and static website hosting configuration. API call fails — check CORS configuration on API Gateway. No answer displayed — check browser console for JavaScript errors.

---

## Phase 5 — Observability

**What to test:** CloudWatch dashboard shows data. CloudTrail trail is active. Budget alerts are configured.

**How to test:**
```
# Confirm CloudWatch dashboard exists
aws cloudwatch list-dashboards --query 'DashboardEntries[*].DashboardName'

# Confirm CloudTrail trail is active
aws cloudtrail get-trail-status --name <trail-name> --query 'IsLogging'

# Confirm Budget exists (requires billing permissions)
aws budgets describe-budgets --account-id <account-id>
```

Open CloudWatch console → Dashboards → rag-chatbot. Send a test query through the frontend and confirm Lambda invocation count increments on the dashboard.

**Pass:** Dashboard visible and showing metric widgets. CloudTrail returns `true` for IsLogging. Budget exists with alerts at $15 and $18.

**Fail:** Dashboard not showing data — wait 5 minutes after sending a test query for metrics to populate. Budget not found — create manually in the Billing console.

---

## Phase 6 — Integration Testing and Cleanup

**What to test:** Full end-to-end system with 5 different questions. No code quality issues.

**How to test:**
```
# Run integration test suite
python tests/integration/test_query.py

# Check for syntax issues in Python files
python -m py_compile backend/ingest/handler.py
python -m py_compile backend/query/handler.py
```

Manually review answers for 5 different questions against the source documents.

**Pass:** All integration tests pass. No Python syntax errors. Jimmy reviews 5 answers and judges them accurate and grounded in source documents. No unused imports or debug logging in source files.

**Fail:** Integration test fails — investigate the specific test case, do not move to Phase 7. Answer quality is poor — review the chunk size, overlap, and top-N selection in the query Lambda.

---

## Phase 7 — Portfolio Polish

**What to test:** GitHub repo is clean and professional. README is complete and accurate.

**How to test:**
- Open `https://github.com/jhubb88/aws-rag-chatbot` in a browser as if you are a recruiter
- Check: README renders correctly, all links work, no placeholder text remains
- Confirm live demo URL in README opens the working frontend
- Confirm `v1.0-complete` tag is visible under Releases/Tags

**Pass:** README complete. Live demo link works. Architecture diagram present. No broken links. Tag visible.

**Fail:** Any broken link or placeholder text remaining — fix before tagging.
