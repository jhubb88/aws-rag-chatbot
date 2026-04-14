# RAG Knowledge Chatbot

A serverless, portfolio-grade chatbot built on AWS that answers plain English questions using real documents as its knowledge base. The system uses a custom retrieval layer — not a managed service — to demonstrate hands-on AWS and Python engineering skills. Users ask a question, the system finds the most relevant content from stored documents, and Claude 3 Haiku generates a grounded, accurate answer.

**[Live Demo — Coming Soon]**

Portfolio: [Advanced Projects — Jimmy Hubb](http://jimmy-advanced-projects.s3-website-us-east-1.amazonaws.com)

---

## Architecture

> Architecture diagram will be added in Phase 7.

The system works in two phases:

**Ingestion (one-time):** Documents are uploaded to S3 → a Lambda function splits them into chunks → each chunk is converted to a vector by Amazon Titan Embeddings v2 → vectors are stored back in S3.

**Query (every request):** User submits a question → API Gateway triggers a Lambda → the question is embedded → cosine similarity identifies the most relevant document chunks → chunks and question are sent to Claude 3 Haiku via Bedrock → answer is returned to the frontend.

---

## Tech Stack

| Service | Purpose |
|---------|---------|
| Amazon S3 | Document storage, vector store, and static frontend hosting |
| AWS Lambda | Ingestion pipeline and query pipeline (serverless compute) |
| Amazon API Gateway | HTTPS endpoint for the chat frontend |
| Amazon Bedrock — Claude 3 Haiku | LLM for answer generation |
| Amazon Bedrock — Titan Embeddings v2 | Text-to-vector conversion for documents and queries |
| AWS CloudFormation | Infrastructure as code — all resources defined and deployed from a single template |
| Amazon CloudWatch | Lambda logs and metrics dashboard |
| AWS CloudTrail | API audit trail |
| AWS Budgets | Cost alerts at $15 and $18 to enforce a $20/month cap |

---

## Project Status

- [x] Phase 0 — Planning and Scaffolding
- [ ] Phase 1 — Infrastructure as Code (CloudFormation)
- [ ] Phase 2 — Document Ingestion Pipeline
- [ ] Phase 3 — Query Pipeline
- [ ] Phase 4 — Frontend (Static Chat UI on S3)
- [ ] Phase 5 — Observability (CloudWatch, CloudTrail, Budgets)
- [ ] Phase 6 — Integration Testing and Cleanup
- [ ] Phase 7 — Portfolio Polish

---

## How to Run Locally

> This section will be filled in during the build phases. Local testing instructions depend on the Lambda and ingestion code, which are written in Phase 2 and 3.

---

## Cost

This project is designed to run under **$20/month** on AWS at demo traffic levels. At typical portfolio usage, actual cost is estimated at $2–5/month, with Bedrock (Claude 3 Haiku) as the primary cost driver. See `docs/COST_GUARDRAILS.md` for the full breakdown and kill switch procedures.

---

## What I Learned

> This section will be written after the build is complete (Phase 7). It will cover the real engineering challenges encountered and how they were solved — not just a list of services used.
