"""
ClinicalSetu - Multi-Agent Collaboration Setup Script
Provisions a Supervisor Agent + 4 Specialist Collaborator Agents using
Amazon Bedrock Multi-Agent Collaboration (Supervisor-Router pattern).

Architecture:
  Supervisor Agent (routes tasks, enforces SOAP-first ordering)
    ├── SOAPAgent (generates structured SOAP notes)
    ├── SummaryAgent (creates patient-friendly summaries)
    ├── ReferralAgent (generates referral letters + discharge summaries)
    └── TrialAgent (matches patients against clinical trials)

All agents share a single Tool Executor Lambda via Action Groups.

Prerequisites:
  - AWS CLI configured with credentials
  - Region: us-east-1
  - Tool Executor Lambda deployed: ClinicalSetu-ToolExecutor

Usage:
  python scripts/setup_multi_agent.py

Environment variables (optional):
  TOOL_LAMBDA_NAME  - Name of tool executor Lambda (default: ClinicalSetu-ToolExecutor)
  AGENT_MODEL_ID    - Foundation model for agents (default: us.amazon.nova-lite-v1:0)
"""

import boto3
import json
import time
import os

# ==========================================
# Configuration
# ==========================================
REGION = os.environ.get("AWS_REGION", "us-east-1")
TOOL_LAMBDA_NAME = os.environ.get("TOOL_LAMBDA_NAME", "ClinicalSetu-ToolExecutor")
AGENT_MODEL_ID = os.environ.get("AGENT_MODEL_ID", "us.amazon.nova-lite-v1:0")

# AWS Clients
sts = boto3.client("sts", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)
bedrock_agent = boto3.client("bedrock-agent", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

ACCOUNT_ID = sts.get_caller_identity()["Account"]

print(f"Account:  {ACCOUNT_ID}")
print(f"Region:   {REGION}")
print(f"Model:    {AGENT_MODEL_ID}")
print(f"Lambda:   {TOOL_LAMBDA_NAME}")
print("=" * 60)


# ==========================================
# Helper Functions
# ==========================================
def get_or_create_agent_role():
    """Create or reuse the IAM role for Bedrock Agents."""
    role_name = "ClinicalSetu-MultiAgentRole"

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
            Description="ClinicalSetu Multi-Agent execution role"
        )
        role_arn = response["Role"]["Arn"]
        print(f"  Created role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
        print(f"  Role exists: {role_name}")

    # Permissions for invoking foundation models
    permission_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                "Resource": [
                    f"arn:aws:bedrock:{REGION}::foundation-model/{AGENT_MODEL_ID}",
                    f"arn:aws:bedrock:{REGION}::foundation-model/us.amazon.nova-lite-v1:0",
                    f"arn:aws:bedrock:{REGION}::foundation-model/us.amazon.nova-micro-v1:0",
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
        PolicyName="ClinicalSetuMultiAgentPolicy",
        PolicyDocument=json.dumps(permission_policy)
    )

    time.sleep(10)  # Wait for IAM propagation
    return role_arn


def get_tool_lambda_arn():
    """Get the ARN of the tool executor Lambda."""
    try:
        info = lambda_client.get_function(FunctionName=TOOL_LAMBDA_NAME)
        return info["Configuration"]["FunctionArn"]
    except Exception:
        print(f"  ERROR: Lambda '{TOOL_LAMBDA_NAME}' not found. Deploy it first!")
        return None


def find_existing_agent(agent_name):
    """Check if an agent already exists by name."""
    paginator = bedrock_agent.get_paginator("list_agents")
    for page in paginator.paginate():
        for a in page.get("agentSummaries", []):
            if a["agentName"] == agent_name:
                return a["agentId"]
    return None


def delete_agent_if_exists(agent_name):
    """Delete an existing agent to allow clean recreation."""
    agent_id = find_existing_agent(agent_name)
    if agent_id:
        try:
            # Delete aliases first
            aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)
            for alias in aliases.get("agentAliasSummaries", []):
                bedrock_agent.delete_agent_alias(
                    agentId=agent_id,
                    agentAliasId=alias["agentAliasId"]
                )
            bedrock_agent.delete_agent(agentId=agent_id)
            print(f"  Deleted existing agent: {agent_name} ({agent_id})")
            time.sleep(5)
        except Exception as e:
            print(f"  Warning: Could not delete {agent_name}: {e}")
    return None


