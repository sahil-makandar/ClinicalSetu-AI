# ClinicalSetu Requirements Document

## 1. Introduction

### 1.1 Purpose

ClinicalSetu is an AI-powered clinical intelligence bridge designed to capture clinical intent once during doctor-patient consultations and transform it into multiple structured outputs. The system serves as a documentation and communication layer that reduces administrative burden while improving care continuity and research readiness.

### 1.2 Target Users

- **Doctors**: Primary care physicians, specialists, and consulting clinicians who need efficient documentation tools
- **Patients**: Individuals seeking clear, understandable summaries of their clinical visits
- **Hospitals**: Healthcare institutions aiming to improve operational efficiency and care coordination
- **Research Teams**: Clinical researchers identifying potential trial candidates through passive eligibility screening

### 1.3 Problem Statement

Clinical information is fragmented across multiple touchpoints in the healthcare journey. Doctors spend significant time on repetitive documentation, patients struggle to understand medical terminology, referrals lack structured context, and research teams manually screen records for trial eligibility. ClinicalSetu addresses these challenges by capturing clinical intent once and generating multiple contextually appropriate outputs.

### 1.4 System Classification

ClinicalSetu is explicitly:

- **Non-diagnostic**: Does not provide medical diagnoses
- **Non-prescriptive**: Does not recommend treatments or medications
- **Doctor-in-the-loop**: All outputs require clinician validation before use
- **Not a medical device**: Functions as a documentation and communication tool only
- **Built on synthetic and public data**: Uses no real patient data in development

## 2. Goals & Objectives

### 2.1 Primary Goals

- **Reduce Documentation Burden**: Minimize time clinicians spend on repetitive administrative tasks
- **Improve Care Continuity**: Ensure consistent, structured information flows across care episodes
- **Improve Referral Clarity**: Provide specialists with complete, structured context for referred patients
- **Enable Passive Research Readiness**: Flag potential trial eligibility without disrupting clinical workflow
- **Ensure Responsible AI Usage**: Maintain human oversight and transparency in all AI-generated outputs

### 2.2 Success Metrics

- Reduction in documentation time per consultation
- Improved patient comprehension of visit summaries
- Decreased referral clarification requests
- Increased research screening efficiency
- Zero autonomous clinical decisions made by the system

## 3. Functional Requirements

### 3.1 Clinical Intent Capture Module

**FR-1.1**: The system shall accept voice input from clinicians during consultations

**FR-1.2**: The system shall accept text input as an alternative to voice

**FR-1.3**: The system shall convert speech to text with medical terminology recognition (optional module)

**FR-1.4**: The system shall extract structured medical context including:
- Chief complaint
- History of present illness
- Past medical history
- Medications
- Allergies
- Physical examination findings
- Assessment
- Plan

**FR-1.5**: The system shall generate editable structured notes from captured input

**FR-1.6**: The system shall preserve clinical intent without interpretation or inference

### 3.2 Clinical Documentation Module

**FR-2.1**: The system shall generate SOAP-style clinical notes containing:
- Subjective findings
- Objective findings
- Assessment
- Plan

**FR-2.2**: The system shall generate discharge summaries including:
- Admission details
- Hospital course
- Discharge diagnosis
- Discharge medications
- Follow-up instructions

**FR-2.3**: The system shall generate referral letters with:
- Reason for referral
- Relevant clinical history
- Current medications
- Specific questions for specialist

**FR-2.4**: The system shall allow clinicians to edit all generated documentation before finalization

**FR-2.5**: The system shall maintain version history of edits made to generated documents

**FR-2.6**: The system shall clearly label all outputs as "AI-Generated - Requires Clinician Validation"

### 3.3 Patient Communication Module

**FR-3.1**: The system shall generate plain-language visit summaries from clinical notes

**FR-3.2**: The system shall highlight follow-up actions in patient summaries including:
- Medication instructions
- Lifestyle modifications
- Follow-up appointment timing
- Investigation requirements

**FR-3.3**: The system shall highlight red-flag symptoms requiring immediate medical attention

**FR-3.4**: The system shall ensure readability for non-medical users (target: 8th-grade reading level)

**FR-3.5**: The system shall avoid medical jargon or provide clear explanations when technical terms are necessary

**FR-3.6**: The system shall include disclaimer text stating the summary is for informational purposes only

