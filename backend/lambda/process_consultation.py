"""
ClinicalSetu - AI-Powered Clinical Intelligence Bridge
Main Lambda Handler: Processes a consultation narrative through Amazon Bedrock
to generate 4 structured outputs (SOAP Note, Patient Summary, Referral Letter, Trial Matching).
"""

import json
import os
import time
import boto3
from pathlib import Path

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

# Bedrock Knowledge Base client (for RAG trial matching)
bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

# Configuration
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
HAIKU_MODEL_ID = os.environ.get("BEDROCK_HAIKU_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
MAX_TOKENS = 4096
TEMPERATURE = 0.3


def load_prompt_template(template_name):
    """Load a prompt template from the prompts directory."""
    # In Lambda, templates are bundled alongside the handler
    template_path = Path(__file__).parent.parent / "prompts" / f"{template_name}.txt"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Fallback: templates in same directory
    alt_path = Path(__file__).parent / "prompts" / f"{template_name}.txt"
    if alt_path.exists():
        return alt_path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt template not found: {template_name}")


def invoke_bedrock(prompt, model_id=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE):
    """Call Amazon Bedrock with the given prompt and return the response text."""
    if model_id is None:
        model_id = MODEL_ID

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })

    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body
    )

    response_body = json.loads(response["body"].read())
    return response_body["content"][0]["text"]


def parse_json_response(response_text):
    """Extract and parse JSON from LLM response, handling markdown code blocks."""
    text = response_text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


def generate_soap_note(consultation_text, patient_context):
    """Generate a structured SOAP note from consultation narrative."""
    template = load_prompt_template("soap_note")
    prompt = template.replace("{consultation_text}", consultation_text)
    prompt = prompt.replace("{patient_context}", json.dumps(patient_context, indent=2))

    response_text = invoke_bedrock(prompt)
    return parse_json_response(response_text)


def generate_patient_summary(soap_note, patient_name, doctor_name):
    """Generate a patient-friendly summary from the SOAP note."""
    template = load_prompt_template("patient_summary")
    prompt = template.replace("{soap_note}", json.dumps(soap_note, indent=2))
    prompt = prompt.replace("{patient_name}", patient_name)
    prompt = prompt.replace("{doctor_name}", doctor_name)

    response_text = invoke_bedrock(prompt)
    return parse_json_response(response_text)


def generate_referral_letter(soap_note, referral_reason, referring_doctor, specialist_type):
    """Generate a specialist referral letter."""
    if not referral_reason:
        return {
            "referral_letter": None,
            "message": "No referral indicated for this consultation",
            "confidence_score": 0
        }

    template = load_prompt_template("referral_letter")
    prompt = template.replace("{soap_note}", json.dumps(soap_note, indent=2))
    prompt = prompt.replace("{referral_reason}", referral_reason)
    prompt = prompt.replace("{referring_doctor}", referring_doctor)
    prompt = prompt.replace("{specialist_type}", specialist_type or "Specialist")
    prompt = prompt.replace("{current_date}", time.strftime("%Y-%m-%d"))

    response_text = invoke_bedrock(prompt)
    return parse_json_response(response_text)


def generate_trial_matches(soap_note, patient_age, patient_gender, clinical_trials_data):
    """Match patient profile against clinical trials using Bedrock (with optional KB RAG)."""
    template = load_prompt_template("trial_matching")
    prompt = template.replace("{soap_note}", json.dumps(soap_note, indent=2))
    prompt = prompt.replace("{patient_age}", str(patient_age))
    prompt = prompt.replace("{patient_gender}", patient_gender)
    prompt = prompt.replace("{clinical_trials}", json.dumps(clinical_trials_data, indent=2))

    # If Knowledge Base is configured, use RAG for enriched trial matching
    if KNOWLEDGE_BASE_ID:
        try:
            return _trial_matching_with_rag(prompt, soap_note)
        except Exception:
            pass  # Fall back to direct Bedrock call

    response_text = invoke_bedrock(prompt)
    return parse_json_response(response_text)


def _trial_matching_with_rag(prompt, soap_note):
    """Use Bedrock Knowledge Bases for RAG-enhanced trial matching."""
    query = f"Find clinical trials relevant to this patient profile: {json.dumps(soap_note.get('assessment', {}))}"

    response = bedrock_agent_runtime.retrieve_and_generate(
        input={"text": query},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": f"arn:aws:bedrock:us-east-1::foundation-model/{MODEL_ID}"
            }
        }
    )

    rag_context = response["output"]["text"]
    enriched_prompt = prompt + f"\n\nADDITIONAL CONTEXT FROM KNOWLEDGE BASE:\n{rag_context}"
    response_text = invoke_bedrock(enriched_prompt)
    return parse_json_response(response_text)


def load_clinical_trials():
    """Load clinical trials data. In production, this would come from S3/DynamoDB."""
    trials_path = Path(__file__).parent.parent.parent / "data" / "clinical_trials.json"
    if trials_path.exists():
        return json.loads(trials_path.read_text(encoding="utf-8"))
    # Fallback for Lambda deployment - load from environment or bundled file
    alt_path = Path(__file__).parent / "clinical_trials.json"
    if alt_path.exists():
        return json.loads(alt_path.read_text(encoding="utf-8"))
    return []


