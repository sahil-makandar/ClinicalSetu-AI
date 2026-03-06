# ClinicalSetu - AWS Deployment Guide

**Time required:** ~20 minutes
**Cost:** ~$5-15 for testing (Lambda free tier, Bedrock charges per token)
**Region:** us-east-1 (N. Virginia)

---

## Prerequisites

- AWS account with $100 credits
- Region set to **us-east-1** (N. Virginia) in the console
- GitHub repo pushed with latest code
- `lambda_deployment.zip` created in project root (run `python scripts/package_lambda.py` if missing)

---

## What Gets Created

| Resource | Service | Purpose |
|----------|---------|---------|
| Bedrock access | Amazon Bedrock | Enable Claude 3 Sonnet model |
| Lambda function | AWS Lambda | Backend API (processes consultations) |
| REST API | API Gateway | HTTPS endpoint for frontend |
| Web app | AWS Amplify | Frontend hosting from GitHub |

**No `.env` files or AWS keys need to be added to any config files.** Lambda uses its IAM role for Bedrock access. Amplify only needs one env var (`VITE_API_URL`).

---

## STEP 1: Verify Bedrock Model Access (2 min)

1. Open **AWS Console** → search **"Amazon Bedrock"** → click it
2. Confirm you're in **us-east-1** (top-right region dropdown)
3. Left sidebar → **Model access**
4. Check that **Anthropic Claude 3 Sonnet** shows **"Access granted"**
5. If NOT granted:
   - Click **Manage model access**
   - Check **Claude 3 Sonnet**
   - Click **Save changes**
   - If a use case form appears, fill: "Healthcare AI prototype, hackathon use, synthetic data only"
   - Approval is usually instant

---

## STEP 2: Create Lambda Function (5 min)

### 2a. Create the function

1. **AWS Console** → search **"Lambda"** → **Create function**
2. Fill in:
   - Function name: `ClinicalSetu-API`
   - Runtime: **Python 3.12**
   - Architecture: **x86_64**
   - Permissions: **Create a new role with basic Lambda permissions**
3. Click **Create function**

### 2b. Upload code

1. On the function page, click **Upload from** → **.zip file**
2. Upload: `lambda_deployment.zip` (13 KB, in your project root)
3. Click **Save**

### 2c. Set handler (IMPORTANT)

1. In the **Code** tab, scroll down to **Runtime settings** → click **Edit**
2. Handler: `lambda_function.lambda_handler`
3. Click **Save**

### 2d. Set timeout and memory

1. Go to **Configuration** tab → **General configuration** → **Edit**
2. Memory: **1024 MB**
3. Timeout: **2 min 0 sec**
4. Click **Save**

### 2e. Add Bedrock permission

