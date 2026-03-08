"""
ClinicalSetu - Multi-Agent Debug & Diagnostics Script
Checks every permission, configuration, and connectivity issue
for the Bedrock Multi-Agent Collaboration setup.

Exit codes:
  0 = all checks passed
  1 = one or more checks failed
"""

import boto3
import json
import os
import sys
import time
import uuid

REGION = os.environ.get("AWS_REGION", "us-east-1")
PROJECT = os.environ.get("PROJECT_NAME", "clinicalsetu")
STAGE = os.environ.get("STAGE", "prod")

sts = boto3.client("sts", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)
bedrock_agent_client = boto3.client("bedrock-agent", region_name=REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=REGION)
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

ACCOUNT_ID = sts.get_caller_identity()["Account"]
CALLER_ARN = sts.get_caller_identity()["Arn"]

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
failures = []


def log(status, msg):
    prefix = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(status, "ℹ️")
    print(f"  {prefix} [{status}] {msg}")
    if status == FAIL:
        failures.append(msg)


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# =====================================================
# 1. BASIC CONNECTIVITY
# =====================================================
section("1. AWS CONNECTIVITY & IDENTITY")
print(f"  Account:  {ACCOUNT_ID}")
print(f"  Region:   {REGION}")
print(f"  Caller:   {CALLER_ARN}")
log(PASS, "AWS credentials are valid")


# =====================================================
# 2. LIST ALL AGENTS
# =====================================================
section("2. BEDROCK AGENTS INVENTORY")

all_agents = []
paginator = bedrock_agent_client.get_paginator("list_agents")
for page in paginator.paginate():
    all_agents.extend(page.get("agentSummaries", []))

clinical_agents = [a for a in all_agents if a["agentName"].startswith("ClinicalSetu")]
print(f"  Found {len(clinical_agents)} ClinicalSetu agents:")

supervisor = None
collaborators = {}
for a in clinical_agents:
    agent_id = a["agentId"]
    name = a["agentName"]
    status = a["agentStatus"]
    print(f"    {name}: {agent_id} (status: {status})")
    if status != "PREPARED":
        log(FAIL, f"Agent {name} is NOT PREPARED (status: {status})")
    else:
        log(PASS, f"Agent {name} is PREPARED")
    if "Supervisor" in name:
        supervisor = a
    else:
        collaborators[name] = a

if not supervisor:
    log(FAIL, "No Supervisor agent found!")
    print("\n❌ FATAL: Cannot continue without a Supervisor agent.")
    sys.exit(1)

SUPERVISOR_ID = supervisor["agentId"]


# =====================================================
# 3. CHECK AGENT ALIASES
# =====================================================
section("3. AGENT ALIASES")

def get_agent_aliases(agent_id, agent_name):
    """Get all aliases for an agent."""
    try:
        resp = bedrock_agent_client.list_agent_aliases(agentId=agent_id)
        aliases = resp.get("agentAliasSummaries", [])
        if not aliases:
            log(FAIL, f"{agent_name} ({agent_id}) has NO aliases — cannot be invoked!")
            return None
        for alias in aliases:
            a_id = alias["agentAliasId"]
            a_name = alias["agentAliasName"]
            a_status = alias.get("agentAliasStatus", "unknown")
            print(f"    {agent_name}: alias={a_name} id={a_id} status={a_status}")
            if a_status != "PREPARED":
                log(WARN, f"{agent_name} alias '{a_name}' status is {a_status} (expected PREPARED)")
            else:
                log(PASS, f"{agent_name} has alias '{a_name}' (PREPARED)")
        return aliases
    except Exception as e:
        log(FAIL, f"Cannot list aliases for {agent_name}: {e}")
        return None


supervisor_aliases = get_agent_aliases(SUPERVISOR_ID, "Supervisor")
supervisor_alias_id = None
if supervisor_aliases:
    # Prefer 'prod' alias, fallback to first
    for a in supervisor_aliases:
        if a["agentAliasName"] == "prod":
            supervisor_alias_id = a["agentAliasId"]
            break
    if not supervisor_alias_id:
        supervisor_alias_id = supervisor_aliases[0]["agentAliasId"]