### 3.4 Referral Intelligence Module

**FR-4.1**: The system shall structure referral context into standardized sections

**FR-4.2**: The system shall extract and highlight the primary reason for referral

**FR-4.3**: The system shall suggest a checklist of potentially missing investigations based on referral reason (labeled as non-clinical suggestion only)

**FR-4.4**: The system shall not recommend specific tests or procedures

**FR-4.5**: The system shall allow referring clinicians to customize suggested checklists

**FR-4.6**: The system shall format referrals for easy specialist review

### 3.5 Research Signal Module

**FR-5.1**: The system shall compare structured visit data against public clinical trial inclusion/exclusion criteria

**FR-5.2**: The system shall flag potential trial eligibility signals based on:
- Age criteria
- Diagnosis criteria
- Treatment history criteria
- Comorbidity criteria

**FR-5.3**: The system shall clearly label all eligibility signals as "Informational Only - Not Clinical Recommendation"

**FR-5.4**: The system shall provide trial identifier and source for each flagged signal

**FR-5.5**: The system shall not automatically enroll or contact patients regarding trials

**FR-5.6**: The system shall require clinician review before any research-related patient communication

**FR-5.7**: The system shall use only publicly available clinical trial criteria (e.g., ClinicalTrials.gov)

## 4. Non-Functional Requirements

### 4.1 Performance

**NFR-1.1**: The system shall generate clinical documentation within 10 seconds of input submission

**NFR-1.2**: The system shall generate patient summaries within 5 seconds of clinical note finalization

**NFR-1.3**: The system shall process research eligibility signals within 15 seconds

**NFR-1.4**: The system shall support concurrent processing of multiple consultation captures

### 4.2 Scalability

**NFR-2.1**: The system shall use serverless architecture to scale automatically with demand

**NFR-2.2**: The system shall handle up to 1000 concurrent consultations without performance degradation

**NFR-2.3**: The system shall support horizontal scaling for increased load

### 4.3 Security

**NFR-3.1**: The system shall encrypt all data in transit using TLS 1.3 or higher

**NFR-3.2**: The system shall encrypt all data at rest using AES-256 encryption

**NFR-3.3**: The system shall implement role-based access control (RBAC)

**NFR-3.4**: The system shall authenticate users before granting access

**NFR-3.5**: The system shall not store real patient identifiable information in the prototype phase

### 4.4 Availability

**NFR-4.1**: The system shall maintain 99.5% uptime during business hours

**NFR-4.2**: The system shall implement graceful degradation if AI services are unavailable

**NFR-4.3**: The system shall provide offline capture capability with delayed processing

### 4.5 Audit Logging

**NFR-5.1**: The system shall log all user actions with timestamp and user identifier

**NFR-5.2**: The system shall log all AI-generated outputs and subsequent clinician edits

**NFR-5.3**: The system shall maintain audit logs for a minimum of 7 years

**NFR-5.4**: The system shall provide audit trail export functionality

### 4.6 Human Validation Workflow

**NFR-6.1**: The system shall require explicit clinician approval before any output is finalized

**NFR-6.2**: The system shall prevent automatic distribution of AI-generated content without human review

**NFR-6.3**: The system shall track validation status for all generated documents

**NFR-6.4**: The system shall provide clear visual indicators distinguishing validated from unvalidated content

## 5. Responsible AI & Compliance

### 5.1 Human-in-the-Loop Requirements

**RAI-1.1**: All AI-generated outputs must be reviewed and validated by a licensed clinician before use

**RAI-1.2**: The system shall not make autonomous clinical decisions

**RAI-1.3**: The system shall not automatically trigger clinical actions without explicit clinician approval

**RAI-1.4**: The system shall provide mechanisms for clinicians to override or modify all AI suggestions

### 5.2 Transparency

**RAI-2.1**: All AI-generated content shall be clearly labeled as such

**RAI-2.2**: The system shall provide explanations for research eligibility signals when available

**RAI-2.3**: The system shall disclose limitations of AI-generated outputs to end users

**RAI-2.4**: The system shall maintain transparency about data sources used for training and inference

### 5.3 Bias Awareness

**RAI-3.1**: The system shall be tested for bias across demographic groups during development

**RAI-3.2**: The system shall document known limitations and potential biases in outputs

**RAI-3.3**: The system shall provide mechanisms for reporting suspected bias or errors

