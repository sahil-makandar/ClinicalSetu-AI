# ClinicalSetu - Prototype Build Checklist

**Hackathon:** AI for Bharat (Professional Track - Healthcare & Life Sciences)
**Deadline:** March 8, 2026 | 11:59 PM IST (Extended)
**Budget:** $100 AWS credits

---

## ⚠️ CRITICAL: Evaluation Order (Sequential & Eliminative)

```
STEP 1: PPT reviewed first        → If fails, NOTHING else is reviewed
STEP 2: Demo Video reviewed next   → Only if PPT passes
STEP 3: Working Prototype URL      → Only if Video passes
STEP 4: GitHub Repository          → Only if all above pass
```

**Priority order for our work: PPT > Video > Live Prototype > Code Quality**

---

## DAY 1 (Feb 28) - Foundation + AI Core ✅ DONE

- [x] AWS Setup - Verify Bedrock model access in us-east-1
- [x] Project scaffolding - monorepo structure
- [x] Synthetic data - 8 Indian clinical consultation narratives
- [x] Synthetic data - 15 India-relevant clinical trials
- [x] Prompt template - SOAP Note generation
- [x] Prompt template - Patient Summary generation
- [x] Prompt template - Referral Letter generation
- [x] Prompt template - Clinical Trial Matching
- [x] Lambda function - `process_consultation.py` (sequential mode for local testing)
- [x] Local dev server - `local_server.py` for testing
- [x] **Bedrock Agent Tool Executor** - `agent_tool_executor.py` (4 tools: SOAP, Summary, Referral, Trials)
- [x] **Bedrock Agent Invoker** - `invoke_agent.py` (API Gateway → Agent orchestration)
- [x] **AWS Setup Script** - `scripts/setup_bedrock_agent.py` (provisions Agent, IAM, S3, Action Groups)
- [x] React app scaffold - Vite + TypeScript + Tailwind
- [x] Login page - Demo doctor profiles + branding
- [x] Dashboard page - Consultation list + stats
- [x] Consultation Input page - Text area + voice + sample cases
- [x] Results page - 4-tab view (SOAP/Summary/Referral/Trials)
- [x] Frontend build passes with zero errors

---

## DAY 2 (Mar 1) - Deploy + PPT 🔄 TODAY

### MORNING: Deploy Agentic Backend to AWS (Person A)
- [ ] Deploy **ClinicalSetu-ToolExecutor** Lambda (agent_tool_executor.py, 1024MB, 120s timeout)
- [ ] Deploy **ClinicalSetu-Invoker** Lambda (invoke_agent.py, 256MB, 120s timeout)
- [ ] Run `python scripts/setup_bedrock_agent.py` to provision:
  - [ ] S3 bucket with clinical trials data
  - [ ] IAM roles (Agent role + KB role)
  - [ ] Bedrock Agent with Claude 3 Sonnet
  - [ ] Action Group with 4 clinical tools
  - [ ] Agent alias (production)
- [ ] Set Agent ID + Alias ID as env vars on Invoker Lambda
- [ ] Create API Gateway REST API (`POST /api/process`, CORS enabled) → Invoker Lambda
- [ ] **Optional**: Create Bedrock Knowledge Base for RAG trial matching
- [ ] Deploy frontend to AWS Amplify (connect GitHub, get live URL)
- [ ] Test end-to-end on live URL

### MORNING: Frontend Polish (Person B)
- [ ] Wire frontend to live API Gateway URL
- [ ] Test end-to-end: text in → 4 AI outputs displayed
- [ ] Handle loading states and error scenarios
- [ ] Take screenshots of every screen for PPT

### AFTERNOON: PPT - THE #1 PRIORITY (Both people)
- [ ] **Slide 1:** Title + Team Sahrova + "Capture Once. Reuse Responsibly."
- [ ] **Slide 2:** Problem (4 pain points: documentation burden, poor continuity, fragmented referrals, missed trials) + India stats (1 doctor per 1,511 people, 500+ patients/day in govt OPDs)
- [ ] **Slide 3:** Solution overview - single input → 4 AI outputs diagram
- [ ] **Slide 4:** Architecture diagram (all 9 AWS services)
  - Must clearly show: React → CloudFront → S3 → API Gateway → Lambda → Bedrock (Nova Lite / Claude Haiku fallback)
  - Also show: Browser → Cognito → Transcribe Medical (streaming), Lambda → DynamoDB (cache)
  - GitHub Actions CI/CD pipeline deploying CloudFormation IaC