def create_agent_with_tools(agent_name, instruction, description, tool_lambda_arn, functions, role_arn):
    """Create a Bedrock Agent with an action group containing specified tools."""
    # Check if agent already exists
    existing_id = find_existing_agent(agent_name)
    if existing_id:
        print(f"  Agent {agent_name} already exists: {existing_id}")
        return existing_id

    response = bedrock_agent.create_agent(
        agentName=agent_name,
        foundationModel=AGENT_MODEL_ID,
        agentResourceRoleArn=role_arn,
        instruction=instruction,
        description=description,
        idleSessionTTLInSeconds=600,
    )
    agent_id = response["agent"]["agentId"]
    print(f"  Created agent: {agent_name} ({agent_id})")

    # Wait for agent to leave Creating state before adding action group
    for attempt in range(30):
        agent_status = bedrock_agent.get_agent(agentId=agent_id)["agent"]["agentStatus"]
        if agent_status != "CREATING":
            print(f"  Agent status: {agent_status}")
            break
        time.sleep(3)

    # Create action group with the agent's tools
    bedrock_agent.create_agent_action_group(
        agentId=agent_id,
        agentVersion="DRAFT",
        actionGroupName=f"{agent_name}-Tools",
        description=f"Tools for {agent_name}",
        actionGroupExecutor={"lambda": tool_lambda_arn},
        functionSchema={"functions": functions},
        actionGroupState="ENABLED"
    )
    print(f"  Added action group with {len(functions)} tool(s)")

    # Grant Bedrock permission to invoke Lambda
    try:
        lambda_client.add_permission(
            FunctionName=TOOL_LAMBDA_NAME,
            StatementId=f"AllowBedrock-{agent_name}",
            Action="lambda:InvokeFunction",
            Principal="bedrock.amazonaws.com",
            SourceAccount=ACCOUNT_ID,
            SourceArn=f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/{agent_id}"
        )
    except Exception as e:
        if "Conflict" in str(e) or "ResourceConflictException" in str(type(e)):
            pass  # Permission already exists
        else:
            print(f"  Warning: Lambda permission: {e}")

    return agent_id


def prepare_agent_and_wait(agent_id, agent_name):
    """Prepare an agent and wait until it's ready."""
    bedrock_agent.prepare_agent(agentId=agent_id)
    for attempt in range(30):
        status = bedrock_agent.get_agent(agentId=agent_id)["agent"]["agentStatus"]
        if status == "PREPARED":
            print(f"  {agent_name} prepared")
            return True
        elif status == "FAILED":
            print(f"  ERROR: {agent_name} preparation failed!")
            return False
        time.sleep(5)
    print(f"  ERROR: {agent_name} preparation timed out")
    return False


