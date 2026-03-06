#!/bin/bash
# ============================================================
# ClinicalSetu - One-Click AWS Deployment Script
# ============================================================
# Usage:  ./infrastructure/deploy.sh
#
# Prerequisites:
#   1. AWS CLI installed and configured (aws configure)
#   2. Region set to us-east-1 (required for Bedrock models)
#   3. Bedrock model access enabled for Amazon Nova Lite + Claude Haiku in AWS Console
#   4. Node.js & npm installed (for frontend build)
#
# What this script does:
#   1. Packages Lambda code into a ZIP
#   2. Creates an S3 bucket and uploads the Lambda ZIP
#   3. Deploys the CloudFormation stack (Lambda + API Gateway + S3 + CloudFront)
#   4. Builds the frontend with the API URL
#   5. Uploads frontend to S3
# ============================================================

set -e

# -- Configuration --
PROJECT_NAME="ClinicalSetu"
STACK_NAME="ClinicalSetu-Stack"
STAGE="prod"
REGION="us-east-1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "=============================================="
echo "  ClinicalSetu - One-Click AWS Deployment"
echo "=============================================="
echo -e "${NC}"

# -- Step 0: Validate prerequisites --
echo -e "${YELLOW}[0/6] Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found. Install it from https://aws.amazon.com/cli/${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}ERROR: npm not found. Install Node.js from https://nodejs.org/${NC}"
    exit 1
fi

# Verify AWS credentials
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region "$REGION" 2>/dev/null)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}ERROR: AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi
echo -e "  AWS Account: ${GREEN}${AWS_ACCOUNT_ID}${NC}"
echo -e "  Region:      ${GREEN}${REGION}${NC}"

# S3 bucket for Lambda code (unique per account)
LAMBDA_BUCKET="${PROJECT_NAME,,}-lambda-${AWS_ACCOUNT_ID}-${REGION}"

# -- Step 1: Package Lambda --
echo ""
echo -e "${YELLOW}[1/6] Packaging Lambda function...${NC}"
cd "$PROJECT_ROOT"
python scripts/package_lambda.py
echo -e "${GREEN}  Lambda packaged successfully.${NC}"

# -- Step 2: Create S3 bucket for Lambda code & upload --
echo ""
echo -e "${YELLOW}[2/6] Uploading Lambda code to S3...${NC}"

# Create bucket if it doesn't exist
if aws s3api head-bucket --bucket "$LAMBDA_BUCKET" --region "$REGION" 2>/dev/null; then
    echo "  Bucket $LAMBDA_BUCKET already exists."
else
    echo "  Creating bucket: $LAMBDA_BUCKET"
    aws s3api create-bucket \
        --bucket "$LAMBDA_BUCKET" \
        --region "$REGION" \
        2>/dev/null
fi

aws s3 cp lambda_deployment.zip "s3://${LAMBDA_BUCKET}/lambda_deployment.zip" --region "$REGION"
echo -e "${GREEN}  Lambda ZIP uploaded to s3://${LAMBDA_BUCKET}/lambda_deployment.zip${NC}"

# -- Step 3: Deploy CloudFormation Stack --
echo ""
echo -e "${YELLOW}[3/6] Deploying CloudFormation stack...${NC}"
echo "  Stack name: $STACK_NAME"
echo "  This may take 3-5 minutes..."

aws cloudformation deploy \
    --template-file "$SCRIPT_DIR/cloudformation.yaml" \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        ProjectName="$PROJECT_NAME" \
        Stage="$STAGE" \
        LambdaS3Bucket="$LAMBDA_BUCKET" \
        LambdaS3Key="lambda_deployment.zip" \
        BedrockModelId="us.amazon.nova-lite-v1:0" \
        FallbackModelId="anthropic.claude-3-haiku-20240307-v1:0" \
    --no-fail-on-empty-changeset

echo -e "${GREEN}  CloudFormation stack deployed successfully!${NC}"

# -- Step 4: Get outputs --
echo ""
echo -e "${YELLOW}[4/6] Retrieving stack outputs...${NC}"

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontUrl'].OutputValue" \
    --output text)

S3_WEBSITE_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendWebsiteUrl'].OutputValue" \
    --output text)

echo -e "  API URL:       ${GREEN}${API_URL}${NC}"
echo -e "  Frontend S3:   ${GREEN}${FRONTEND_BUCKET}${NC}"
echo -e "  CloudFront:    ${GREEN}${CLOUDFRONT_URL}${NC}"

# -- Step 5: Build frontend with API URL --
echo ""
echo -e "${YELLOW}[5/6] Building frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

# Set the API URL for the build
export VITE_API_URL="$API_URL"
npm install
npm run build

echo -e "${GREEN}  Frontend built successfully.${NC}"

# -- Step 6: Upload frontend to S3 --
echo ""
echo -e "${YELLOW}[6/6] Deploying frontend to S3...${NC}"

aws s3 sync dist/ "s3://${FRONTEND_BUCKET}/" \
    --region "$REGION" \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html"

# Upload index.html with no-cache
aws s3 cp dist/index.html "s3://${FRONTEND_BUCKET}/index.html" \
    --region "$REGION" \
    --cache-control "no-cache, no-store, must-revalidate"

echo -e "${GREEN}  Frontend deployed to S3!${NC}"

# -- Done! --
echo ""
echo -e "${CYAN}=============================================="
echo "  DEPLOYMENT COMPLETE!"
echo "==============================================${NC}"
echo ""
echo -e "  ${GREEN}Frontend (CloudFront): ${CLOUDFRONT_URL}${NC}"
echo -e "  ${GREEN}Frontend (S3):         ${S3_WEBSITE_URL}${NC}"
echo -e "  ${GREEN}API Endpoint:          ${API_URL}/api/process${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT REMINDERS:${NC}"
echo "  1. Ensure Bedrock model access is enabled in us-east-1:"
echo "     AWS Console -> Amazon Bedrock -> Model access"
echo "     -> Enable: Amazon Nova Lite + Anthropic Claude 3 Haiku (fallback)"
echo "  2. CloudFront may take 5-10 minutes to fully propagate"
echo "  3. Use the S3 website URL if CloudFront isn't ready yet"
echo ""
echo -e "${YELLOW}AWS SERVICES DEPLOYED:${NC}"
echo "  - Lambda (Python 3.12)     : Backend API"
echo "  - API Gateway (REST)       : HTTPS endpoint"
echo "  - S3                       : Frontend hosting + Lambda code"
echo "  - CloudFront               : CDN with HTTPS"
echo "  - DynamoDB                 : Response caching"
echo "  - Amazon Bedrock           : Nova Lite (primary) + Claude Haiku (fallback)"
echo ""
