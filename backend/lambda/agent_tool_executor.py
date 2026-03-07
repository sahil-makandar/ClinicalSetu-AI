"""
ClinicalSetu - Bedrock Agent Tool Executor Lambda
This Lambda is invoked BY Bedrock Agent collaborator sub-agents when they use their clinical tools.

Part of the Multi-Agent Collaboration architecture:
  Supervisor Agent -> Collaborator Agents -> THIS Lambda (shared tool executor)

Tools:
  1. generate_soap - Structures clinical narrative into SOAP note
  2. generate_patient_summary - Creates patient-friendly summary from SOAP
  3. generate_referral - Drafts specialist referral letter
  4. generate_discharge - Generates discharge/visit summary from SOAP
  5. search_trials - Matches patient against clinical trials (with optional KB RAG)

Features:
  - Bedrock Converse API (model-agnostic: works with Nova Lite, Claude, etc.)
  - Retry with exponential backoff + jitter for throttling
  - Model fallback chain: Nova Lite (primary) -> Nova Micro (fallback)
"""

import json
import os
import time
import random
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)
bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

# Model configuration - same as monolithic Lambda for consistency
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
FALLBACK_MODEL_ID = os.environ.get("BEDROCK_FALLBACK_MODEL_ID", "us.amazon.nova-micro-v1:0")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
MAX_TOKENS = 4096
TEMPERATURE = 0.3

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0
MAX_DELAY = 15.0


def get_param(parameters, name):
    """Extract a named parameter from the Bedrock Agent parameters list."""
    for p in parameters:
        if p["name"] == name:
            return p["value"]
    return None


def invoke_bedrock(prompt, model_id=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE):
    """
    Call Amazon Bedrock using the Converse API (model-agnostic).
    Retries with exponential backoff + jitter, then falls back to secondary model.
    """
    if model_id is None:
        model_id = MODEL_ID

    models_to_try = [model_id]
    if model_id != FALLBACK_MODEL_ID:
        models_to_try.append(FALLBACK_MODEL_ID)

    last_error = None

    for current_model in models_to_try:
        for attempt in range(MAX_RETRIES):
            try:
                response = bedrock_runtime.converse(
                    modelId=current_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    inferenceConfig={
                        "maxTokens": max_tokens,
                        "temperature": temperature
                    }
                )
                return response["output"]["message"]["content"][0]["text"]

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                last_error = e

                if error_code in ("ThrottlingException", "TooManyRequestsException",
                                  "ServiceUnavailableException", "ModelTimeoutException"):
                    delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
                    print(f"[ClinicalSetu] {error_code} on {current_model}, retry {attempt+1}/{MAX_RETRIES} after {delay:.1f}s")
                    time.sleep(delay)
                    continue
                else:
                    raise
            except Exception as e:
                last_error = e
                delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
                time.sleep(delay)

        print(f"[ClinicalSetu] Exhausted retries on {current_model}, trying next model...")

    raise last_error or Exception("All Bedrock invocation attempts failed")


def parse_json_response(text):
    """Parse JSON from LLM response, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


def load_prompt_template(template_name):
    """Load a prompt template from the prompts directory."""
    template_path = Path(__file__).parent.parent / "prompts" / f"{template_name}.txt"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    alt_path = Path(__file__).parent / "prompts" / f"{template_name}.txt"
    if alt_path.exists():
        return alt_path.read_text(encoding="utf-8")
    return None


# ==========================================
# TOOL 1: SOAP Note Generation
# ==========================================
def tool_generate_soap(params):
    consultation_text = get_param(params, "consultation_text")
    patient_name = get_param(params, "patient_name") or "Patient"
    patient_age = get_param(params, "patient_age") or "Unknown"
    patient_gender = get_param(params, "patient_gender") or "Unknown"

    template = load_prompt_template("soap_note")
    if template:
        prompt = template.replace("{consultation_text}", consultation_text)
        prompt = prompt.replace("{patient_context}", json.dumps({
            "name": patient_name,
            "age": patient_age,
            "gender": patient_gender
        }, indent=2))
    else:
        prompt = f"""You are a clinical documentation assistant for ClinicalSetu. Transform the consultation narrative into a structured SOAP note.

