# ClinicalSetu - Prototype Build Checklist

**Hackathon:** AI for Bharat (Professional Track - Healthcare & Life Sciences)
**Deadline:** March 8, 2026 | 11:59 PM IST (Extended)
**Budget:** $100 AWS credits

---

## Evaluation Order (Sequential & Eliminative)

```
STEP 1: PPT reviewed first        -> If fails, NOTHING else is reviewed
STEP 2: Demo Video reviewed next   -> Only if PPT passes
STEP 3: Working Prototype URL      -> Only if Video passes
STEP 4: GitHub Repository          -> Only if all above pass
```

**Priority order for our work: PPT > Video > Live Prototype > Code Quality**

---

## DAY 1 (Feb 28) - Foundation + AI Core -- DONE

- [x] AWS Setup - Verify Bedrock model access in us-east-1
- [x] Project scaffolding - monorepo structure
- [x] Synthetic data - 8 Indian clinical consultation narratives
- [x] Synthetic data - 15 India-relevant clinical trials
- [x] Prompt template - SOAP Note generation
- [x] Prompt template - Patient Summary generation
- [x] Prompt template - Referral Letter generation
- [x] Prompt template - Clinical Trial Matching
- [x] Prompt template - Discharge Summary generation
- [x] Lambda function - `process_consultation.py` (monolithic mode with caching)
- [x] Local dev server - `local_server.py` for testing
- [x] **Bedrock Agent Tool Executor** - `agent_tool_executor.py` (5 tools: SOAP, Summary, Referral, Discharge, Trials)
- [x] **Bedrock Agent Invoker** - `invoke_agent.py` (API Gateway -> Multi-Agent orchestration)
- [x] **Multi-Agent Setup Script** - `scripts/setup_multi_agent.py` (Supervisor + 4 specialists)
- [x] React app scaffold - Vite + TypeScript + Tailwind
- [x] Login page - Doctor profiles + Patient phone+OTP login
- [x] Dashboard page - Consultation list + stats
- [x] Consultation Input page - Text area + voice + sample cases
- [x] Results page - 5-tab view (SOAP/Summary/Referral/Discharge/Trials)
- [x] Patient Portal page - Visit history from DynamoDB
- [x] Frontend build passes with zero errors

---

## DAY 2 (Mar 1) - Deploy + PPT -- DONE

### Deploy Agentic Backend to AWS
- [x] CloudFormation template with all 13 services
- [x] Deploy via GitHub Actions CI/CD pipeline
- [x] Lambda x5: Agent Invoker (+ Function URL) + Tool Executor + Trial Fetcher + Visit API + Translate
- [x] Multi-Agent Collaboration: Supervisor + 4 specialists (SOAP, Summary, Referral, Trial)
- [x] IAM roles with inference-profile ARNs for cross-region Nova Lite/Micro
- [x] AmazonBedrockFullAccess on agent service role
- [x] Resource-based Lambda permission for bedrock.amazonaws.com
- [x] Agent aliases (prod) created and updated after each prepare
- [x] API Gateway REST API with CORS (6 endpoints)
- [x] Bedrock Knowledge Base + OpenSearch Serverless for RAG trial matching
- [x] DynamoDB x2 tables (cache + visits with GSI)
- [x] Cognito Identity Pool for Transcribe Medical
- [x] EventBridge daily trial data refresh
- [x] CloudFront CDN with HTTPS + SPA routing
- [x] Frontend deployed to S3 via CI/CD
- [x] End-to-end tested on live URL

### Frontend
- [x] Wired to live API Gateway URL
- [x] Multi-agent toggle (process-agent endpoint)
- [x] Save/fetch visits via Visit API
- [x] Transcribe Medical real-time streaming
- [x] Loading states and error scenarios
- [x] 9 Indian language translation on all tabs

### PPT
- [x] 12 slides covering problem, solution, architecture, AWS services, AI pipeline, responsible AI, India impact, RAG pipeline, roadmap
- [x] WHY AI is required: Unstructured -> structured multi-format
- [x] HOW AWS services are used: 13 services deployed via CloudFormation
- [x] WHAT value the AI layer adds: 5 outputs, confidence scoring, trial matching, speech-to-text, multilingual

---

## DAY 3 (Mar 2) - Demo Video + Polish -- DONE

- [x] Demo video script written
- [x] Problem statement + solution overview
- [x] Live demo walkthrough (all tabs, all outputs)
- [x] AWS architecture deep-dive
- [x] Impact + roadmap
- [x] Recorded and uploaded