collaborator_alias_arns = []
for name, agent in collaborators.items():
    aliases = get_agent_aliases(agent["agentId"], name)
    if aliases:
        for a in aliases:
            arn = f"arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:agent-alias/{agent['agentId']}/{a['agentAliasId']}"
            collaborator_alias_arns.append(arn)


# =====================================================
# 4. SUPERVISOR SERVICE ROLE PERMISSIONS
# =====================================================
section("4. SUPERVISOR SERVICE ROLE PERMISSIONS")

try:
    sup_detail = bedrock_agent_client.get_agent(agentId=SUPERVISOR_ID)["agent"]
    role_arn = sup_detail.get("agentResourceRoleArn", "")
    role_name = role_arn.split("/")[-1] if "/" in role_arn else role_arn
    print(f"  Supervisor role ARN: {role_arn}")
    print(f"  Supervisor role name: {role_name}")

    # List inline policies
    inline_policies = iam.list_role_policies(RoleName=role_name)["PolicyNames"]
    print(f"  Inline policies: {inline_policies}")

    # List attached policies
    attached_policies = iam.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
    print(f"  Attached policies: {[p['PolicyName'] for p in attached_policies]}")

    # Check each inline policy for required permissions
    has_invoke_agent = False
    has_get_agent_alias = False
    has_invoke_model = False
    invoke_agent_resources = []

    for pol_name in inline_policies:
        doc = iam.get_role_policy(RoleName=role_name, PolicyName=pol_name)["PolicyDocument"]
        print(f"\n  Policy: {pol_name}")
        print(f"  {json.dumps(doc, indent=4)}")

        for stmt in doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            resources = stmt.get("Resource", [])
            if isinstance(resources, str):
                resources = [resources]

            if "bedrock:InvokeAgent" in actions:
                has_invoke_agent = True
                invoke_agent_resources.extend(resources)
            if "bedrock:GetAgentAlias" in actions:
                has_get_agent_alias = True
            if "bedrock:InvokeModel" in actions:
                has_invoke_model = True

    # Also check attached managed policies
    for pol in attached_policies:
        if "BedrockFullAccess" in pol["PolicyName"] or "Bedrock" in pol["PolicyName"]:
            has_invoke_model = True
            has_invoke_agent = True
            has_get_agent_alias = True
            log(PASS, f"Attached managed policy: {pol['PolicyName']} (covers model + agent permissions)")

    # Check if a broad managed policy covers all permissions (skip detailed resource check)
    has_broad_managed_policy = any(
        p["PolicyName"] in ("AmazonBedrockFullAccess", "AdministratorAccess")
        for p in attached_policies
    )

    if has_invoke_model:
        log(PASS, "Role has bedrock:InvokeModel")
        if has_broad_managed_policy:
            log(PASS, "Managed policy covers all model + inference-profile resources (skipping detailed resource check)")
        else:
            # Check if inference-profile ARNs are included (needed for us.* model IDs)
            all_model_resources = []
            for pol_name in inline_policies:
                doc = iam.get_role_policy(RoleName=role_name, PolicyName=pol_name)["PolicyDocument"]
                for stmt in doc.get("Statement", []):
                    actions = stmt.get("Action", [])
                    if isinstance(actions, str):
                        actions = [actions]
                    if "bedrock:InvokeModel" in actions:
                        res = stmt.get("Resource", [])
                        if isinstance(res, str):
                            res = [res]
                        all_model_resources.extend(res)
            has_inference_profile = any("inference-profile" in r for r in all_model_resources)
            has_foundation_model = any("foundation-model" in r for r in all_model_resources)
            print(f"  Model resources: {all_model_resources}")
            if has_inference_profile:
                log(PASS, "Role has inference-profile ARNs (needed for us.* model IDs)")
            else:
                log(FAIL, "Role MISSING inference-profile ARNs! Agents use us.amazon.nova-lite-v1:0 which is a cross-region inference profile, NOT a foundation-model. Add: arn:aws:bedrock:REGION:ACCOUNT:inference-profile/us.amazon.nova-lite-v1:0")
            if has_foundation_model:
                log(PASS, "Role has foundation-model ARNs")
    else:
        log(FAIL, "Role MISSING bedrock:InvokeModel — agents cannot call foundation models!")

    if has_invoke_agent:
        log(PASS, f"Role has bedrock:InvokeAgent on resources: {invoke_agent_resources}")
    else:
        log(FAIL, "Role MISSING bedrock:InvokeAgent — Supervisor cannot invoke collaborators!")

    if has_get_agent_alias:
        log(PASS, "Role has bedrock:GetAgentAlias")
    else:
        log(FAIL, "Role MISSING bedrock:GetAgentAlias — needed for multi-agent collaboration!")

    # Check if collaborator alias ARNs are covered by the policy resources
    if invoke_agent_resources:
        print(f"\n  Checking collaborator ARNs against policy resources...")
        for collab_arn in collaborator_alias_arns:
            matched = False
            for res in invoke_agent_resources:
                # Simple wildcard matching
                if res.endswith("/*") or res == "*":
                    prefix = res.replace("/*", "/")
                    if collab_arn.startswith(prefix) or res == "*":
                        matched = True
                        break
                elif collab_arn == res:
                    matched = True
                    break
            if matched:
                log(PASS, f"Collaborator ARN covered: {collab_arn}")
            else:
                log(FAIL, f"Collaborator ARN NOT covered by policy: {collab_arn}")
                log(FAIL, f"  Policy resources: {invoke_agent_resources}")

    # Check trust policy
    trust = iam.get_role(RoleName=role_name)["Role"]["AssumeRolePolicyDocument"]
    print(f"\n  Trust policy:")
    print(f"  {json.dumps(trust, indent=4)}")
    trust_principals = []
    for stmt in trust.get("Statement", []):
        principal = stmt.get("Principal", {})
        if isinstance(principal, dict):
            trust_principals.extend(principal.get("Service", []) if isinstance(principal.get("Service"), list) else [principal.get("Service", "")])
        elif isinstance(principal, str):
            trust_principals.append(principal)

    if "bedrock.amazonaws.com" in trust_principals:
        log(PASS, "Trust policy allows bedrock.amazonaws.com")
    else:
        log(FAIL, f"Trust policy does NOT allow bedrock.amazonaws.com! Principals: {trust_principals}")

