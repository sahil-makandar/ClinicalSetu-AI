"""
ClinicalSetu - Agent Integration Test with Quick-Fill Patient Data
Tests the multi-agent orchestration with all 5 sample patients from the frontend.
Provides detailed debugging output to diagnose empty/failed agent responses.

Usage:
  python scripts/test_agent_quickfill.py

Environment variables:
  AWS_REGION (default: us-east-1)
  PROJECT_NAME (default: clinicalsetu)
  STAGE (default: prod)
"""

import boto3
import json
import os
import sys
import time
import uuid
import traceback

REGION = os.environ.get("AWS_REGION", "us-east-1")
PROJECT = os.environ.get("PROJECT_NAME", "clinicalsetu")
STAGE = os.environ.get("STAGE", "prod")

lambda_client = boto3.client("lambda", region_name=REGION)

INVOKER_LAMBDA = f"{PROJECT}-agent-invoker-{STAGE}"

# All 5 quick-fill patients from frontend/src/data/sampleConsultations.ts
QUICK_FILL_PATIENTS = [
    {
        "id": "CONSULT-001",
        "patient": {"name": "Rajesh Kumar Sharma", "age": 55, "gender": "Male", "patient_id": "SYN-PT-10001"},
        "doctor": {"name": "Dr. Rojina Mallick", "speciality": "Internal Medicine", "hospital": "City General Hospital, Kolkata, West Bengal"},
        "consultation_text": "Patient Rajesh Kumar Sharma, 55-year-old male, comes for a follow-up visit for his diabetes management. He was diagnosed with Type 2 Diabetes Mellitus about 3 years ago. He reports his fasting blood sugar at home has been running between 140-160 mg/dL over the past month. He says he has been taking Glycomet GP 2 regularly but admits to being irregular with his evening walk. He complains of occasional tingling in both feet for the past 2 weeks, worse at night. No visual disturbances. He also mentions feeling more tired than usual. He has a history of hypertension controlled on Telmisartan 40mg daily. No chest pain, no breathlessness. Family history of diabetes in mother. On examination, BP is 138/86 mmHg, pulse 78/min regular, weight 82 kg. BMI calculated at 28.4. Foot examination shows diminished sensation to monofilament testing in both feet, dorsalis pedis pulses palpable bilaterally. Rest of the systemic examination is unremarkable. HbA1c from last month was 8.2%. I'm going to increase his Glycomet GP to the GP 3 formulation, add Tab Pregabalin 75mg at bedtime for the neuropathy symptoms, and order a comprehensive metabolic panel, lipid profile, urine microalbumin, and a repeat HbA1c in 3 months. I've also advised strict dietary control and at least 30 minutes of walking daily. I want to refer him to an ophthalmologist for a diabetic retinopathy screening since it hasn't been done in over a year. Follow up in 6 weeks.",
        "referral_reason": "Diabetic retinopathy screening - not done in over 1 year",
        "specialist_type": "Ophthalmology"
    },
    {
        "id": "CONSULT-002",
        "patient": {"name": "Priya Venkatesh", "age": 34, "gender": "Female", "patient_id": "SYN-PT-10002"},
        "doctor": {"name": "Dr. Sahil Makandar", "speciality": "General Medicine", "hospital": "Apollo Clinic, Mapusa, Goa"},
        "consultation_text": "Priya Venkatesh, 34-year-old female, presents with complaints of persistent fatigue and joint pain for the past 3 months. She describes the fatigue as overwhelming, not relieved by rest, and affecting her work as a software engineer. Joint pain is primarily in the small joints of both hands, especially the proximal interphalangeal joints and metacarpophalangeal joints, with morning stiffness lasting about 45 minutes. She also reports a butterfly-shaped rash on her cheeks that worsens with sun exposure, which appeared about 2 months ago. She has noticed some hair thinning recently. No fever, no oral ulcers, no Raynaud's phenomenon. She has no significant past medical history. She is not on any regular medications. No known allergies. On examination, she appears fatigued. BP 118/76 mmHg, pulse 82/min, temp 37.1C. Malar rash noted on both cheeks. Mild synovitis of the PIP and MCP joints bilaterally, no deformity. No lymphadenopathy. Chest clear, heart sounds normal. I'm suspecting Systemic Lupus Erythematosus and have ordered ANA, anti-dsDNA antibodies, complement levels C3 and C4, CBC with differential, ESR, CRP, urinalysis with microscopy, and serum creatinine. I've advised her to use sunscreen SPF 50+ and avoid prolonged sun exposure. Starting her on Hydroxychloroquine 200mg twice daily. Referring to Rheumatology for further evaluation and confirmation. Follow up in 2 weeks with reports.",
        "referral_reason": "Suspected Systemic Lupus Erythematosus - needs rheumatological evaluation and confirmation",
        "specialist_type": "Rheumatology"
    },
    {
        "id": "CONSULT-003",
        "patient": {"name": "Arjun Reddy Patil", "age": 62, "gender": "Male", "patient_id": "SYN-PT-10003"},
        "doctor": {"name": "Dr. Meera Joshi", "speciality": "Pulmonology", "hospital": "Government District Hospital, Hyderabad"},
        "consultation_text": "Arjun Reddy Patil, 62-year-old male, retired auto-rickshaw driver, comes with complaints of progressive breathlessness on exertion for the past 6 months, now getting breathless even walking to the bathroom. He has a chronic productive cough with whitish sputum, occasionally yellowish, for the past 2 years. He is a heavy smoker, about 30 pack-years, and quit smoking only 6 months ago. He also reports weight loss of about 5 kg in the past 3 months without any change in appetite. He had pulmonary tuberculosis 15 years ago, completed DOTS treatment. No hemoptysis. No chest pain. No fever currently. He has no other comorbidities. On examination, he is thin built, BMI 19.2, appears breathless at rest. SpO2 is 91% on room air, respiratory rate 22/min, BP 126/80 mmHg. Chest examination shows bilateral wheezing with prolonged expiratory phase, reduced air entry in the right upper zone. No clubbing. Spirometry done today shows FEV1 of 42% predicted, FEV1/FVC ratio 0.58, indicating severe obstructive pattern with no significant bronchodilator reversibility. Chest X-ray shows hyperinflated lungs with a suspicious opacity in the right upper lobe measuring about 2.5 cm. Given his history and findings, I am diagnosing him with severe COPD, GOLD Stage 3. The right upper lobe opacity is concerning and needs further evaluation. Starting him on Tiotropium 18 mcg inhaler once daily, Budesonide-Formoterol 200/6 mcg inhaler twice daily, and SOS Salbutamol inhaler. Ordering a HRCT chest urgently, sputum for AFB and cytology, and CBC. Referring to Oncology for evaluation of the lung opacity. Follow up in 1 week with CT report.",
        "referral_reason": "Suspicious right upper lobe opacity 2.5 cm on chest X-ray - needs CT evaluation and oncological assessment",
        "specialist_type": "Oncology"
    },
    {
        "id": "CONSULT-005",
        "patient": {"name": "Sanjay Gupta", "age": 48, "gender": "Male", "patient_id": "SYN-PT-10005"},
        "doctor": {"name": "Dr. Rojina Mallick", "speciality": "Internal Medicine", "hospital": "City General Hospital, Kolkata, West Bengal"},
        "consultation_text": "Sanjay Gupta, 48-year-old male, businessman, comes with acute onset severe headache for 2 days. He describes it as a throbbing pain, predominantly right-sided, associated with nausea and sensitivity to light. Pain is 8/10 in severity. He has had similar episodes in the past, about 2-3 times a year, usually triggered by stress or skipped meals. This episode started after a particularly stressful week at work and he missed lunch yesterday. He took Combiflam but no relief. He also mentions his blood pressure readings at home have been slightly elevated, around 140-145/90-92 mmHg, and he is currently not on any antihypertensive medication. He has a family history of hypertension and his father had a stroke at age 60. No visual aura, no weakness, no speech difficulties, no neck stiffness, no fever. On examination, he is in moderate distress due to headache. BP 148/94 mmHg, pulse 86/min, afebrile. Neurological examination is completely normal - cranial nerves intact, no focal deficits, no papilledema on fundoscopy, no meningeal signs. I am diagnosing this as a migraine without aura. Also noting Stage 1 hypertension that needs treatment. For the acute migraine, prescribing Tab Sumatriptan 50mg now and can repeat after 2 hours if needed, Tab Domperidone 10mg for nausea. For prevention given his frequency, starting Tab Propranolol 40mg twice daily which will also help with his blood pressure. Advising lifestyle modifications - regular meals, stress management, adequate sleep, regular exercise. Ordering basic blood work including fasting lipid profile and blood sugar given his age, family history, and newly detected hypertension. Follow up in 2 weeks.",
        "referral_reason": "",
        "specialist_type": ""
    },
    {
        "id": "CONSULT-006",
        "patient": {"name": "Lakshmi Devi Agarwal", "age": 70, "gender": "Female", "patient_id": "SYN-PT-10006"},
        "doctor": {"name": "Dr. Sahil Makandar", "speciality": "General Medicine", "hospital": "Apollo Clinic, Mapusa, Goa"},
        "consultation_text": "Lakshmi Devi Agarwal, 70-year-old female, retired school teacher, brought by her son with complaints of progressive memory loss over the past 1 year. The son reports she has been forgetting recent conversations, misplacing things frequently, repeating questions, and getting confused about the day of the week. She got lost in her own neighborhood last month. She has also become increasingly withdrawn and less interested in her usual activities like reading and watching television. Sleep is disturbed with frequent nighttime awakenings. She has a history of well-controlled hypertension on Amlodipine 5mg, hypothyroidism on Thyronorm 50mcg, and osteoarthritis of both knees. Her husband passed away 2 years ago. No history of falls, no urinary incontinence, no visual or auditory hallucinations, no personality changes. On examination, she is oriented to person but not fully to time and place. BP 134/78 mmHg, pulse 72/min. Mini Mental State Examination score is 20/30, with deficits mainly in recall, attention, and orientation. Cranial nerves are intact, no focal neurological deficits, gait is normal. I am considering early Alzheimer's dementia versus vascular cognitive impairment. Ordering MRI brain with volumetric analysis, complete blood count, metabolic panel, vitamin B12 levels, folate levels, thyroid function tests to rule out reversible causes. Starting Tab Donepezil 5mg once at bedtime. Referring to Neurology for comprehensive cognitive assessment and further evaluation. Follow up in 4 weeks with reports.",
        "referral_reason": "Progressive cognitive decline - needs comprehensive neurocognitive assessment and MRI-guided evaluation for dementia",
        "specialist_type": "Neurology"
    },
]


