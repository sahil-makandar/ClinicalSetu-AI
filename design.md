# ClinicalSetu: Enterprise Architecture Design

## Document Overview

ClinicalSetu is a clinical intelligence bridge that captures clinical intent once and reuses it across documentation, patient summaries, referrals, and research signaling. This document provides an enterprise-architecture level design for a non-diagnostic, doctor-in-the-loop healthcare AI platform built on AWS services.

**Core Principles:**
- Non-diagnostic system
- Doctor-in-the-loop validation required
- Built using Amazon Bedrock and Amazon Q
- Operates on synthetic and public datasets only
- No PHI storage in prototype phase

---

## 1. System Architecture Overview

### High-Level Architecture

The ClinicalSetu platform follows a serverless, event-driven architecture leveraging AWS managed services for scalability, security, and cost efficiency.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │  Doctor Interface    │      │  Patient Interface   │        │
│  │  (React/Vue SPA)     │      │  (Mobile/Web)        │        │
│  └──────────────────────┘      └──────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Amazon API Gateway (REST/WebSocket)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  AWS Lambda Functions                                     │  │
│  │  - Input Handler  - Validation Service                    │  │
│  │  - Orchestrator   - Output Generator                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI Processing Layer                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Amazon Bedrock                                           │  │
│  │  - Claude 3 / Titan models                                │  │
│  │  - Prompt orchestration                                   │  │
│  │  - Guardrails                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Speech Layer (Optional)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Amazon Transcribe Medical                                │  │
│  │  - Real-time streaming                                    │  │
│  │  - Medical vocabulary                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Knowledge Layer                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Amazon Q Business                                        │  │
│  │  - RAG over public clinical guidelines                    │  │
│  │  - Trial protocol knowledge base                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Amazon OpenSearch Serverless                             │  │
│  │  - Vector embeddings                                      │  │
│  │  - Semantic search                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Amazon DynamoDB                                          │  │
│  │  - Structured clinical records                            │  │
│  │  - Session metadata                                       │  │
│  │  - Audit logs                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Amazon S3                                                │  │
│  │  - Raw transcripts                                        │  │
│  │  - Generated documents                                    │  │
│  │  - Synthetic datasets                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Characteristics

- **Serverless**: All compute resources scale automatically based on demand
- **Event-driven**: Asynchronous processing via EventBridge and SQS
- **Stateless**: No session affinity required for horizontal scaling
- **Decoupled**: Services communicate via APIs and message queues
- **Secure**: Encryption at rest and in transit, IAM-based access control

---

## 2. Component-Level Design

### 2.1 Doctor Interface

The doctor interface is a web-based single-page application that serves as the primary interaction point for clinicians.

**Input Capture Module**

- **Voice Input**: WebRTC-based audio streaming to Amazon Transcribe Medical
  - Real-time transcription with medical vocabulary
  - Speaker diarization for multi-participant consultations
  - Punctuation and formatting restoration
  - Confidence scoring per utterance

- **Text Input**: Rich text editor with autocomplete
  - Medical terminology suggestions
  - Template-based quick entry
  - Structured field capture (vitals, medications, allergies)
  - Free-form clinical notes

- **Hybrid Mode**: Combination of voice and text
  - Voice-to-text with manual corrections
  - Text annotations on voice transcripts
  - Section-wise input method switching

**Editable Documentation Preview**

- Real-time rendering of AI-generated structured output
- Side-by-side view: raw input vs. structured output
- Inline editing capabilities with change tracking
- Section-level regeneration triggers
- Diff visualization for AI suggestions vs. doctor edits
- Version history with rollback capability

**Validation Workflow**

- Mandatory review checkpoints before finalization
- Field-level validation status indicators
- Missing information alerts
- Confidence score display per section
- Explicit approval action required
- Rejection with feedback loop to retrain prompts

**Technical Implementation**

- Framework: React with TypeScript
- State Management: Redux Toolkit for complex state
- API Communication: Axios with retry logic
- Real-time Updates: WebSocket connection via API Gateway
- Authentication: AWS Cognito with MFA
- Hosting: Amazon CloudFront + S3 static hosting

---

### 2.2 AI Structuring Engine

The AI Structuring Engine is the core intelligence component that transforms unstructured clinical narratives into structured, reusable clinical data.

**LLM Prompt Orchestration**

- **Prompt Template Library**: Versioned prompt templates stored in DynamoDB
  - SOAP note generation template
  - Patient summary template
  - Referral letter template
  - Research eligibility template

- **Prompt Chaining Strategy**:
  1. Initial extraction prompt: Extract entities and relationships
  2. Validation prompt: Check for inconsistencies and missing data
  3. Formatting prompt: Apply SOAP or other clinical documentation standards
  4. Refinement prompt: Enhance clarity and completeness

- **Context Management**:
  - Sliding window for long consultations
  - Relevant history injection from previous visits
  - Guideline snippets from RAG system
  - Patient context (synthetic demographics, history)

**Structured Extraction Pipeline**

```
Raw Input → Entity Recognition → Relationship Mapping → Schema Validation → Output Generation
```

**Entity Recognition**:
- Chief complaint
- History of present illness
- Past medical history
- Medications (current and discontinued)
- Allergies
- Vital signs
- Physical examination findings
- Assessment and differential diagnosis
- Treatment plan
- Follow-up instructions

**Relationship Mapping**:
- Symptom → Diagnosis associations
- Medication → Condition associations
- Temporal relationships (onset, duration, progression)
- Causal relationships (drug reactions, complications)

**Schema Validation**:
- JSON Schema enforcement for structured outputs
- Required field validation
- Data type checking
- Range validation for numeric values
- Terminology validation against SNOMED CT / ICD-10 codes

**SOAP Formatting Logic**

The system generates clinical notes following the SOAP (Subjective, Objective, Assessment, Plan) format:

- **Subjective**: Patient-reported symptoms, history, concerns
  - Extracted from: "Patient states...", "Reports...", "Complains of..."
  - Temporal markers preserved
  - Direct quotes when relevant

- **Objective**: Measurable clinical findings
  - Vital signs structured as key-value pairs
  - Physical examination findings organized by system
  - Lab results and imaging findings

