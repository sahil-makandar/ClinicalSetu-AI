# ClinicalSetu — PPT Slide-by-Slide Content

> **Instructions**: 12 slides total. Text goes on left half, visuals/icons/cliparts on right half. Keep text minimal on actual slides — this doc has full details for reference.

---

## SLIDE 1 — Title Slide

**Team Name**: Team Sahrova

**Problem Statement**: Healthcare & Life Sciences — AI-powered Clinical Documentation

**Team Leader Name**: Mahaboobsab Makandar

**ClinicalSetu** — *Capture Once. Reuse Responsibly.*

AI-powered clinical documentation bridge for India's 1.4 billion — built entirely on AWS.

> VISUAL (right half): ClinicalSetu logo/icon + AWS logo + a stethoscope-meets-circuit-board graphic. Keep the title slide clean and bold.

---

## SLIDE 2 — Brief about the Idea + Problem

**India's Healthcare Documentation Crisis**

- **1 doctor : 1,511 patients** (WHO recommends 1:1,000)
- Govt doctors see **80-100 patients/day** — only **4 min per patient**
- **70% of consultation time = paperwork**, not patient care
- Patients leave **confused** — no summary in their language
- Referrals **incomplete** — specialists re-ask everything
- Patient records **fragmented** across hospitals
- **Zero clinical trial discovery** at point of care

**Result**: Doctors burn out. Patients fall through cracks. Research stalls.

**Our Idea**: Doctor speaks/types **one clinical narrative** → ClinicalSetu's AI generates **5 structured outputs** (SOAP note, patient summary, referral letter, discharge summary, clinical trial matches) across **two portals** (doctor + patient) — all on AWS serverless infrastructure.

> VISUAL (right half): Infographic showing a stressed doctor with stack of papers, a clock showing "4 min", a confused patient, and broken chain between hospitals. Use icons for each pain point.

---

## SLIDE 3 — Why AI is Required + AI Value to User Experience

**AI is the core engine — not a wrapper or a chatbot layer**

| Without AI | With ClinicalSetu AI |
|-----------|---------------------|
| Doctor writes SOAP, summary, referral, discharge **separately — 4x effort** | **One narrative** → AI generates all 5 outputs simultaneously |
| Patient gets no summary or incomprehensible jargon | AI translates to **plain language in 9 Indian languages** |
| Referrals lack context → specialist wastes time | AI structures referral with **urgency scoring + full clinical context** |
| Clinical trial matching = **manual chart review** | **RAG pipeline** semantically matches against real ClinicalTrials.gov data |
| No voice input for busy doctors | **Amazon Transcribe Medical** — real-time clinical speech-to-text |

**Why this can't exist without AI:**
- Every consultation is **unique natural language** — templates/forms can't handle it
- **Multi-Agent Collaboration**: 4 specialist AI agents process in parallel (mirrors real hospital teams)
- **RAG (Retrieval-Augmented Generation)**: Real trial data retrieval, not hallucinated matches
- **Medical speech recognition**: Domain-specific voice capture with clinical vocabulary

**AI Value to User**: Transforms a 4-minute chaotic consultation into structured, actionable, multi-stakeholder documentation — saving **70% documentation time** and enabling doctors to see **20+ more patients/day**.

> VISUAL (right half): Before/After split graphic. Left side: doctor drowning in papers writing 4 separate documents. Right side: doctor speaking into mic, AI engine in middle, 5 clean documents flowing out. Use arrow/transformation visual.

---

## SLIDE 4 — How AWS Services Are Used + Architecture Diagram

**12 AWS Services — All Deployed, Fully Serverless**

