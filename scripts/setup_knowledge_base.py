"""
ClinicalSetu - Bedrock Knowledge Base Setup Script
Provisions Amazon Bedrock Knowledge Base for clinical trial RAG.

Architecture:
  S3 (trial JSONs) -> Titan Embeddings v2 -> OpenSearch Serverless -> Bedrock KB
  TrialAgent -> retrieve_and_generate() API -> KB

Prerequisites:
  - AWS CLI configured with credentials
  - Region: us-east-1
  - Trial data in data/trials/ (run fetch_trials.py --local first)

Usage:
  python scripts/setup_knowledge_base.py

Outputs:
  KNOWLEDGE_BASE_ID=...
  TRIALS_BUCKET=...
  DATA_SOURCE_ID=...
"""

import boto3
import json
import time
import os
import glob

REGION = os.environ.get("AWS_REGION", "us-east-1")
KB_NAME = "ClinicalSetu-TrialKB"
KB_DESCRIPTION = "Clinical trial data for patient-trial matching RAG"
EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
EMBEDDING_MODEL_ARN = f"arn:aws:bedrock:{REGION}::foundation-model/{EMBEDDING_MODEL}"

sts = boto3.client("sts", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
bedrock_agent = boto3.client("bedrock-agent", region_name=REGION)

ACCOUNT_ID = sts.get_caller_identity()["Account"]
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRIALS_BUCKET = f"clinicalsetu-trials-{ACCOUNT_ID}-{REGION}"

print(f"Account:  {ACCOUNT_ID}")
print(f"Region:   {REGION}")
print(f"Bucket:   {TRIALS_BUCKET}")
print("=" * 60)


def create_trials_bucket():
    """Create S3 bucket for trial data."""
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=TRIALS_BUCKET)
        else:
            s3.create_bucket(
                Bucket=TRIALS_BUCKET,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        print(f"  Created bucket: {TRIALS_BUCKET}")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"  Bucket exists: {TRIALS_BUCKET}")
    except Exception as e:
        if "BucketAlreadyOwnedByYou" in str(e) or "BucketAlreadyExists" in str(e):
            print(f"  Bucket exists: {TRIALS_BUCKET}")
        else:
            raise


def upload_trial_data():
    """Upload trial JSON files from data/trials/ to S3."""
    trials_dir = os.path.join(PROJECT_ROOT, "data", "trials")
    if not os.path.exists(trials_dir):
        print(f"  WARNING: {trials_dir} not found. Run fetch_trials.py --local first.")
        return 0

    files = glob.glob(os.path.join(trials_dir, "*.json"))
    if not files:
        print(f"  WARNING: No trial files found in {trials_dir}")
        return 0

    count = 0
    for filepath in files:
        filename = os.path.basename(filepath)
        key = f"trials/{filename}"
        s3.upload_file(filepath, TRIALS_BUCKET, key)
        count += 1

    print(f"  Uploaded {count} trial files to s3://{TRIALS_BUCKET}/trials/")
    return count


def get_or_create_kb_role():
    """Create IAM role for Bedrock Knowledge Base."""
    role_name = "ClinicalSetu-KnowledgeBaseRole"

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {"aws:SourceAccount": ACCOUNT_ID},
                },
            }
        ],
    }

    try:
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="ClinicalSetu Knowledge Base execution role",
        )
        role_arn = response["Role"]["Arn"]
        print(f"  Created role: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
        print(f"  Role exists: {role_name}")

    # Permissions: S3 read + Bedrock embeddings + OpenSearch Serverless
    permission_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": [
                    f"arn:aws:s3:::{TRIALS_BUCKET}",
                    f"arn:aws:s3:::{TRIALS_BUCKET}/*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": [EMBEDDING_MODEL_ARN],
            },
            {
                "Effect": "Allow",
                "Action": ["aoss:APIAccessAll"],
                "Resource": [f"arn:aws:aoss:{REGION}:{ACCOUNT_ID}:collection/*"],
            },
        ],
    }

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="ClinicalSetuKBPolicy",
        PolicyDocument=json.dumps(permission_policy),
    )

    time.sleep(10)  # Wait for IAM propagation
    return role_arn


def find_existing_kb():
    """Check if Knowledge Base already exists."""
    try:
        paginator = bedrock_agent.get_paginator("list_knowledge_bases")
        for page in paginator.paginate():
            for kb in page.get("knowledgeBaseSummaries", []):
                if kb["name"] == KB_NAME:
                    return kb["knowledgeBaseId"]
    except Exception:
        pass
    return None