CRITICAL SAFETY RULES:
1. You are a documentation assistant, not a diagnostic tool
2. Never suggest diagnoses not mentioned by the doctor
3. Never recommend treatments or medications not mentioned by the doctor
4. Flag any information that seems clinically inconsistent
5. If uncertain, mark the section for doctor review

PATIENT: {patient_name}, {patient_age} years old, {patient_gender}

CONSULTATION NARRATIVE:
{consultation_text}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "subjective": {{
    "chief_complaint": "",
    "history_of_present_illness": "",
    "review_of_systems": {{
      "relevant_positives": [],
      "relevant_negatives": []
    }},
    "past_medical_history": [],
    "medications": [],
    "allergies": []
  }},
  "objective": {{
    "vitals": {{}},
    "physical_exam": {{
      "general": "",
      "systems_examined": []
    }},
    "investigations": []
  }},
  "assessment": {{
    "primary_diagnosis": "",
    "secondary_diagnoses": [],
    "clinical_reasoning": ""
  }},
  "plan": {{
    "medications_prescribed": [],
    "investigations_ordered": [],
    "procedures_planned": [],
    "referrals": [],
    "follow_up": "",
    "patient_education": []
  }},
  "confidence_scores": {{
    "subjective": 85,
    "objective": 80,
    "assessment": 75,
    "plan": 90
  }},
  "flags": []
}}"""

    return parse_json_response(invoke_bedrock(prompt))


# ==========================================
# TOOL 2: Patient Summary Generation
# ==========================================
def tool_generate_patient_summary(params):
    soap_note_json = get_param(params, "soap_note_json")
    patient_name = get_param(params, "patient_name") or "Patient"
    doctor_name = get_param(params, "doctor_name") or "Doctor"

    template = load_prompt_template("patient_summary")
    if template:
        prompt = template.replace("{soap_note}", soap_note_json if isinstance(soap_note_json, str) else json.dumps(soap_note_json, indent=2))
        prompt = prompt.replace("{patient_name}", patient_name)
        prompt = prompt.replace("{doctor_name}", doctor_name)
    else:
        prompt = f"""You are a patient communication assistant for ClinicalSetu. Convert the SOAP note into a patient-friendly summary.

GUIDELINES:
- Use simple, non-technical language (8th-grade reading level)
- Explain medical terms in parentheses
- Focus on actionable information
- Avoid alarming language
- Include warning signs

PATIENT: {patient_name}
DOCTOR: {doctor_name}
SOAP NOTE: {soap_note_json}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "greeting": "Dear {patient_name},",
  "visit_summary": "",
  "what_the_doctor_found": "",
  "your_diagnosis": "",
  "your_treatment_plan": {{
    "medications": [
      {{
        "name": "",
        "what_its_for": "",
        "how_to_take": "",
        "important_notes": ""
      }}
    ],
    "lifestyle_advice": [],
    "tests_ordered": [
      {{
        "test_name": "",
        "why_needed": ""
      }}
    ]
  }},
  "follow_up": {{
    "next_appointment": "",
    "what_to_bring": []
  }},
  "warning_signs": [],
  "questions_to_ask": [],
  "disclaimer": "This summary was generated by AI based on your doctor's notes. Always follow your doctor's verbal instructions."
}}"""

    return parse_json_response(invoke_bedrock(prompt))


# ==========================================
# TOOL 3: Referral Letter Generation
# ==========================================
def tool_generate_referral(params):
    soap_note_json = get_param(params, "soap_note_json")
    referral_reason = get_param(params, "referral_reason")
    referring_doctor = get_param(params, "referring_doctor") or "Doctor"
    specialist_type = get_param(params, "specialist_type") or "Specialist"

    template = load_prompt_template("referral_letter")
    if template:
        prompt = template.replace("{soap_note}", soap_note_json if isinstance(soap_note_json, str) else json.dumps(soap_note_json, indent=2))
        prompt = prompt.replace("{referral_reason}", referral_reason or "General specialist consultation")
        prompt = prompt.replace("{referring_doctor}", referring_doctor)
        prompt = prompt.replace("{specialist_type}", specialist_type)
        prompt = prompt.replace("{current_date}", time.strftime("%Y-%m-%d"))
    else:
        prompt = f"""You are a clinical referral assistant for ClinicalSetu. Generate a structured specialist referral letter.

