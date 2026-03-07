"""
Package the ClinicalSetu Lambda functions into deployment ZIPs.
Run: python scripts/package_lambda.py

Creates:
  - lambda_deployment.zip       (monolithic handler - fallback)
  - agent_lambda_deployment.zip (agent tool executor + invoker)
"""

import zipfile
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SHARED_PROMPTS = [
    ("backend/prompts/soap_note.txt", "prompts/soap_note.txt"),
    ("backend/prompts/patient_summary.txt", "prompts/patient_summary.txt"),
    ("backend/prompts/referral_letter.txt", "prompts/referral_letter.txt"),
    ("backend/prompts/trial_matching.txt", "prompts/trial_matching.txt"),
    ("backend/prompts/discharge_summary.txt", "prompts/discharge_summary.txt"),
]

SHARED_DATA = []


def create_zip(output_name, files):
    output_path = os.path.join(PROJECT_ROOT, output_name)
    print(f"\nPackaging {output_name}...")
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for src_rel, dest in files:
            src_abs = os.path.join(PROJECT_ROOT, src_rel)
            if not os.path.exists(src_abs):
                print(f"  WARNING: {src_rel} not found, skipping!")
                continue
            zf.write(src_abs, dest)
            size = os.path.getsize(src_abs)
            print(f"  + {dest} ({size:,} bytes)")
    zip_size = os.path.getsize(output_path)
    print(f"  Done! {output_name}: {zip_size:,} bytes ({zip_size/1024:.1f} KB)")


# 1. Monolithic Lambda (fallback path)
create_zip("lambda_deployment.zip", [
    ("backend/lambda/process_consultation.py", "lambda_function.py"),
    *SHARED_PROMPTS,
    *SHARED_DATA,
])

# 2. Agent Lambda (tool executor + invoker + monolithic fallback + trial fetcher)
create_zip("agent_lambda_deployment.zip", [
    ("backend/lambda/agent_tool_executor.py", "agent_tool_executor.py"),
    ("backend/lambda/invoke_agent.py", "invoke_agent.py"),
    ("backend/lambda/process_consultation.py", "process_consultation.py"),
    ("backend/lambda/fetch_trials.py", "fetch_trials.py"),
    ("backend/lambda/visit_api.py", "visit_api.py"),
    *SHARED_PROMPTS,
    *SHARED_DATA,
])