except Exception as e:
    log(FAIL, f"Cannot check supervisor role: {e}")


# =====================================================
# 5. SUPERVISOR COLLABORATOR ASSOCIATIONS
# =====================================================
section("5. SUPERVISOR COLLABORATOR ASSOCIATIONS")

try:
    assoc_resp = bedrock_agent_client.list_agent_collaborators(
        agentId=SUPERVISOR_ID,
        agentVersion="DRAFT"
    )
    associations = assoc_resp.get("agentCollaboratorSummaries", [])
    print(f"  Found {len(associations)} collaborator associations:")
    for assoc in associations:
        collab_name = assoc.get("collaboratorName", "unknown")
        # Try to get alias ARN from the descriptor
        print(f"    {collab_name}: {json.dumps(assoc, indent=6, default=str)}")
        log(PASS, f"Collaborator associated: {collab_name}")

    expected = {"ClinicalSetu-SOAPAgent", "ClinicalSetu-SummaryAgent", "ClinicalSetu-ReferralAgent", "ClinicalSetu-TrialAgent"}
    found = {a.get("collaboratorName", "") for a in associations}
    missing = expected - found
    if missing:
        log(FAIL, f"Missing collaborator associations: {missing}")
    else:
        log(PASS, "All 4 collaborators are associated with supervisor")
except Exception as e:
    log(FAIL, f"Cannot list collaborator associations: {e}")


# =====================================================
# 6. TOOL EXECUTOR LAMBDA
# =====================================================
section("6. TOOL EXECUTOR LAMBDA")