def test_patient(patient_data, index, total):
    """Invoke the agent Lambda with a single patient and return detailed results."""
    patient_name = patient_data["patient"]["name"]
    consult_id = patient_data["id"]

    print(f"\n{'='*70}")
    print(f"  TEST {index}/{total}: {patient_name} ({consult_id})")
    print(f"{'='*70}")
    print(f"  Age: {patient_data['patient']['age']}, Gender: {patient_data['patient']['gender']}")
    print(f"  Doctor: {patient_data['doctor']['name']}, {patient_data['doctor'].get('speciality', 'N/A')}")
    print(f"  Referral: {patient_data.get('referral_reason') or 'None'}")
    print(f"  Consultation text length: {len(patient_data['consultation_text'])} chars")

    # Build the Lambda payload (same format as API Gateway / Function URL)
    payload = {
        "httpMethod": "POST",
        "body": json.dumps(patient_data)
    }

    start_time = time.time()

    try:
        print(f"\n  Invoking Lambda: {INVOKER_LAMBDA}...")
        response = lambda_client.invoke(
            FunctionName=INVOKER_LAMBDA,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
            LogType="Tail"  # Get CloudWatch logs
        )

        elapsed = time.time() - start_time
        status_code = response.get("StatusCode", 0)
        func_error = response.get("FunctionError", "")

        # Decode CloudWatch log tail
        import base64
        log_tail = ""
        if "LogResult" in response:
            log_tail = base64.b64decode(response["LogResult"]).decode("utf-8", errors="replace")

        payload_bytes = response["Payload"].read().decode("utf-8")

        print(f"  Lambda HTTP status: {status_code}")
        print(f"  Elapsed: {elapsed:.1f}s")

        if func_error:
            print(f"\n  FUNCTION ERROR: {func_error}")
            print(f"  Payload: {payload_bytes[:2000]}")
            print(f"\n  CloudWatch Log Tail:")
            print(f"  {log_tail}")
            return {
                "patient": patient_name,
                "status": "LAMBDA_ERROR",
                "error": func_error,
                "elapsed": elapsed,
                "details": payload_bytes[:500]
            }

        result = json.loads(payload_bytes)
        body_status = result.get("statusCode", 0)

        if body_status != 200:
            body_raw = result.get("body", "{}")
            if isinstance(body_raw, str):
                try:
                    body = json.loads(body_raw)
                except json.JSONDecodeError:
                    body = {"raw": body_raw}
            else:
                body = body_raw
            error_msg = body.get("error", str(body)[:500])
            print(f"\n  API ERROR (status {body_status}): {error_msg}")
            print(f"\n  CloudWatch Log Tail:")
            print(f"  {log_tail}")
            return {
                "patient": patient_name,
                "status": f"API_ERROR_{body_status}",
                "error": error_msg,
                "elapsed": elapsed
            }

        # Parse successful response
        body = json.loads(result.get("body", "{}")) if isinstance(result.get("body"), str) else result

        # Extract and analyze each output section
        soap = body.get("soap_note", {})
        summary = body.get("patient_summary", {})
        referral = body.get("referral_letter", {})
        discharge = body.get("discharge_summary", {})
        trials = body.get("trial_matches", {})
        agent_summary = body.get("agent_summary", "")
        steps = body.get("processing_steps", [])
        metadata = body.get("metadata", {})

        # Detailed output analysis
        soap_empty = not soap or soap == {}
        summary_empty = not summary or summary == {}
        referral_empty = not referral or referral == {}
        discharge_empty = not discharge or discharge == {}
        trials_empty = not trials or trials == {}
        agent_summary_empty = not agent_summary or agent_summary.strip() == ""

        has_referral = bool(patient_data.get("referral_reason"))

        print(f"\n  --- Response Analysis ---")
        print(f"  Agent Summary: {'EMPTY' if agent_summary_empty else f'{len(agent_summary)} chars'}")
        print(f"  Processing Steps: {len(steps)}")
        print(f"  SOAP Note: {'EMPTY' if soap_empty else 'OK'}")
        print(f"  Patient Summary: {'EMPTY' if summary_empty else 'OK'}")
        print(f"  Referral Letter: {'EMPTY' if referral_empty else 'OK'} (expected: {'Yes' if has_referral else 'No referral'})")
        print(f"  Discharge Summary: {'EMPTY' if discharge_empty else 'OK'}")
        print(f"  Trial Matches: {'EMPTY' if trials_empty else 'OK'}")
        print(f"  Architecture: {metadata.get('architecture', 'N/A')}")
        print(f"  Tools Called: {metadata.get('tools_called', 0)}")
        print(f"  Agents Invoked: {metadata.get('agents_invoked', 0)}")
        print(f"  Processing Time: {metadata.get('total_processing_time_ms', 0)}ms")

        # Print processing steps for debugging
        if steps:
            print(f"\n  --- Processing Steps ---")
            for i, step in enumerate(steps, 1):
                print(f"    {i}. {step.get('step', '?')} (status: {step.get('status', '?')})")

        # Print agent summary (first 500 chars)
        if agent_summary:
            print(f"\n  --- Agent Summary (first 500 chars) ---")
            print(f"  {agent_summary[:500]}")

        # Check for SOAP note content
        if not soap_empty:
            print(f"\n  --- SOAP Note Keys ---")
            print(f"  Keys: {list(soap.keys())}")
            if "subjective" in soap:
                subj = soap["subjective"]
                subj_preview = json.dumps(subj)[:200] if isinstance(subj, dict) else str(subj)[:200]
                print(f"  Subjective (preview): {subj_preview}")

        # Check for patient summary content
        if not summary_empty:
            print(f"\n  --- Patient Summary Keys ---")
            print(f"  Keys: {list(summary.keys())}")

        # Print CloudWatch logs if any output is empty
        all_outputs_present = not soap_empty and not summary_empty and not discharge_empty
        if not all_outputs_present:
            print(f"\n  --- CloudWatch Log Tail (outputs missing) ---")
            print(f"  {log_tail}")

        # Determine overall status
        if soap_empty and summary_empty and discharge_empty:
            status = "FAIL_ALL_EMPTY"
        elif soap_empty or summary_empty:
            status = "PARTIAL"
        else:
            status = "PASS"

        return {
            "patient": patient_name,
            "status": status,
            "elapsed": elapsed,
            "soap_present": not soap_empty,
            "summary_present": not summary_empty,
            "referral_present": not referral_empty,
            "discharge_present": not discharge_empty,
            "trials_present": not trials_empty,
            "agent_summary_length": len(agent_summary),
            "steps_count": len(steps),
            "tools_called": metadata.get("tools_called", 0),
            "agents_invoked": metadata.get("agents_invoked", 0),
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n  EXCEPTION: {e}")
        traceback.print_exc()
        return {
            "patient": patient_name,
            "status": "EXCEPTION",
            "error": str(e),
            "elapsed": elapsed
        }


def main():
    print("=" * 70)
    print("  ClinicalSetu - Agent Integration Test (All Quick-Fill Patients)")
    print("=" * 70)
    print(f"  Region: {REGION}")
    print(f"  Lambda: {INVOKER_LAMBDA}")
    print(f"  Patients: {len(QUICK_FILL_PATIENTS)}")

    # Verify Lambda exists and check its config
    print(f"\n--- Pre-flight: Checking Lambda configuration ---")
    try:
        func = lambda_client.get_function(FunctionName=INVOKER_LAMBDA)
        env_vars = func["Configuration"].get("Environment", {}).get("Variables", {})
        agent_id = env_vars.get("BEDROCK_AGENT_ID", "")
        alias_id = env_vars.get("BEDROCK_AGENT_ALIAS_ID", "")
        timeout = func["Configuration"]["Timeout"]
        memory = func["Configuration"]["MemorySize"]
        print(f"  BEDROCK_AGENT_ID: {agent_id or 'EMPTY!'}")
        print(f"  BEDROCK_AGENT_ALIAS_ID: {alias_id or 'EMPTY!'}")
        print(f"  Timeout: {timeout}s, Memory: {memory}MB")

        if not agent_id or not alias_id:
            print("\n  FATAL: Agent ID or Alias ID not configured on Lambda!")
            print("  The agent invoker will return 500 for all requests.")
            sys.exit(1)
    except Exception as e:
        print(f"  FATAL: Cannot access Lambda {INVOKER_LAMBDA}: {e}")
        sys.exit(1)

    # Run tests sequentially (to avoid throttling)
    results = []
    total = len(QUICK_FILL_PATIENTS)

    for i, patient_data in enumerate(QUICK_FILL_PATIENTS, 1):
        result = test_patient(patient_data, i, total)
        results.append(result)

        # Small delay between tests to avoid Bedrock throttling
        if i < total:
            print(f"\n  Waiting 5s before next test (avoid throttling)...")
            time.sleep(5)

    # Final summary
    print(f"\n\n{'='*70}")
    print(f"  TEST SUMMARY")
    print(f"{'='*70}")

    passed = 0
    failed = 0
    partial = 0

    for r in results:
        status = r["status"]
        patient = r["patient"]
        elapsed = r.get("elapsed", 0)

        if status == "PASS":
            icon = "PASS"
            passed += 1
        elif status == "PARTIAL":
            icon = "PARTIAL"
            partial += 1
        else:
            icon = "FAIL"
            failed += 1

        detail = ""
        if "error" in r:
            detail = f" - Error: {r['error'][:100]}"
        elif status == "PASS" or status == "PARTIAL":
            outputs = []
            if r.get("soap_present"): outputs.append("SOAP")
            if r.get("summary_present"): outputs.append("Summary")
            if r.get("referral_present"): outputs.append("Referral")
            if r.get("discharge_present"): outputs.append("Discharge")
            if r.get("trials_present"): outputs.append("Trials")
            detail = f" - Outputs: [{', '.join(outputs)}] Steps: {r.get('steps_count', 0)} Agents: {r.get('agents_invoked', 0)}"

        print(f"  [{icon}] {patient} ({elapsed:.1f}s){detail}")

    print(f"\n  Total: {total} | Passed: {passed} | Partial: {partial} | Failed: {failed}")

    if failed > 0:
        print(f"\n  RESULT: FAILURES DETECTED - {failed}/{total} patients had empty/error responses")
        print(f"  Review the detailed output above to diagnose why specific patients fail.")
        print(f"  Common causes:")
        print(f"    1. Bedrock throttling (too many concurrent agent calls)")
        print(f"    2. Agent timeout (consultation text too long for model context)")
        print(f"    3. Tool executor Lambda errors (check CloudWatch logs)")
        print(f"    4. Prompt format issues (special characters in consultation text)")
        sys.exit(1)
    elif partial > 0:
        print(f"\n  RESULT: PARTIAL - {partial}/{total} patients had some missing outputs")
        # Don't fail on partial — agent sometimes skips optional outputs
        sys.exit(0)
    else:
        print(f"\n  RESULT: ALL PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
