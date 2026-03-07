"""
ClinicalSetu - AI-Powered Clinical Intelligence Bridge
Main Lambda Handler: Processes a consultation narrative through Amazon Bedrock
to generate 5 structured outputs (SOAP Note, Patient Summary, Referral Letter,
Discharge Summary, Trial Matching).

Features:
- Retry with exponential backoff for Bedrock throttling
- Fallback to secondary model if primary model fails (Nova Lite -> Nova Micro)
- DynamoDB caching to reduce costs and improve latency
- Partial result handling (returns completed steps even if later steps fail)
"""

import json
import os
import time
import hashlib
import random
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

# Initialize AWS clients
bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

# DynamoDB client for caching
CACHE_TABLE = os.environ.get("DYNAMODB_CACHE_TABLE", "ClinicalSetu-Cache")
CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() == "true"
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))

# Configuration - Primary: Amazon Nova Lite (cost-efficient), Fallback: Nova Micro
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
FALLBACK_MODEL_ID = os.environ.get("BEDROCK_FALLBACK_MODEL_ID", "us.amazon.nova-micro-v1:0")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
MAX_TOKENS = 4096
TEMPERATURE = 0.3

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 15.0  # seconds


def _get_cache_table():
    """Get DynamoDB table, returns None if table doesn't exist."""
    try:
        table = dynamodb.Table(CACHE_TABLE)
        table.load()
        return table
    except ClientError:
        return None


def _compute_cache_key(consultation_text, patient, referral_reason):
    """Create a hash key from the consultation input for caching."""
    cache_input = json.dumps({
        "text": consultation_text.strip().lower(),
        "age": patient.get("age"),
        "gender": patient.get("gender"),
        "referral": referral_reason or ""
    }, sort_keys=True)
    return hashlib.sha256(cache_input.encode()).hexdigest()


def _get_cached_result(cache_key):
    """Check DynamoDB for a cached result."""
    if not CACHE_ENABLED:
        return None
    table = _get_cache_table()
    if not table:
        return None
    try:
        response = table.get_item(Key={"cache_key": cache_key})
        item = response.get("Item")
        if item:
            # Check TTL (24 hours)
            cached_at = item.get("cached_at", 0)
            if time.time() - cached_at < 86400:
                return json.loads(item["result_json"])
    except Exception:
        pass
    return None


def _put_cached_result(cache_key, result):
    """Store a result in DynamoDB cache."""
    if not CACHE_ENABLED:
        return
    table = _get_cache_table()
    if not table:
        return
    try:
        table.put_item(Item={
            "cache_key": cache_key,
            "result_json": json.dumps(result),
            "cached_at": int(time.time()),
            "ttl": int(time.time()) + 86400  # 24h TTL
        })
    except Exception:
        pass  # Caching failure should not break the main flow


def load_prompt_template(template_name):
    """Load a prompt template from the prompts directory."""
    template_path = Path(__file__).parent.parent / "prompts" / f"{template_name}.txt"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    alt_path = Path(__file__).parent / "prompts" / f"{template_name}.txt"
    if alt_path.exists():
        return alt_path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt template not found: {template_name}")


def invoke_bedrock(prompt, model_id=None, max_tokens=MAX_TOKENS, temperature=TEMPERATURE):
    """
    Call Amazon Bedrock using the Converse API (model-agnostic: works with Nova, Claude, etc.)
    Retries with exponential backoff, then falls back to secondary model.
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
                    time.sleep(delay)
                    continue
                else:
                    raise
            except Exception as e:
                last_error = e
                delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
                time.sleep(delay)

    raise last_error or Exception("All Bedrock invocation attempts failed")


def parse_json_response(response_text):
    """Extract and parse JSON from LLM response, handling markdown code blocks."""
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
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


def generate_discharge_summary(soap_note, patient_name, patient_age, patient_gender, doctor_name):
    """Generate a structured discharge/visit summary from the SOAP note."""
    template = load_prompt_template("discharge_summary")
    prompt = template.replace("{soap_note}", json.dumps(soap_note, indent=2))
    prompt = prompt.replace("{patient_name}", patient_name)
    prompt = prompt.replace("{patient_age}", str(patient_age))
    prompt = prompt.replace("{patient_gender}", patient_gender)
    prompt = prompt.replace("{doctor_name}", doctor_name)
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

    if KNOWLEDGE_BASE_ID:
        try:
            return _trial_matching_with_rag(prompt, soap_note)
        except Exception:
            pass

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
    """Load clinical trials data."""
    trials_path = Path(__file__).parent.parent.parent / "data" / "clinical_trials.json"
    if trials_path.exists():
        return json.loads(trials_path.read_text(encoding="utf-8"))
    alt_path = Path(__file__).parent / "clinical_trials.json"
    if alt_path.exists():
        return json.loads(alt_path.read_text(encoding="utf-8"))
    return []


def translate_patient_summary(summary, target_language):
    """Translate a patient summary into a regional Indian language using Bedrock."""
    prompt = f"""Translate the following patient summary into {target_language}.
Keep the EXACT same JSON structure and keys in English, but translate ALL values into {target_language}.
Keep medication names in English (transliterated names in parentheses where helpful).
Use simple, conversational {target_language} that a patient with basic literacy can understand.

PATIENT SUMMARY JSON:
{json.dumps(summary, indent=2, ensure_ascii=False)}