tool_lambda_name = f"{PROJECT}-tool-executor-{STAGE}"
try:
    func = lambda_client.get_function(FunctionName=tool_lambda_name)
    func_arn = func["Configuration"]["FunctionArn"]
    print(f"  Lambda: {tool_lambda_name}")
    print(f"  ARN: {func_arn}")
    print(f"  Runtime: {func['Configuration']['Runtime']}")
    print(f"  Timeout: {func['Configuration']['Timeout']}s")
    print(f"  Memory: {func['Configuration']['MemorySize']}MB")
    log(PASS, f"Tool executor Lambda exists: {tool_lambda_name}")

    # Check resource-based policy
    try:
        policy_resp = lambda_client.get_policy(FunctionName=tool_lambda_name)
        policy_doc = json.loads(policy_resp["Policy"])
        print(f"\n  Resource-based policy:")
        bedrock_allowed = False
        for stmt in policy_doc.get("Statement", []):
            principal = stmt.get("Principal", {})
            if isinstance(principal, dict):
                svc = principal.get("Service", "")
            else:
                svc = principal
            action = stmt.get("Action", "")
            print(f"    SID={stmt.get('Sid','?')} Principal={svc} Action={action}")
            if "bedrock" in str(svc).lower():
                bedrock_allowed = True
        if bedrock_allowed:
            log(PASS, "Bedrock has permission to invoke Tool Executor Lambda")
        else:
            log(FAIL, "Bedrock does NOT have resource-based permission to invoke Tool Executor Lambda!")
            log(FAIL, "Fix: Add lambda:InvokeFunction permission for bedrock.amazonaws.com")
    except lambda_client.exceptions.ResourceNotFoundException:
        log(FAIL, "Tool Executor Lambda has NO resource-based policy — Bedrock cannot invoke it!")

    # Check Tool Executor Lambda's execution role for Converse/InvokeModel + inference-profile permissions
    tool_role_arn = func["Configuration"]["Role"]
    tool_role_name = tool_role_arn.split("/")[-1]
    print(f"\n  Execution role: {tool_role_name}")

    tool_inline_pols = iam.list_role_policies(RoleName=tool_role_name)["PolicyNames"]
    tool_has_converse = False
    tool_has_inference_profile = False
    for pol_name in tool_inline_pols:
        doc = iam.get_role_policy(RoleName=tool_role_name, PolicyName=pol_name)["PolicyDocument"]
        for stmt in doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            if any(a in actions for a in ("bedrock:Converse", "bedrock:InvokeModel", "bedrock:*", "*")):
                tool_has_converse = True
                res = stmt.get("Resource", [])
                if isinstance(res, str):
                    res = [res]
                if any("inference-profile" in r or r == "*" for r in res):
                    tool_has_inference_profile = True
    # Also check managed policies
    tool_attached = iam.list_attached_role_policies(RoleName=tool_role_name)["AttachedPolicies"]
    for pol in tool_attached:
        if "BedrockFullAccess" in pol["PolicyName"] or pol["PolicyName"] == "AdministratorAccess":
            tool_has_converse = True
            tool_has_inference_profile = True

    if tool_has_converse:
        log(PASS, f"Tool executor role has bedrock:Converse/InvokeModel")
    else:
        log(FAIL, f"Tool executor role MISSING bedrock:Converse — tools cannot call Bedrock models!")

    if tool_has_inference_profile:
        log(PASS, f"Tool executor role has inference-profile ARNs")
    else:
        log(FAIL, f"Tool executor role MISSING inference-profile ARNs! Model us.amazon.nova-lite-v1:0 is an inference profile, not a foundation-model. Add inference-profile/* to the IAM policy resources.")

    # Direct invocation test of the tool executor
    print(f"\n  Direct tool executor test (generate_soap with minimal input)...")
    try:
        tool_test_payload = {
            "actionGroup": "ClinicalTools",
            "function": "generate_soap",
            "parameters": [
                {"name": "consultation_text", "value": "Patient Ravi Kumar, 45M, headache 2 days. No fever. BP 130/80. Prescribed paracetamol 500mg TDS x3 days."},
                {"name": "patient_name", "value": "Ravi Kumar"},
                {"name": "patient_age", "value": "45"},
                {"name": "patient_gender", "value": "Male"}
            ]
        }
        tool_resp = lambda_client.invoke(
            FunctionName=tool_lambda_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(tool_test_payload)
        )
        tool_status = tool_resp.get("StatusCode", 0)
        tool_func_error = tool_resp.get("FunctionError", "")
        tool_payload = json.loads(tool_resp["Payload"].read().decode("utf-8"))

        if tool_func_error:
            log(FAIL, f"Tool executor returned function error: {tool_func_error}")
            print(f"    Payload: {json.dumps(tool_payload, indent=2)[:500]}")
        else:
            tool_response = tool_payload.get("response", {})
            func_resp = tool_response.get("functionResponse", {})
            resp_state = func_resp.get("responseState", "")
            resp_body = func_resp.get("responseBody", {}).get("TEXT", {}).get("body", "")

            if resp_state == "FAILURE":
                log(FAIL, f"Tool executor generate_soap FAILED: {resp_body[:300]}")
            elif resp_body:
                try:
                    parsed = json.loads(resp_body)
                    has_subjective = "subjective" in parsed
                    has_objective = "objective" in parsed
                    log(PASS, f"Tool executor generate_soap returned valid SOAP (subjective={has_subjective}, objective={has_objective})")
                except json.JSONDecodeError:
                    log(WARN, f"Tool executor returned non-JSON: {resp_body[:200]}")
            else:
                log(WARN, f"Tool executor returned empty body")
    except Exception as e:
        log(FAIL, f"Tool executor direct invocation failed: {e}")

