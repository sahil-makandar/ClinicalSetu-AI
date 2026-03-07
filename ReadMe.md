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

---

## AWS Architecture (10 Services — All Deployed)

```
┌──────────────────────────────────────────────────────────────┐
│                       AWS CLOUD                               │
│                                                               │
│  GitHub Actions CI/CD ──► CloudFormation (IaC)                │
│                                                               │
│  ┌───────────┐  ┌──────────┐  ┌──────────────┐  ┌────────┐  │
│  │CloudFront │  │   S3     │  │ API Gateway  │  │ Lambda │  │
│  │  (CDN)    │─►│(Frontend)│  │  (REST API)  │─►│x3      │  │
│  │  HTTPS    │  │          │  │  + CORS      │  │Python  │  │
│  └───────────┘  └──────────┘  └──────────────┘  └───┬────┘  │
│                                                       │       │
│                   ┌───────────────┬───────────────────┤       │
│                   ▼               ▼                   ▼       │
│           ┌──────────────┐ ┌──────────┐  ┌─────────────────┐ │
│           │ Amazon       │ │ DynamoDB │  │ Bedrock Agents  │ │
│           │ Bedrock      │ │ (Cache)  │  │ Multi-Agent     │ │
│           │ Nova Lite    │ │ 24h TTL  │  │ Collaboration   │ │
│           │ + Haiku      │ │ PAY/REQ  │  │ (Supervisor +   │ │
│           │ (fallback)   │ └──────────┘  │  4 Specialists) │ │
│           └──────────────┘               └─────────────────┘ │
│                                                               │
│  Browser ──► Cognito Identity Pool ──► Transcribe Medical     │
│              (unauthenticated)          (streaming speech)     │
└──────────────────────────────────────────────────────────────┘
```

### AWS Services

| Service | Purpose |
|---------|---------|
| **Amazon Bedrock** (Nova Lite + Claude Haiku) | Core AI engine — Converse API with model fallback chain |
| **Bedrock Multi-Agent Collaboration** | Supervisor-Router pattern: 1 supervisor + 4 specialist agents |
| **AWS Lambda** (Python 3.12, x3) | Monolithic handler + Agent Invoker + Tool Executor |
| **Amazon API Gateway** (REST) | Unified API with CORS (`/api/process`, `/api/process-agent`, `/api/translate`) |
| **Amazon S3** | Frontend static hosting + Lambda deployment packages |
| **Amazon CloudFront** | CDN with HTTPS, SPA error routing |
| **Amazon DynamoDB** | Response caching — SHA-256 keys, 24h TTL, PAY_PER_REQUEST |
| **Amazon Cognito** | Identity Pool for secure browser-to-AWS Transcribe access |
| **Amazon Transcribe Medical** | Real-time clinical speech-to-text streaming |
| **AWS CloudFormation** | Infrastructure as Code — entire stack in one template |

### CI/CD

Push to `main` triggers GitHub Actions which:
1. Packages Lambda function
2. Uploads to S3
3. Deploys CloudFormation stack (creates/updates all 9 services)
4. Builds React frontend with API URL injected
5. Syncs to S3 + invalidates CloudFront cache

---

## Technical Highlights

- **Bedrock Multi-Agent Collaboration** — Supervisor-Router pattern: supervisor agent orchestrates 4 specialist agents (SOAP, Summary, Referral+Discharge, Trials). Each agent has its own instruction set, tools, and domain expertise. Mirrors real clinical workflows where different specialists handle different documentation.
- **Bedrock Converse API** — Model-agnostic; works with Nova Lite and Claude Haiku without format changes
- **Retry with exponential backoff + jitter** — 3 retries per model, handles Bedrock throttling
- **Model fallback chain** — Nova Lite (primary) → Claude Haiku (auto-failover if throttled)
- **Multi-agent → Monolithic fallback** — If multi-agent times out, auto-falls back to monolithic pipeline
- **Partial result handling** — Each AI step is isolated; one failure doesn't block other outputs
- **DynamoDB response caching** — SHA-256 hash of input, 24h TTL, fail-safe (cache errors never break main flow)
- **Amazon Transcribe Medical** — Real-time streaming via Cognito unauthenticated identity, clinical vocabulary optimized
- **9 Indian language translation** — On-demand via Bedrock, available on all output tabs

---

## Responsible AI

ClinicalSetu is **NOT a diagnostic tool**. It is a **documentation assistant**.

- Non-diagnostic by design — prompts explicitly instruct "documentation assistant, not diagnostic tool"
- Doctor-in-the-loop — every field is editable, nothing is final until doctor approves
- Confidence scoring — per-section scores with color coding (green/yellow/red)
- AI disclaimers on every output tab
- Synthetic data only — zero real patient data

---

## Project Structure

```
├── backend/
│   ├── lambda/
│   │   ├── process_consultation.py    # Monolithic handler (Converse API + caching)
│   │   ├── invoke_agent.py            # Multi-agent invoker (Supervisor Agent)
│   │   └── agent_tool_executor.py     # Tool executor (called by collaborator agents)
│   ├── prompts/                       # Prompt templates for each output
│   └── local_server.py               # Local dev server
├── frontend/
│   ├── src/
│   │   ├── pages/                     # ConsultationPage, ResultsPage, LoginPage
│   │   ├── services/
│   │   │   ├── api.ts                 # API client (multi-agent toggle)
│   │   │   └── transcribeService.ts   # Amazon Transcribe Medical streaming
│   │   └── types/                     # TypeScript interfaces
│   └── package.json
├── infrastructure/
│   └── cloudformation.yaml            # All AWS services defined (IaC)
├── .github/workflows/
│   └── deploy.yml                     # CI/CD pipeline
└── scripts/
    ├── setup_multi_agent.py           # Provisions 5 Bedrock agents
    └── package_lambda.py              # Lambda packaging script
```

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

- **Amazon Nova Lite** as primary model — ~80% cheaper than Claude Sonnet
- **DynamoDB PAY_PER_REQUEST** — pay only for what you use, 25GB free tier
- **Response caching** — repeat consultations hit cache, zero Bedrock cost
- **Serverless everything** — zero cost when idle
- Estimated cost per consultation: **$0.003-0.01** (5 Bedrock calls)

---

## About

Built by **Team Sahrova** for the AI for Bharat Hackathon (Professional Track - Healthcare & Life Sciences).

*One narrative. Five outputs. Nine languages. Zero diagnoses.*
