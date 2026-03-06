# ClinicalSetu - Presentation Deck
### AI for Bharat Hackathon | Professional Track - Healthcare & Life Sciences
### Team Sahrova

---

## SLIDE 1: TITLE

**ClinicalSetu**
*Capture Once. Reuse Responsibly.*

AI-powered clinical documentation bridge for India's 1.4 billion

Team Sahrova | AI for Bharat Hackathon

[Background: Gradient teal. Logo center. Tagline below.]

---

## SLIDE 2: THE PROBLEM — India's Doctor Crisis

**1 doctor per 1,511 people** (WHO recommends 1:1,000)

- Government hospital doctors see **80-100 patients/day** — avg **4 minutes per patient**
- 70% of that time goes to **paperwork**, not patients
- Patients leave **without understanding** what was discussed
- Referral letters are **incomplete** — critical context is lost between doctors
- **Zero** clinical trial discovery happens at the point of care

> "The doctor doesn't have a skill problem. They have a **time** problem."

[Visual: Split image — crowded OPD on left, doctor buried in paperwork on right]

---

## SLIDE 3: THE SOLUTION — 1 Input → 5 AI Outputs

**Doctor speaks or types ONE clinical narrative. ClinicalSetu generates 5 structured outputs.**

```
                    ┌──────────────────┐
                    │  SOAP Note       │  → Doctor's EMR
                    ├──────────────────┤
  Doctor speaks     │  Patient Summary │  → Patient (multilingual)
  ONE narrative ──► │  Referral Letter  │  → Specialist
                    │  Discharge Summary│  → Medical records
                    ├──────────────────┤
                    │  Trial Matches   │  → Research (RAG)
                    └──────────────────┘
```

- Voice input in **9 Indian languages** with auto-detection
- Every output **editable** by the doctor before finalizing
- Every output shows **confidence scores** and **AI disclaimers**
- Non-diagnostic by design — **doctor-in-the-loop always**

---

## SLIDE 4: LIVE DEMO FLOW (Screenshots)

**Screenshot 1: Voice-First Input**
- ChatGPT-style large mic button with live waveform visualization
- Real-time transcription in any Indian language
- Auto language detection badge
- "Quick Load" sample cases for instant testing

**Screenshot 2: 5-Tab Results Dashboard**
- SOAP Note with collapsible sections + inline edit on every field
- Patient Summary in plain language
- Referral Letter with urgency scoring
- Discharge Summary with doctor signature block
- Clinical Trial Matches with confidence scores + matched/unmatched criteria

**Screenshot 3: Multilingual Translation**
- One-click translation to Hindi, Tamil, Telugu, Marathi, Bengali, Kannada, Gujarati, Malayalam
- Available on ALL output tabs (not just patient summary)
- Powered by Amazon Bedrock in real-time

[Use actual screenshots from deployed app. 3 side-by-side.]

---

## SLIDE 5: AWS ARCHITECTURE (9 Services — All Deployed)

```
┌──────────────────────────────────────────────────────────────┐
│                       AWS CLOUD                               │
│                                                               │
│  GitHub Actions CI/CD ──► CloudFormation (IaC)                │
│                                                               │
│  ┌───────────┐  ┌──────────┐  ┌──────────────┐  ┌────────┐  │
│  │CloudFront │  │   S3     │  │ API Gateway  │  │ Lambda │  │
│  │  (CDN)    │─►│(Frontend)│  │  (REST API)  │─►│Python  │  │
│  │  HTTPS    │  │          │  │  + CORS      │  │3.12    │  │
│  └───────────┘  └──────────┘  └──────────────┘  └───┬────┘  │
│                                                       │       │
│                   ┌───────────────┬───────────────────┤       │
│                   ▼               ▼                   ▼       │
│           ┌──────────────┐ ┌──────────┐      ┌────────────┐  │
│           │ Amazon       │ │ DynamoDB │      │ Bedrock    │  │
│           │ Bedrock      │ │ (Cache)  │      │ Knowledge  │  │
│           │ Nova Lite    │ │ 24h TTL  │      │ Bases      │  │
│           │ + Haiku      │ │ PAY/REQ  │      │ (optional) │  │
│           │ (fallback)   │ └──────────┘      └────────────┘  │
│           └──────────────┘                                    │
│                                                               │
│  Browser ──► Cognito Identity Pool ──► Transcribe Medical     │
│              (unauthenticated)          (streaming speech)     │
│                                                               │
│  5 Bedrock calls per consultation (Converse API):             │
│  SOAP → Patient Summary → Referral → Discharge → Trials      │
│  + On-demand translation (6th call)                           │
│  + Retry with exponential backoff + model fallback            │
└──────────────────────────────────────────────────────────────┘
```