REFERRING DOCTOR: {referring_doctor}
SPECIALIST TYPE: {specialist_type}
REFERRAL REASON: {referral_reason}
DATE: {time.strftime("%Y-%m-%d")}
SOAP NOTE: {soap_note_json}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "referral_letter": {{
    "date": "{time.strftime("%Y-%m-%d")}",
    "to": "The {specialist_type}",
    "from": "{referring_doctor}",
    "patient_summary": {{
      "demographics": "",
      "presenting_complaint": ""
    }},
    "reason_for_referral": "",
    "relevant_history": {{
      "current_condition": "",
      "relevant_past_history": [],
      "current_medications": [],
      "allergies": ""
    }},
    "investigations": {{
      "completed": [],
      "pending": [],
      "recommended_before_visit": []
    }},
    "clinical_questions": [],
    "urgency": {{
      "level": "routine",
      "reasoning": ""
    }},
    "patient_preparation_checklist": []
  }},
  "confidence_score": 80,
  "flags": []
}}"""

    return parse_json_response(invoke_bedrock(prompt))


# ==========================================
# TOOL 4: Discharge Summary Generation
# ==========================================
def tool_generate_discharge(params):
    soap_note_json = get_param(params, "soap_note_json")
    patient_name = get_param(params, "patient_name") or "Patient"
    patient_age = get_param(params, "patient_age") or "Unknown"
    patient_gender = get_param(params, "patient_gender") or "Unknown"
    doctor_name = get_param(params, "doctor_name") or "Doctor"

    template = load_prompt_template("discharge_summary")
    if template:
        prompt = template.replace("{soap_note}", soap_note_json if isinstance(soap_note_json, str) else json.dumps(soap_note_json, indent=2))
        prompt = prompt.replace("{patient_name}", patient_name)
        prompt = prompt.replace("{patient_age}", str(patient_age))
        prompt = prompt.replace("{patient_gender}", patient_gender)
        prompt = prompt.replace("{doctor_name}", doctor_name)
        prompt = prompt.replace("{current_date}", time.strftime("%Y-%m-%d"))
    else:
        prompt = f"""You are a clinical documentation assistant for ClinicalSetu. Generate a structured discharge/visit summary from the SOAP note.

CRITICAL SAFETY RULES:
1. You are a documentation assistant, not a diagnostic tool
2. Never suggest diagnoses not mentioned by the doctor
3. Never recommend treatments or medications not mentioned by the doctor

SOAP NOTE: {soap_note_json}
PATIENT: {patient_name}, {patient_age} years, {patient_gender}
DOCTOR: {doctor_name}
DATE: {time.strftime("%Y-%m-%d")}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "discharge_summary": {{
    "header": {{
      "facility": "Hospital/Clinic name from doctor context",
      "patient_name": "{patient_name}",
      "age_gender": "{patient_age}y / {patient_gender}",
      "date_of_visit": "{time.strftime("%Y-%m-%d")}",
      "attending_physician": "{doctor_name}",
      "visit_type": "OPD Consultation"
    }},
    "chief_complaint": "",
    "history_of_present_illness": "",
    "past_medical_history": "",
    "examination_findings": "",
    "investigations": {{
      "completed": [],
      "ordered": []
    }},
    "diagnosis": {{
      "primary": "",
      "secondary": []
    }},
    "treatment_given": {{
      "medications": [],
      "procedures": [],
      "advice": []
    }},
    "condition_at_discharge": "",
    "follow_up_plan": {{
      "next_visit": "",
      "investigations_before_visit": [],
      "referrals": [],
      "emergency_instructions": ""
    }},
    "doctor_signature": {{
      "name": "{doctor_name}",
      "designation": "",
      "date": "{time.strftime("%Y-%m-%d")}"
    }}
  }},
  "confidence_score": 85,
  "disclaimer": "AI-Generated - Requires Clinician Validation."
}}"""

    return parse_json_response(invoke_bedrock(prompt))


# ==========================================
# TOOL 5: Clinical Trial Matching (with RAG)
# ==========================================
def tool_search_trials(params):
    soap_assessment = get_param(params, "soap_assessment")
    patient_age = get_param(params, "patient_age") or "Unknown"
    patient_gender = get_param(params, "patient_gender") or "Unknown"

    # Try to parse assessment to extract diagnosis
    try:
        assessment = json.loads(soap_assessment) if isinstance(soap_assessment, str) else soap_assessment
        diagnosis = assessment.get("primary_diagnosis", "unspecified")
    except (json.JSONDecodeError, AttributeError):
        diagnosis = str(soap_assessment)
        assessment = {"primary_diagnosis": diagnosis}

    # Use Knowledge Base RAG if configured
    rag_context = ""
    if KNOWLEDGE_BASE_ID:
        try:
            query = f"Clinical trials for {diagnosis} in {patient_gender} patients aged {patient_age} in India"
            rag_response = bedrock_agent_runtime.retrieve_and_generate(
                input={"text": query},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                        "modelArn": f"arn:aws:bedrock:us-east-1::foundation-model/{MODEL_ID}"
                    }
                }
            )
            rag_context = rag_response["output"]["text"]
        except Exception as e:
            print(f"[ClinicalSetu] KB RAG failed: {e}")

    # Load bundled trial data as fallback context
    bundled_trials = ""
    trials_path = Path(__file__).parent / "clinical_trials.json"
    if trials_path.exists():
        bundled_trials = trials_path.read_text(encoding="utf-8")

    prompt = f"""You are a clinical research signal engine for ClinicalSetu.