- **Assessment**: Clinical reasoning and diagnosis
  - Primary diagnosis
  - Differential diagnoses with reasoning
  - Problem list with status (active, resolved, chronic)
  - Risk stratification

- **Plan**: Treatment and follow-up
  - Medications with dosage, frequency, duration
  - Procedures and interventions
  - Referrals to specialists
  - Follow-up timeline
  - Patient education points

**Parallel Output Generation**

The system generates multiple outputs simultaneously from a single clinical encounter:

```
                    ┌─→ SOAP Note
                    │
Clinical Input  ────┼─→ Patient Summary (layperson language)
                    │
                    ├─→ Referral Letter (specialist-focused)
                    │
                    └─→ Research Eligibility Signals
```

Implementation via AWS Step Functions:
- Parallel state execution
- Independent Lambda invocations per output type
- Aggregation of results
- Failure handling with partial success support

**Technical Implementation**

- Amazon Bedrock API invocation via boto3
- Model: Claude 3 Sonnet for complex reasoning, Titan for simpler tasks
- Temperature: 0.3 for consistency
- Max tokens: 4096 per invocation
- Retry logic: Exponential backoff with jitter
- Timeout: 30 seconds per LLM call
- Prompt injection detection via Bedrock Guardrails
- Output filtering for sensitive content

---

### 2.3 Referral Processor

The Referral Processor transforms clinical visit data into structured referral documents optimized for specialist review.

**Structured Transformation Logic**

Input: SOAP note + patient context
Output: Specialist-focused referral letter

Transformation steps:
1. **Relevance Filtering**: Extract only information relevant to referral reason
2. **Context Enrichment**: Add pertinent history and test results
3. **Question Formulation**: Generate specific clinical questions for specialist
4. **Urgency Classification**: Categorize as routine, urgent, or emergent
5. **Supporting Documentation**: List attached reports and images

**Checklist Generation Logic**

For each referral, generate a pre-visit checklist:
- Required tests before specialist visit
- Medications to continue/hold
- Documents to bring
- Questions to prepare
- Insurance authorization requirements

**Specialty-Specific Templates**

- Cardiology: Focus on cardiac risk factors, ECG findings, symptoms
- Endocrinology: Metabolic panel, hormone levels, growth charts
- Neurology: Neurological examination, imaging, symptom timeline
- Oncology: Pathology reports, staging, performance status

**Technical Implementation**

- Lambda function: ReferralProcessorFunction
- Input: Clinical record ID from DynamoDB
- Processing: Bedrock API call with referral-specific prompt
- Output: Structured JSON + formatted PDF via AWS Lambda with Puppeteer layer
- Storage: S3 bucket with lifecycle policies
- Notification: EventBridge event for downstream systems

---

### 2.4 Research Signal Engine

The Research Signal Engine identifies potential clinical trial eligibility based on patient presentation and public trial protocols.

**RAG Pipeline Over Public Trial Protocols**

Data Sources:
- ClinicalTrials.gov public API
- Published trial protocols (PubMed, preprint servers)
- Inclusion/exclusion criteria databases

Indexing Pipeline:
1. **Data Ingestion**: Scheduled Lambda fetches trial data
2. **Criteria Extraction**: LLM extracts structured criteria from free text
3. **Embedding Generation**: Amazon Bedrock Titan Embeddings
4. **Vector Storage**: OpenSearch Serverless vector index
5. **Metadata Storage**: DynamoDB for structured trial metadata

**Criteria Extraction**

For each trial protocol:
- Age range
- Gender requirements
- Diagnosis codes (ICD-10)
- Disease stage/severity
- Prior treatment requirements
- Exclusion criteria (comorbidities, medications)
- Geographic restrictions

**Eligibility Signal Generation**

Matching Process:
1. **Patient Profile Extraction**: Structured data from clinical record
2. **Semantic Search**: Vector similarity search in OpenSearch
3. **Criteria Matching**: Rule-based evaluation of inclusion/exclusion criteria
4. **Confidence Scoring**: 0-100 score based on criteria match percentage
5. **Ranking**: Sort trials by relevance and confidence

Output Format:
```json
{
  "patient_id": "synthetic_12345",
  "signals": [
    {
      "trial_id": "NCT12345678",
      "trial_title": "Study of Drug X in Condition Y",
      "confidence_score": 85,
      "matched_criteria": ["age", "diagnosis", "disease_stage"],
      "unmatched_criteria": ["prior_therapy"],
      "missing_information": ["genetic_marker_status"],
      "trial_phase": "Phase 3",
      "enrollment_status": "Recruiting",
      "locations": ["Site A", "Site B"]
    }
  ]
}
```

**Non-Binding Classification Logic**

Critical safeguards:
- All signals marked as "informational only"
- Disclaimer: "Not a recommendation for enrollment"
- Requires physician review and patient consent
- No automated enrollment or contact
- Confidence thresholds for display (minimum 60%)

**Technical Implementation**

- Lambda function: ResearchSignalFunction
- Trigger: EventBridge rule on clinical record finalization
- Vector search: OpenSearch Serverless with k-NN
- Embedding model: Amazon Bedrock Titan Embeddings v2
- Caching: ElastiCache for frequently accessed trial data
- Batch processing: SQS queue for asynchronous processing

---

## 3. Data Flow Sequence

### End-to-End Clinical Encounter Flow

**Step 1: Consultation Input**

1. Doctor initiates new encounter in web interface
2. API Gateway authenticates request via Cognito
3. Lambda creates session record in DynamoDB
4. WebSocket connection established for real-time updates
5. Doctor selects input mode: voice, text, or hybrid

**Step 2: Speech-to-Text (If Voice Input Used)**

1. Browser captures audio via WebRTC
2. Audio stream sent to Amazon Transcribe Medical via WebSocket
3. Real-time transcription returned to frontend
4. Interim results displayed with confidence scores
5. Final transcript stored in S3 with encryption
6. Transcript ID linked to session in DynamoDB

**Step 3: LLM Structuring**