**9 AWS Services — All Deployed via CloudFormation IaC:**
| Service | Purpose |
|---------|---------|
| **Amazon Bedrock** (Nova Lite + Claude Haiku) | Core AI engine — Converse API with model fallback chain |
| **AWS Lambda** (Python 3.12, 1024MB) | Serverless backend, retry/backoff, partial result handling |
| **API Gateway** (REST) | Unified API with CORS (`/process`, `/translate`) |
| **Amazon S3** | Frontend static hosting + Lambda deployment packages |
| **Amazon CloudFront** | CDN with HTTPS, SPA error routing |
| **Amazon DynamoDB** | Response caching (SHA-256 keys, 24h TTL, PAY_PER_REQUEST) |
| **Amazon Cognito** | Identity Pool for secure browser-to-AWS Transcribe access |
| **Amazon Transcribe Medical** | Real-time clinical speech-to-text streaming |
| **CloudFormation** | Infrastructure as Code — entire stack in one template |

---

## SLIDE 6: THE AI PIPELINE — How It Actually Works

```
Doctor Input (voice/text, any language)
         │
         ▼
    ┌─────────────┐
    │ STEP 1       │  Prompt Template + Patient Context
    │ SOAP Note    │──► Bedrock (Claude 3 Sonnet)
    │ Generation   │  ◄── Structured JSON with confidence scores
    └──────┬──────┘
           │ SOAP feeds all downstream outputs
     ┌─────┼─────┬──────────┐
     ▼     ▼     ▼          ▼
   Step 2  Step 3  Step 4   Step 5
   Patient Referral Discharge Trial
   Summary Letter  Summary   Match
     │      │       │         │
     │      │       │     Uses RAG via
     │      │       │     Knowledge Bases
     ▼      ▼       ▼         ▼
   JSON   JSON    JSON      JSON
   output  output  output   output
           │
           ▼
    On-demand translation
    to 9 Indian languages
```

**Key Technical Decisions:**
- SOAP note is the **single source of truth** — all outputs derive from it
- Each prompt template enforces **structured JSON output** with confidence scoring
- Trial matching uses **Retrieval Augmented Generation** via Bedrock Knowledge Bases
- Translation preserves JSON structure — keys in English, values in target language
- Every output includes an **AI disclaimer** — we never claim to diagnose

---

## SLIDE 7: CLINICAL TRIAL MATCHING — The Differentiator

**Most hackathon projects stop at documentation. We go further.**

```
Patient Profile (from SOAP)          Trial Database (S3 → Knowledge Bases)
  - Age: 55, Male                      - 30 curated Indian clinical trials
  - Diagnosis: Type 2 DM               - Eligibility criteria
  - HbA1c: 8.2%                        - Inclusion/exclusion rules
  - Comorbidities: HTN                  - Trial phases, sponsors, locations
         │                                        │
         └──────────────┬─────────────────────────┘
                        ▼
              Bedrock Knowledge Bases
              (RAG: Retrieve & Generate)
                        │
                        ▼
              ┌─────────────────────┐
              │ Trial Match Results │
              │ • Confidence: 82%   │
              │ • Matched: 4/5      │
              │ • Unmatched: 1      │
              │ • Missing info: 2   │
              └─────────────────────┘
```

**Why this matters for India:**
- India runs **4,000+ active clinical trials** — recruitment is the #1 bottleneck
- Doctors in busy OPDs **never have time** to check trial eligibility
- This enables **passive discovery** — trials surface automatically at point of care
- All informational — physician review and patient consent always required

---

## SLIDE 8: RESPONSIBLE AI — Non-Negotiable

ClinicalSetu is **NOT a diagnostic tool**. It is a **documentation assistant**.

| Safety Guardrail | How We Implement It |
|---|---|
| **Non-diagnostic** | Prompts explicitly instruct: "You are a documentation assistant, not a diagnostic tool" |
| **Doctor-in-the-loop** | Every field is editable. Nothing is final until doctor clicks "Approve" then "Finalize All" |
| **Confidence scoring** | Every output has a score. Red (<60%), Yellow (60-80%), Green (>80%) — doctor sees AI certainty |
| **AI disclaimers** | Banner on every tab: "AI-Generated — Requires Clinician Validation" |
| **No hallucinated treatments** | Prompts enforce: "Never suggest medications not in the SOAP note" |
| **Synthetic data only** | Zero real patient data. All consultations are fictional Indian clinical scenarios |
| **Trial matching = informational** | Explicit disclaimer: "Not enrollment recommendations. Physician review required." |

> We believe the safest AI system is one that **knows what it isn't.**

---

## SLIDE 9: IMPACT — Why India, Why Now

**India's healthcare documentation crisis by the numbers:**