Return ONLY valid JSON with the same structure, all values translated to {target_language}. No markdown, no code blocks."""

    response_text = invoke_bedrock(prompt)
    return parse_json_response(response_text)


def _run_step(step_name, fn, results, model_used=None):
    """Run a processing step with error isolation. Returns the result or None on failure."""
    step_start = time.time()
    try:
        result = fn()
        results["processing_steps"].append({
            "step": step_name,
            "duration_ms": int((time.time() - step_start) * 1000),
            "model": model_used or MODEL_ID,
            "status": "completed"
        })
        return result
    except Exception as e:
        results["processing_steps"].append({
            "step": step_name,
            "duration_ms": int((time.time() - step_start) * 1000),
            "model": model_used or MODEL_ID,
            "status": "failed",
            "error": str(e)
        })
        return None


def lambda_handler(event, context):
    """
    Main Lambda handler. Routes based on path:
    - POST /api/process  -> process consultation
    - POST /api/translate -> translate patient summary
    """
    path = event.get("path", "") or event.get("resource", "")
    if "/translate" in path:
        return _handle_translate(event)

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

        # Check DynamoDB cache first
        cache_key = _compute_cache_key(consultation_text, patient, referral_reason)
        cached = _get_cached_result(cache_key)
        if cached:
            cached["metadata"]["cache_hit"] = True
            return {
                "statusCode": 200,
                "headers": _cors_headers(),
                "body": json.dumps(cached, indent=2)
            }

        start_time = time.time()
        results = {"processing_steps": []}

        # Step 1: SOAP Note (critical - all others depend on this)
        soap_note = _run_step(
            "SOAP Note Generation",
            lambda: generate_soap_note(
                consultation_text,
                patient_context={
                    "name": patient["name"],
                    "age": patient["age"],
                    "gender": patient["gender"],
                    "id": patient.get("patient_id", "N/A")
                }
            ),
            results
        )

        if soap_note is None:
            return _error_response(500, "SOAP Note generation failed. Please try again.")

        results["soap_note"] = soap_note

        # Step 2: Patient Summary
        patient_summary = _run_step(
            "Patient Summary Generation",
            lambda: generate_patient_summary(soap_note, patient["name"], doctor["name"]),
            results
        )
        results["patient_summary"] = patient_summary or {
            "error": "Generation failed", "message": "Patient summary could not be generated."
        }

        # Step 3: Referral Letter
        referral_letter = _run_step(
            "Referral Letter Generation",
            lambda: generate_referral_letter(
                soap_note, referral_reason,
                f"{doctor['name']}, {doctor['speciality']}",
                specialist_type
            ),
            results
        )
        results["referral_letter"] = referral_letter or {
            "error": "Generation failed", "message": "Referral letter could not be generated."
        }

        # Step 4: Discharge Summary
        discharge_summary = _run_step(
            "Discharge Summary Generation",
            lambda: generate_discharge_summary(
                soap_note, patient["name"], patient["age"],
                patient["gender"], f"{doctor['name']}, {doctor['speciality']}"
            ),
            results
        )
        results["discharge_summary"] = discharge_summary or {
            "error": "Generation failed", "message": "Discharge summary could not be generated."
        }

        # Step 5: Clinical Trial Matching
        trial_matches = _run_step(
            "Clinical Trial Matching",
            lambda: generate_trial_matches(
                soap_note, patient["age"], patient["gender"], load_clinical_trials()
            ),
            results
        )
        results["trial_matches"] = trial_matches or {
            "error": "Generation failed", "message": "Trial matching could not be completed."
        }

        # Metadata
        total_duration = int((time.time() - start_time) * 1000)
        completed = sum(1 for s in results["processing_steps"] if s["status"] == "completed")
        total = len(results["processing_steps"])

        results["metadata"] = {
            "total_processing_time_ms": total_duration,
            "model_used": MODEL_ID,
            "fallback_model": FALLBACK_MODEL_ID,
            "consultation_id": body.get("id", f"CONSULT-{int(time.time())}"),
            "patient_id": patient.get("patient_id", "N/A"),
            "steps_completed": f"{completed}/{total}",
            "cache_hit": False,
            "disclaimer": "AI-Generated - Requires Clinician Validation. This output is for informational purposes only and does not constitute medical advice, diagnosis, or treatment recommendations.",
            "version": "1.1.0"
        }

        # Cache the result in DynamoDB
        _put_cached_result(cache_key, results)

        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps(results, indent=2)
        }

    except KeyError as e:
        return _error_response(400, f"Missing required field: {str(e)}")
    except json.JSONDecodeError as e:
        return _error_response(400, f"Invalid JSON in request or AI response: {str(e)}")
    except Exception as e:
        return _error_response(500, f"Internal error: {str(e)}")


def _handle_translate(event):
    """Handle translation of patient summary into regional languages."""
    try:
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", event)

        summary = body["summary"]
        target_language = body["target_language"]

        translated = translate_patient_summary(summary, target_language)

        return {
            "statusCode": 200,
            "headers": _cors_headers(),
            "body": json.dumps({"translated_summary": translated}, ensure_ascii=False)
        }
    except Exception as e:
        return _error_response(500, f"Translation error: {str(e)}")


def _cors_headers():
    """Standard CORS headers."""
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS"
    }


def _error_response(status_code, message):
    """Return a structured error response."""
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps({
            "error": message,
            "disclaimer": "AI-Generated - Requires Clinician Validation"
        })
    }


# For local testing
if __name__ == "__main__":
    data_path = Path(__file__).parent.parent.parent / "data" / "synthetic_consultations.json"
    consultations = json.loads(data_path.read_text(encoding="utf-8"))

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
    print("\n=== DISCHARGE SUMMARY ===")
    print(json.dumps(result_body.get("discharge_summary", {}), indent=2)[:500])
    print("\n=== TRIAL MATCHES ===")
    print(json.dumps(result_body.get("trial_matches", {}), indent=2)[:500])
    print("\n=== METADATA ===")
    print(json.dumps(result_body.get("metadata", {}), indent=2))
