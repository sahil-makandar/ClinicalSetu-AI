# ClinicalSetu

**Capture Once. Reuse Responsibly.**

AI-powered clinical documentation bridge for India's 1.4 billion — built on AWS.

**Team Sahrova** | AI for Bharat Hackathon | Professional Track - Healthcare & Life Sciences

---

## Problem

India has **1 doctor per 1,511 people** (WHO recommends 1:1,000). Government hospital doctors see 80-100 patients/day with ~4 minutes per patient. 70% of that time goes to paperwork. Patients leave without understanding what was discussed. Referrals are incomplete. Clinical trial discovery never happens at point of care.

## Solution

Doctor speaks or types **one clinical narrative**. ClinicalSetu generates **5 structured outputs**:

1. **SOAP Note** — Structured clinical documentation for EMR
2. **Patient Summary** — Plain-language explanation (translatable to 9 Indian languages)
3. **Referral Letter** — Context-rich specialist referral with urgency scoring
4. **Discharge Summary** — Complete visit record with treatment plan
5. **Clinical Trial Matches** — RAG-powered trial eligibility matching with confidence scores

Every output is **editable** by the doctor, shows **confidence scores**, and includes **AI disclaimers**.

### Two Portals

- **Doctor Portal** — Conduct consultations, review AI outputs, finalize and save visit records
- **Patient Portal** — Patients log in with phone + OTP, view their visit history, medications, follow-up instructions, and warning signs across all hospitals

---

## AWS Architecture (13 Services — All Deployed)

```
┌──────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD                                │
│                                                                  │
│  GitHub Actions CI/CD ──► CloudFormation (IaC)                   │
│                                                                  │
│  ┌───────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────┐ │
│  │CloudFront │  │   S3     │  │ API Gateway  │  │  Lambda    │ │
│  │  (CDN)    │─►│(Frontend)│  │  (REST API)  │─►│  x5        │ │
│  │  HTTPS    │  │          │  │  + CORS      │  │  Python    │ │
│  └───────────┘  └──────────┘  └──────────────┘  └─────┬──────┘ │
│                                                         │        │
│         ┌──────────────┬──────────────┬─────────────────┤        │
│         ▼              ▼              ▼                  ▼        │
│  ┌────────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │  Bedrock   │ │ DynamoDB │ │ Bedrock      │ │ Bedrock      │ │
│  │  Nova Lite │ │ x2 Tables│ │ Multi-Agent  │ │ Knowledge    │ │
│  │  + Micro   │ │ Cache +  │ │ Collaboration│ │ Bases (RAG)  │ │
│  │ (fallback) │ │ Visits   │ │ Supervisor + │ │ Clinical     │ │
│  │            │ │          │ │ 4 Specialists│ │ Trials       │ │
│  └────────────┘ └──────────┘ └──────────────┘ └──────────────┘ │
│                                                                  │
│  Browser ──► Cognito Identity Pool ──► Transcribe Medical        │
│              (unauthenticated)          (streaming speech)        │
└──────────────────────────────────────────────────────────────────┘
```

### AWS Services

| Service | Purpose |
|---------|---------|
| **Amazon Bedrock** (Nova Lite + Nova Micro) | Core AI engine — Converse API with cross-region inference profiles and model fallback chain |
| **Bedrock Multi-Agent Collaboration** | Supervisor-Router pattern: 1 supervisor + 4 specialist agents |
| **Bedrock Knowledge Bases** | RAG pipeline for clinical trial matching (ClinicalTrials.gov real data, Titan Embeddings, OpenSearch Serverless) |
| **AWS Lambda** (Python 3.12, x5) | Agent Invoker + Tool Executor + Trial Fetcher + Visit API + Translate |
| **Amazon API Gateway** (REST) | Unified API with CORS (`/api/process`, `/api/process-agent`, `/api/translate`, `/api/save-visit`, `/api/patient-visits`) |
| **Amazon S3** | Frontend static hosting + Lambda deployment packages |
| **Amazon CloudFront** | CDN with HTTPS, SPA error routing |
| **Amazon DynamoDB** (x2 tables) | Response caching (SHA-256 keys, 24h TTL) + Patient visits persistence (composite keys, GSI) |
| **Amazon OpenSearch Serverless** | Vector store for clinical trial embeddings (used by Knowledge Bases) |
| **Amazon Cognito** | Identity Pool for secure browser-to-AWS Transcribe access |
| **Amazon Transcribe Medical** | Real-time clinical speech-to-text streaming |
| **Amazon EventBridge** | Scheduled daily clinical trial data refresh from ClinicalTrials.gov |
| **AWS CloudFormation** | Infrastructure as Code — entire stack in one template |