**RAI-3.4**: The system shall undergo regular bias audits as part of maintenance cycles

### 5.4 Data Usage Restrictions

**RAI-4.1**: The system shall use only synthetic patient data for development and testing

**RAI-4.2**: The system shall use only publicly available clinical guidelines and trial criteria

**RAI-4.3**: The system shall not train models on real patient data without explicit consent and ethical approval

**RAI-4.4**: The system shall comply with applicable data protection regulations

### 5.5 Clear Limitations

**RAI-5.1**: The system shall display prominent disclaimers stating:
- "This system does not provide medical diagnosis"
- "This system does not recommend treatments"
- "This system is not a medical device"
- "All outputs require validation by a licensed clinician"

**RAI-5.2**: The system shall educate users on appropriate use cases and limitations during onboarding

**RAI-5.3**: The system shall prevent use cases outside its intended scope through design constraints

## 6. Constraints

### 6.1 Technical Constraints

**C-1.1**: The prototype shall not integrate with live hospital information systems

**C-1.2**: The prototype shall not connect to electronic health record (EHR) systems

**C-1.3**: The system shall not perform real-time diagnosis or clinical decision support

### 6.2 Data Constraints

**C-2.1**: The system shall use no real patient data during development or demonstration

**C-2.2**: The system shall rely on synthetic datasets that simulate realistic consultations

**C-2.3**: The system shall use only publicly available clinical guidelines and research criteria

### 6.3 Operational Constraints

**C-3.1**: The system shall not automatically trigger clinical actions without human approval

**C-3.2**: The system shall not send communications to patients without clinician review

**C-3.3**: The system shall not make autonomous referral decisions

## 7. Assumptions

### 7.1 User Behavior Assumptions

**A-1.1**: Clinicians will review and validate all AI-generated outputs before use

**A-1.2**: Clinicians will provide accurate and complete input during clinical intent capture

**A-1.3**: Patients will read generated summaries and follow up with questions to their clinicians

### 7.2 Data Assumptions

**A-2.1**: Synthetic datasets adequately simulate real-world clinical consultations

**A-2.2**: Public clinical trial criteria are sufficiently detailed for eligibility signal generation

**A-2.3**: Public clinical guidelines provide adequate reference material for documentation structure

### 7.3 Technical Assumptions

**A-3.1**: AI models can accurately extract structured information from clinical narratives

**A-3.2**: Speech-to-text technology can handle medical terminology with acceptable accuracy

**A-3.3**: Natural language generation can produce clinically appropriate documentation

### 7.4 Regulatory Assumptions

**A-4.1**: The system as designed does not constitute a medical device requiring regulatory approval

**A-4.2**: Use of synthetic data is acceptable for prototype demonstration

**A-4.3**: Human-in-the-loop design mitigates regulatory concerns for AI-generated clinical content

## 8. Future Scope

### 8.1 System Integration

**FS-1.1**: Integration with Hospital Information Systems (HIS) for seamless workflow

**FS-1.2**: Bidirectional integration with Electronic Health Record (EHR) systems

**FS-1.3**: Integration with laboratory and radiology information systems

**FS-1.4**: ABDM (Ayushman Bharat Digital Mission) interoperability for national health stack integration

### 8.2 Feature Enhancements

**FS-2.1**: Multilingual support for regional languages in India

**FS-2.2**: Voice output for patient summaries (text-to-speech)

**FS-2.3**: Mobile application for patient access to visit summaries

**FS-2.4**: Telemedicine integration for remote consultations

### 8.3 Analytics & Insights

**FS-3.1**: Structured analytics dashboard for hospital administrators

**FS-3.2**: Aggregate reporting on documentation efficiency metrics

**FS-3.3**: Research pipeline analytics for trial recruitment effectiveness

**FS-3.4**: Quality improvement insights based on documentation patterns

### 8.4 Advanced Capabilities

**FS-4.1**: Predictive models for care pathway optimization (with appropriate validation)

**FS-4.2**: Automated coding assistance for billing and insurance (non-binding suggestions)

**FS-4.3**: Clinical decision support integration (with regulatory compliance)

**FS-4.4**: Longitudinal patient journey visualization

---

## Document Control

**Version**: 1.0  
**Last Updated**: February 15, 2026  
**Status**: Draft  
**Owner**: Team Sahrova - ClinicalSetu Development Team 