except Exception as e:
    log(FAIL, f"Tool executor Lambda not found: {e}")


# =====================================================
# 7. AGENT INVOKER LAMBDA
# =====================================================
section("7. AGENT INVOKER LAMBDA")

invoker_lambda_name = f"{PROJECT}-agent-invoker-{STAGE}"
try:
    func = lambda_client.get_function(FunctionName=invoker_lambda_name)
    env_vars = func["Configuration"].get("Environment", {}).get("Variables", {})
    agent_id_env = env_vars.get("BEDROCK_AGENT_ID", "")
    alias_id_env = env_vars.get("BEDROCK_AGENT_ALIAS_ID", "")
    print(f"  Lambda: {invoker_lambda_name}")
    print(f"  BEDROCK_AGENT_ID = '{agent_id_env}'")
    print(f"  BEDROCK_AGENT_ALIAS_ID = '{alias_id_env}'")

    if not agent_id_env:
        log(FAIL, "BEDROCK_AGENT_ID env var is EMPTY — Lambda doesn't know which agent to call!")
    elif agent_id_env != SUPERVISOR_ID:
        log(FAIL, f"BEDROCK_AGENT_ID mismatch! Lambda has '{agent_id_env}' but Supervisor is '{SUPERVISOR_ID}'")
    else:
        log(PASS, f"BEDROCK_AGENT_ID matches Supervisor: {agent_id_env}")

    if not alias_id_env:
        log(FAIL, "BEDROCK_AGENT_ALIAS_ID env var is EMPTY!")
    else:
        # Verify this alias actually exists
        try:
            alias_detail = bedrock_agent_client.get_agent_alias(
                agentId=SUPERVISOR_ID,
                agentAliasId=alias_id_env
            )
            alias_status = alias_detail["agentAlias"]["agentAliasStatus"]
            if alias_status == "PREPARED":
                log(PASS, f"BEDROCK_AGENT_ALIAS_ID '{alias_id_env}' exists and is PREPARED")
            else:
                log(WARN, f"BEDROCK_AGENT_ALIAS_ID '{alias_id_env}' status is {alias_status}")
        except Exception as e:
            log(FAIL, f"BEDROCK_AGENT_ALIAS_ID '{alias_id_env}' is INVALID: {e}")

    # Check Lambda's execution role
    lambda_role_arn = func["Configuration"]["Role"]
    lambda_role_name = lambda_role_arn.split("/")[-1]
    print(f"\n  Execution role: {lambda_role_name}")

    inline_pols = iam.list_role_policies(RoleName=lambda_role_name)["PolicyNames"]
    lambda_has_invoke_agent = False
    for pol_name in inline_pols:
        doc = iam.get_role_policy(RoleName=lambda_role_name, PolicyName=pol_name)["PolicyDocument"]
        for stmt in doc.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]
            if "bedrock:InvokeAgent" in actions:
                lambda_has_invoke_agent = True

    if lambda_has_invoke_agent:
        log(PASS, "Lambda execution role has bedrock:InvokeAgent permission")
    else:
        log(FAIL, "Lambda execution role MISSING bedrock:InvokeAgent!")

except Exception as e:
    log(FAIL, f"Agent invoker Lambda not found: {e}")


# =====================================================
# 8. FOUNDATION MODEL ACCESS
# =====================================================
section("8. FOUNDATION MODEL ACCESS")

