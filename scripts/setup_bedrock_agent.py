"""
ClinicalSetu - One-time AWS Setup Script
Provisions the Bedrock Agent, Action Group, Knowledge Base, and IAM roles.

Prerequisites:
  - AWS CLI configured with credentials (aws configure)
  - Region: us-east-1
  - Two Lambda functions already deployed:
    1. ClinicalSetu-ToolExecutor (agent_tool_executor.py)
    2. ClinicalSetu-Invoker (invoke_agent.py)
  - S3 bucket with clinical trials data uploaded

Usage:
  python scripts/setup_bedrock_agent.py

Environment variables (optional):
  TOOL_LAMBDA_NAME  - Name of tool executor Lambda (default: ClinicalSetu-ToolExecutor)
  S3_BUCKET         - S3 bucket name for trial data (default: clinicalsetu-data-{account_id})
"""

import boto3
import json
import time
import os
import sys

# ==========================================
# Configuration
# ==========================================
REGION = "us-east-1"
TOOL_LAMBDA_NAME = os.environ.get("TOOL_LAMBDA_NAME", "ClinicalSetu-ToolExecutor")
S3_BUCKET = os.environ.get("S3_BUCKET", "")  # Set below after getting account_id

# Clients
sts = boto3.client("sts", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)
bedrock_agent = boto3.client("bedrock-agent", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

ACCOUNT_ID = sts.get_caller_identity()["Account"]
if not S3_BUCKET:
    S3_BUCKET = f"clinicalsetu-data-{ACCOUNT_ID}"

print(f"Account: {ACCOUNT_ID}")
print(f"Region:  {REGION}")
print(f"Bucket:  {S3_BUCKET}")
print(f"Lambda:  {TOOL_LAMBDA_NAME}")
print("=" * 60)


# ==========================================
# Step 1: Create S3 Bucket & Upload Trial Data
# ==========================================
def setup_s3():
    print("\n[1/7] Setting up S3 bucket...")
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
        print(f"  Bucket {S3_BUCKET} already exists")
    except Exception:
        s3.create_bucket(Bucket=S3_BUCKET)
        print(f"  Created bucket: {S3_BUCKET}")

    # Upload clinical trials data
    trials_path = os.path.join(os.path.dirname(__file__), "..", "data", "clinical_trials.json")
    if os.path.exists(trials_path):
        s3.upload_file(trials_path, S3_BUCKET, "data/clinical_trials.json")
        print(f"  Uploaded clinical_trials.json to s3://{S3_BUCKET}/data/")
    else:
        print(f"  WARNING: {trials_path} not found!")


# ==========================================
# Step 2: Create IAM Roles
# ==========================================
def create_agent_role():
    print("\n[2/7] Creating IAM roles...")
    role_name = "ClinicalSetu-AgentRole"

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {"aws:SourceAccount": ACCOUNT_ID},
                "ArnLike": {"AWS:SourceArn": f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/*"}
            }
        }]
    }

    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="ClinicalSetu Bedrock Agent execution role"
        )
        role_arn = response["Role"]["Arn"]
        print(f"  Created role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
        print(f"  Role already exists: {role_name}")

    # Attach permissions
    permission_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": [
                    f"arn:aws:bedrock:{REGION}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                    f"arn:aws:bedrock:{REGION}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
                    f"arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v2:0"
                ]
            },
            {
                "Effect": "Allow",
                "Action": ["bedrock:Retrieve", "bedrock:RetrieveAndGenerate"],
                "Resource": f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:knowledge-base/*"
            }
        ]
    }

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="ClinicalSetuAgentPolicy",
        PolicyDocument=json.dumps(permission_policy)
    )
    print(f"  Attached permissions policy")

    # KB role
    kb_role_name = "ClinicalSetu-KBRole"
    kb_trust = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {"aws:SourceAccount": ACCOUNT_ID}
            }
        }]
    }

    try:
        kb_resp = iam.create_role(
            RoleName=kb_role_name,
            AssumeRolePolicyDocument=json.dumps(kb_trust),
            Description="ClinicalSetu Knowledge Base role"
        )
        kb_role_arn = kb_resp["Role"]["Arn"]
        print(f"  Created KB role: {kb_role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        kb_role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{kb_role_name}"
        print(f"  KB Role already exists: {kb_role_name}")

    kb_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": f"arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v2:0"
            },
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": [
                    f"arn:aws:s3:::{S3_BUCKET}",
                    f"arn:aws:s3:::{S3_BUCKET}/*"
                ]
            }
        ]
    }

    iam.put_role_policy(
        RoleName=kb_role_name,
        PolicyName="ClinicalSetuKBPolicy",
        PolicyDocument=json.dumps(kb_policy)
    )

    time.sleep(10)  # Wait for IAM propagation
    return role_arn, kb_role_arn


# ==========================================
# Step 3: Create Bedrock Agent
# ==========================================
def create_agent(agent_role_arn):
    print("\n[3/7] Creating Bedrock Agent...")

    instruction = """You are ClinicalSetu, an AI clinical intelligence assistant for healthcare providers in India.
Your purpose is to process clinical consultation narratives and produce structured documentation.

When a doctor provides a clinical consultation narrative, you MUST follow these steps in order:

1. FIRST: Call generate_soap with the consultation text and patient details to create a structured SOAP note.
2. SECOND: Call generate_patient_summary with the SOAP note JSON output, patient name, and doctor name.
3. THIRD: If a referral reason is mentioned, call generate_referral with the SOAP note JSON, referral reason, doctor info, and specialist type. If no referral is needed, skip this step.
4. FOURTH: Call search_trials with the SOAP assessment JSON, patient age, and gender to find matching clinical trials.

CRITICAL RULES:
- You are a documentation assistant, NOT a diagnostic tool
- Never suggest diagnoses not mentioned by the doctor
- Never recommend treatments or medications
- All outputs must include the disclaimer: "AI-Generated - Requires Clinician Validation"
- Always call generate_soap FIRST, as other tools depend on its output
- Pass the SOAP note output as soap_note_json parameter to subsequent tools

After all tools complete, provide a brief summary of what was generated."""

    try:
        response = bedrock_agent.create_agent(
            agentName="ClinicalSetu-Agent",
            foundationModel="anthropic.claude-3-sonnet-20240229-v1:0",
            agentResourceRoleArn=agent_role_arn,
            instruction=instruction,
            description="Clinical intelligence agent - SOAP notes, patient summaries, referrals, trial matching",
            idleSessionTTLInSeconds=1800,
        )
        agent_id = response["agent"]["agentId"]
        print(f"  Agent created: {agent_id}")
        return agent_id
    except Exception as e:
        if "already exists" in str(e).lower() or "ConflictException" in str(type(e)):
            # List agents and find ours
            agents = bedrock_agent.list_agents()
            for a in agents.get("agentSummaries", []):
                if a["agentName"] == "ClinicalSetu-Agent":
                    agent_id = a["agentId"]
                    print(f"  Agent already exists: {agent_id}")
                    return agent_id
        raise


# ==========================================
# Step 4: Add Action Group (4 Tools)
# ==========================================
def create_action_group(agent_id):
    print("\n[4/7] Creating Action Group with 4 clinical tools...")

    # Get Lambda ARN
    try:
        lambda_info = lambda_client.get_function(FunctionName=TOOL_LAMBDA_NAME)
        tool_lambda_arn = lambda_info["Configuration"]["FunctionArn"]
    except Exception:
        print(f"  ERROR: Lambda '{TOOL_LAMBDA_NAME}' not found. Deploy it first!")
        print(f"  Skipping action group creation.")
        return None

    functions = [
        {
            "name": "generate_soap",
            "description": "Generates a structured SOAP note from a clinical consultation narrative. Call this FIRST.",
            "parameters": {
                "consultation_text": {"description": "The raw consultation narrative from the doctor", "type": "string", "required": True},
                "patient_name": {"description": "Full name of the patient", "type": "string", "required": True},
                "patient_age": {"description": "Age of the patient in years", "type": "integer", "required": True},
                "patient_gender": {"description": "Gender: Male/Female/Other", "type": "string", "required": True}
            },
            "requireConfirmation": "DISABLED"
        },
        {
            "name": "generate_patient_summary",
            "description": "Creates a patient-friendly summary from a SOAP note. Call AFTER generate_soap.",
            "parameters": {
                "soap_note_json": {"description": "The SOAP note as a JSON string (output from generate_soap)", "type": "string", "required": True},
                "patient_name": {"description": "Full name of the patient", "type": "string", "required": True},
                "doctor_name": {"description": "Full name and title of the doctor", "type": "string", "required": True}
            },
            "requireConfirmation": "DISABLED"
        },
        {
            "name": "generate_referral",
            "description": "Generates a specialist referral letter. Only call if doctor indicated a referral is needed.",
            "parameters": {
                "soap_note_json": {"description": "The SOAP note as a JSON string", "type": "string", "required": True},
                "referral_reason": {"description": "Clinical reason for the referral", "type": "string", "required": True},
                "referring_doctor": {"description": "Name and designation of referring doctor", "type": "string", "required": True},
                "specialist_type": {"description": "Type of specialist (e.g., Cardiology, Neurology)", "type": "string", "required": False}
            },
            "requireConfirmation": "DISABLED"
        },
        {
            "name": "search_trials",
            "description": "Searches clinical trials knowledge base for trials matching the patient profile. Uses RAG.",
            "parameters": {
                "soap_assessment": {"description": "The Assessment section of the SOAP note as JSON string", "type": "string", "required": True},
                "patient_age": {"description": "Age of the patient in years", "type": "integer", "required": True},
                "patient_gender": {"description": "Gender of the patient", "type": "string", "required": True}
            },
            "requireConfirmation": "DISABLED"
        }
    ]

    try:
        response = bedrock_agent.create_agent_action_group(
            agentId=agent_id,
            agentVersion="DRAFT",
            actionGroupName="ClinicalTools",
            description="4 clinical documentation tools for ClinicalSetu",
            actionGroupExecutor={"lambda": tool_lambda_arn},
            functionSchema={"functions": functions},
            actionGroupState="ENABLED"
        )
        ag_id = response["agentActionGroup"]["actionGroupId"]
        print(f"  Action group created: {ag_id}")

        # Grant Bedrock permission to invoke Lambda
        try:
            lambda_client.add_permission(
                FunctionName=TOOL_LAMBDA_NAME,
                StatementId="AllowBedrockAgentInvoke",
                Action="lambda:InvokeFunction",
                Principal="bedrock.amazonaws.com",
                SourceAccount=ACCOUNT_ID,
                SourceArn=f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/{agent_id}"
            )
            print(f"  Lambda invoke permission granted to Bedrock Agent")
        except Exception as e:
            if "ResourceConflictException" in str(type(e)):
                print(f"  Lambda permission already exists")
            else:
                print(f"  WARNING: Could not add Lambda permission: {e}")

        return ag_id
    except Exception as e:
        if "ConflictException" in str(type(e)):
            print(f"  Action group already exists, continuing...")
            return "existing"
        raise


# ==========================================
# Step 5: Prepare and Create Alias
# ==========================================
def prepare_and_alias(agent_id):
    print("\n[5/7] Preparing agent...")
    bedrock_agent.prepare_agent(agentId=agent_id)

    # Wait for preparation
    for attempt in range(30):
        status = bedrock_agent.get_agent(agentId=agent_id)["agent"]["agentStatus"]
        print(f"  Status: {status} (attempt {attempt + 1})")
        if status == "PREPARED":
            break
        elif status == "FAILED":
            print("  ERROR: Agent preparation failed!")
            return None
        time.sleep(10)

    print("\n[6/7] Creating agent alias...")
    try:
        alias_response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName="prod-v1",
            description="ClinicalSetu production alias"
        )
        alias_id = alias_response["agentAlias"]["agentAliasId"]
        print(f"  Alias created: {alias_id}")
        return alias_id
    except Exception as e:
        if "ConflictException" in str(type(e)):
            # List aliases
            aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)
            for a in aliases.get("agentAliasSummaries", []):
                if a["agentAliasName"] == "prod-v1":
                    alias_id = a["agentAliasId"]
                    print(f"  Alias already exists: {alias_id}")
                    return alias_id
        raise


# ==========================================
# Step 7: Output Summary
# ==========================================
def print_summary(agent_id, alias_id):
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print(f"\nBEDROCK_AGENT_ID={agent_id}")
    print(f"BEDROCK_AGENT_ALIAS_ID={alias_id}")
    print(f"S3_BUCKET={S3_BUCKET}")
    print(f"\nSet these as environment variables on your ClinicalSetu-Invoker Lambda:")
    print(f"  BEDROCK_AGENT_ID={agent_id}")
    print(f"  BEDROCK_AGENT_ALIAS_ID={alias_id}")
    print(f"\nArchitecture:")
    print(f"  Frontend → API GW → ClinicalSetu-Invoker → Bedrock Agent → ClinicalSetu-ToolExecutor")
    print(f"                                                          └→ Knowledge Base (RAG)")


# ==========================================
# Main
# ==========================================
if __name__ == "__main__":
    print("\nClinicalSetu - AWS Bedrock Agent Setup")
    print("=" * 60)

    setup_s3()
    agent_role_arn, kb_role_arn = create_agent_role()
    agent_id = create_agent(agent_role_arn)

    # Prepare once before adding action group
    bedrock_agent.prepare_agent(agentId=agent_id)
    time.sleep(15)

    create_action_group(agent_id)
    alias_id = prepare_and_alias(agent_id)

    if alias_id:
        print_summary(agent_id, alias_id)
    else:
        print("\nSetup incomplete. Check errors above.")