def create_knowledge_base(role_arn):
    """Create Bedrock Knowledge Base with OpenSearch Serverless vector store."""
    existing_id = find_existing_kb()
    if existing_id:
        print(f"  KB exists: {KB_NAME} ({existing_id})")
        return existing_id

    response = bedrock_agent.create_knowledge_base(
        name=KB_NAME,
        description=KB_DESCRIPTION,
        roleArn=role_arn,
        knowledgeBaseConfiguration={
            "type": "VECTOR",
            "vectorKnowledgeBaseConfiguration": {
                "embeddingModelArn": EMBEDDING_MODEL_ARN,
                "embeddingModelConfiguration": {
                    "bedrockEmbeddingModelConfiguration": {
                        "dimensions": 1024,
                    }
                },
            },
        },
        storageConfiguration={
            "type": "OPENSEARCH_SERVERLESS",
            "opensearchServerlessConfiguration": {
                "collectionArn": "auto",
                "vectorIndexName": "clinicalsetu-trials",
                "fieldMapping": {
                    "vectorField": "embedding",
                    "textField": "text",
                    "metadataField": "metadata",
                },
            },
        },
    )

    kb_id = response["knowledgeBase"]["knowledgeBaseId"]
    print(f"  Created KB: {KB_NAME} ({kb_id})")

    # Wait for KB to be active
    for attempt in range(30):
        kb = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
        status = kb["knowledgeBase"]["status"]
        if status == "ACTIVE":
            print(f"  KB status: ACTIVE")
            return kb_id
        elif status == "FAILED":
            failure = kb["knowledgeBase"].get("failureReasons", [])
            print(f"  KB FAILED: {failure}")
            raise Exception(f"Knowledge Base creation failed: {failure}")
        print(f"  KB status: {status} (waiting...)")
        time.sleep(10)

    raise Exception("KB creation timed out")


def create_data_source(kb_id):
    """Create S3 data source for the Knowledge Base."""
    # Check for existing data source
    try:
        existing = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
        for ds in existing.get("dataSourceSummaries", []):
            if ds["name"] == "ClinicalTrials-S3":
                print(f"  Data source exists: {ds['dataSourceId']}")
                return ds["dataSourceId"]
    except Exception:
        pass

    response = bedrock_agent.create_data_source(
        knowledgeBaseId=kb_id,
        name="ClinicalTrials-S3",
        description="Clinical trial data from ClinicalTrials.gov",
        dataSourceConfiguration={
            "type": "S3",
            "s3Configuration": {
                "bucketArn": f"arn:aws:s3:::{TRIALS_BUCKET}",
                "inclusionPrefixes": ["trials/"],
            },
        },
        vectorIngestionConfiguration={
            "chunkingConfiguration": {
                "chunkingStrategy": "FIXED_SIZE",
                "fixedSizeChunkingConfiguration": {
                    "maxTokens": 300,
                    "overlapPercentage": 10,
                },
            }
        },
    )

    ds_id = response["dataSource"]["dataSourceId"]
    print(f"  Created data source: {ds_id}")
    return ds_id


def start_sync(kb_id, ds_id):
    """Start data ingestion job."""
    try:
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
        )
        job_id = response["ingestionJob"]["ingestionJobId"]
        print(f"  Started ingestion job: {job_id}")

        # Wait for initial sync to complete (up to 5 min)
        for attempt in range(30):
            job = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
                ingestionJobId=job_id,
            )
            status = job["ingestionJob"]["status"]
            if status == "COMPLETE":
                stats = job["ingestionJob"].get("statistics", {})
                print(f"  Ingestion complete: {stats}")
                return True
            elif status == "FAILED":
                reasons = job["ingestionJob"].get("failureReasons", [])
                print(f"  Ingestion FAILED: {reasons}")
                return False
            print(f"  Ingestion status: {status}...")
            time.sleep(10)

        print("  Ingestion still running (continuing without waiting)")
        return True
    except Exception as e:
        print(f"  Sync error: {e}")
        return False


def main():
    print("\nClinicalSetu - Knowledge Base Setup")
    print("=" * 60)

    # Step 1: Create S3 bucket
    print("\n[1/6] Creating S3 bucket for trial data...")
    create_trials_bucket()

    # Step 2: Upload trial data
    print("\n[2/6] Uploading trial data to S3...")
    count = upload_trial_data()
    if count == 0:
        print("  No trial data to upload. Running fetch_trials.py --local first...")
        import subprocess
        fetch_script = os.path.join(PROJECT_ROOT, "backend", "lambda", "fetch_trials.py")
        subprocess.run(["python", fetch_script, "--local"], check=True)
        count = upload_trial_data()

    # Step 3: Create IAM role
    print("\n[3/6] Setting up IAM role...")
    role_arn = get_or_create_kb_role()

    # Step 4: Create Knowledge Base
    print("\n[4/6] Creating Bedrock Knowledge Base...")
    kb_id = create_knowledge_base(role_arn)

    # Step 5: Create data source
    print("\n[5/6] Creating S3 data source...")
    ds_id = create_data_source(kb_id)

    # Step 6: Start initial sync
    print("\n[6/6] Starting initial data sync...")
    start_sync(kb_id, ds_id)

    # Output
    print("\n" + "=" * 60)
    print("KNOWLEDGE BASE SETUP COMPLETE")
    print("=" * 60)
    print(f"\nKNOWLEDGE_BASE_ID={kb_id}")
    print(f"TRIALS_BUCKET={TRIALS_BUCKET}")
    print(f"DATA_SOURCE_ID={ds_id}")
    print(f"\nSet these on your Tool Executor Lambda:")
    print(f"  KNOWLEDGE_BASE_ID={kb_id}")
    print(f"  DATA_SOURCE_ID={ds_id}")
    print(f"  TRIALS_BUCKET={TRIALS_BUCKET}")
    print(f"\nArchitecture:")
    print(f"  EventBridge (daily) -> Trial Fetcher Lambda -> S3 -> KB -> TrialAgent RAG")


if __name__ == "__main__":
    main()
