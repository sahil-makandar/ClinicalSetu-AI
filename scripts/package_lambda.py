"""
Package the ClinicalSetu Lambda function into a deployment ZIP.
Run: python scripts/package_lambda.py

Creates: lambda_deployment.zip in the project root.
Upload this ZIP to AWS Lambda via the console.
"""

import zipfile
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_ZIP = os.path.join(PROJECT_ROOT, "lambda_deployment.zip")

files_to_include = [
    # Lambda handler (main entry point)
    ("backend/lambda/process_consultation.py", "lambda_function.py"),
    # Prompt templates (Lambda expects them in prompts/ relative to handler)
    ("backend/prompts/soap_note.txt", "prompts/soap_note.txt"),
    ("backend/prompts/patient_summary.txt", "prompts/patient_summary.txt"),
    ("backend/prompts/referral_letter.txt", "prompts/referral_letter.txt"),
    ("backend/prompts/trial_matching.txt", "prompts/trial_matching.txt"),
    # Clinical trials data (bundled for in-context matching)
    ("data/clinical_trials.json", "clinical_trials.json"),
]

print("Packaging ClinicalSetu Lambda...")
print(f"Output: {OUTPUT_ZIP}")
print()

with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    for src_rel, dest in files_to_include:
        src_abs = os.path.join(PROJECT_ROOT, src_rel)
        if not os.path.exists(src_abs):
            print(f"  WARNING: {src_rel} not found, skipping!")
            continue
        zf.write(src_abs, dest)
        size = os.path.getsize(src_abs)
        print(f"  + {dest} ({size:,} bytes)")

zip_size = os.path.getsize(OUTPUT_ZIP)
print(f"\nDone! ZIP size: {zip_size:,} bytes ({zip_size/1024:.1f} KB)")
print(f"\nNext steps:")
print(f"  1. Go to AWS Lambda console")
print(f"  2. Create function 'ClinicalSetu-API' (Python 3.12)")
print(f"  3. Upload {OUTPUT_ZIP}")
print(f"  4. Set Handler to: lambda_function.lambda_handler")
print(f"  5. Set timeout to 120s, memory to 1024MB")
print(f"  6. Add Bedrock InvokeModel permission to the execution role")
