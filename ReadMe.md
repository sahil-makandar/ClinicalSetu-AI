# ClinicalSetu

ClinicalSetu is an AI-powered clinical intelligence bridge designed for the Professional Track – AI for Healthcare & Life Sciences.

It captures clinical intent once during a doctor–patient consultation and responsibly transforms it into structured documentation, patient-friendly summaries, referral packets, and research eligibility signals.

---

## 🚩 Problem

In real-world healthcare settings:

- Doctors spend excessive time on documentation
- Patients leave without clear understanding
- Referrals lack structured context
- Potential clinical trial candidates go unnoticed

ClinicalSetu addresses this fragmentation by acting as a single source of clinical truth.

---

## 💡 Solution Overview

ClinicalSetu:

- Captures clinical intent (voice/text input)
- Structures it into editable SOAP-style documentation
- Generates:
  - Clinical notes
  - Discharge summaries
  - Referral packets
  - Plain-language patient summaries
  - Research eligibility signals (based on public trial data)

**Key Principle:** Capture once → reuse responsibly

---

## 🛡 Responsible AI Design

ClinicalSetu:

- Does not diagnose
- Does not recommend treatments
- Requires clinician validation
- Uses only synthetic and publicly available data
- Is not a medical device

**Important:** All outputs are informational and must be reviewed by healthcare professionals.

---

## 🏗 Architecture (High-Level)

### Frontend Layer
- Doctor Interface
- Patient Interface

### Application Layer
- AWS Lambda + API Gateway

### AI Layer
- Amazon Bedrock (LLM processing)
- AWS Transcribe (optional speech-to-text)

### Knowledge Layer
- Amazon Q (RAG over public guidelines & trial criteria)

### Data Layer
- Synthetic structured visit records (DynamoDB / S3)

---

## 📄 Documentation

This repository contains:

- **requirements.md** – Functional & non-functional requirements
- **design.md** – System architecture & technical design

---

## 🔮 Future Scope

- HIS integrations
- Multilingual support
- Advanced analytics dashboard
- ABDM-aligned interoperability


## About

This project was conceptualized and developed as part of the AI for Bharat Hackathon (Professional Track – Healthcare & Life Sciences).