test_models = ["us.amazon.nova-lite-v1:0", "us.amazon.nova-micro-v1:0"]
for model_id in test_models:
    try:
        resp = bedrock_runtime.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": "Say OK"}]}],
            inferenceConfig={"maxTokens": 10}
        )
        output = resp["output"]["message"]["content"][0]["text"]
        log(PASS, f"Model {model_id} accessible (response: '{output[:30]}')")
    except Exception as e:
        log(FAIL, f"Model {model_id} NOT accessible: {e}")


# =====================================================
# 8.5. CHECK CALLER'S OWN INVOKEAGENT PERMISSION
# =====================================================
section("8.5. CALLER INVOKEAGENT PERMISSION")

# The caller (IAM user/role running this script) also needs bedrock:InvokeAgent
print(f"  Caller: {CALLER_ARN}")
print(f"  Checking if caller has bedrock:InvokeAgent permission...")

# Try to simulate the policy
try:
    iam_resource = boto3.resource("iam", region_name=REGION)
    # Extract user or role name from ARN
    if ":user/" in CALLER_ARN:
        caller_type = "user"
        caller_name = CALLER_ARN.split(":user/")[-1]
        # Check user policies
        user = iam_resource.User(caller_name)
        all_policies = []
        # Inline policies
        for pol in user.policies.all():
            doc = pol.policy_document
            all_policies.append(("inline:" + pol.name, doc))
        # Attached policies
        for pol in user.attached_policies.all():
            # Get the default version
            policy = iam_resource.Policy(pol.arn)
            version = policy.default_version
            all_policies.append(("attached:" + pol.policy_name, version.document))
        # Check groups
        for group in user.groups.all():
            for pol in group.policies.all():
                all_policies.append(("group-inline:" + pol.name, pol.policy_document))
            for pol in group.attached_policies.all():
                policy = iam_resource.Policy(pol.arn)
                version = policy.default_version
                all_policies.append(("group-attached:" + pol.policy_name, version.document))

        caller_has_invoke_agent = False
        for pol_name, doc in all_policies:
            for stmt in doc.get("Statement", []):
                if stmt.get("Effect") != "Allow":
                    continue
                actions = stmt.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]
                for action in actions:
                    if action in ("bedrock:InvokeAgent", "bedrock:*", "*"):
                        caller_has_invoke_agent = True
                        print(f"    Found InvokeAgent in policy: {pol_name}")
                        break

        if caller_has_invoke_agent:
            log(PASS, "Caller has bedrock:InvokeAgent permission")
        else:
            log(FAIL, f"Caller IAM user '{caller_name}' does NOT have bedrock:InvokeAgent permission!")
            log(FAIL, "  This means the debug script cannot invoke agents directly.")
            log(FAIL, "  Add bedrock:InvokeAgent to the user's policy, or use bedrock:* for full access.")
            print(f"\n  All policies found for {caller_name}:")
            for pol_name, doc in all_policies:
                print(f"    {pol_name}:")
                for stmt in doc.get("Statement", []):
                    print(f"      Effect={stmt.get('Effect')} Actions={stmt.get('Action')}")
    elif ":role/" in CALLER_ARN or ":assumed-role/" in CALLER_ARN:
        print(f"  Caller is a role — skipping detailed user policy check")
        log(WARN, "Cannot check role-based caller permissions in detail from here")
except Exception as e:
    log(WARN, f"Could not check caller permissions: {e}")


# =====================================================
# 9. INVOKE EACH COLLABORATOR AGENT DIRECTLY
# =====================================================
section("9. TEST INVOKE EACH COLLABORATOR AGENT (as current caller)")