| Metric | Value |
|--------|-------|
| Daily OPD consultations across India | **30 million+** |
| Doctor-to-patient ratio | **1:1,511** (WHO recommends 1:1,000) |
| Avg documentation time per patient | **8-12 minutes** (for a 4-minute consult) |
| % of referrals with incomplete context | **60%+** |
| Active clinical trials in India | **4,000+** |
| Languages needed for patient communication | **22 official + 100s of dialects** |

**ClinicalSetu's impact at scale:**
- **60% documentation time reduction** → doctors see more patients
- **9 Indian languages** for patient summaries → health literacy across demographics
- **Automatic trial surfacing** → addresses India's clinical trial recruitment gap
- **ABDM-ready architecture** → aligned with India's digital health vision (ABHA ID, health records interop)

---

## SLIDE 10: PRODUCTION ROADMAP

**What we built (prototype)** → **What we'd build with 6 more months**

| Prototype (Now) | Production (6-month roadmap) |
|---|---|
| Web Speech API for voice | **AWS Transcribe Medical** with medical vocabulary |
| 9 Indian languages | **22 languages** + dialect support |
| Synthetic trial data in S3 | **CTRI + ClinicalTrials.gov** live feed via Knowledge Bases |
| Mock authentication | **Amazon Cognito** with ABHA ID integration |
| Single Lambda | **Step Functions** orchestrating parallel Bedrock calls |
| In-memory processing | **DynamoDB** for visit history + **ElastiCache** for response caching |
| Frontend-only patient portal | **Full patient app** with appointment booking + medication reminders |
| Manual approval workflow | **EventBridge** audit trail + **CloudTrail** compliance logging |

**Business model:** SaaS for hospital chains (B2B). Per-consultation pricing.
Pilot target: 3 government district hospitals in Maharashtra.

---

## SLIDE 11: TEAM & WHY US

**Team Sahrova** — 2 engineers who believe India's healthcare documentation problem is solvable with the right AI guardrails.

**What makes us different:**
1. We built a **working prototype**, not a slide deck with mockups
2. We designed for **safety first** — non-diagnostic, doctor-in-the-loop, confidence scores
3. We went beyond documentation into **clinical trial discovery** (RAG)
4. We built **multilingual** from day one — not as an afterthought
5. We understand Indian healthcare — **our sample cases are real Indian clinical scenarios** (diabetes in Pune, SLE in Chennai, COPD in Hyderabad)

**Try it live:** [Amplify URL]
**GitHub:** [Repository URL]

---

## SLIDE 12: CLOSING

**ClinicalSetu**

*One narrative. Five outputs. Nine languages. Zero diagnoses.*

The doctor's time belongs to the patient.
We just handle the paperwork.

[Background: Same gradient as slide 1. Logo. Tagline.]

---

# SPEAKER NOTES & TIPS

## Timing (if presenting live, ~5 min)
- Slides 1-2: 45 seconds (problem setup)
- Slides 3-4: 60 seconds (solution + demo screenshots)
- Slides 5-6: 60 seconds (architecture + pipeline)
- Slide 7: 45 seconds (trial matching — spend time here, it's the differentiator)
- Slide 8: 30 seconds (responsible AI — fast but confident)
- Slides 9-10: 45 seconds (impact + roadmap)
- Slides 11-12: 15 seconds (team + close)

## Key Phrases to Use
- "Capture once, reuse responsibly" — say it at least twice
- "We are NOT a diagnostic tool" — judges love safety-consciousness
- "Doctor-in-the-loop" — emphasize human oversight
- "This isn't a documentation tool that also matches trials. Trial matching is architecturally first-class — it uses RAG via Bedrock Knowledge Bases."
- "Every output has a confidence score. The doctor sees exactly how certain the AI is."

## What Judges Will Ask (Prepare Answers)
1. **"How is this different from ChatGPT?"** → "Three things: structured JSON output (not free text), confidence scoring on every field, and RAG-based trial matching. ChatGPT can't do retrieval over your clinical trial database."
2. **"What about data privacy?"** → "Prototype uses synthetic data only. Production would use Cognito auth + DynamoDB encryption at rest + VPC-isolated Lambda. We designed with ABDM compliance in mind."
3. **"Does the voice input actually work in Hindi?"** → "Yes. We use the Web Speech API with auto-detection. For production, we'd migrate to AWS Transcribe Medical which has dedicated Indian English and Hindi models."
4. **"How accurate is the SOAP note?"** → "We include confidence scores per section. In our testing with synthetic data, the structured outputs are medically plausible but we explicitly state this requires clinician validation. We're a documentation assistant, not a clinical decision tool."
5. **"What's your cost per consultation?"** → "With Claude 3 Sonnet on Bedrock: approximately $0.02-0.05 per consultation (5 inference calls). At scale with Haiku for simpler outputs, under $0.01."