def lambda_handler(event, context):
    """
    Main Lambda handler.
    Expects a JSON body with:
    - consultation_text: string (the doctor's narrative)
    - patient: { name, age, gender, patient_id }
    - doctor: { name, speciality, hospital }
    - referral_reason: string or null
    - specialist_type: string or null
    """
    try:
        # Parse input
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", event)

        consultation_text = body["consultation_text"]
        patient = body["patient"]
        doctor = body["doctor"]
        referral_reason = body.get("referral_reason")
        specialist_type = body.get("specialist_type")

        start_time = time.time()
        results = {"processing_steps": []}

        # Step 1: Generate SOAP Note (all other outputs depend on this)
        step_start = time.time()
        soap_note = generate_soap_note(
            consultation_text,
            patient_context={
                "name": patient["name"],
                "age": patient["age"],
                "gender": patient["gender"],
                "id": patient.get("patient_id", "N/A")
            }
        )
        results["soap_note"] = soap_note
        results["processing_steps"].append({
            "step": "SOAP Note Generation",
            "duration_ms": int((time.time() - step_start) * 1000),
            "model": MODEL_ID,
            "status": "completed"
        })

        # Step 2: Generate Patient Summary (depends on SOAP)
        step_start = time.time()
        patient_summary = generate_patient_summary(
            soap_note,
            patient["name"],
            doctor["name"]
        )
        results["patient_summary"] = patient_summary
        results["processing_steps"].append({
            "step": "Patient Summary Generation",
            "duration_ms": int((time.time() - step_start) * 1000),
            "model": MODEL_ID,
            "status": "completed"
        })

        # Step 3: Generate Referral Letter (depends on SOAP)
        step_start = time.time()
        referral_letter = generate_referral_letter(
            soap_note,
            referral_reason,
            f"{doctor['name']}, {doctor['speciality']}",
            specialist_type
        )
        results["referral_letter"] = referral_letter
        results["processing_steps"].append({
            "step": "Referral Letter Generation",
            "duration_ms": int((time.time() - step_start) * 1000),
            "model": MODEL_ID,
            "status": "completed"
        })

        # Step 4: Clinical Trial Matching (depends on SOAP)
        step_start = time.time()
        clinical_trials = load_clinical_trials()
        trial_matches = generate_trial_matches(
            soap_note,
            patient["age"],
            patient["gender"],
            clinical_trials
        )
        results["trial_matches"] = trial_matches
        results["processing_steps"].append({
            "step": "Clinical Trial Matching",
            "duration_ms": int((time.time() - step_start) * 1000),
            "model": MODEL_ID,
            "status": "completed"
        })

        # Metadata
        total_duration = int((time.time() - start_time) * 1000)
        results["metadata"] = {
            "total_processing_time_ms": total_duration,
            "model_used": MODEL_ID,
            "consultation_id": body.get("id", f"CONSULT-{int(time.time())}"),
            "patient_id": patient.get("patient_id", "N/A"),
            "disclaimer": "AI-Generated - Requires Clinician Validation. This output is for informational purposes only and does not constitute medical advice, diagnosis, or treatment recommendations.",
            "version": "1.0.0"
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            },
            "body": json.dumps(results, indent=2)
        }

    except KeyError as e:
        return _error_response(400, f"Missing required field: {str(e)}")
    except json.JSONDecodeError as e:
        return _error_response(400, f"Invalid JSON in request or AI response: {str(e)}")
    except Exception as e:
        return _error_response(500, f"Internal error: {str(e)}")


def _error_response(status_code, message):
    """Return a structured error response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "POST, OPTIONS"
        },
        "body": json.dumps({
            "error": message,
            "disclaimer": "AI-Generated - Requires Clinician Validation"
        })
    }


# For local testing
if __name__ == "__main__":
    # Load a sample consultation
    data_path = Path(__file__).parent.parent.parent / "data" / "synthetic_consultations.json"
    consultations = json.loads(data_path.read_text(encoding="utf-8"))

    # Test with first consultation
    test_event = consultations[0]
    print("Testing with consultation:", test_event["id"])
    print("Patient:", test_event["patient"]["name"])
    print("-" * 60)

    result = lambda_handler(test_event, None)
    result_body = json.loads(result["body"])

    print("\n=== SOAP NOTE ===")
    print(json.dumps(result_body.get("soap_note", {}), indent=2)[:500])
    print("\n=== PATIENT SUMMARY ===")
    print(json.dumps(result_body.get("patient_summary", {}), indent=2)[:500])
    print("\n=== REFERRAL LETTER ===")
    print(json.dumps(result_body.get("referral_letter", {}), indent=2)[:500])
    print("\n=== TRIAL MATCHES ===")
    print(json.dumps(result_body.get("trial_matches", {}), indent=2)[:500])
    print("\n=== METADATA ===")
    print(json.dumps(result_body.get("metadata", {}), indent=2))