1. Go to **Configuration** tab → **Permissions**
2. Click the **Role name** link (opens IAM in a new tab)
3. Click **Add permissions** → **Create inline policy**
4. Click **JSON** tab, paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/*"
    }
  ]
}
```

5. Click **Next** → Policy name: `BedrockAccess` → **Create policy**

### 2f. Test it (optional but recommended)

1. Go back to Lambda → **Test** tab
2. Create test event with this JSON:

```json
{
  "body": "{\"consultation_text\":\"Patient John, 45M, presents with headache for 2 days. BP 140/90. Prescribed paracetamol.\",\"patient\":{\"name\":\"John\",\"age\":45,\"gender\":\"Male\"},\"doctor\":{\"name\":\"Dr. Test\",\"speciality\":\"General Medicine\",\"hospital\":\"Test Hospital\"},\"referral_reason\":null,\"specialist_type\":null}"
}
```

3. Click **Test** — should return statusCode 200 with SOAP note, summary, trials
4. Takes ~30-60 seconds on first run

---

## STEP 3: Create API Gateway (5 min)

### 3a. Create the API

1. **AWS Console** → search **"API Gateway"** → **Create API**
2. Choose **REST API** (NOT HTTP API, NOT private) → **Build**
3. Settings:
   - Protocol: REST
   - Create new API: **New API**
   - API name: `ClinicalSetu-API`
4. Click **Create API**

### 3b. Create resources

1. Click **Actions** → **Create Resource**
   - Resource name: `api`
   - Check ✅ **Enable API Gateway CORS**
   - Click **Create Resource**
2. Select `/api`, click **Actions** → **Create Resource**
   - Resource name: `process`
   - Check ✅ **Enable API Gateway CORS**
   - Click **Create Resource**

### 3c. Create POST method

1. Select `/api/process`
2. Click **Actions** → **Create Method** → choose **POST** → click the ✓ checkmark
3. Integration type: **Lambda Function**
4. Check ✅ **Use Lambda Proxy integration**
5. Lambda Function: `ClinicalSetu-API`
6. Click **Save** → **OK** on the permission popup

### 3d. Enable CORS on POST

1. Select `/api/process`
2. Click **Actions** → **Enable CORS**
3. Leave defaults (all origins, all headers)
4. Click **Enable CORS and replace existing CORS headers** → **Yes, replace**

### 3e. Deploy the API

1. Click **Actions** → **Deploy API**
2. Deployment stage: **[New Stage]**
3. Stage name: `prod`
4. Click **Deploy**

### 3f. Copy the invoke URL

You'll see something like:

```
Invoke URL: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod
```

**Save this URL** — you need it for Step 4.

Your full API endpoint will be:
```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/api/process
```

---

## STEP 4: Deploy Frontend to Amplify (5 min)

### 4a. Push code to GitHub first

```bash
cd c:/Users/Admin/Desktop/Hackathons/AI-for-Bharat-AWS
git add -A
git commit -m "Deploy-ready: professional UI + Lambda package"
git push origin main
```

### 4b. Create Amplify app

1. **AWS Console** → search **"AWS Amplify"** → **New app** → **Host web app**
2. Source: **GitHub** → **Continue**
3. Authorize AWS Amplify if prompted
4. Select your repository + branch `main`
5. Click **Next**

### 4c. Configure build settings

1. App name: `ClinicalSetu`
2. Click **Edit** on the build spec and replace with:

```yaml
version: 1
applications:
  - frontend:
      phases:
        preBuild:
          commands:
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: dist
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
    appRoot: frontend
```

3. Click **Next**

### 4d. Add environment variable

1. Expand **Advanced settings** → **Environment variables**
2. Add:
   - Key: `VITE_API_URL`
   - Value: `https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod` (your API Gateway URL from Step 3f)

### 4e. Deploy

1. Click **Save and deploy**
2. Wait ~2-3 minutes for build
3. You'll get a live URL like: `https://main.xxxxxxxxxx.amplifyapp.com`

---

## STEP 5: Test End-to-End (2 min)

1. Open the Amplify URL in your browser
2. Select a doctor profile (Dr. Ananya or Dr. Suresh)
3. Click any sample case to load it
4. Click **"Process with AI"**
5. Wait ~30-60 seconds for all 4 outputs
6. Verify:
   - [ ] SOAP Note tab shows structured data with confidence scores
   - [ ] Patient Summary tab shows plain-language summary
   - [ ] Referral Letter tab shows referral (if case has one) or "No referral indicated"
   - [ ] Trial Matches tab shows matched clinical trials
   - [ ] "AI-Generated" disclaimer appears on every tab
   - [ ] No console errors (F12 → Console)

---

## Troubleshooting

### Lambda returns timeout error
- Increase timeout to 2 minutes (Configuration → General configuration)
- Increase memory to 1024 MB
- Bedrock calls can take 15-30 seconds each, x4 = up to 120 seconds total

### Lambda returns "AccessDeniedException" for Bedrock
- Check the IAM inline policy is attached (Step 2e)
- Make sure the Resource ARN uses `us-east-1` and has `/*` at the end
- Make sure you're in us-east-1 region

### API Gateway returns CORS error
- Re-do Step 3d (Enable CORS)
- Make sure you deployed after enabling CORS (Step 3e)
- Check that the frontend VITE_API_URL doesn't have a trailing slash

### Amplify build fails
- Check that appRoot is set to `frontend`
- Check that the build spec YAML is correct (Step 4c)
- Check the build logs in Amplify console for specific errors

### Frontend loads but API calls fail
- Check browser console (F12) for the exact error
- Verify VITE_API_URL environment variable in Amplify matches your API Gateway URL
- Test the API Gateway URL directly with curl:
  ```bash
  curl -X POST https://YOUR-API-URL/prod/api/process \
    -H "Content-Type: application/json" \
    -d '{"consultation_text":"Test","patient":{"name":"Test","age":30,"gender":"Male"},"doctor":{"name":"Dr. Test","speciality":"GM","hospital":"H"}}'
  ```

### Bedrock model not available
- Go to Bedrock Console → Model access
- Make sure Claude 3 Sonnet is enabled
- If you see a form, fill it out — approval is usually instant

---

## Architecture (for reference)

```
User Browser
    ↓
AWS Amplify (React frontend)
    ↓ POST /api/process
API Gateway (REST, CORS enabled)
    ↓ Lambda Proxy
Lambda: ClinicalSetu-API (Python 3.12)
    ↓ bedrock:InvokeModel (x4 calls)
Amazon Bedrock (Claude 3 Sonnet)
    → SOAP Note
    → Patient Summary
    → Referral Letter
    → Clinical Trial Matches
```

---

## Cost Estimate

| Service | Estimated Cost |
|---------|---------------|
| Lambda | Free tier (1M requests/month) |
| API Gateway | Free tier (1M calls/month) |
| Amplify | Free tier (build + hosting) |
| Bedrock (Claude 3 Sonnet) | ~$0.30-0.50 per consultation |
| S3 | Free tier |
| **Total for ~30 test runs** | **~$10-15** |

---

## Files Reference

| File | Purpose |
|------|---------|
| `lambda_deployment.zip` | Upload to Lambda (contains handler + prompts + trial data) |
| `scripts/package_lambda.py` | Re-generates the ZIP if you change code |
| `frontend/.env` | Local dev only (points to localhost:3001) |
| `frontend/.env.example` | Template showing what env vars are available |
| `backend/local_server.py` | Local testing server (not deployed) |