| AWS Service | What It Does in ClinicalSetu |
|------------|-----|
| **Amazon Bedrock** (Nova Lite + Claude Haiku) | Core AI engine — Converse API with automatic model fallback |
| **Bedrock Multi-Agent Collaboration** | Supervisor + 4 specialist agents processing in parallel |
| **Bedrock Knowledge Bases** | RAG pipeline for clinical trial matching |
| **Amazon OpenSearch Serverless** | Vector store for trial embeddings (Titan Embeddings) |
| **AWS Lambda** (x4 functions) | All backend logic — zero servers to manage |
| **Amazon API Gateway** | REST API with CORS — 5 endpoints |
| **Amazon Transcribe Medical** | Real-time clinical speech-to-text in browser |
| **Amazon Cognito** | Secure identity for browser-to-AWS access |
| **Amazon DynamoDB** (x2 tables) | Response cache (24h TTL) + Patient visit data |
| **Amazon S3** | Frontend hosting + Lambda deployment packages |
| **Amazon CloudFront** | HTTPS CDN for global delivery |
| **AWS CloudFormation** | Entire infrastructure as code — one template |

**CI/CD**: GitHub Actions → auto-packages Lambda → deploys CloudFormation → builds frontend → syncs S3 → invalidates CloudFront cache. Push to `main` = full deployment.

> **ARCHITECTURE DIAGRAM TO CREATE (full right half or full slide):**
>
> Draw this as a layered architecture with arrows showing data flow:
>
> **Top Layer — User Layer:**
> - Doctor (browser) with mic icon → labeled "Voice/Text Input"
> - Patient (browser/phone) → labeled "Phone + OTP Login"
>
> **Second Layer — CDN + Hosting:**
> - CloudFront (CDN, HTTPS) → S3 (React Frontend)
> - Arrow from browsers to CloudFront
>
> **Third Layer — API Layer:**
> - API Gateway (REST, 5 endpoints) sitting in the middle
> - Arrow from CloudFront to API Gateway
> - Also show: Browser → Cognito Identity Pool → Transcribe Medical (separate path for voice, bypasses API Gateway)
>
> **Fourth Layer — Compute:**
> - Lambda x4 boxes: "Process Consultation" | "Agent Invoker" | "Tool Executor" | "Visit API"
> - Arrows from API Gateway to each Lambda
>
> **Fifth Layer — AI/ML Layer:**
> - Amazon Bedrock box containing: Nova Lite (primary) → Claude Haiku (fallback)
> - Bedrock Multi-Agent Collaboration box: Supervisor Agent → 4 sub-agents (SOAP, Summary, Referral+Discharge, Trials)
> - Bedrock Knowledge Bases → OpenSearch Serverless (vector store with Titan Embeddings)
> - Arrows from Lambdas to Bedrock services
>
> **Sixth Layer — Data Layer:**
> - DynamoDB Table 1: "Response Cache" (SHA-256 keys, 24h TTL)
> - DynamoDB Table 2: "Patient Visits" (composite keys, GSI on phone)
> - Arrow from Lambda to both DynamoDB tables
>
> **Side annotation:**
> - GitHub Actions → CloudFormation (CI/CD pipeline on the side)
>
> Use official AWS service icons for each service. Color code: orange for compute, blue for AI, green for data, purple for security.

---

## SLIDE 5 — List of Features

**Core Features**

- **Voice-First Clinical Input** — Speak naturally, Amazon Transcribe Medical captures with clinical vocabulary
- **AI-Powered SOAP Notes** — Auto-generated structured clinical documentation (Subjective, Objective, Assessment, Plan)
- **Patient Summary in 9 Languages** — Plain-language explanation translatable to Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi
- **Smart Referral Letters** — Context-rich specialist referrals with urgency scoring
- **Discharge Summaries** — Complete visit record with medications, follow-up plan, warning signs
- **Clinical Trial Matching (RAG)** — Semantic matching against real ClinicalTrials.gov data with confidence scores
- **Doctor Portal** — Dashboard, consultation history, AI-assisted documentation, finalize & save
- **Patient Portal** — Phone + OTP login, cross-hospital visit history, medications, follow-up instructions
- **Confidence Scoring** — Color-coded (green/yellow/red) per output section
- **Doctor-in-the-Loop** — Every AI output is editable and requires doctor approval before finalization
- **Response Caching** — Identical consultations served from DynamoDB cache (zero AI cost on repeat)
- **Model Fallback Chain** — Nova Lite → Claude Haiku auto-failover if throttled