1. Input Handler Lambda receives raw transcript/text
2. Prompt template retrieved from DynamoDB
3. Context enrichment:
   - Patient history fetched from DynamoDB
   - Relevant guidelines retrieved via Amazon Q RAG
4. Bedrock API invoked with constructed prompt
5. LLM response parsed and validated against JSON schema
6. Confidence scores calculated per section
7. Structured output sent to frontend via WebSocket

**Step 4: Structured Record Storage**

1. Validated structured data written to DynamoDB
2. Record status set to "pending_review"
3. Audit log entry created with timestamp and user ID
4. S3 backup of raw and structured data
5. EventBridge event published: "RecordStructured"

**Step 5: Parallel Generation of Outputs**

Triggered by "RecordStructured" event:

1. Step Functions workflow initiated with parallel branches:
   
   **Branch A: Patient Summary**
   - Lambda invokes Bedrock with patient-friendly prompt
   - Medical jargon translated to layperson terms
   - Summary stored in S3 and DynamoDB
   
   **Branch B: Referral Letter (if applicable)**
   - Referral Processor Lambda invoked
   - Specialty-specific template applied
   - PDF generated and stored in S3
   
   **Branch C: Research Signals**
   - Research Signal Engine Lambda invoked
   - Vector search in OpenSearch
   - Eligibility signals calculated and stored
   
   **Branch D: SOAP Note Finalization**
   - Final formatting applied
   - Clinical codes assigned (ICD-10, CPT)
   - Billing-ready document generated

2. All branches execute concurrently
3. Results aggregated by Step Functions
4. Completion event published to EventBridge

**Step 6: Doctor Validation**

1. Frontend receives completion notification via WebSocket
2. All generated outputs displayed in review interface
3. Doctor reviews each section:
   - Edits inline as needed
   - Marks sections as approved/rejected
   - Adds additional notes
4. Changes tracked with version control
5. Validation status updated in DynamoDB
6. If rejected, feedback sent to prompt optimization pipeline

**Step 7: Final Output Delivery**

1. Doctor clicks "Finalize" button
2. Lambda function processes finalization:
   - Record status updated to "finalized"
   - Immutable copy created in S3 Glacier
   - Audit log entry with digital signature
3. Outputs made available:
   - SOAP note: PDF download
   - Patient summary: Secure patient portal link
   - Referral letter: Encrypted email to specialist
   - Research signals: Display in research tab
4. Analytics event sent to CloudWatch for monitoring
5. Session closed, resources cleaned up

### Sequence Diagram

```
Doctor → API Gateway → Lambda → Bedrock → DynamoDB
  │           │          │         │          │
  │           │          │         │          │
  ├─ Input ──→├─ Auth ──→├─ LLM ──→├─ Store ─→│
  │           │          │         │          │
  │           │          │         │          │
  ←─ Output ─←├─ WS ────←├─ Parse ←─ Fetch ──←
```

---

## 4. AI Model Design

### Foundation Models via Amazon Bedrock

**Model Selection Strategy**

- **Claude 3 Sonnet**: Primary model for complex clinical reasoning
  - Use cases: SOAP note generation, differential diagnosis, clinical reasoning
  - Context window: 200K tokens
  - Strengths: Medical knowledge, nuanced understanding, safety

- **Claude 3 Haiku**: Fast model for simple tasks
  - Use cases: Entity extraction, classification, simple formatting
  - Lower latency and cost
  - Suitable for real-time interactions

- **Amazon Titan Text**: Fallback and specialized tasks
  - Use cases: Embeddings generation, simple text generation
  - Cost-effective for high-volume operations

**Model Configuration**

```python
bedrock_config = {
    "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
    "inferenceConfig": {
        "temperature": 0.3,  # Low for consistency
        "topP": 0.9,
        "maxTokens": 4096
    },
    "guardrailConfig": {
        "guardrailIdentifier": "clinical-safety-guardrail",
        "guardrailVersion": "1"
    }
}
```

### Prompt Templates

**SOAP Note Generation Template**

```
You are a clinical documentation assistant. Transform the following consultation transcript into a structured SOAP note.

IMPORTANT CONSTRAINTS:
- Do not diagnose or recommend treatments
- Only structure information provided by the doctor
- Flag any ambiguous or missing information
- Use standard medical terminology
- Include confidence scores for extracted entities

PATIENT CONTEXT:
{patient_history}

RELEVANT GUIDELINES:
{rag_context}

CONSULTATION TRANSCRIPT:
{transcript}

OUTPUT FORMAT:
Return a JSON object with the following structure:
{
  "subjective": { "chief_complaint": "", "hpi": "", "ros": {} },
  "objective": { "vitals": {}, "physical_exam": {} },
  "assessment": { "diagnoses": [], "differential": [] },
  "plan": { "medications": [], "procedures": [], "follow_up": "" },
  "confidence_scores": {}
}
```

**Patient Summary Template**

```
Convert the following clinical note into a patient-friendly summary.

GUIDELINES:
- Use simple, non-technical language
- Explain medical terms in parentheses
- Focus on actionable information for the patient
- Maintain accuracy while simplifying
- Avoid alarming language

CLINICAL NOTE:
{soap_note}

OUTPUT: Plain text summary, 200-300 words
```

### Guardrail Prompts

**System-Level Guardrails (Bedrock Guardrails)**

1. **Content Filtering**
   - Block harmful content generation
   - Filter PII leakage attempts
   - Detect prompt injection attacks
   - Prevent jailbreak attempts

2. **Topic Restrictions**
   - Block diagnostic recommendations
   - Prevent treatment suggestions beyond doctor input
   - Flag out-of-scope queries
   - Restrict to documentation tasks only

3. **Sensitive Information Redaction**
   - Automatic PII detection and masking
   - Synthetic data validation
   - Prevent real patient data processing

**Prompt-Level Guardrails**

Embedded in every prompt:
```
CRITICAL SAFETY RULES:
1. You are a documentation assistant, not a diagnostic tool
2. Never suggest diagnoses not mentioned by the doctor
3. Never recommend treatments or medications
4. Flag any information that seems clinically inconsistent
5. If uncertain, mark the section for doctor review
6. Do not make assumptions about missing information
```