---

## DAY 4-8 (Mar 4-8) - Final Testing + Debugging + Submit -- DONE

- [x] Live URL loads on Chrome, Firefox, Edge
- [x] All sample consultations produce valid outputs
- [x] All 5 output tabs render correctly
- [x] Disclaimers visible on every AI-generated output
- [x] Confidence scores display correctly
- [x] Patient portal with visit history works
- [x] Debug multi-agent accessDeniedException (root cause: inference profile IAM)
- [x] Fix agent service role (attach AmazonBedrockFullAccess)
- [x] Fix Tool Executor Lambda role (add inference-profile ARNs)
- [x] Fix collaborator output parsing in invoke_agent.py (collaboratorInvocationOutput)
- [x] Remove debug steps from CI/CD workflow
- [x] Remove URLs from GitHub Step Summary (public repo)
- [x] Update all documentation
- [x] Final code push to GitHub

---

## Submission Requirements

| Eval Order | Requirement | Status |
|:--:|-------------|:------:|
| **1st** | **Project PPT** (10-12 slides) | DONE |
| **2nd** | **Demo Video** (max 3 min) | DONE |
| **3rd** | **Working Prototype URL** | DONE |
| **4th** | **GitHub Repository** | DONE |
| -- | Project Summary | DONE |

---

## AWS Services (13 Deployed)

| Service | Purpose | Status |
|---------|---------|:------:|
| **Amazon Bedrock** (Nova Lite + Nova Micro) | Core AI — Converse API with cross-region inference profiles | DEPLOYED |
| **Bedrock Multi-Agent Collaboration** | Supervisor-Router: 1 supervisor + 4 specialist agents | DEPLOYED |
| **Bedrock Knowledge Bases** | RAG for clinical trial matching (Titan Embeddings V2 + OpenSearch Serverless) | DEPLOYED |
| **AWS Lambda** (Python 3.12, x5) | API + Agent Invoker + Tool Executor + Trial Fetcher + Visit API | DEPLOYED |
| **Amazon API Gateway** (REST) | Unified API with CORS (6 endpoints) | DEPLOYED |
| **Amazon S3** | Frontend hosting + Lambda code + Clinical trial data | DEPLOYED |
| **Amazon CloudFront** | CDN with HTTPS, SPA error routing | DEPLOYED |
| **Amazon DynamoDB** (x2 tables) | Response caching + Patient visits (composite keys, GSI) | DEPLOYED |
| **Amazon OpenSearch Serverless** | Vector store for clinical trial embeddings | DEPLOYED |
| **Amazon Cognito** | Identity Pool for Transcribe Medical browser access | DEPLOYED |
| **Amazon Transcribe Medical** | Real-time clinical speech-to-text streaming | DEPLOYED |
| **Amazon EventBridge** | Daily clinical trial data refresh from ClinicalTrials.gov | DEPLOYED |
| **AWS CloudFormation** | Infrastructure as Code — entire stack in one template | DEPLOYED |

---

## Scoring Strategy

| Criterion (Weight) | How We Score High |
|---|---|
| **Implementation (50%)** | 13 AWS services deployed via CloudFormation IaC. Bedrock Multi-Agent Collaboration (Supervisor + 4 Specialists). Converse API with retry/fallback (Nova Lite -> Nova Micro). DynamoDB caching. Knowledge Base RAG. Transcribe Medical streaming. EventBridge scheduling. CI/CD via GitHub Actions. |
| **Technical Depth (20%)** | Multi-agent orchestration with Supervisor-Router pattern. Cross-region inference profiles. Exponential backoff + jitter. Model-agnostic Converse API. Collaborator output trace parsing. Lambda Function URL (bypasses API Gateway 29s timeout). SHA-256 cache keys. Cognito unauthenticated identity. Composite DynamoDB keys with GSI. |
| **Cost Efficiency (10%)** | Amazon Nova Lite as primary model (~80% cheaper than Sonnet). Nova Micro fallback. DynamoDB PAY_PER_REQUEST + 24h TTL cache. Serverless everything. CloudFront caching. ~$0.003-0.01 per consultation. |
| **Impact (10%)** | 1 doctor per 1,511 people. 500+ patients/day in govt hospitals. ABDM alignment. 9 Indian languages. Clinical trial democratization. Two portals (Doctor + Patient). |
| **Completeness & Presentation (10%)** | Live URL, polished UI, rehearsed video, professional PPT, comprehensive README, full documentation. |