> VISUAL (right half): Feature grid with icons — mic icon for voice, document icon for SOAP, globe icon for languages, arrow icon for referral, flask icon for trials, shield icon for responsible AI. Use a clean 2x6 or 3x4 grid layout.

---

## SLIDE 6 — Process Flow Diagram

**End-to-End User Flow**

> **FLOW DIAGRAM TO CREATE (full slide or large right section):**
>
> Draw a horizontal flow with two parallel tracks (Doctor Track on top, Patient Track on bottom), converging at DynamoDB in the middle:
>
> **DOCTOR TRACK (top row, left to right):**
> 1. **Doctor Login** (icon: person + lock) → "SSO/Email authentication"
> 2. **Dashboard** (icon: grid) → "View past consultations, start new one"
> 3. **Consultation Page** (icon: mic + keyboard) → "Voice input via Transcribe Medical OR text input + Enter patient phone number & details"
> 4. **Click 'Process with AI'** (icon: play button) → "Sends narrative to API Gateway → Lambda"
> 5. **Multi-Agent Processing** (icon: brain with 4 branches) → "Supervisor routes to 4 specialist agents in parallel"
>    - Branch 1: SOAP Agent → Structured clinical note
>    - Branch 2: Summary Agent → Patient-friendly summary
>    - Branch 3: Referral+Discharge Agent → Referral letter + discharge summary
>    - Branch 4: Trials Agent → queries Knowledge Base (RAG) → trial matches with confidence scores
> 6. **Results Page** (icon: tabs) → "4-tab view: SOAP | Summary | Referral+Discharge | Trials. Each tab shows confidence score + AI disclaimer. Doctor can EDIT any field."
> 7. **Finalize & Save** (icon: checkmark) → "Doctor approves → saved to DynamoDB Visits Table (linked to patient phone)"
>
> **PATIENT TRACK (bottom row, left to right):**
> 1. **Patient Login** (icon: phone) → "Phone number + OTP verification"
> 2. **Visit History** (icon: list) → "All visits from ANY hospital using ClinicalSetu (cross-hospital via DynamoDB GSI)"
> 3. **Visit Details** (icon: document) → "Diagnosis, medications, follow-up instructions, warning signs, doctor info"
>
> **CENTER CONNECTION:**
> - Arrow from Doctor's "Finalize" step DOWN to DynamoDB
> - Arrow from DynamoDB DOWN to Patient's "Visit History"
> - Label the connection: "DynamoDB Visits Table — PK: HOSPITAL#PHONE, SK: VISIT#timestamp, GSI: phone-index"
>
> Use consistent arrow colors: blue for doctor flow, green for patient flow, orange for AI processing.

---

## SLIDE 7 — Wireframes/Mock Diagrams

**Key Screens (Add actual screenshots or mockups here)**

**Doctor Portal — 4 Key Screens:**

1. **Login Page**: Clean login with "Doctor Login (SSO)" and "Patient Login (Phone+OTP)" toggle
2. **Consultation Page**: Split layout — left side has voice recorder (big mic button) + text area for clinical narrative. Right side has patient details form (name, age, gender, phone number). Bottom has "Process with AI" button.
3. **Results Page**: Tabbed interface with 4 tabs — SOAP Note | Patient Summary | Referral & Discharge | Clinical Trials. Each tab shows: generated content (editable text area), confidence score badge (green/yellow/red), translate button (9 languages dropdown), AI disclaimer banner. Bottom has "Finalize & Save Visit" button.
4. **Dashboard**: Cards showing recent consultations with patient name, date, diagnosis snippet. "New Consultation" button prominent.

**Patient Portal — 2 Key Screens:**

5. **Visit History**: List of past visits showing date, hospital name, doctor name, primary diagnosis. Each is clickable.
6. **Visit Detail**: Full visit summary — diagnosis, medications list, follow-up instructions, warning signs (highlighted in red/orange), doctor & hospital info.

> VISUAL: Add your actual prototype screenshots here in a 2x3 grid or 3x2 layout. If screenshots aren't ready, create simple wireframe boxes showing the layout described above with labeled sections.

---

