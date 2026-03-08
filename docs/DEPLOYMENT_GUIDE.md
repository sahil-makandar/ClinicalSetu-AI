# ClinicalSetu - AWS Deployment Guide

**Deployment method:** Fully automated via GitHub Actions CI/CD
**Time required:** ~10 minutes (push and wait)
**Region:** us-east-1 (N. Virginia)

---

## Prerequisites

- AWS account with credits
- Region set to **us-east-1** (N. Virginia)
- GitHub repository with code pushed to `main` branch
- The following GitHub Secrets configured:
  - `AWS_ACCESS_KEY_ID` — IAM user access key
  - `AWS_SECRET_ACCESS_KEY` — IAM user secret key

### IAM User Requirements

The deployer IAM user needs these permissions:
- `AdministratorAccess` (recommended for hackathon) **OR** the following:
  - CloudFormation full access
  - Lambda full access
  - API Gateway full access
  - S3 full access
  - DynamoDB full access
  - IAM role creation (`CAPABILITY_NAMED_IAM`)
  - Bedrock full access (agents, models, knowledge bases)
  - OpenSearch Serverless access
  - CloudFront access
  - Cognito Identity Pool access
  - EventBridge access

### Bedrock Model Access

Before first deployment, enable model access in the AWS Console:

1. Open **AWS Console** → **Amazon Bedrock** → **Model access**
2. Confirm region is **us-east-1**
3. Enable access for:
   - **Amazon Nova Lite** (primary model)
   - **Amazon Nova Micro** (fallback model)
   - **Amazon Titan Text Embeddings V2** (for Knowledge Base RAG)
4. These use cross-region inference profiles (`us.amazon.nova-lite-v1:0`, `us.amazon.nova-micro-v1:0`)

---

## What Gets Deployed

The CI/CD pipeline deploys **13 AWS services** via a single CloudFormation template:

| Resource | Service | Purpose |
|----------|---------|---------|
| AI Engine | Amazon Bedrock (Nova Lite + Nova Micro) | Core AI — Converse API with cross-region inference profiles |
| Multi-Agent | Bedrock Multi-Agent Collaboration | Supervisor-Router: 1 supervisor + 4 specialist agents |
| RAG Pipeline | Bedrock Knowledge Bases + OpenSearch Serverless | Clinical trial matching with Titan Embeddings |
| Compute | AWS Lambda x5 (Python 3.12) | API + Agent Invoker + Tool Executor + Trial Fetcher + Visit API |
| API | Amazon API Gateway (REST) | HTTPS endpoint with CORS |
| Frontend | Amazon S3 + CloudFront | Static hosting with CDN and HTTPS |
| Database | Amazon DynamoDB x2 tables | Response cache + Patient visits |
| Auth | Amazon Cognito Identity Pool | Browser-to-Transcribe Medical access |
| Speech | Amazon Transcribe Medical | Real-time clinical speech-to-text |
| Scheduler | Amazon EventBridge | Daily clinical trial data refresh |
| IaC | AWS CloudFormation | Infrastructure as Code |

---

## Deployment Steps

### Step 1: Configure GitHub Secrets

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Add these repository secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

### Step 2: Push to Main Branch

```bash
git push origin main
```

This triggers the GitHub Actions workflow (`.github/workflows/deploy.yml`) which:

1. **Fetches clinical trial data** from ClinicalTrials.gov
2. **Packages Lambda functions** into deployment ZIPs
3. **Uploads ZIPs** to S3
4. **Deploys CloudFormation stack** — creates all AWS resources
5. **Sets up Multi-Agent Collaboration** (one-time, idempotent):
   - Creates IAM role with `AmazonBedrockFullAccess`
   - Provisions 4 collaborator agents (SOAP, Summary, Referral, Trial)
   - Provisions 1 supervisor agent with collaborator associations
   - Creates production aliases for all agents
   - Updates Agent Invoker Lambda with agent IDs
6. **Sets up Knowledge Base** (one-time, idempotent):
   - Creates OpenSearch Serverless collection + vector index
   - Creates Bedrock Knowledge Base with Titan Embeddings V2
   - Syncs clinical trial data
7. **Seeds synthetic visit data** into DynamoDB (one-time)
8. **Builds React frontend** with environment variables injected
9. **Syncs frontend to S3** + invalidates CloudFront cache

### Step 3: Monitor Deployment

- Go to GitHub → **Actions** tab → click the running workflow
- Full deployment takes ~8-12 minutes
- The deployment summary shows all deployed services

### Step 4: Skip One-Time Steps on Subsequent Deploys

After first successful deployment, set these GitHub repository **Variables** (not Secrets) to skip one-time setup:

| Variable | Value | Purpose |
|----------|-------|---------|
| `MULTI_AGENT_SETUP_DONE` | `true` | Skip agent provisioning |
| `KNOWLEDGE_BASE_SETUP_DONE` | `true` | Skip KB + OpenSearch setup |
| `SEED_DATA_DONE` | `true` | Skip synthetic data seeding |

Set at: Repository → Settings → Secrets and variables → Actions → Variables

---

## Architecture