### Output Schema Enforcement

**JSON Schema Validation**

All LLM outputs validated against predefined schemas:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["subjective", "objective", "assessment", "plan"],
  "properties": {
    "subjective": {
      "type": "object",
      "required": ["chief_complaint"]
    }
  }
}
```

Validation process:
1. Parse LLM response as JSON
2. Validate against schema using jsonschema library
3. If validation fails, retry with corrective prompt
4. Maximum 3 retry attempts
5. If still fails, flag for manual review

### Confidence Scoring

**Entity-Level Confidence**

For each extracted entity, calculate confidence based on:
- Explicit mention in transcript (high confidence)
- Inferred from context (medium confidence)
- Assumed based on guidelines (low confidence)

Scoring formula:
```
confidence = (explicit_score * 0.7) + (context_score * 0.2) + (consistency_score * 0.1)
```

**Section-Level Confidence**

Aggregate entity confidences within each SOAP section:
```
section_confidence = min(entity_confidences) * 0.5 + avg(entity_confidences) * 0.5
```

Display thresholds:
- Green (>80%): High confidence, minimal review needed
- Yellow (60-80%): Medium confidence, review recommended
- Red (<60%): Low confidence, mandatory review

### Logging

**Comprehensive Logging Strategy**

1. **Request Logging**
   - Timestamp, user ID, session ID
   - Input length and type
   - Model and parameters used
   - Request ID for tracing

2. **Response Logging**
   - Output length and structure
   - Confidence scores
   - Processing time
   - Token usage

3. **Error Logging**
   - Exception type and stack trace
   - Input that caused error (sanitized)
   - Retry attempts
   - Fallback actions taken

4. **Audit Logging**
   - All doctor edits to AI outputs
   - Approval/rejection decisions
   - Finalization timestamps
   - Access patterns

**Log Storage**

- CloudWatch Logs for operational logs (30-day retention)
- S3 for long-term audit logs (7-year retention)
- CloudWatch Insights for log analysis
- Alarms for error rate thresholds

---

## 5. Knowledge Retrieval (RAG) Design

### Indexing of Public Guidelines

**Data Sources**

- Clinical practice guidelines (AHA, ADA, NCCN, etc.)
- Evidence-based medicine databases (UpToDate, DynaMed)
- Public health protocols (CDC, WHO)
- Medical textbooks and review articles
- Drug information databases (FDA labels, drug interactions)

**Ingestion Pipeline**

1. **Data Collection**
   - Scheduled Lambda functions fetch updates
   - Web scraping with respect for robots.txt
   - API integrations where available
   - Manual upload for proprietary licensed content

2. **Document Processing**
   - PDF/HTML parsing using AWS Textract
   - Section identification (introduction, methods, recommendations)
   - Metadata extraction (publication date, authors, specialty)
   - Quality filtering (peer-reviewed sources prioritized)

3. **Chunking Strategy**
   - Semantic chunking: Split at section boundaries
   - Chunk size: 500-1000 tokens with 100-token overlap
   - Preserve context: Include document title and section header in each chunk
   - Metadata tagging: Specialty, condition, evidence level

4. **Embedding Generation**
   - Model: Amazon Bedrock Titan Embeddings v2
   - Dimension: 1024
   - Batch processing: 25 documents per API call
   - Caching: Store embeddings in S3 for reuse

5. **Vector Index Creation**
   - OpenSearch Serverless with k-NN plugin
   - Index settings: HNSW algorithm, ef_construction=512, m=16
   - Metadata fields: source, date, specialty, evidence_level
   - Refresh interval: Daily for new content

### Trial Protocol Ingestion

**ClinicalTrials.gov Integration**

1. **API Polling**
   - Daily fetch of new and updated trials
   - Filter criteria: Active recruiting, interventional studies
   - Geographic filter: Configurable by deployment region

2. **Criteria Extraction**
   - LLM-based extraction of inclusion/exclusion criteria
   - Structured format:
     ```json
     {
       "inclusion": [
         {"criterion": "Age 18-65", "type": "age", "min": 18, "max": 65}
       ],
       "exclusion": [
         {"criterion": "Pregnant", "type": "condition"}
       ]
     }
     ```

3. **Embedding and Indexing**
   - Trial description and criteria embedded
   - Separate index from guidelines
   - Metadata: phase, status, sponsor, locations

### Query Augmentation

**Retrieval Process**

1. **Query Formulation**
   - Extract key clinical concepts from SOAP note
   - Identify primary diagnosis and symptoms
   - Include relevant patient demographics

2. **Query Expansion**
   - Add synonyms and related terms
   - Include ICD-10 and SNOMED codes
   - Expand abbreviations

3. **Hybrid Search**
   - Vector search: Semantic similarity (70% weight)
   - Keyword search: Exact term matching (30% weight)
   - Combined scoring for final ranking

4. **Filtering**
   - Recency: Prefer guidelines from last 5 years
   - Evidence level: Prioritize high-quality evidence
   - Specialty match: Align with consultation context

5. **Retrieval Parameters**
   - Top-k: 5 most relevant chunks
   - Similarity threshold: 0.7 minimum
   - Diversity: MMR (Maximal Marginal Relevance) to avoid redundancy

### Context Window Management

**Challenge**: LLM context limits require careful management of retrieved content.

**Strategy**:

1. **Prioritization**
   - Rank retrieved chunks by relevance score
   - Include highest-scoring chunks first
   - Reserve space for patient context and transcript

2. **Token Budget Allocation**
   - System prompt: 500 tokens
   - Patient context: 1000 tokens
   - Retrieved guidelines: 2000 tokens
   - Consultation transcript: 4000 tokens
   - Output space: 4096 tokens
   - Total: ~12K tokens (well within Claude 3 limits)

3. **Summarization Fallback**
   - If retrieved content exceeds budget, summarize using Haiku
   - Extract key recommendations only
   - Preserve citations

4. **Iterative Retrieval**
   - For complex cases, multiple RAG calls
   - First pass: General guidelines
   - Second pass: Specific condition management
   - Third pass: Drug interactions or contraindications

### Citation Handling

**Transparency Requirements**

Every guideline-based suggestion must include:
- Source document title
- Publication date
- Relevant section or page number
- Evidence level (if available)
- Direct quote or paraphrase indicator

**Citation Format**

```
[Recommendation] 
Source: American Heart Association Guidelines 2023, Section 4.2
Evidence Level: Class I, Level A
```

**Implementation**

- Citations stored as metadata in vector index
- Retrieved alongside content chunks
- Displayed in UI as expandable references
- Linked to original source when available

**Amazon Q Integration**

Amazon Q Business provides an additional RAG layer:
- Pre-built connectors for common data sources
- Automatic indexing and updates
- Natural language query interface
- Built-in access controls
- Usage: Supplementary knowledge retrieval for complex queries

---

## 6. Security & Privacy Design

### Encrypted Data at Rest and in Transit

**Data in Transit**

- All API communications over HTTPS (TLS 1.3)
- WebSocket connections encrypted via WSS
- Certificate management via AWS Certificate Manager
- Perfect Forward Secrecy enabled
- HSTS headers enforced

**Data at Rest**

- S3: Server-side encryption with AWS KMS (SSE-KMS)
- DynamoDB: Encryption at rest enabled by default
- OpenSearch: Encryption at rest with KMS keys
- EBS volumes: Encrypted for Lambda execution environments
- CloudWatch Logs: Encrypted with KMS

**Key Management**

- AWS KMS for encryption key management
- Separate keys per data classification level
- Automatic key rotation enabled (annual)
- Key policies restrict access to specific IAM roles
- CloudTrail logging of all key usage

### IAM Role-Based Access

**Principle of Least Privilege**

Each component has dedicated IAM role with minimal permissions:

**Lambda Execution Roles**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*:*:model/anthropic.claude-3-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/ClinicalRecords"
    }
  ]
}
```

