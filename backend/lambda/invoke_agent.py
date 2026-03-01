"""
ClinicalSetu - Agent Invoker Lambda
Called by API Gateway. Invokes the Bedrock Agent which orchestrates the 4 clinical tools.

This is the agentic architecture:
  Frontend → API Gateway → THIS Lambda → Bedrock Agent → Tool Executor Lambda
                                                      → Knowledge Base (RAG)

The Bedrock Agent DECIDES which tools to call and in what order based on the consultation.
"""

import json
import os
import uuid
import time
import boto3

bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

AGENT_ID = os.environ.get("BEDROCK_AGENT_ID", "")
AGENT_ALIAS_ID = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "")


def lambda_handler(event, context):
    """
    Main handler. Accepts consultation data, invokes the Bedrock Agent,
    collects the streamed response and tool trace, returns structured results.
    """
    try:
        # Parse input from API Gateway
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", event)

        consultation_text = body["consultation_text"]
        patient = body["patient"]
        doctor = body["doctor"]
        referral_reason = body.get("referral_reason") or ""
        specialist_type = body.get("specialist_type") or ""

        start_time = time.time()

        # Build the agent prompt
        referral_instruction = (
            f"A referral is needed to {specialist_type}. Reason: {referral_reason}. "
            "Please generate a referral letter using the generate_referral tool."
            if referral_reason
            else "No referral is needed for this consultation. Skip the generate_referral tool."
        )

        agent_prompt = f"""Process this clinical consultation for {patient['name']} and generate all required documentation.

CLINICAL CONSULTATION NARRATIVE:
{consultation_text}

PATIENT DETAILS:
- Name: {patient['name']}
- Age: {patient['age']} years
- Gender: {patient['gender']}
- Patient ID: {patient.get('patient_id', 'N/A')}

DOCTOR: {doctor['name']}, {doctor.get('speciality', 'General Medicine')}, {doctor.get('hospital', '')}

REFERRAL: {referral_instruction}

Please execute the following steps in order:
1. Call generate_soap with the consultation narrative and patient details
2. Call generate_patient_summary with the SOAP note output, patient name, and doctor name
3. {"Call generate_referral with the SOAP note, referral reason, doctor info, and specialist type" if referral_reason else "Skip referral (not needed)"}
4. Call search_trials with the SOAP assessment, patient age, and patient gender

After all tools complete, provide a brief summary of what was generated."""

        session_id = body.get("id", str(uuid.uuid4()))

        # Invoke the Bedrock Agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=agent_prompt,
            enableTrace=True,
            sessionState={
                "sessionAttributes": {
                    "patient_id": patient.get("patient_id", "N/A"),
                    "consultation_id": session_id,
                    "doctor_name": doctor["name"]
                }
            }
        )

        # Collect streamed response and trace
        agent_response_text = ""
        processing_steps = []
        tool_outputs = {}

        for event_item in response.get("completion", []):
            if "chunk" in event_item:
                chunk_bytes = event_item["chunk"].get("bytes", b"")
                if isinstance(chunk_bytes, bytes):
                    agent_response_text += chunk_bytes.decode("utf-8")
                else:
                    agent_response_text += str(chunk_bytes)

            if "trace" in event_item:
                trace = event_item["trace"].get("trace", {})

                # Capture orchestration trace for processing steps
                if "orchestrationTrace" in trace:
                    orch = trace["orchestrationTrace"]

                    # Tool invocation
                    if "invocationInput" in orch:
                        inv = orch["invocationInput"]
                        if "actionGroupInvocationInput" in inv:
                            tool_info = inv["actionGroupInvocationInput"]
                            tool_name = tool_info.get("function", "unknown")
                            processing_steps.append({
                                "step": f"Agent called: {tool_name}",
                                "duration_ms": 0,
                                "model": MODEL_ID_DISPLAY,
                                "status": "invoked"
                            })

                    # Tool response
                    if "observation" in orch:
                        obs = orch["observation"]
                        if "actionGroupInvocationOutput" in obs:
                            output = obs["actionGroupInvocationOutput"]
                            output_text = output.get("text", "")
                            # Try to parse the tool output
                            try:
                                parsed = json.loads(output_text)
                                # Identify which tool this is from based on content
                                if "subjective" in parsed and "objective" in parsed:
                                    tool_outputs["soap_note"] = parsed
                                elif "greeting" in parsed or "visit_summary" in parsed:
                                    tool_outputs["patient_summary"] = parsed
                                elif "referral_letter" in parsed:
                                    tool_outputs["referral_letter"] = parsed
                                elif "trial_matches" in parsed:
                                    tool_outputs["trial_matches"] = parsed
                            except (json.JSONDecodeError, TypeError):
                                pass

        total_duration = int((time.time() - start_time) * 1000)

        # Build the response in the same format the frontend expects
        result = {
            "soap_note": tool_outputs.get("soap_note", {}),
            "patient_summary": tool_outputs.get("patient_summary", {}),
            "referral_letter": tool_outputs.get("referral_letter", {
                "referral_letter": None,
                "message": "No referral indicated" if not referral_reason else "Referral generation pending",
                "confidence_score": 0
            }),
            "trial_matches": tool_outputs.get("trial_matches", {
                "trial_matches": [],
                "summary": "No trial matches found",
                "disclaimer": "INFORMATIONAL ONLY"
            }),
            "agent_summary": agent_response_text,
            "processing_steps": processing_steps,
            "metadata": {
                "total_processing_time_ms": total_duration,
                "model_used": MODEL_ID_DISPLAY,
                "agent_id": AGENT_ID,
                "agent_alias_id": AGENT_ALIAS_ID,
                "session_id": session_id,
                "consultation_id": body.get("id", session_id),
                "patient_id": patient.get("patient_id", "N/A"),
                "architecture": "Bedrock Agent with Tool Use (Agentic)",
                "tools_called": len(processing_steps),
                "disclaimer": "AI-Generated - Requires Clinician Validation. This output does not constitute medical advice.",
                "version": "2.0.0-agent"
            }
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST, OPTIONS"
            },
            "body": json.dumps(result, indent=2)
        }

    except KeyError as e:
        return _error_response(400, f"Missing required field: {str(e)}")
    except Exception as e:
        return _error_response(500, f"Agent invocation error: {str(e)}")


MODEL_ID_DISPLAY = "anthropic.claude-3-sonnet-20240229-v1:0"


def _error_response(status_code, message):
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
