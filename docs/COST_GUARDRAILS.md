# COST GUARDRAILS — RAG Knowledge Chatbot

## Hard Cap

**$20/month total. Do not exceed this.**

---

## AWS Budgets Setup

Create two budget alerts manually in the AWS Billing console before Phase 1 begins.

| Alert | Threshold | Action |
|-------|----------|--------|
| Warning | $15 spent in current month | Review spending in Cost Explorer. Identify what is driving cost. |
| Critical | $18 spent in current month | Immediately review. Consider disabling non-essential services. |

**How to create a budget:**
1. AWS Console → Billing and Cost Management → Budgets
2. Create budget → Cost budget
3. Period: Monthly. Budget amount: $20
4. Add alert: 75% of $20 = $15 → email notification
5. Add second alert: 90% of $20 = $18 → email notification
6. Use your AWS account email for notifications

---

## Per-Service Cost Estimates (MVP, Demo Traffic)

"Demo traffic" means: a few test sessions per day, no sustained load.

| Service | Estimated Cost | Notes |
|---------|---------------|-------|
| S3 (storage) | ~$0.01/month | A few MB of documents and vector JSON files |
| S3 (requests) | ~$0.01/month | Infrequent reads during queries |
| Lambda | ~$0/month | Free tier: 1M requests, 400,000 GB-seconds/month |
| API Gateway | ~$0/month | Free tier: 1M REST API calls/month (first 12 months) |
| Bedrock — Titan Embeddings v2 | ~$0.10/month | Ingestion is one-time. Query embeddings: $0.00002 per 1K tokens |
| Bedrock — Claude 3 Haiku | ~$1–3/month | $0.25/1M input tokens, $1.25/1M output tokens. 10–50 test queries/day |
| CloudWatch Logs | ~$0.50/month | $0.50/GB ingested. Lambda logs at demo scale are small |
| CloudWatch Metrics | ~$0/month | Basic metrics are free |
| CloudTrail | ~$0/month | First trail delivering to S3 is free |
| AWS Budgets | ~$0/month | First two budget alerts per month are free |
| **Total** | **~$2–5/month** | Well within the $20 cap |

---

## Bedrock Is the Primary Cost Driver

At demo scale, everything except Bedrock is effectively free.

**Claude 3 Haiku cost estimate:**
- Input: $0.25 per 1,000,000 tokens
- Output: $1.25 per 1,000,000 tokens
- A typical RAG query: ~1,500 input tokens (system prompt + retrieved chunks + question) + ~200 output tokens
- Cost per query: ~$0.000375 + ~$0.00025 = ~$0.0006 per query
- 1,000 queries/month = ~$0.60
- 5,000 queries/month = ~$3.00

**Titan Embeddings v2 cost estimate:**
- $0.00002 per 1,000 tokens
- Ingestion (one-time): a few thousand tokens for a small document set = ~$0.01
- Per query embedding: ~100 tokens = ~$0.000002 per query — negligible

---

## How to Check Current Spend

**In the AWS console:**
- Billing → Cost Explorer → View by service → filter to current month

**Via CLI:**
```bash
# Total spend for current month
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --query 'ResultsByTime[0].Total.UnblendedCost.Amount'

# Spend broken down by service
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[0].Groups[*].[Keys[0],Metrics.UnblendedCost.Amount]' \
  --output table
```

Note: Cost Explorer data has a ~24-hour delay. It does not show real-time spend.

---

## What to Shut Down First If Costs Spike

Follow this order — shut down the biggest cost drivers first.

1. **API Gateway** — disable or delete the stage. This stops all incoming queries immediately. No queries = no Bedrock calls.
2. **Lambda** — set reserved concurrency to 0 on the query Lambda. This blocks execution even if the API Gateway endpoint is still reachable.
3. **Bedrock** — there is no "disable" switch for Bedrock. Blocking the Lambda is the equivalent.
4. **CloudWatch Logs** — if log volume is unexpectedly high, reduce Lambda log level or set a shorter retention period (e.g., 7 days instead of 30).
5. **S3** — only relevant if you have stored a very large number of vector files. At demo scale this is not a concern.

---

## Kill Switch

If the budget alert fires at $18, take these actions immediately:

```bash
# 1. Block the query Lambda from executing
aws lambda put-function-concurrency \
  --function-name rag-chatbot-query \
  --reserved-concurrent-executions 0

# 2. Confirm it is blocked
aws lambda get-function-concurrency --function-name rag-chatbot-query
```

Then investigate Cost Explorer to find what caused the spike before re-enabling.

To re-enable:
```bash
aws lambda delete-function-concurrency --function-name rag-chatbot-query
```

---

## Cost Optimization Notes

- Do not run ingestion repeatedly on the same documents — embeddings are generated once and cached in S3
- Keep the top-N chunks per query at 3–5; more chunks = longer prompts = higher Bedrock cost
- Set CloudWatch log retention to 14 days (configured in CloudFormation) to avoid unbounded log storage costs
- Delete the CloudFormation stack when the project is not being actively tested or demoed