```
User Browser
    ↓
CloudFront (CDN + HTTPS)
    ↓
S3 (React SPA)
    ↓ POST /api/process-agent
API Gateway (REST, CORS)
    ↓ Lambda Proxy
Agent Invoker Lambda
    ↓ bedrock:InvokeAgent
Supervisor Agent (Bedrock Multi-Agent Collaboration)
    ├── SOAPAgent → Tool Executor Lambda → Bedrock Converse (Nova Lite)
    ├── SummaryAgent → Tool Executor Lambda → Bedrock Converse (Nova Lite)
    ├── ReferralAgent → Tool Executor Lambda → Bedrock Converse (Nova Lite)
    └── TrialAgent → Tool Executor Lambda → Bedrock Converse (Nova Lite) + Knowledge Base RAG
```

---

## IAM Roles (created automatically)

| Role | Purpose |
|------|---------|
| `clinicalsetu-lambda-role-prod` | Lambda execution role for tool executor + other Lambdas (Bedrock Converse + DynamoDB + inference profiles) |
| `clinicalsetu-agent-invoker-role-prod` | Agent Invoker Lambda role (bedrock:InvokeAgent + Converse + inference profiles) |
| `ClinicalSetu-MultiAgentRole` | Bedrock Agent service role (AmazonBedrockFullAccess + Lambda invoke + KB access) |

---

## Testing

### Quick Test via API

```bash
curl -X POST https://YOUR-API-GATEWAY-URL/prod/api/process-agent \
  -H "Content-Type: application/json" \
  -d '{
    "consultation_text": "Patient Ravi Kumar, 45M, headache 2 days. No fever. BP 130/80. Prescribed paracetamol 500mg TDS x3 days.",
    "patient": {"name": "Ravi Kumar", "age": 45, "gender": "Male", "patient_id": "TEST-001"},
    "doctor": {"name": "Dr. Sharma", "speciality": "General Medicine", "hospital": "City Hospital"}
  }'
```

### Debug Multi-Agent Issues

If agents aren't working, run the diagnostic script:

```bash
pip install boto3
python scripts/debug_agents.py
```

This performs 11 checks: AWS connectivity, agent inventory, aliases, IAM permissions, collaborator associations, Lambda resource policies, model access, and end-to-end invocation tests.

---

## Troubleshooting

### `accessDeniedException` on InvokeAgent
- **Cause**: Lambda execution role missing permissions or agent service role missing inference profile ARNs
- **Fix**: The CloudFormation template includes all required permissions including `inference-profile/*` ARNs. Re-deploy the stack.

### SOAP Note generation returns empty
- **Cause**: Tool Executor Lambda's IAM role needs `bedrock:Converse` on both `foundation-model/*` AND `inference-profile/*` resources (Nova Lite uses cross-region inference profiles)
- **Fix**: CloudFormation template includes these. Re-deploy.

### Supervisor responds but no tool outputs
- **Cause**: The invoke_agent Lambda must parse `collaboratorInvocationOutput` from the Bedrock trace (not just `actionGroupInvocationOutput`)
- **Fix**: Already handled in `invoke_agent.py`

### Multi-agent returns error
- Check Agent Invoker Lambda environment variables: `BEDROCK_AGENT_ID` and `BEDROCK_AGENT_ALIAS_ID` must be set
- Run `debug_agents.py` to diagnose
- Check Lambda Function URL is configured (bypasses API Gateway 29s timeout)

### CORS errors
- API Gateway CORS is configured in CloudFormation
- Lambda responses include CORS headers
- Check that frontend `VITE_API_URL` doesn't have a trailing slash

---

## Cost Estimate

| Service | Estimated Cost |
|---------|---------------|
| Lambda x5 | Free tier (1M requests/month) |
| API Gateway | Free tier (1M calls/month) |
| S3 + CloudFront | Free tier |
| DynamoDB | Free tier (PAY_PER_REQUEST, 25GB) |
| Bedrock (Nova Lite) | ~$0.003-0.01 per consultation |
| OpenSearch Serverless | ~$0.24/hr per OCU (2 OCUs minimum when active) |
| Cognito | Free tier |
| EventBridge | Free tier |
| **Total for ~30 test runs** | **~$5-10** |

---

## Local Development

```bash
# Backend
cd backend
pip install boto3
python local_server.py    # Runs on localhost:3001

# Frontend
cd frontend
npm install
cp .env.example .env      # Edit VITE_API_URL to localhost:3001
npm run dev                # Runs on localhost:5173
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `infrastructure/cloudformation.yaml` | All AWS resources (IaC) |
| `.github/workflows/deploy.yml` | CI/CD pipeline |
| `scripts/setup_multi_agent.py` | Provisions Bedrock agents (run by CI/CD) |
| `scripts/setup_knowledge_base.py` | Sets up RAG pipeline (run by CI/CD) |
| `scripts/package_lambda.py` | Packages Lambda ZIPs (run by CI/CD) |
| `scripts/debug_agents.py` | 11-point diagnostic for multi-agent debugging |
| `scripts/seed_visits.py` | Seeds synthetic visit data |
| `backend/lambda/invoke_agent.py` | Multi-agent invoker + collaborator output parsing |
| `backend/lambda/agent_tool_executor.py` | Shared tool executor for all collaborator agents |
| `backend/lambda/process_consultation.py` | Standalone handler (Converse API + caching) |