CRITICAL: All signals are INFORMATIONAL ONLY - not recommendations for enrollment.

PATIENT PROFILE:
- Age: {patient_age} years
- Gender: {patient_gender}
- Assessment: {json.dumps(assessment, indent=2)}

{f"KNOWLEDGE BASE RESULTS:{chr(10)}{rag_context}" if rag_context else ""}

AVAILABLE CLINICAL TRIALS:
{bundled_trials[:8000] if bundled_trials else "No trial data available."}

Match this patient against clinical trials. Only include matches with confidence >= 60%.
Return ONLY valid JSON (no markdown, no code blocks):
{{
  "patient_profile_extracted": {{
    "age": {patient_age},
    "gender": "{patient_gender}",
    "primary_diagnosis": "{diagnosis}",
    "comorbidities": [],
    "current_medications": []
  }},
  "trial_matches": [
    {{
      "trial_id": "NCT...",
      "trial_title": "",
      "trial_phase": "",
      "sponsor": "",
      "enrollment_status": "Recruiting",
      "matched_criteria": [
        {{
          "criterion": "",
          "patient_value": "",
          "required_value": "",
          "match": true
        }}
      ],
      "unmatched_criteria": [],
      "missing_information": [],
      "confidence_score": 75,
      "locations": [],
      "contact_info": ""
    }}
  ],
  "summary": "",
  "disclaimer": "INFORMATIONAL ONLY: These are potential eligibility signals. A qualified physician must review all criteria. Patient consent is always required."
}}"""

    return parse_json_response(invoke_bedrock(prompt))


# ==========================================
# Lambda Entry Point
# ==========================================
def lambda_handler(event, context):
    """
    Called by Bedrock Agent collaborators. Routes to the correct tool based on event["function"].
    Returns response in the exact format Bedrock Agent expects.
    """
    action_group = event.get("actionGroup", "ClinicalTools")
    function_name = event.get("function", "")
    parameters = event.get("parameters", [])

    print(f"[ClinicalSetu] Tool called: {function_name}")
    print(f"[ClinicalSetu] Parameters: {json.dumps(parameters, default=str)[:500]}")

    try:
        if function_name == "generate_soap":
            result = tool_generate_soap(parameters)
        elif function_name == "generate_patient_summary":
            result = tool_generate_patient_summary(parameters)
        elif function_name == "generate_referral":
            result = tool_generate_referral(parameters)
        elif function_name == "generate_discharge":
            result = tool_generate_discharge(parameters)
        elif function_name == "search_trials":
            result = tool_search_trials(parameters)
        else:
            result = {"error": f"Unknown function: {function_name}"}

        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": action_group,
                "function": function_name,
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps(result)
                        }
                    }
                }
            },
            "sessionAttributes": event.get("sessionAttributes", {}),
            "promptSessionAttributes": event.get("promptSessionAttributes", {})
        }

    except Exception as e:
        print(f"[ClinicalSetu] ERROR in {function_name}: {str(e)}")
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": action_group,
                "function": function_name,
                "functionResponse": {
                    "responseState": "FAILURE",
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({"error": str(e)})
                        }
                    }
                }
            },
            "sessionAttributes": event.get("sessionAttributes", {}),
            "promptSessionAttributes": event.get("promptSessionAttributes", {})
        }