**User Access Control**

- AWS Cognito for authentication
- Multi-factor authentication required for doctors
- Role-based access: Doctor, Admin, Auditor
- Session timeout: 30 minutes of inactivity
- IP allowlisting for administrative functions

**Service-to-Service Authentication**

- IAM roles for service authentication
- No long-lived credentials
- Temporary security tokens via STS
- VPC endpoints for private connectivity

### No Storage of PHI (Prototype)

**Synthetic Data Only**

- All patient data is synthetically generated
- No real patient information processed
- Synthetic data generation using Synthea or similar tools
- Clear labeling of all data as synthetic

**Future HIPAA Compliance Preparation**

For production deployment with real PHI:
- HIPAA-eligible AWS services only
- Business Associate Agreement (BAA) with AWS
- Encryption of all PHI
- Access logging and monitoring
- Data retention and disposal policies
- Breach notification procedures
- Regular security assessments

**Data Minimization**

- Collect only data necessary for functionality
- Automatic data anonymization where possible
- No storage of raw audio beyond processing
- Transcripts stored without identifiers
- Aggregated analytics only

### Audit Logging

**Comprehensive Audit Trail**

All system actions logged:
- User authentication and authorization events
- Data access (read, write, delete)
- AI model invocations with inputs/outputs
- Configuration changes
- Administrative actions
- Failed access attempts

**Log Structure**

```json
{
  "timestamp": "2026-02-15T10:30:00Z",
  "event_type": "clinical_record_access",
  "user_id": "doctor_12345",
  "session_id": "sess_abc123",
  "resource_id": "record_xyz789",
  "action": "read",
  "ip_address": "10.0.1.50",
  "user_agent": "Mozilla/5.0...",
  "result": "success"
}
```

**Log Analysis**

- CloudWatch Insights for query and analysis
- Automated anomaly detection
- Alerts for suspicious patterns
- Regular audit reports for compliance
- Immutable log storage in S3 Glacier

### Controlled Access to AI Outputs

**Access Control Matrix**

| Role | View Records | Edit Records | Approve Records | Access AI Outputs | Admin Functions |
|------|--------------|--------------|-----------------|-------------------|-----------------|
| Doctor | Own only | Own only | Own only | Yes | No |
| Supervisor | Team | Team | Team | Yes | Limited |
| Admin | All | No | No | No | Yes |
| Auditor | All | No | No | Logs only | No |

**Output Access Restrictions**

- AI-generated outputs marked as "draft" until doctor approval
- Watermarking of unapproved outputs
- Version control with approval status
- Automatic expiration of unapproved drafts (7 days)
- No external sharing of unapproved content

---

## 7. Responsible AI Controls

### Human Validation Checkpoints

**Mandatory Review Points**

1. **Pre-Finalization Review**
   - Doctor must explicitly review all AI-generated sections
   - Checkbox confirmation for each SOAP component
   - Cannot finalize without reviewing all sections
   - Minimum review time enforced (prevents accidental approval)

2. **High-Risk Content Flagging**
   - Automatic flagging of:
     - Controlled substance prescriptions
     - High-risk procedures
     - Conflicting information
     - Low confidence scores (<60%)
   - Flagged content requires additional confirmation

3. **Peer Review (Optional)**
   - Complex cases can be flagged for peer review
   - Second doctor must review and approve
   - Collaborative editing with change tracking

4. **Patient Consent**
   - Patients informed of AI assistance in documentation
   - Opt-out mechanism available
   - Consent logged in audit trail

### No Clinical Decision Automation

**Strict Boundaries**

The system explicitly does NOT:
- Make diagnostic decisions
- Recommend treatments independently
- Prescribe medications
- Order tests or procedures
- Triage patients
- Provide clinical advice to patients directly

**Enforcement Mechanisms**

1. **Prompt Engineering**
   - All prompts explicitly prohibit diagnostic recommendations
   - Instructions to structure only, not suggest

2. **Output Filtering**
   - Post-processing to detect and remove diagnostic language
   - Flagging of phrases like "I recommend", "Patient should", "Diagnosis is"
   - Replacement with "Doctor noted", "Doctor recommended"

3. **UI Design**
   - Clear labeling: "AI-Assisted Documentation" not "AI Diagnosis"
   - Disclaimers on every page
   - No autonomous actions without doctor initiation