def create_agent_alias(agent_id, agent_name):
    """Create a production alias for an agent."""
    try:
        response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName="prod",
            description=f"{agent_name} production alias"
        )
        alias_id = response["agentAlias"]["agentAliasId"]
        alias_arn = response["agentAlias"]["agentAliasArn"]
        print(f"  Alias created for {agent_name}: {alias_id}")

        # Wait for alias to be active
        for _ in range(20):
            alias_status = bedrock_agent.get_agent_alias(
                agentId=agent_id, agentAliasId=alias_id
            )["agentAlias"]["agentAliasStatus"]
            if alias_status == "PREPARED":
                break
            time.sleep(3)

        return alias_id, alias_arn
    except Exception as e:
        if "Conflict" in str(e) or "ConflictException" in str(type(e)):
            aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)
            for a in aliases.get("agentAliasSummaries", []):
                if a["agentAliasName"] == "prod":
                    alias_id = a["agentAliasId"]
                    # Update alias to point to latest version
                    update_resp = bedrock_agent.update_agent_alias(
                        agentId=agent_id,
                        agentAliasId=alias_id,
                        agentAliasName="prod"
                    )
                    alias_arn = update_resp.get("agentAlias", {}).get("agentAliasArn", "")
                    if not alias_arn:
                        # Construct ARN manually
                        alias_arn = f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent-alias/{agent_id}/{alias_id}"
                    print(f"  Alias updated for {agent_name}: {alias_id}")
                    # Wait for alias update
                    for _ in range(20):
                        alias_status = bedrock_agent.get_agent_alias(
                            agentId=agent_id, agentAliasId=alias_id
                        )["agentAlias"]["agentAliasStatus"]
                        if alias_status == "PREPARED":
                            break
                        time.sleep(3)
                    return alias_id, alias_arn
        raise


# ==========================================
# Tool Definitions for Each Agent
# ==========================================
SOAP_TOOLS = [
    {
        "name": "generate_soap",
        "description": "Generates a structured SOAP note from a clinical consultation narrative.",
        "parameters": {
            "consultation_text": {"description": "The raw consultation narrative from the doctor", "type": "string", "required": True},
            "patient_name": {"description": "Full name of the patient", "type": "string", "required": True},
            "patient_age": {"description": "Age of the patient in years", "type": "string", "required": True},
            "patient_gender": {"description": "Gender: Male/Female/Other", "type": "string", "required": True}
        },
        "requireConfirmation": "DISABLED"
    }
]

SUMMARY_TOOLS = [
    {
        "name": "generate_patient_summary",
        "description": "Creates a patient-friendly summary from a SOAP note in simple language.",
        "parameters": {
            "soap_note_json": {"description": "The SOAP note as a JSON string", "type": "string", "required": True},
            "patient_name": {"description": "Full name of the patient", "type": "string", "required": True},
            "doctor_name": {"description": "Full name and title of the doctor", "type": "string", "required": True}
        },
        "requireConfirmation": "DISABLED"
    }
]

REFERRAL_DISCHARGE_TOOLS = [
    {
        "name": "generate_referral",
        "description": "Generates a specialist referral letter from a SOAP note.",
        "parameters": {
            "soap_note_json": {"description": "The SOAP note as a JSON string", "type": "string", "required": True},
            "referral_reason": {"description": "Clinical reason for the referral", "type": "string", "required": True},
            "referring_doctor": {"description": "Name and designation of referring doctor", "type": "string", "required": True},
            "specialist_type": {"description": "Type of specialist (e.g., Cardiology)", "type": "string", "required": False}
        },
        "requireConfirmation": "DISABLED"
    },
    {
        "name": "generate_discharge",
        "description": "Generates a structured discharge/visit summary from a SOAP note.",
        "parameters": {
            "soap_note_json": {"description": "The SOAP note as a JSON string", "type": "string", "required": True},
            "patient_name": {"description": "Full name of the patient", "type": "string", "required": True},
            "patient_age": {"description": "Age of the patient in years", "type": "string", "required": True},
            "patient_gender": {"description": "Gender: Male/Female/Other", "type": "string", "required": True},
            "doctor_name": {"description": "Full name and title of the doctor", "type": "string", "required": True}
        },
        "requireConfirmation": "DISABLED"
    }
]

TRIAL_TOOLS = [
    {
        "name": "search_trials",
        "description": "Matches a patient profile against clinical trials database using the SOAP assessment.",
        "parameters": {
            "soap_assessment": {"description": "The Assessment section of the SOAP note as JSON string", "type": "string", "required": True},
            "patient_age": {"description": "Age of the patient in years", "type": "string", "required": True},
            "patient_gender": {"description": "Gender of the patient", "type": "string", "required": True}
        },
        "requireConfirmation": "DISABLED"
    }
]

