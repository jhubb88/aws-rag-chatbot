# PROJECT BRIEF — RAG Knowledge Chatbot

## What This Project Is

A serverless chatbot on AWS that answers plain English questions using real documents as its knowledge base. When a user asks a question, the system finds the most relevant chunks from stored documents and passes them to an AI model to generate a grounded answer.

This is called Retrieval-Augmented Generation (RAG). The chatbot does not make things up — every answer is tied to something in the source documents.

## What This Project Is Not

- It is not a general-purpose AI assistant that answers anything
- It is not using a pre-built RAG service (Bedrock Knowledge Bases is explicitly excluded)
- It is not a production multi-tenant application (no user accounts in MVP)
- It is not a chatbot that remembers previous conversations (stateless in MVP)

---

## The RAG Pipeline — Plain English

RAG works in two phases: **ingestion** and **query**.

### Ingestion Phase (runs once, or when documents change)

1. Source documents (resume, project writeups, etc.) are dropped into an S3 bucket
2. A Lambda function reads each document and splits it into small chunks (e.g., 500 words each)
3. Each chunk is sent to Amazon Titan Embeddings v2, which converts it into a list of numbers (a vector) that represents its meaning
4. Those vectors are saved back to S3 alongside the original text chunks
5. Result: a searchable knowledge base stored in S3

### Query Phase (runs every time a user asks a question)

1. The user types a question in the chat UI
2. The question is sent to API Gateway, which triggers a Lambda function
3. That Lambda converts the question into a vector using Titan Embeddings v2
4. The Lambda loads all stored vectors from S3 and computes cosine similarity — finding which document chunks are most similar in meaning to the question
5. The top matching chunks are retrieved and assembled into a prompt
6. The prompt is sent to Claude 3 Haiku via Amazon Bedrock
7. Claude generates a plain English answer using only the retrieved context
8. The answer is returned to the user through API Gateway

---

## MVP Scope

| Component | Decision | Reason |
|-----------|----------|--------|
| LLM | Claude 3 Haiku via Bedrock | Fast, cheap, high quality for Q&A |
| Embeddings | Amazon Titan Embeddings v2 | AWS-native, no external dependency |
| Vector store | S3 (JSON files) | No additional service needed at demo scale |
| Retrieval | Custom Lambda with cosine similarity | Demonstrates engineering skill vs. using Bedrock Knowledge Bases |
| API layer | API Gateway + Lambda | Serverless, scales to zero, free tier covers demo traffic |
| Frontend | Static HTML/CSS/JS on S3 | Simple, no framework needed, free to host |
| Infrastructure | CloudFormation | Repeatable, version-controlled, professional |
| Observability | CloudWatch + CloudTrail + AWS Budgets | Logging, audit trail, cost control |

## Phase 2 Scope (not in MVP)

- DynamoDB — conversation history and session management
- Cognito — user authentication
- CloudFront — CDN and custom domain for the frontend
- Custom domain name
- Multi-document ingestion UI

---

## Source Documents

> **Note:** Source documents are placeholders at this stage. The `data/documents/` folder has been created locally but is excluded from git. Documents (resume, project writeups, etc.) will be dropped into this folder before the ingestion phase begins. Do not start Phase 2 (ingestion) until source documents are confirmed and placed in `data/documents/`.

---

## What Success Looks Like

### For a recruiter visiting the live demo

- The chat UI loads in a browser with no errors
- They type a question like "What AWS services has Jimmy worked with?" and get a specific, accurate answer within a few seconds
- The answer is clearly grounded in real content, not generic AI output
- The page looks clean and works on a laptop browser

### For a recruiter reading the GitHub repo

- The README explains the project clearly without jargon
- The architecture is documented and makes sense
- The code is organized, readable, and commented where needed
- The CloudFormation template shows infrastructure-as-code discipline
- The project shows real AWS engineering skill, not just "I followed a tutorial"

---

## Responsibilities

### Claude Code is responsible for

- Writing all application code (Lambda functions, ingestion scripts, query logic)
- Writing the CloudFormation template
- Writing the frontend HTML/CSS/JS
- Writing all planning and documentation files
- Running verifications and reporting results
- Flagging blockers immediately rather than guessing

### Jimmy is responsible for

- Providing AWS credentials and confirming access
- Confirming Bedrock model access (Claude 3 Haiku + Titan Embeddings v2)
- Setting up AWS Budget alerts
- Dropping source documents into `data/documents/` before ingestion
- Testing the live demo and giving feedback
- Approving each phase before moving to the next
- Pushing to GitHub at milestones (or confirming Claude Code does it)
- Making final decisions on any architecture trade-offs