### Output Disclaimers

**Prominent Disclaimers**

Displayed on all AI-generated content:

```
⚠️ AI-ASSISTED CONTENT
This document was generated with AI assistance and requires physician review.
This system does not diagnose, treat, or provide medical advice.
All clinical decisions remain the responsibility of the treating physician.
```

**Patient-Facing Disclaimers**

On patient summaries:

```
This summary was prepared with AI assistance under physician supervision.
It is for informational purposes only and does not replace medical advice.
Contact your healthcare provider with questions or concerns.
```

**Research Signal Disclaimers**

On trial eligibility signals:

```
⚠️ INFORMATIONAL ONLY
These research trial matches are for informational purposes only.
This is not a recommendation for trial enrollment.
Discuss with your physician before considering any clinical trial.
Eligibility determination requires formal screening by trial investigators.
```

### Bias Monitoring Approach

**Potential Bias Sources**

1. **Training Data Bias**
   - Foundation models may reflect biases in medical literature
   - Historical underrepresentation of certain demographics
   - Geographic and socioeconomic biases

2. **Prompt Bias**
   - Implicit assumptions in prompt design
   - Language that may favor certain presentations

3. **Retrieval Bias**
   - RAG system may preferentially retrieve certain guidelines
   - Recency bias vs. established evidence

**Monitoring Strategy**

1. **Output Analysis**
   - Regular sampling of AI outputs
   - Analysis for demographic disparities
   - Comparison across patient demographics (synthetic data)
   - Statistical testing for significant differences

2. **Feedback Collection**
   - Doctor feedback on AI suggestions
   - Tracking of edit patterns
   - Identification of systematic errors

3. **Guideline Diversity**
   - Ensure RAG corpus includes diverse sources
   - International guidelines, not just US-based
   - Representation of different practice settings

4. **Regular Audits**
   - Quarterly bias assessment reports
   - External review by clinical ethics board
   - Prompt refinement based on findings

**Mitigation Strategies**

- Diverse prompt testing across demographics
- Explicit instructions to avoid assumptions
- Confidence scoring to flag uncertain outputs
- Human review as ultimate safeguard

### Explainability Layer

**Transparency Mechanisms**

1. **Source Attribution**
   - Every AI-generated statement linked to source
   - "Based on transcript: [quote]"
   - "Informed by guideline: [citation]"

2. **Reasoning Display**
   - Show intermediate steps in AI processing
   - "Extracted entities: [list]"
   - "Applied template: SOAP Note v2.1"
   - "Retrieved guidelines: [titles]"

3. **Confidence Visualization**
   - Color-coded confidence scores
   - Hover tooltips with explanation
   - "High confidence: Explicitly stated by doctor"
   - "Low confidence: Inferred from context"

4. **Edit History**
   - Track all AI suggestions vs. doctor edits
   - Highlight changes made by doctor
   - Learn from edit patterns to improve prompts

5. **Model Card**
   - Accessible documentation of AI capabilities
   - Known limitations and failure modes
   - Performance metrics on test datasets
   - Update log with version history

---

## 8. Scalability & Deployment

### Serverless Architecture

**Benefits**

- No server management or patching
- Automatic scaling from zero to thousands of requests
- Pay-per-use pricing model
- Built-in high availability
- Reduced operational overhead

**Core Serverless Components**

1. **AWS Lambda**
   - Stateless compute for all business logic
   - Concurrent execution limit: 1000 (adjustable)
   - Memory allocation: 1024-3008 MB based on function
   - Timeout: 30 seconds for API calls, 15 minutes for batch processing

2. **Amazon API Gateway**
   - REST API for synchronous requests
   - WebSocket API for real-time updates
   - Request throttling: 10,000 requests per second
   - Caching enabled for read-heavy endpoints

3. **AWS Step Functions**
   - Orchestration of parallel output generation
   - Error handling and retry logic
   - Visual workflow monitoring
   - Standard workflows for cost efficiency

4. **Amazon EventBridge**
   - Event-driven architecture
   - Decoupling of services
   - Scheduled triggers for batch jobs

### Stateless Compute

**Design Principles**

- No session state stored in compute layer
- All state persisted in DynamoDB or S3
- Lambda functions can be terminated and restarted without data loss
- Idempotent operations for retry safety

**State Management**

- Session state: DynamoDB with TTL
- User preferences: DynamoDB
- Temporary processing state: S3 with lifecycle policies
- Cache: ElastiCache Redis for frequently accessed data

**Connection Pooling**

- Database connections managed via RDS Proxy (if RDS used)
- HTTP connection reuse for Bedrock API calls
- WebSocket connection management via API Gateway

### Horizontal Scaling

**Auto-Scaling Characteristics**

1. **Lambda Concurrency**
   - Automatic scaling based on incoming requests
   - Reserved concurrency for critical functions
   - Provisioned concurrency for latency-sensitive functions
   - Burst capacity: 500-3000 concurrent executions

2. **DynamoDB**
   - On-demand capacity mode for unpredictable workloads
   - Provisioned capacity with auto-scaling for steady workloads
   - Global tables for multi-region deployment
   - DAX for read-heavy caching

3. **OpenSearch Serverless**
   - Automatic scaling of compute and storage
   - No cluster management required
   - Pay for indexed data and queries

4. **S3**
   - Virtually unlimited storage
   - Automatic scaling of throughput
   - No capacity planning required

**Load Distribution**

- CloudFront for global content delivery
- Multi-AZ deployment for high availability
- Regional failover via Route 53
- API Gateway throttling to prevent overload

**Performance Optimization**

- Lambda function warming to reduce cold starts
- Connection pooling and reuse
- Batch processing for bulk operations
- Asynchronous processing for non-critical tasks
- Caching at multiple layers (CloudFront, API Gateway, ElastiCache)

### Cost-Scaling Characteristics

**Cost Model**

The serverless architecture provides favorable cost-scaling properties:

**Low Usage (0-100 consultations/day)**
- Lambda: ~$10/month (free tier eligible)
- DynamoDB: ~$5/month (on-demand)
- S3: ~$2/month
- Bedrock: ~$50/month (primary cost)
- Total: ~$70/month