for name, agent in collaborators.items():
    agent_id = agent["agentId"]
    aliases = get_agent_aliases(agent_id, name)
    if not aliases:
        log(FAIL, f"Cannot test {name} — no aliases")
        continue

    alias_id = aliases[0]["agentAliasId"]
    session_id = str(uuid.uuid4())

    print(f"\n  Testing {name} (agent={agent_id}, alias={alias_id})...")
    try:
        resp = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText="Test connectivity. Just reply with OK.",
            enableTrace=False
        )
        # Read the stream
        response_text = ""
        for event in resp.get("completion", []):
            if "chunk" in event:
                chunk_bytes = event["chunk"].get("bytes", b"")
                if isinstance(chunk_bytes, bytes):
                    response_text += chunk_bytes.decode("utf-8")
        log(PASS, f"{name} responded: '{response_text[:80]}'")
    except Exception as e:
        error_str = str(e)
        log(FAIL, f"{name} INVOKE FAILED: {error_str}")
        if "accessDenied" in error_str.lower():
            log(FAIL, f"  -> This is a PERMISSION issue. Check {name}'s service role and model access.")
        elif "throttl" in error_str.lower():
            log(WARN, f"  -> Throttled. Retry later.")
        elif "timeout" in error_str.lower():
            log(WARN, f"  -> Timeout. Model may be slow.")


# =====================================================
# 10. INVOKE SUPERVISOR AGENT (END-TO-END TEST)
# =====================================================
section("10. TEST INVOKE SUPERVISOR AGENT (END-TO-END)")

if supervisor_alias_id:
    session_id = str(uuid.uuid4())
    test_prompt = """Process this clinical consultation:

CONSULTATION: Patient Ravi Kumar, 45 year old male, presents with headache for 2 days.
No fever, no vomiting. BP 130/80. Prescribed paracetamol 500mg TDS for 3 days.

PATIENT: Name=Ravi Kumar, Age=45, Gender=Male
DOCTOR: Dr. Sharma, General Medicine, City Hospital
REFERRAL: No referral needed. Skip the generate_referral tool.

Please coordinate with your specialist agents to generate all documentation."""

    print(f"  Supervisor: {SUPERVISOR_ID}")
    print(f"  Alias: {supervisor_alias_id}")
    print(f"  Session: {session_id}")
    print(f"  Sending test consultation...")

    try:
        resp = bedrock_agent_runtime.invoke_agent(
            agentId=SUPERVISOR_ID,
            agentAliasId=supervisor_alias_id,
            sessionId=session_id,
            inputText=test_prompt,
            enableTrace=True
        )

        response_text = ""
        traces = []
        for event in resp.get("completion", []):
            if "chunk" in event:
                chunk_bytes = event["chunk"].get("bytes", b"")
                if isinstance(chunk_bytes, bytes):
                    response_text += chunk_bytes.decode("utf-8")
            if "trace" in event:
                trace = event["trace"].get("trace", {})
                if "orchestrationTrace" in trace:
                    orch = trace["orchestrationTrace"]
                    # Log collaborator invocations
                    if "invocationInput" in orch:
                        inv = orch["invocationInput"]
                        if "collaboratorInvocationInput" in inv:
                            collab = inv["collaboratorInvocationInput"]
                            collab_name = collab.get("collaboratorName", "?")
                            print(f"    -> Supervisor delegating to: {collab_name}")
                        if "actionGroupInvocationInput" in inv:
                            tool = inv["actionGroupInvocationInput"]
                            func_name = tool.get("function", "?")
                            print(f"    -> Tool called: {func_name}")
                    if "observation" in orch:
                        obs = orch["observation"]
                        if "actionGroupInvocationOutput" in obs:
                            out_text = obs["actionGroupInvocationOutput"].get("text", "")
                            print(f"    <- Tool response: {out_text[:200]}...")
                        if "collaboratorInvocationOutput" in obs:
                            collab_out = obs["collaboratorInvocationOutput"]
                            collab_name = collab_out.get("collaboratorName", "?")
                            collab_text = collab_out.get("output", {}).get("text", "")
                            print(f"    <- Collaborator {collab_name} response ({len(collab_text)} chars): {collab_text[:300]}...")
                    # Check for errors in trace
                    if "failureTrace" in trace:
                        ft = trace["failureTrace"]
                        print(f"    !! FAILURE TRACE: {json.dumps(ft, default=str)}")
                if "failureTrace" in trace:
                    ft = trace["failureTrace"]
                    log(FAIL, f"Failure trace: {json.dumps(ft, default=str)}")

        if response_text:
            print(f"\n  Supervisor response ({len(response_text)} chars):")
            print(f"  {response_text[:500]}")
            log(PASS, "Supervisor end-to-end test PASSED")
        else:
            log(WARN, "Supervisor returned empty response")

    except Exception as e:
        error_str = str(e)
        log(FAIL, f"Supervisor INVOKE FAILED: {error_str}")
        if "accessDenied" in error_str.lower():
            log(FAIL, "  -> PERMISSION ISSUE. Likely causes:")
            log(FAIL, "     1. Supervisor's service role missing bedrock:InvokeAgent for collaborators")
            log(FAIL, "     2. Supervisor's service role missing bedrock:InvokeModel for foundation model")
            log(FAIL, "     3. Collaborator agents' roles missing bedrock:InvokeModel")
            log(FAIL, "     4. Tool Executor Lambda missing resource-based policy for bedrock.amazonaws.com")
        elif "dependencyFailed" in error_str.lower():
            log(FAIL, "  -> DEPENDENCY FAILED. A collaborator or its Lambda tool failed.")
            log(FAIL, "     Check Tool Executor Lambda CloudWatch logs for details.")
