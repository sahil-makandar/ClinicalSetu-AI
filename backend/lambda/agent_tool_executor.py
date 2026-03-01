"""
ClinicalSetu - Bedrock Agent Tool Executor Lambda
This Lambda is invoked BY the Bedrock Agent when it decides to use one of 4 clinical tools.
The agent orchestrates which tools to call and in what order -- this is the "agentic" behavior.

Tools:
  1. generate_soap - Structures clinical narrative into SOAP note
  2. generate_patient_summary - Creates patient-friendly summary from SOAP
  3. generate_referral - Drafts specialist referral letter
  4. search_trials - Matches patient against clinical trials (with optional KB RAG)
"""

import json
import os
import time
import boto3

bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)
bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")


def get_param(parameters, name):
    """Extract a named parameter from the Bedrock Agent parameters list."""
    for p in parameters:
        if p["name"] == name:
            return p["value"]
    return None


def invoke_claude(prompt, max_tokens=4096):
    """Call Claude via Bedrock InvokeModel."""
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}]
    })
    response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body
    )
    return json.loads(response["body"].read())["content"][0]["text"]


def parse_json_response(text):
    """Parse JSON from LLM response, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


# ==========================================
# TOOL 1: SOAP Note Generation
# ==========================================
def tool_generate_soap(params):
    consultation_text = get_param(params, "consultation_text")
    patient_name = get_param(params, "patient_name")
    patient_age = get_param(params, "patient_age")
    patient_gender = get_param(params, "patient_gender")

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

    return parse_json_response(invoke_claude(prompt))


# ==========================================
# TOOL 2: Patient Summary Generation
# ==========================================
def tool_generate_patient_summary(params):
    soap_note_json = get_param(params, "soap_note_json")
    patient_name = get_param(params, "patient_name")
    doctor_name = get_param(params, "doctor_name")

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

    return parse_json_response(invoke_claude(prompt))


# ==========================================
# TOOL 3: Referral Letter Generation
# ==========================================
def tool_generate_referral(params):
    soap_note_json = get_param(params, "soap_note_json")
    referral_reason = get_param(params, "referral_reason")
    referring_doctor = get_param(params, "referring_doctor")
    specialist_type = get_param(params, "specialist_type") or "Specialist"

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

    return parse_json_response(invoke_claude(prompt))


# ==========================================
# TOOL 4: Clinical Trial Matching (with RAG)
# ==========================================
def tool_search_trials(params):
    soap_assessment = get_param(params, "soap_assessment")
    patient_age = get_param(params, "patient_age")
    patient_gender = get_param(params, "patient_gender")

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
            print(f"KB RAG failed: {e}")

    # Load bundled trial data as fallback context
    from pathlib import Path
    trials_path = Path(__file__).parent / "clinical_trials.json"
    bundled_trials = ""
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

    return parse_json_response(invoke_claude(prompt))


# ==========================================
# Lambda Entry Point
# ==========================================
def lambda_handler(event, context):
    """
    Called by Bedrock Agent. Routes to the correct tool based on event["function"].
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