**Medium Usage (1,000 consultations/day)**
- Lambda: ~$100/month
- DynamoDB: ~$50/month
- S3: ~$20/month
- Bedrock: ~$500/month
- Total: ~$700/month

**High Usage (10,000 consultations/day)**
- Lambda: ~$800/month
- DynamoDB: ~$400/month
- S3: ~$150/month
- Bedrock: ~$4,500/month
- Total: ~$6,000/month

**Cost Optimization Strategies**

1. **Model Selection**
   - Use Haiku for simple tasks (10x cheaper than Sonnet)
   - Cache common responses
   - Batch processing where possible

2. **Storage Optimization**
   - S3 Intelligent-Tiering for automatic cost optimization
   - Lifecycle policies to move old data to Glacier
   - DynamoDB TTL to auto-delete expired sessions

3. **Compute Optimization**
   - Right-size Lambda memory allocation
   - Use Step Functions Express for high-volume workflows
   - Asynchronous processing to reduce API Gateway costs

4. **Data Transfer**
   - CloudFront caching to reduce origin requests
   - VPC endpoints to avoid NAT gateway costs
   - Regional deployment to minimize cross-region transfer

**Cost Monitoring**

- AWS Cost Explorer for spend analysis
- Budget alerts at 80% and 100% thresholds
- Cost allocation tags for per-feature tracking
- Regular cost optimization reviews

---

## 9. Limitations

### Not a Medical Device

**Regulatory Status**

- ClinicalSetu is a documentation tool, not a medical device
- Not subject to FDA regulation as currently designed
- Does not meet the definition of a medical device per FDA guidance
- No claims of diagnostic or therapeutic capability
- Intended for administrative efficiency, not clinical decision-making

**Implications**

- Cannot be marketed as improving clinical outcomes
- Cannot claim to reduce medical errors
- Cannot be used as sole basis for clinical decisions
- Requires physician oversight for all outputs

**Future Regulatory Considerations**

If functionality expands to include:
- Clinical decision support with recommendations
- Autonomous triage or diagnosis
- Treatment optimization algorithms

Then FDA registration as a medical device may be required.

### Not a Diagnostic Engine

**Explicit Non-Diagnostic Design**

The system is intentionally designed to avoid diagnostic functionality:

- No symptom-to-diagnosis mapping
- No differential diagnosis generation (only structuring doctor's input)
- No probability scoring for diagnoses
- No treatment recommendations
- No drug-drug interaction checking (future enhancement)
- No clinical calculators (e.g., risk scores)

**What It Does**

- Structures information provided by the doctor
- Formats clinical notes according to standards
- Retrieves relevant guidelines for reference
- Identifies potential research trial matches (informational only)

**What It Does NOT Do**

- Diagnose conditions
- Recommend treatments
- Interpret lab results
- Analyze imaging
- Predict outcomes
- Replace physician judgment

### Prototype-Level Integration

**Current Integration Maturity**

- Standalone system, not integrated with EHR/HIS
- Manual data entry required
- No bidirectional data sync
- Limited interoperability
- Synthetic data only

**Integration Gaps**

1. **EHR Integration**
   - No HL7 or FHIR interfaces
   - No single sign-on with hospital systems
   - No automatic patient data import
   - No export to billing systems

2. **Lab/Imaging Integration**
   - No automatic result import
   - Manual entry of lab values
   - No DICOM integration for imaging

3. **Pharmacy Integration**
   - No e-prescribing capability
   - No formulary checking
   - No automatic medication reconciliation

4. **Scheduling Integration**
   - No calendar sync
   - Manual appointment tracking
   - No automated follow-up scheduling

**Prototype Scope**

- Proof of concept for AI-assisted documentation
- Demonstration of technical feasibility
- User experience validation
- Performance benchmarking
- Not production-ready for clinical deployment

### Uses Synthetic Data Only

**Data Characteristics**

- All patient data generated using Synthea or similar tools
- Realistic but entirely fictional
- No real patient information
- No PHI (Protected Health Information)
- Clearly labeled as synthetic in all records

**Limitations of Synthetic Data**

1. **Realism Gaps**
   - May not capture full complexity of real cases
   - Edge cases underrepresented
   - Atypical presentations missing
   - Cultural and linguistic diversity limited

2. **Validation Constraints**
   - Cannot validate against real clinical outcomes
   - Performance metrics may not generalize
   - User feedback based on simulated scenarios

3. **Training Limitations**
   - Doctors training on synthetic cases
   - May not reflect actual workflow challenges
   - Limited stress testing under real conditions

**Transition to Real Data**

For production deployment:
- HIPAA compliance required
- IRB approval for any research use
- Patient consent mechanisms
- Data governance framework
- Privacy impact assessment
- Security audit and penetration testing

---

## 10. Future Enhancements

### HIS Integration

**Planned Integration Points**

1. **HL7/FHIR Interfaces**
   - Bidirectional data exchange with EHR systems
   - Patient demographics import
   - Problem list synchronization
   - Medication reconciliation
   - Lab result import
   - Appointment scheduling integration

2. **Single Sign-On (SSO)**
   - SAML 2.0 or OAuth 2.0 integration
   - Unified authentication with hospital systems
   - Role-based access control sync
   - Audit trail integration

3. **Workflow Integration**
   - Embedded within EHR interface (iframe or native)
   - Context-aware launch (patient context passed)
   - Seamless navigation between systems
   - Unified task management

4. **Billing Integration**
   - Automatic CPT code suggestion
   - ICD-10 code validation
   - Charge capture automation
   - Claims submission support

**Technical Approach**

- AWS HealthLake for FHIR data management
- API Gateway for secure external access
- Event-driven sync via EventBridge
- Conflict resolution strategies for data discrepancies

### Multilingual Models

**Language Support Roadmap**

Phase 1: English (current)
Phase 2: Spanish, Mandarin, Hindi
Phase 3: French, Arabic, Portuguese, German
Phase 4: Additional languages based on demand

**Technical Implementation**

1. **Multilingual LLMs**
   - Claude 3 supports 100+ languages
   - Language detection and routing
   - Translation layer for non-English inputs
   - Culturally appropriate output formatting

2. **Localized Guidelines**
   - Regional clinical practice guidelines
   - Country-specific drug formularies
   - Local regulatory compliance
   - Cultural considerations in patient communication

3. **UI Localization**
   - Internationalization (i18n) framework
   - Right-to-left language support
   - Date/time format localization
   - Currency and unit conversions

**Challenges**

- Medical terminology translation accuracy
- Maintaining clinical precision across languages
- Regulatory compliance in different jurisdictions
- Dialect and regional variations

### Advanced Analytics Dashboard

**Analytics Capabilities**

1. **Operational Metrics**
   - Consultation volume trends
   - Average documentation time
   - AI acceptance rate (% of suggestions kept)
   - Edit patterns and common corrections
   - System performance metrics (latency, errors)

2. **Clinical Insights**
   - Common diagnoses and trends
   - Referral patterns by specialty
   - Medication prescribing patterns
   - Follow-up compliance rates
   - Research trial enrollment tracking

3. **Quality Metrics**
   - Documentation completeness scores
   - Guideline adherence rates
   - Peer review outcomes
   - Patient satisfaction (if collected)
   - Adverse event tracking

4. **AI Performance**
   - Confidence score distributions
   - Model accuracy on validation sets
   - Prompt effectiveness metrics
   - RAG retrieval relevance scores
   - Bias monitoring dashboards

**Technical Implementation**

- Amazon QuickSight for visualization
- AWS Glue for ETL pipelines
- Amazon Athena for ad-hoc queries
- S3 data lake for analytics storage
- Real-time dashboards via CloudWatch

**Privacy Considerations**

- Aggregated data only, no individual patient drill-down
- De-identification of any exported data
- Role-based access to analytics
- Compliance with data retention policies

### Federated Data Pipelines (Future)

**Vision**

Enable multi-institutional collaboration while preserving data privacy and sovereignty.

**Federated Learning Approach**

1. **Decentralized Training**
   - Models trained locally at each institution
   - Only model updates shared, not raw data
   - Aggregation of model weights centrally
   - Improved model performance without data sharing

2. **Privacy-Preserving Techniques**
   - Differential privacy for model updates
   - Secure multi-party computation
   - Homomorphic encryption for sensitive computations
   - Federated analytics for aggregate insights

3. **Use Cases**
   - Rare disease research across institutions
   - Multi-site clinical trial recruitment
   - Benchmarking and quality improvement
   - Collaborative guideline development

**Technical Architecture**

- AWS Clean Rooms for secure data collaboration
- Amazon SageMaker for federated learning
- Blockchain for audit trail (optional)
- Standardized data schemas (FHIR)

**Challenges**

- Institutional data governance agreements
- Regulatory compliance across jurisdictions
- Technical complexity and coordination
- Trust and transparency requirements

**Additional Future Enhancements**

1. **Voice Biometrics**
   - Speaker identification for multi-participant consultations
   - Voice authentication for doctors
   - Emotion detection for patient distress

2. **Clinical Decision Support**
   - Drug-drug interaction checking
   - Allergy alerts
   - Clinical calculators (risk scores, dosing)
   - Evidence-based order sets

3. **Patient Engagement**
   - Patient portal with AI-generated summaries
   - Automated follow-up reminders
   - Health education content personalization
   - Symptom tracking and reporting

4. **Research Automation**
   - Automated case report form population
   - Real-time adverse event detection
   - Protocol deviation identification
   - Recruitment optimization

5. **Mobile Applications**
   - Native iOS and Android apps
   - Offline mode with sync
   - Voice input optimization for mobile
   - Telemedicine integration

6. **Advanced AI Capabilities**
   - Multi-modal inputs (images, waveforms)
   - Predictive analytics for outcomes
   - Personalized treatment recommendations
   - Automated literature review and synthesis

---

## Conclusion

ClinicalSetu represents a responsible approach to AI-assisted clinical documentation, prioritizing physician oversight, patient safety, and data privacy. The architecture leverages AWS managed services for scalability, security, and cost efficiency while maintaining clear boundaries around the system's non-diagnostic nature.

The serverless, event-driven design ensures the platform can scale from prototype to production while maintaining consistent performance and security. The doctor-in-the-loop validation workflow ensures that all AI outputs are reviewed and approved by qualified clinicians before finalization.

By focusing on documentation efficiency rather than clinical decision-making, ClinicalSetu provides value to healthcare providers while avoiding the regulatory and ethical complexities of diagnostic AI systems. The platform's modular architecture allows for incremental enhancement and integration with existing healthcare IT infrastructure as the product matures.

The use of synthetic data in the prototype phase enables safe development and testing while preparing the technical and governance foundation for eventual deployment with real patient data under appropriate regulatory frameworks.

---

## Appendix: AWS Service Summary

| Service | Purpose | Key Features |
|---------|---------|--------------|
| Amazon Bedrock | AI model hosting | Claude 3, Titan models, Guardrails |
| Amazon Q | Knowledge retrieval | RAG, public guidelines, trial protocols |
| AWS Lambda | Serverless compute | Auto-scaling, event-driven |
| API Gateway | API management | REST, WebSocket, throttling |
| DynamoDB | NoSQL database | Structured records, sessions, audit logs |
| S3 | Object storage | Documents, transcripts, backups |
| OpenSearch Serverless | Vector search | Embeddings, semantic search |
| Transcribe Medical | Speech-to-text | Medical vocabulary, real-time |
| Step Functions | Workflow orchestration | Parallel processing, error handling |
| EventBridge | Event bus | Decoupling, event routing |
| Cognito | Authentication | User management, MFA |
| KMS | Key management | Encryption keys, rotation |
| CloudWatch | Monitoring | Logs, metrics, alarms |
| CloudFront | CDN | Global distribution, caching |
| VPC | Networking | Isolation, security groups |

---

**Document Version:** 1.0  
**Last Updated:** February 15, 2026  
**Status:** Draft for Review
**Owner**: Team Sahrova - ClinicalSetu Development Team 