- [ ] **Slide 5:** AWS Services - WHY each service + HOW it's used + WHAT value it adds
  - **Amazon Bedrock** (Nova Lite + Claude Haiku): Converse API with model fallback chain
  - **AWS Lambda**: Serverless backend with retry/backoff, partial result handling
  - **API Gateway**: REST API with CORS (`/process`, `/translate`)
  - **Amazon S3**: Frontend static hosting + Lambda deployment packages
  - **Amazon CloudFront**: CDN with HTTPS, SPA routing
  - **Amazon DynamoDB**: Response caching (SHA-256 keys, 24h TTL, PAY_PER_REQUEST)
  - **Amazon Cognito**: Identity Pool for unauthenticated Transcribe Medical access
  - **Amazon Transcribe Medical**: Real-time clinical speech-to-text streaming
  - **CloudFormation**: Infrastructure as Code — one-click deployment
- [ ] **Slide 6:** AI Pipeline deep-dive - Converse API, retry/fallback chain, prompt engineering, JSON schema validation, confidence scoring, DynamoDB caching
- [ ] **Slide 7:** Demo screenshots (SOAP Note, Patient Summary, Referral Letter, Trial Matches)
- [ ] **Slide 8:** Responsible AI - non-diagnostic by design, doctor-in-the-loop validation, "AI-Generated" disclaimers, synthetic data only, Bedrock Guardrails
- [ ] **Slide 9:** India Impact - ABDM alignment, rural telemedicine, multilingual roadmap, clinical trial access democratization
- [ ] **Slide 10:** RAG Pipeline for Trial Matching - S3 → Titan Embeddings → Knowledge Base → semantic search → confidence scoring
- [ ] **Slide 11:** Production Roadmap - Step Functions parallel orchestration, HealthLake FHIR, ABDM/ABHA integration, Bedrock Guardrails
- [ ] **Slide 12:** Summary + key differentiators + call to action

### Must answer these 3 questions clearly in PPT (evaluation criteria):
- [ ] **WHY AI is required:** Unstructured clinical narratives → structured multi-format outputs. Rule-based systems can't do this.
- [ ] **HOW AWS services are used:** 9 services in architecture slide — every one deployed and functional
- [ ] **WHAT value the AI layer adds:** 5 outputs from 1 input, confidence scoring, trial matching, medical speech-to-text, multilingual translation

---

## DAY 3 (Mar 2) - Demo Video + Polish

### MORNING: Demo Video (max 3 min) - THE #2 PRIORITY
- [ ] Write script (every second counts)
- [ ] 0:00-0:20 Problem statement (Indian healthcare documentation burden)
- [ ] 0:20-0:40 Solution overview + architecture (use PPT slides)
- [ ] 0:40-2:00 LIVE demo walkthrough:
  - Login → select doctor
  - Load sample case OR enter narrative
  - Click "Process with AI" → show progress
  - Show SOAP Note tab (confidence scores, structured output)
  - Show Patient Summary tab (plain language)
  - Show Referral Letter tab (urgency, checklist)
  - Show Trial Matches tab (confidence bars, matched criteria)
  - Edit a section → Approve → Finalize
- [ ] 2:00-2:30 AWS services deep-dive (show architecture diagram)
- [ ] 2:30-2:50 Impact (30M consultations/day, ABDM, rural access)
- [ ] 2:50-3:00 Production roadmap + closing
- [ ] Record with OBS/screen recorder, clear audio
- [ ] Rehearse at least 2x before final recording
- [ ] Upload to YouTube/Google Drive (public link)

### AFTERNOON: Final Polish
- [ ] UI polish - responsive, loading animations, branding consistency
- [ ] Error handling - graceful messages for all failure modes
- [ ] Update README.md with live URL, architecture, setup instructions, screenshots
- [ ] Write project summary (500 words)

---

## DAY 4 (Mar 4) - Final Testing + Submit ⚠️ NO NEW FEATURES

