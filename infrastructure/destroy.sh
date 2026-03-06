#!/bin/bash
# ============================================================
# ClinicalSetu - Teardown Script
# Deletes all resources created by deploy.sh
# ============================================================
# Usage: ./infrastructure/destroy.sh
# ============================================================

set -e

STACK_NAME="ClinicalSetu-Stack"
REGION="us-east-1"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${RED}"
echo "=============================================="
echo "  ClinicalSetu - TEARDOWN"
echo "=============================================="
echo -e "${NC}"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region "$REGION")
LAMBDA_BUCKET="clinicalsetu-lambda-${AWS_ACCOUNT_ID}-${REGION}"

echo -e "${YELLOW}This will DELETE all ClinicalSetu resources:${NC}"
echo "  - CloudFormation stack: $STACK_NAME"
echo "  - Lambda deployment bucket: $LAMBDA_BUCKET"
echo "  - All associated resources (Lambda, API Gateway, S3, CloudFront, IAM)"
echo ""
read -p "Are you sure? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Get the frontend bucket name before deleting the stack
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text 2>/dev/null || echo "")

# Empty S3 buckets (CloudFormation can't delete non-empty buckets)
if [ -n "$FRONTEND_BUCKET" ] && [ "$FRONTEND_BUCKET" != "None" ]; then
    echo -e "${YELLOW}Emptying frontend bucket: ${FRONTEND_BUCKET}${NC}"
    aws s3 rm "s3://${FRONTEND_BUCKET}" --recursive --region "$REGION" 2>/dev/null || true
fi

echo -e "${YELLOW}Emptying Lambda bucket: ${LAMBDA_BUCKET}${NC}"
aws s3 rm "s3://${LAMBDA_BUCKET}" --recursive --region "$REGION" 2>/dev/null || true

# Delete CloudFormation stack
echo -e "${YELLOW}Deleting CloudFormation stack: ${STACK_NAME}${NC}"
aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
echo "Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
echo -e "${GREEN}Stack deleted.${NC}"

# Delete Lambda code bucket
echo -e "${YELLOW}Deleting Lambda bucket: ${LAMBDA_BUCKET}${NC}"
aws s3api delete-bucket --bucket "$LAMBDA_BUCKET" --region "$REGION" 2>/dev/null || true

echo ""
echo -e "${GREEN}=============================================="
echo "  All ClinicalSetu resources have been deleted."
echo "==============================================${NC}"