# ==========================================
# Agent Instructions
# ==========================================
SOAP_INSTRUCTION = """You are the SOAP Note Specialist for ClinicalSetu, a clinical documentation system for Indian healthcare providers.

When given a consultation narrative with patient details, call the generate_soap tool to produce a structured SOAP note.

CRITICAL RULES:
- You are a documentation assistant, NOT a diagnostic tool
- Never suggest diagnoses or treatments not mentioned by the doctor
- Always pass the complete consultation narrative to the tool
- Return the SOAP note output exactly as received from the tool"""

SUMMARY_INSTRUCTION = """You are the Patient Communication Specialist for ClinicalSetu, responsible for creating patient-friendly summaries.

When given a SOAP note JSON with patient and doctor details, call the generate_patient_summary tool.

GUIDELINES:
- The summary should use simple, non-technical language (8th-grade reading level)
- Medical terms should be explained in parentheses
- Focus on actionable information the patient needs
- Return the summary output exactly as received from the tool"""

REFERRAL_DISCHARGE_INSTRUCTION = """You are the Clinical Documentation Specialist for ClinicalSetu, responsible for referral letters and discharge summaries.

You have TWO tools:
1. generate_referral - Creates specialist referral letters (only call if referral_reason is provided)
2. generate_discharge - Creates discharge/visit summaries (always call this)

When given a SOAP note JSON with patient and doctor details:
- ALWAYS call generate_discharge to produce a discharge summary
- If referral information is provided, ALSO call generate_referral
- Return all outputs exactly as received from the tools

CRITICAL: Never suggest diagnoses or treatments not present in the SOAP note."""

TRIAL_INSTRUCTION = """You are the Clinical Trial Matching Specialist for ClinicalSetu.

When given a SOAP assessment with patient demographics, call the search_trials tool to find matching clinical trials.

CRITICAL RULES:
- All trial matches are INFORMATIONAL ONLY, not enrollment recommendations
- A qualified physician must review all eligibility criteria
- Patient consent is always required before any trial participation
- Return the trial matching output exactly as received from the tool"""

SUPERVISOR_INSTRUCTION = """You are the ClinicalSetu Supervisor, coordinating a team of specialist agents to process clinical consultations for Indian healthcare providers.

You have 4 specialist collaborators:
1. SOAPAgent - Generates structured SOAP notes from consultation narratives
2. SummaryAgent - Creates patient-friendly summaries from SOAP notes
3. ReferralAgent - Generates referral letters AND discharge summaries from SOAP notes
4. TrialAgent - Matches patients against clinical trials from SOAP assessments

MANDATORY WORKFLOW (follow this exactly):
1. FIRST: Send the full consultation narrative and patient details to SOAPAgent. Wait for the SOAP note.
2. THEN send the SOAP note to ALL three remaining agents:
   - Send SOAP note + patient name + doctor name to SummaryAgent
   - Send SOAP note + patient details + doctor name + referral info (if any) to ReferralAgent
   - Send SOAP assessment + patient age + gender to TrialAgent
3. Collect ALL outputs and return them.

CRITICAL RULES:
- SOAPAgent MUST complete before calling any other agent
- You are a documentation coordinator, NOT a diagnostic tool
- Never modify the outputs from specialist agents
- Never suggest diagnoses or treatments not in the original consultation
- All outputs include AI disclaimers — do not remove them

After all agents complete, provide a brief summary of what was generated."""