### Final Testing Checklist
- [ ] Live URL loads on Chrome, Firefox, Edge
- [ ] Live URL loads on mobile browser
- [ ] All 5 sample consultations produce valid outputs
- [ ] All 4 output tabs render correctly with data
- [ ] Disclaimers visible on every AI-generated output
- [ ] Confidence scores display correctly (green/yellow/red)
- [ ] Edit → Approve → Finalize workflow works
- [ ] No console errors
- [ ] Test from different network (not home WiFi)

### Submission (before 11:59 PM IST)
- [ ] Push final code to GitHub
- [ ] Verify GitHub repo is public
- [ ] Submit on hackathon portal:
  - [ ] GitHub repo link
  - [ ] Working prototype URL (Amplify)
  - [ ] Demo video link (YouTube/Drive)
  - [ ] Project PPT (uploaded)
  - [ ] Project summary (text)

---

## Submission Requirements vs Evaluation Priority

| Eval Order | Requirement | Status | Priority |
|:--:|-------------|:------:|:--------:|
| **1st** | **Project PPT** (10-12 slides) | ⬜ | 🔴 HIGHEST |
| **2nd** | **Demo Video** (max 3 min) | ⬜ | 🔴 HIGH |
| **3rd** | **Working Prototype URL** | ⬜ | 🟡 HIGH |
| **4th** | **GitHub Repository** | ⬜ | 🟡 MEDIUM |
| -- | Project Summary | ⬜ | 🟢 QUICK |

---

## AWS Services (for slides/docs)

| Service | Purpose | Built? | Mentioned in PPT? |
|---------|---------|:------:|:------------------:|
| **Amazon Bedrock** (Nova Lite + Claude Haiku fallback) | Core AI engine — Converse API with retry/fallback | ✅ deployed | ✅ HIGHLIGHT |
| **Bedrock Multi-Agent Collaboration** | Supervisor-Router: 1 supervisor + 4 specialist agents | ✅ built | ✅ HIGHLIGHT |
| **AWS Lambda** (Python 3.12, x3) | Monolithic + Agent Invoker + Tool Executor | ✅ deployed | ✅ |
| **Amazon API Gateway** (REST) | Unified API with CORS (`/process`, `/process-agent`, `/translate`) | ✅ deployed | ✅ |
| **Amazon S3** | Frontend hosting + Lambda code storage | ✅ deployed | ✅ |
| **Amazon CloudFront** | CDN with HTTPS for frontend | ✅ deployed | ✅ |
| **Amazon DynamoDB** | Response caching with 24h TTL (PAY_PER_REQUEST) | ✅ deployed | ✅ |
| **Amazon Cognito** | Identity Pool for Transcribe Medical browser access | ✅ deployed | ✅ |
| **Amazon Transcribe Medical** | Real-time clinical speech-to-text streaming | ✅ deployed | ✅ |
| Bedrock Knowledge Bases | RAG for clinical trial matching | ⬜ optional | ✅ |
| *AWS HealthLake* | *FHIR integration (roadmap)* | 📋 | ✅ roadmap slide |

---

## Scoring Strategy

| Criterion (Weight) | How We Score High |
|---|---|
| **Implementation (50%)** | 10 AWS services deployed via CloudFormation IaC. Bedrock Multi-Agent Collaboration (Supervisor + 4 Specialists). Converse API with retry/fallback (Nova Lite → Claude Haiku). DynamoDB caching. Transcribe Medical streaming. CI/CD via GitHub Actions. |
| **Technical Depth (20%)** | Multi-agent orchestration with Supervisor-Router pattern. Exponential backoff + jitter. Model-agnostic Converse API. Auto-fallback from multi-agent to monolithic. SHA-256 cache keys. Cognito unauthenticated identity. |
| **Cost Efficiency (10%)** | Amazon Nova Lite as primary model (~80% cheaper than Sonnet). DynamoDB PAY_PER_REQUEST + 24h TTL cache. Serverless everything. CloudFront caching. |
| **Impact (10%)** | 1 doctor per 1,511 people. 500+ patients/day in govt hospitals. ABDM alignment. 9 Indian languages. Clinical trial democratization. |
| **Completeness & Presentation (10%)** | Live URL, polished UI, rehearsed video, professional PPT, comprehensive README. |