### CI/CD

Push to `main` triggers GitHub Actions which:
1. Fetches latest clinical trial data from ClinicalTrials.gov
2. Packages Lambda functions into deployment ZIPs
3. Uploads to S3
4. Deploys CloudFormation stack (creates/updates all 13 services)
5. Sets up Bedrock Multi-Agent Collaboration (Supervisor + 4 specialists with IAM roles, action groups, aliases)
6. Sets up Bedrock Knowledge Base + OpenSearch Serverless for RAG
7. Seeds synthetic visit data into DynamoDB
8. Builds React frontend with API URL + Cognito pool ID injected
9. Syncs to S3 + invalidates CloudFront cache

---

## Technical Highlights

- **Bedrock Multi-Agent Collaboration** — Supervisor-Router pattern: supervisor agent orchestrates 4 specialist agents (SOAP, Summary, Referral+Discharge, Trials). Each agent has its own instruction set, tools, and domain expertise. Mirrors real clinical workflows where different specialists handle different documentation.
- **RAG Pipeline for Trial Matching** — Real clinical trial data from ClinicalTrials.gov, embedded with Amazon Titan Embeddings, stored in OpenSearch Serverless, queried via Bedrock Knowledge Bases for semantic trial matching with confidence scores.
- **Patient Data Persistence** — DynamoDB visits table with composite keys (`HOSPITAL#<hospital>#PHONE#<phone>` PK, `VISIT#<timestamp>` SK) for multi-tenant isolation. Global Secondary Index on phone number enables cross-hospital patient queries.
- **Patient Portal with Phone+OTP Login** — Patients authenticate with phone number + OTP, view visit history from any hospital/clinic that used ClinicalSetu. Visit details include diagnosis, medications, follow-up instructions, and warning signs.
- **Bedrock Converse API** — Model-agnostic; works with Nova Lite and Nova Micro via cross-region inference profiles
- **Retry with exponential backoff + jitter** — 3 retries per model, handles Bedrock throttling
- **Model fallback chain** — Nova Lite (primary) → Nova Micro (auto-failover if throttled)
- **Lambda Function URL** — Bypasses API Gateway 29s timeout; supports long-running multi-agent orchestration
- **Partial result handling** — Each AI step is isolated; one failure doesn't block other outputs
- **DynamoDB response caching** — SHA-256 hash of input, 24h TTL, fail-safe (cache errors never break main flow)
- **EventBridge scheduled trial refresh** — Daily automated ClinicalTrials.gov data sync with Knowledge Base re-indexing
- **Amazon Transcribe Medical** — Real-time streaming via Cognito unauthenticated identity, clinical vocabulary optimized
- **9 Indian language translation** — On-demand via Bedrock, available on all output tabs

---

## Data Flow

### Doctor → Patient Journey

```
1. Doctor logs in (SSO/email)
2. Doctor starts consultation → speaks or types clinical narrative
3. Amazon Transcribe Medical converts speech to text (real-time)
4. Doctor enters patient phone number + details
5. Click "Process with AI" → Multi-Agent Collaboration processes narrative
   ├── SOAP Specialist Agent → Structured clinical note
   ├── Summary Specialist Agent → Patient-friendly summary
   ├── Referral+Discharge Agent → Referral letter + discharge summary
   └── Trials Specialist Agent → RAG-powered trial matching
6. Doctor reviews, edits, validates each output
7. Doctor clicks "Finalize" → visit saved to DynamoDB (linked to patient phone)
8. Patient logs in with phone + OTP → sees visit summary, meds, follow-up
```

---

## Responsible AI

ClinicalSetu is **NOT a diagnostic tool**. It is a **documentation assistant**.

- Non-diagnostic by design — prompts explicitly instruct "documentation assistant, not diagnostic tool"
- Doctor-in-the-loop — every field is editable, nothing is final until doctor approves
- Confidence scoring — per-section scores with color coding (green/yellow/red)
- AI disclaimers on every output tab
- Synthetic data only — zero real patient data
- Multi-tenant data isolation — hospital-scoped patient data with composite DynamoDB keys