## SLIDE 8 — Technologies Utilized

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Vite | Fast, type-safe single-page application |
| **Backend** | Python 3.12 on AWS Lambda (x4) | Serverless compute — zero server management |
| **AI Core** | Amazon Bedrock (Nova Lite + Claude Haiku) | LLM inference via Converse API with fallback |
| **AI Architecture** | Bedrock Multi-Agent Collaboration | Supervisor-Router with 4 specialist agents |
| **RAG** | Bedrock Knowledge Bases + Titan Embeddings | Semantic clinical trial matching |
| **Vector Store** | Amazon OpenSearch Serverless | Trial embedding storage and retrieval |
| **Voice** | Amazon Transcribe Medical | Real-time clinical speech-to-text |
| **Auth** | Amazon Cognito Identity Pool | Secure browser-to-AWS service access |
| **Database** | Amazon DynamoDB (x2 tables) | Response caching + patient visit persistence |
| **API** | Amazon API Gateway (REST) | 5 endpoints with CORS |
| **Hosting** | Amazon S3 + CloudFront | Static hosting with HTTPS CDN |
| **IaC** | AWS CloudFormation | Full infrastructure in one YAML template |
| **CI/CD** | GitHub Actions | Auto-deploy on push to main |

> VISUAL (right half): Tech stack pyramid or layered diagram — Frontend at top, API in middle, AI/Compute below, Data at bottom. Use tech logos for each.

---

## SLIDE 9 — Estimated Implementation Cost

**Prototype Cost (Current)**

| Component | Monthly Cost |
|-----------|-------------|
| Lambda (x4) | ~$0 (free tier: 1M requests) |
| API Gateway | ~$0 (free tier: 1M calls) |
| DynamoDB (x2) | ~$0 (free tier: 25GB + 25 WCU/RCU) |
| S3 + CloudFront | ~$1-2 |
| Bedrock (Nova Lite) | ~$5-15 (pay per token) |
| Transcribe Medical | ~$2-5 |
| OpenSearch Serverless | ~$20-30 |
| Cognito | ~$0 (free tier: 50K MAU) |
| **Total Prototype** | **~$30-50/month** |

**Per-Consultation Cost: $0.003 - $0.01**
- Nova Lite is **80% cheaper** than Claude Sonnet
- DynamoDB caching eliminates re-processing cost
- Serverless = **$0 when idle**

**At Scale (10,000 consultations/day)**

| Component | Monthly Cost |
|-----------|-------------|
| Bedrock AI calls | ~$300-1,000 |
| DynamoDB | ~$50-100 |
| Lambda + API GW | ~$20-50 |
| OpenSearch Serverless | ~$200-400 |
| **Total** | **~$600-1,500/month** |
| **Revenue** (SaaS @ $10/doctor/month, 500 doctors) | **$5,000/month** |

> VISUAL (right half): Cost breakdown pie chart + comparison bar showing ClinicalSetu cost vs traditional documentation software cost. Highlight the $0.003-0.01 per consultation as a big callout number.

---

## SLIDE 10 — Prototype Snapshots + Performance

**Prototype Performance Benchmarks**

| Metric | Result |
|--------|--------|
| SOAP Note generation | ~3-5 seconds |
| Patient Summary generation | ~2-4 seconds |
| Referral + Discharge generation | ~3-5 seconds |
| Clinical Trial RAG matching | ~5-8 seconds |
| Full multi-agent processing (all 5 outputs) | ~8-15 seconds |
| Speech-to-text latency | Real-time (~200ms chunks) |
| Frontend load time (CloudFront) | <1 second |
| API cold start (Lambda) | ~2-3 seconds (first call only) |
| Cache hit response | <500ms |
| Concurrent consultation support | 1000+ (serverless auto-scale) |

**Resilience Tested:**
- Model fallback: Nova Lite throttled → Claude Haiku auto-failover in <1s
- Multi-agent timeout → Monolithic pipeline fallback in <2s
- Cache miss → full processing; Cache hit → instant response
- Partial failure: One agent failing doesn't block other outputs

*(Add 2-3 screenshots of your working prototype showing the consultation page, results page with AI outputs, and patient portal)*