else:
    log(FAIL, "Cannot test Supervisor — no alias found")


# =====================================================
# 11. INVOKE VIA LAMBDA (tests Lambda's own role)
# =====================================================
section("11. TEST VIA LAMBDA INVOCATION (uses Lambda execution role)")

try:
    test_payload = {
        "httpMethod": "POST",
        "body": json.dumps({
            "consultation_text": "Patient Ravi Kumar, 45 year old male, presents with headache for 2 days. No fever, no vomiting. BP 130/80. Prescribed paracetamol 500mg TDS for 3 days.",
            "patient": {"name": "Ravi Kumar", "age": 45, "gender": "Male", "patient_id": "TEST-001"},
            "doctor": {"name": "Dr. Sharma", "speciality": "General Medicine", "hospital": "City Hospital"}
        })
    }

    print(f"  Invoking Lambda: {invoker_lambda_name}...")
    print(f"  This tests the Lambda's own execution role (not the caller's permissions)")

    resp = lambda_client.invoke(
        FunctionName=invoker_lambda_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(test_payload)
    )

    status_code = resp.get("StatusCode", 0)
    func_error = resp.get("FunctionError", "")
    payload = json.loads(resp["Payload"].read().decode("utf-8"))

    print(f"  Lambda HTTP status: {status_code}")
    if func_error:
        print(f"  Lambda function error: {func_error}")
        log(FAIL, f"Lambda invocation returned function error: {func_error}")
        print(f"  Payload: {json.dumps(payload, indent=2)[:1000]}")
    else:
        body_status = payload.get("statusCode", 0)
        print(f"  Response statusCode: {body_status}")

        if body_status == 200:
            body = json.loads(payload.get("body", "{}"))
            has_soap = bool(body.get("soap_note"))
            has_summary = bool(body.get("patient_summary"))
            arch = body.get("metadata", {}).get("architecture", "")
            print(f"  Architecture: {arch}")
            print(f"  Has SOAP note: {has_soap}")
            print(f"  Has patient summary: {has_summary}")

            if "fallback" in arch.lower():
                log(WARN, f"Lambda fell back to monolithic: {arch}")
                fallback_reason = body.get("metadata", {}).get("fallback_reason", "unknown")
                log(FAIL, f"Multi-agent path failed, fallback reason: {fallback_reason}")
            else:
                log(PASS, f"Lambda E2E test PASSED via multi-agent! Architecture: {arch}")
        else:
            body = payload.get("body", "{}")
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except Exception:
                    pass
            error_msg = body.get("error", str(body)[:300]) if isinstance(body, dict) else str(body)[:300]
            log(FAIL, f"Lambda returned status {body_status}: {error_msg}")

except Exception as e:
    log(FAIL, f"Lambda invocation failed: {e}")


# =====================================================
# SUMMARY
# =====================================================
section("DEBUG SUMMARY")
if failures:
    print(f"\n  ❌ {len(failures)} FAILURE(S) FOUND:\n")
    for i, f in enumerate(failures, 1):
        print(f"    {i}. {f}")
    print(f"\n  Fix the above issues and re-run this script.")
    sys.exit(1)
else:
    print(f"\n  ✅ ALL CHECKS PASSED — no issues found.")
    print(f"  If InvokeAgent still fails, check CloudTrail for detailed denial reasons.")
    sys.exit(0)
