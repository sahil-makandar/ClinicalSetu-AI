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
- [ ] **Slide 4:** Architecture diagram (Prototype: solid lines + Production: dashed lines)
  - Must clearly show: React → Amplify → API Gateway → Invoker Lambda → **Bedrock Agent** → Tool Executor Lambda → Bedrock (Claude 3 Sonnet)
  - Also show: Bedrock Agent → Knowledge Base (RAG) → S3
- [ ] **Slide 5:** AWS Services - WHY each service + HOW it's used + WHAT value it adds
  - **Bedrock Agent**: Agentic orchestration - DECIDES which tools to call based on consultation
  - **Bedrock (Claude 3 Sonnet)**: Foundation model for clinical reasoning
  - **Knowledge Bases**: RAG pipeline for semantic trial matching
  - **Lambda** (x2): Serverless compute - Invoker + Tool Executor
  - **API Gateway**: Secure REST API with CORS
  - **Amplify**: CI/CD + hosting from GitHub
  - **S3**: Clinical trial data store for KB
- [ ] **Slide 6:** AI Pipeline deep-dive - **agentic tool use**, prompt engineering, JSON schema validation, confidence scoring
- [ ] **Slide 7:** Demo screenshots (SOAP Note, Patient Summary, Referral Letter, Trial Matches)
- [ ] **Slide 8:** Responsible AI - non-diagnostic by design, doctor-in-the-loop validation, "AI-Generated" disclaimers, synthetic data only, Bedrock Guardrails
- [ ] **Slide 9:** India Impact - ABDM alignment, rural telemedicine, multilingual roadmap, clinical trial access democratization
- [ ] **Slide 10:** RAG Pipeline for Trial Matching - S3 → Titan Embeddings → Knowledge Base → semantic search → confidence scoring
- [ ] **Slide 11:** Production Roadmap - Cognito auth, Step Functions orchestration, DynamoDB persistence, Transcribe Medical speech-to-text, HealthLake FHIR
- [ ] **Slide 12:** Summary + key differentiators + call to action

### Must answer these 3 questions clearly in PPT (evaluation criteria):
- [ ] **WHY AI is required:** Unstructured clinical narratives → structured multi-format outputs. Rule-based systems can't do this.
- [ ] **HOW AWS services are used:** Architecture slide shows exact service-to-service flow
- [ ] **WHAT value the AI layer adds:** 4 outputs from 1 input, confidence scoring, trial matching via RAG

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
| **Amazon Bedrock Agent** | Agentic orchestration with tool use | ✅ code | ✅ HIGHLIGHT |
| Amazon Bedrock (Claude 3 Sonnet) | Foundation model - clinical reasoning | ✅ code | ✅ |
| Bedrock Knowledge Bases | RAG for clinical trial matching | ⬜ deploy | ✅ |
| AWS Lambda (x2 Python) | Invoker + Tool Executor | ✅ code | ✅ |
| Amazon API Gateway | REST API endpoint | ⬜ deploy | ✅ |
| AWS Amplify | Frontend hosting from GitHub | ⬜ deploy | ✅ |
| Amazon S3 | Trial data store for KB | ⬜ deploy | ✅ |
| *Amazon Cognito* | *Auth (roadmap)* | 📋 | ✅ roadmap slide |
| *Amazon DynamoDB* | *Persistence (roadmap)* | 📋 | ✅ roadmap slide |
| *Amazon Transcribe Medical* | *Speech-to-text (roadmap)* | 📋 | ✅ roadmap slide |
| *AWS HealthLake* | *FHIR integration (roadmap)* | 📋 | ✅ roadmap slide |

---

## Scoring Strategy

| Criterion (Weight) | How We Score High |
|---|---|
| **Technical Excellence (30%)** | **Bedrock Agent** with tool use (agentic, not just prompts). KB RAG for trials. 2 Lambdas + API GW + Amplify. JSON validation, safety guardrails, serverless. |
| **Innovation & Creativity (30%)** | **Agentic AI** (agent decides tools). "Capture Once" = 4 outputs from 1 input. Trial matching via RAG. Confidence scoring. Non-diagnostic by design. |
| **Impact & Relevance (25%)** | 1 doctor per 1,511 people. 500+ patients/day in govt hospitals. ABDM alignment. Rural telemedicine. Multilingual roadmap. Clinical trial democratization. |
| **Completeness & Presentation (15%)** | Live URL, polished UI, rehearsed video, professional PPT, comprehensive README. |