> VISUAL: Performance metrics as a dashboard-style graphic with green checkmarks. Add actual prototype screenshots below.

---

## SLIDE 11 — Additional Details / Future Development + Responsible AI

**Responsible AI (Built-In, Not Bolted-On)**
- **Non-diagnostic**: System NEVER provides diagnoses — documentation assistant only
- **Doctor-in-the-loop**: Every output is editable, nothing auto-published
- **Confidence scoring**: Color-coded per section (green >85%, yellow 60-85%, red <60%)
- **AI disclaimers**: Every output tab shows "AI-Generated — Requires Clinician Validation"
- **Synthetic data only**: Zero real patient data in prototype
- **Multi-tenant isolation**: Hospital-scoped DynamoDB keys prevent cross-tenant access

**Future Development Roadmap**

| Phase | What | When |
|-------|------|------|
| Phase 1 | Working prototype (12 AWS services) | **Now — Complete** |
| Phase 2 | ABDM Integration (Ayushman Bharat Digital Mission) | Q2 2026 |
| Phase 3 | EHR/HIS plug-in for existing hospital systems | Q3 2026 |
| Phase 4 | Patient mobile app + WhatsApp bot for summaries | Q4 2026 |
| Phase 5 | Multi-specialty AI models + regional voice I/O | 2027 |

**Business Model**
- **Hospitals/Clinics**: SaaS subscription ($5-15/doctor/month)
- **Pharma/CROs**: Clinical trial matching API (per-match fee)
- **Government (NHA)**: Public health integration contracts

> VISUAL (right half): Roadmap as a timeline with milestone icons. Responsible AI section as a shield/checklist graphic.

---

## SLIDE 12 — Prototype Assets + Thank You

**Prototype Assets**

- **GitHub Repository**: *(paste your public repo URL)*
- **Demo Video** (Max 3 min): *(paste your YouTube/Drive link)*
- **Live Prototype**: *(paste your CloudFront URL)*

---

**ClinicalSetu**

*One narrative. Five outputs. Nine languages. Two portals. Zero diagnoses.*

**Team Sahrova** | AI for Bharat Hackathon | Powered by AWS

**Thank You**

> VISUAL: Use the hackathon's thank you slide template. Add QR codes for GitHub repo, demo video, and live prototype URLs.

---

---

# APPENDIX — JUDGE Q&A CHEAT SHEET (Don't put this in PPT)

**Q: How is AI load-bearing here, not just a wrapper?**
A: Remove AI and the product literally cannot exist. Every consultation is unique natural language — no template can handle it. We use Multi-Agent Collaboration (4 specialist agents), RAG pipeline with real trial data, and medical speech recognition. Three distinct AI systems, not one API call.

**Q: Why these specific AWS services?**
A: Each service solves a specific problem — Bedrock for inference, Multi-Agent for parallel domain processing, Knowledge Bases for grounded trial matching (no hallucination), Transcribe Medical for clinical vocabulary, DynamoDB for sub-millisecond patient data, CloudFormation for reproducible infra. We're not using services for the sake of counting them.

**Q: How is this feasible in real Indian hospitals?**
A: Voice-first (zero learning curve for doctors), works on low bandwidth (CloudFront CDN), costs $0.003-0.01 per consultation (affordable for public hospitals), and doesn't require EHR integration (standalone system that doctors access via browser).

**Q: What about patient data privacy?**
A: Prototype uses synthetic data only. Architecture supports multi-tenant isolation via DynamoDB composite keys (HOSPITAL#phone pattern). Cognito handles auth. CloudFront serves over HTTPS. No PII leaves the AWS region.

**Q: Revenue model?**
A: Three streams — Hospital SaaS ($5-15/doctor/month), Pharma trial matching API (per-match), Government contracts (ABDM integration). At 500 doctors, revenue = $5K/month vs $600-1500 infra cost = profitable from day one.

**Q: What makes this India-specific, not a generic solution?**
A: Built for India's 1:1,511 doctor ratio, 4-minute consultations, multilingual patients (9 languages), fragmented hospital records, ABDM roadmap alignment, and $0.003 cost point designed for public hospital budgets.
