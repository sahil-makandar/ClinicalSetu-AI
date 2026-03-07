"""
ClinicalSetu - Multi-Agent Invoker Lambda
Called by API Gateway. Invokes the Bedrock Supervisor Agent which orchestrates
4 specialist collaborator agents via Multi-Agent Collaboration.

Architecture:
  Frontend -> API Gateway -> THIS Lambda -> Supervisor Agent (Bedrock)
                                              |-> SOAPAgent
                                              |-> SummaryAgent
                                              |-> ReferralAgent
                                              |-> TrialAgent

Fallback: If multi-agent fails, falls back to monolithic process_consultation handler.
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
MODEL_ID_DISPLAY = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")


def _invoke_multi_agent(event):
    """Invoke the Supervisor Agent and parse the multi-agent response."""
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

Please coordinate with your specialist agents:
1. SOAPAgent: Generate SOAP note from the consultation narrative
2. SummaryAgent: Create patient-friendly summary from the SOAP note
3. ReferralAgent: Generate discharge summary (and referral letter if needed) from the SOAP note
4. TrialAgent: Match patient against clinical trials from the SOAP assessment

After all agents complete, provide a brief summary of what was generated."""

    session_id = body.get("id", str(uuid.uuid4()))

    # Invoke the Supervisor Agent
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
                    # Track collaborator invocations
                    if "collaboratorInvocationInput" in inv:
                        collab = inv["collaboratorInvocationInput"]
                        collab_name = collab.get("collaboratorName", "unknown")
                        processing_steps.append({
                            "step": f"Supervisor -> {collab_name}",
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
                        _parse_tool_output(output_text, tool_outputs)

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
        "discharge_summary": tool_outputs.get("discharge_summary", {}),
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
            "architecture": "Bedrock Multi-Agent Collaboration (Supervisor + 4 Specialists)",
            "tools_called": len([s for s in processing_steps if "Agent called" in s.get("step", "")]),
            "agents_invoked": len([s for s in processing_steps if "Supervisor ->" in s.get("step", "")]),
            "disclaimer": "AI-Generated - Requires Clinician Validation. This output does not constitute medical advice.",
            "version": "3.0.0-multi-agent"
        }
    }

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps(result, indent=2)
    }


def _parse_tool_output(output_text, tool_outputs):
    """Parse tool output and classify it into the correct result category."""
    try:
        parsed = json.loads(output_text)
        # Identify which tool this is from based on content
        if "subjective" in parsed and "objective" in parsed:
            tool_outputs["soap_note"] = parsed
        elif "greeting" in parsed or "visit_summary" in parsed:
            tool_outputs["patient_summary"] = parsed
        elif "referral_letter" in parsed:
            tool_outputs["referral_letter"] = parsed
        elif "discharge_summary" in parsed or ("header" in parsed and "condition_at_discharge" in parsed):
            tool_outputs["discharge_summary"] = parsed
        elif "trial_matches" in parsed:
            tool_outputs["trial_matches"] = parsed
    except (json.JSONDecodeError, TypeError):
        pass


def lambda_handler(event, context):
    """
    Main handler. Tries multi-agent first, falls back to monolithic on failure.
    """
    # Handle CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": _cors_headers(), "body": ""}

    if not AGENT_ID or not AGENT_ALIAS_ID:
        print("[ClinicalSetu] No agent configured, using monolithic fallback")
        return _fallback(event, context)

    try:
        return _invoke_multi_agent(event)
    except Exception as e:
        print(f"[ClinicalSetu] Multi-agent failed: {e}, falling back to monolithic")
        return _fallback(event, context, fallback_reason=str(e))


def _fallback(event, context, fallback_reason=None):
    """Fall back to the monolithic process_consultation handler."""
    try:
        from process_consultation import lambda_handler as monolithic_handler
        result = monolithic_handler(event, context)
        # Tag the response as fallback
        if result.get("statusCode") == 200:
            body = json.loads(result["body"])
            body["metadata"]["architecture"] = "Monolithic (fallback from multi-agent)"
            if fallback_reason:
                body["metadata"]["fallback_reason"] = fallback_reason
            result["body"] = json.dumps(body, indent=2)
        return result
    except Exception as e2:
        return _error_response(500, f"Both multi-agent and fallback failed: {e2}")


def _cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS"
    }


def _error_response(status_code, message):
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps({
            "error": message,
            "disclaimer": "AI-Generated - Requires Clinician Validation"
        })
    }