# ==========================================
# Main Setup Flow
# ==========================================
def main():
    print("\nClinicalSetu - Multi-Agent Collaboration Setup")
    print("=" * 60)

    # Step 1: IAM Role
    print("\n[1/6] Setting up IAM role...")
    role_arn = get_or_create_agent_role()

    # Step 2: Get Tool Lambda ARN
    print("\n[2/6] Checking Tool Executor Lambda...")
    tool_lambda_arn = get_tool_lambda_arn()
    if not tool_lambda_arn:
        print("\nABORTED: Deploy the Tool Executor Lambda first.")
        return

    # Step 3: Create 4 Collaborator Agents
    print("\n[3/6] Creating collaborator agents...")
    collaborators = {}

    agents_config = [
        ("ClinicalSetu-SOAPAgent", SOAP_INSTRUCTION,
         "SOAP Note specialist - structures clinical narratives", SOAP_TOOLS),
        ("ClinicalSetu-SummaryAgent", SUMMARY_INSTRUCTION,
         "Patient Summary specialist - plain-language communication", SUMMARY_TOOLS),
        ("ClinicalSetu-ReferralAgent", REFERRAL_DISCHARGE_INSTRUCTION,
         "Referral and Discharge specialist - clinical documentation", REFERRAL_DISCHARGE_TOOLS),
        ("ClinicalSetu-TrialAgent", TRIAL_INSTRUCTION,
         "Clinical Trial Matching specialist - research signals", TRIAL_TOOLS),
    ]

    for agent_name, instruction, description, tools in agents_config:
        print(f"\n  --- {agent_name} ---")
        agent_id = create_agent_with_tools(
            agent_name, instruction, description, tool_lambda_arn, tools, role_arn
        )
        if prepare_agent_and_wait(agent_id, agent_name):
            alias_id, alias_arn = create_agent_alias(agent_id, agent_name)
            collaborators[agent_name] = {
                "agent_id": agent_id,
                "alias_id": alias_id,
                "alias_arn": alias_arn
            }
        else:
            print(f"  FAILED to prepare {agent_name}. Continuing...")

    if len(collaborators) < 4:
        print(f"\nWARNING: Only {len(collaborators)}/4 collaborators ready.")

    # Step 4: Create Supervisor Agent
    print("\n[4/6] Creating Supervisor Agent...")
    supervisor_name = "ClinicalSetu-Supervisor"
    existing_id = find_existing_agent(supervisor_name)
    if existing_id:
        print(f"  Supervisor already exists: {existing_id}")
        supervisor_id = existing_id
    else:
        response = bedrock_agent.create_agent(
            agentName=supervisor_name,
            foundationModel=AGENT_MODEL_ID,
            agentResourceRoleArn=role_arn,
            instruction=SUPERVISOR_INSTRUCTION,
            description="ClinicalSetu Supervisor - coordinates 4 specialist agents for clinical documentation",
            idleSessionTTLInSeconds=600,
            agentCollaboration="SUPERVISOR_ROUTER",
        )
        supervisor_id = response["agent"]["agentId"]
        print(f"  Created supervisor: {supervisor_id}")

    # Wait for supervisor to leave CREATING state
    for attempt in range(30):
        sup_status = bedrock_agent.get_agent(agentId=supervisor_id)["agent"]["agentStatus"]
        if sup_status != "CREATING":
            print(f"  Supervisor status: {sup_status}")
            break
        if attempt % 5 == 0:
            print(f"  Waiting for supervisor... ({sup_status})")
        time.sleep(3)

    # Step 4.5: Add IAM permissions for supervisor to invoke collaborator agents
    print("\n[4.5/6] Updating IAM role with collaborator invoke permissions...")
    collab_arns = []
    for name, info in collaborators.items():
        collab_arns.append(f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent-alias/{info['agent_id']}/*")
    if collab_arns:
        collab_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeAgent", "bedrock:GetAgentAlias"],
                    "Resource": collab_arns
                },
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:GetAgent"],
                    "Resource": [f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent/*"]
                }
            ]
        }
        iam.put_role_policy(
            RoleName="ClinicalSetu-MultiAgentRole",
            PolicyName="ClinicalSetuCollaboratorInvokePolicy",
            PolicyDocument=json.dumps(collab_policy)
        )
        print(f"  Added invoke permissions for {len(collab_arns)} collaborators")
        print("  Waiting for IAM policy propagation...")
        time.sleep(15)  # IAM propagation can take 10-15s

    # Step 5: Associate Collaborators with Supervisor
    print("\n[5/6] Associating collaborators with supervisor...")
    collaboration_instructions = {
        "ClinicalSetu-SOAPAgent": "Call this agent FIRST with the consultation narrative and patient details. It generates a structured SOAP note. Its output is required by ALL other agents. Do not call any other agent until SOAPAgent returns.",
        "ClinicalSetu-SummaryAgent": "Call AFTER SOAPAgent completes. Send the SOAP note JSON, patient name, and doctor name. It creates a patient-friendly summary in simple language.",
        "ClinicalSetu-ReferralAgent": "Call AFTER SOAPAgent completes. Send the SOAP note JSON, patient details, doctor name, and referral information (if any). It generates a referral letter (if referral needed) AND a discharge summary.",
        "ClinicalSetu-TrialAgent": "Call AFTER SOAPAgent completes. Send the SOAP assessment section, patient age, and gender. It matches the patient against clinical trials. All matches are informational only.",
    }

    associated_count = 0
    for agent_name, collab_info in collaborators.items():
        for retry in range(3):
            try:
                bedrock_agent.associate_agent_collaborator(
                    agentId=supervisor_id,
                    agentVersion="DRAFT",
                    agentDescriptor={"aliasArn": collab_info["alias_arn"]},
                    collaboratorName=agent_name,
                    collaborationInstruction=collaboration_instructions.get(agent_name, ""),
                    relayConversationHistory="TO_COLLABORATOR"
                )
                print(f"  Associated: {agent_name}")
                associated_count += 1
                break
            except Exception as e:
                if "Conflict" in str(e) or "ConflictException" in str(type(e)):
                    print(f"  Already associated: {agent_name}")
                    associated_count += 1
                    break
                elif retry < 2:
                    print(f"  Retry {retry+1}/3 associating {agent_name}: {e}")
                    time.sleep(15)
                else:
                    print(f"  FAILED to associate {agent_name}: {e}")

    if associated_count == 0:
        print("  ERROR: No collaborators associated! Cannot prepare supervisor.")
        return

    # Prepare supervisor and create alias
    print("\n[6/6] Preparing supervisor...")
    if prepare_agent_and_wait(supervisor_id, "Supervisor"):
        supervisor_alias_id, _ = create_agent_alias(supervisor_id, "Supervisor")
    else:
        print("  ERROR: Supervisor preparation failed!")
        return

    # Summary
    print("\n" + "=" * 60)
    print("MULTI-AGENT SETUP COMPLETE")
    print("=" * 60)
    print(f"\nSupervisor Agent:")
    print(f"  BEDROCK_AGENT_ID={supervisor_id}")
    print(f"  BEDROCK_AGENT_ALIAS_ID={supervisor_alias_id}")
    print(f"\nCollaborator Agents:")
    for name, info in collaborators.items():
        print(f"  {name}: {info['agent_id']} (alias: {info['alias_id']})")
    print(f"\nSet these on your ClinicalSetu-Invoker Lambda:")
    print(f"  BEDROCK_AGENT_ID={supervisor_id}")
    print(f"  BEDROCK_AGENT_ALIAS_ID={supervisor_alias_id}")
    print(f"\nArchitecture:")
    print(f"  Frontend -> API GW -> Invoker Lambda -> Supervisor Agent")
    print(f"                                           |-> SOAPAgent -> Tool Executor Lambda")
    print(f"                                           |-> SummaryAgent -> Tool Executor Lambda")
    print(f"                                           |-> ReferralAgent -> Tool Executor Lambda")
    print(f"                                           |-> TrialAgent -> Tool Executor Lambda")


if __name__ == "__main__":
    main()