---

## Project Structure

```
├── backend/
│   ├── lambda/
│   │   ├── process_consultation.py    # Standalone handler (Converse API + caching)
│   │   ├── invoke_agent.py            # Multi-agent invoker (Supervisor Agent + collaborator output parsing)
│   │   ├── agent_tool_executor.py     # Tool executor (called by collaborator agents via action groups)
│   │   ├── visit_api.py               # Patient visit persistence (save/fetch from DynamoDB)
│   │   └── fetch_trials.py            # ClinicalTrials.gov data fetcher + Knowledge Base sync
│   ├── prompts/                       # Prompt templates for each output
│   └── local_server.py               # Local dev server
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx          # Doctor SSO + Patient phone+OTP login
│   │   │   ├── DashboardPage.tsx      # Doctor dashboard with consultation history
│   │   │   ├── ConsultationPage.tsx   # Voice/text input + patient details + phone
│   │   │   ├── ResultsPage.tsx        # 4-tab AI outputs + finalize & save
│   │   │   └── PatientPortalPage.tsx  # Patient visit history from DynamoDB
│   │   ├── services/
│   │   │   ├── api.ts                 # API client (multi-agent toggle, save/fetch visits)
│   │   │   └── transcribeService.ts   # Amazon Transcribe Medical streaming
│   │   └── types/                     # TypeScript interfaces (Patient, Visit, etc.)
│   └── package.json
├── infrastructure/
│   └── cloudformation.yaml            # All AWS resources (IaC) — Lambda, API GW, DynamoDB x2, S3, CloudFront, Cognito
├── data/
│   └── clinical_trials/               # Real ClinicalTrials.gov data for RAG
├── .github/workflows/
│   └── deploy.yml                     # CI/CD pipeline
├── scripts/
│   ├── setup_multi_agent.py           # Provisions 5 Bedrock agents (supervisor + 4 specialists)
│   ├── setup_knowledge_base.py        # Sets up RAG pipeline (OpenSearch Serverless + Knowledge Base)
│   ├── package_lambda.py              # Lambda packaging script
│   ├── seed_visits.py                 # Seeds synthetic visit data into DynamoDB
│   ├── debug_agents.py                # 11-point diagnostic script for multi-agent debugging
│   └── setup_bedrock_agent.py         # Legacy single-agent setup
└── docs/
    ├── design.md                      # Enterprise architecture design
    ├── requirements.md                # Functional & non-functional requirements
    ├── checklist.md                   # Build checklist & scoring strategy
    └── DEPLOYMENT_GUIDE.md            # Manual deployment guide
```

---

## DynamoDB Schema

### Cache Table (Response Caching)
- **PK**: `cache_key` (SHA-256 hash of consultation input)
- **TTL**: 24 hours
- Stores complete AI processing results to avoid re-processing identical consultations

### Visits Table (Patient Data Persistence)
- **PK**: `HOSPITAL#{hospital}#PHONE#{phone}` — multi-tenant isolation per clinic
- **SK**: `VISIT#{ISO-timestamp}` — sorted by date
- **GSI** (`phone-index`): PK = `phone_number`, SK = `visit_date` — enables cross-hospital patient queries
- Stores: diagnosis, medications, patient summary, follow-up, warning signs, doctor/hospital info

---

## Local Development

```bash
# Backend
cd backend
pip install boto3
python local_server.py

# Frontend
cd frontend
npm install
cp .env.example .env  # Edit VITE_API_URL
npm run dev
```

## Deployment

Push to `main` branch — GitHub Actions handles everything automatically.

Required GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

---

## Cost Efficiency

- **Amazon Nova Lite** as primary model — ~80% cheaper than Claude Sonnet, cross-region inference profiles for high availability
- **Amazon Nova Micro** as fallback — automatic failover on throttling, even cheaper
- **DynamoDB PAY_PER_REQUEST** — pay only for what you use, 25GB free tier
- **Response caching** — repeat consultations hit cache, zero Bedrock cost
- **Serverless everything** — zero cost when idle
- Estimated cost per consultation: **$0.003-0.01** (multi-agent orchestration with 5 specialist tool calls)

---

## About

Built by **Team Sahrova** for the AI for Bharat Hackathon (Professional Track - Healthcare & Life Sciences).

*One narrative. Five outputs. Nine languages. Two portals. Zero diagnoses.*
