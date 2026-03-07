"""
ClinicalSetu - Bedrock Knowledge Base Setup Script
Provisions Amazon Bedrock Knowledge Base for clinical trial RAG.

Architecture:
  S3 (trial JSONs) -> Titan Embeddings v2 -> OpenSearch Serverless -> Bedrock KB
  TrialAgent -> retrieve_and_generate() API -> KB

Steps:
  1. Create S3 bucket for trial data
  2. Upload trial data to S3
  3. Create IAM role for KB
  4. Create OpenSearch Serverless collection + security policies + vector index
  5. Create Bedrock Knowledge Base pointing to AOSS collection
  6. Create S3 data source
  7. Start initial data sync

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
AOSS_COLLECTION_NAME = "clinicalsetu-trials"
AOSS_INDEX_NAME = "clinicalsetu-trials-index"

sts = boto3.client("sts", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
bedrock_agent = boto3.client("bedrock-agent", region_name=REGION)
aoss = boto3.client("opensearchserverless", region_name=REGION)

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


def create_aoss_security_policies(role_arn):
    """Create OpenSearch Serverless encryption, network, and data access policies."""

    # 1. Encryption policy (required before collection creation)
    enc_policy_name = "clinicalsetu-enc"
    try:
        aoss.create_security_policy(
            name=enc_policy_name,
            type="encryption",
            policy=json.dumps({
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{AOSS_COLLECTION_NAME}"],
                    }
                ],
                "AWSOwnedKey": True,
            }),
        )
        print(f"  Created encryption policy: {enc_policy_name}")
    except Exception as e:
        if "Conflict" in str(e):
            print(f"  Encryption policy exists: {enc_policy_name}")
        else:
            raise

    # 2. Network policy (allow public access for simplicity in hackathon)
    net_policy_name = "clinicalsetu-net"
    try:
        aoss.create_security_policy(
            name=net_policy_name,
            type="network",
            policy=json.dumps([
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{AOSS_COLLECTION_NAME}"],
                        },
                        {
                            "ResourceType": "dashboard",
                            "Resource": [f"collection/{AOSS_COLLECTION_NAME}"],
                        },
                    ],
                    "AllowFromPublic": True,
                }
            ]),
        )
        print(f"  Created network policy: {net_policy_name}")
    except Exception as e:
        if "Conflict" in str(e):
            print(f"  Network policy exists: {net_policy_name}")
        else:
            raise

    # 3. Data access policy (allow KB role + current caller to read/write)
    caller_arn = sts.get_caller_identity()["Arn"]
    data_policy_name = "clinicalsetu-data"
    try:
        aoss.create_access_policy(
            name=data_policy_name,
            type="data",
            policy=json.dumps([
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{AOSS_COLLECTION_NAME}"],
                            "Permission": [
                                "aoss:CreateCollectionItems",
                                "aoss:DeleteCollectionItems",
                                "aoss:UpdateCollectionItems",
                                "aoss:DescribeCollectionItems",
                            ],
                        },
                        {
                            "ResourceType": "index",
                            "Resource": [f"index/{AOSS_COLLECTION_NAME}/*"],
                            "Permission": [
                                "aoss:CreateIndex",
                                "aoss:DeleteIndex",
                                "aoss:UpdateIndex",
                                "aoss:DescribeIndex",
                                "aoss:ReadDocument",
                                "aoss:WriteDocument",
                            ],
                        },
                    ],
                    "Principal": [role_arn, caller_arn],
                }
            ]),
        )
        print(f"  Created data access policy: {data_policy_name}")
    except Exception as e:
        if "Conflict" in str(e):
            print(f"  Data access policy exists: {data_policy_name}")
        else:
            raise


def get_or_create_aoss_collection():
    """Create OpenSearch Serverless collection for vector storage."""
    # Check if collection already exists
    try:
        response = aoss.batch_get_collection(names=[AOSS_COLLECTION_NAME])
        details = response.get("collectionDetails", [])
        if details:
            collection = details[0]
            collection_id = collection["id"]
            collection_arn = collection["arn"]
            print(f"  Collection exists: {AOSS_COLLECTION_NAME} ({collection_id})")
            # Wait for ACTIVE status
            for _ in range(30):
                resp = aoss.batch_get_collection(ids=[collection_id])
                status = resp["collectionDetails"][0]["status"]
                if status == "ACTIVE":
                    endpoint = resp["collectionDetails"][0].get("collectionEndpoint", "")
                    return collection_arn, endpoint
                print(f"  Collection status: {status}...")
                time.sleep(10)
            endpoint = collection.get("collectionEndpoint", "")
            return collection_arn, endpoint
    except Exception:
        pass

    # Create new collection
    response = aoss.create_collection(
        name=AOSS_COLLECTION_NAME,
        type="VECTORSEARCH",
        description="ClinicalSetu clinical trial vector store for RAG",
    )
    collection_id = response["createCollectionDetail"]["id"]
    collection_arn = response["createCollectionDetail"]["arn"]
    print(f"  Created collection: {AOSS_COLLECTION_NAME} ({collection_id})")

    # Wait for collection to become ACTIVE
    endpoint = ""
    for attempt in range(60):
        resp = aoss.batch_get_collection(ids=[collection_id])
        details = resp["collectionDetails"][0]
        status = details["status"]
        if status == "ACTIVE":
            endpoint = details.get("collectionEndpoint", "")
            print(f"  Collection ACTIVE: {endpoint}")
            break
        elif status == "FAILED":
            raise Exception(f"Collection creation failed")
        if attempt % 6 == 0:
            print(f"  Collection status: {status} (waiting...)")
        time.sleep(10)

    return collection_arn, endpoint


def create_vector_index(endpoint):
    """Create the vector index in OpenSearch Serverless collection."""
    if not endpoint:
        print("  WARNING: No endpoint available, skipping index creation")
        return

    # Use opensearch-py if available, otherwise use urllib
    try:
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth

        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            REGION,
            "aoss",
            session_token=credentials.token,
        )

        host = endpoint.replace("https://", "")
        client = OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300,
        )

        # Check if index exists
        if client.indices.exists(index=AOSS_INDEX_NAME):
            print(f"  Index exists: {AOSS_INDEX_NAME}")
            return

        # Create vector index
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                }
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {
                            "engine": "faiss",
                            "name": "hnsw",
                            "space_type": "l2",
                        },
                    },
                    "text": {"type": "text"},
                    "metadata": {"type": "text"},
                }
            },
        }

        client.indices.create(index=AOSS_INDEX_NAME, body=index_body)
        print(f"  Created vector index: {AOSS_INDEX_NAME}")

        # Wait for index to propagate in AOSS before Bedrock can validate it
        print("  Waiting for index propagation in OpenSearch Serverless...")
        for wait_attempt in range(12):
            time.sleep(10)
            try:
                if client.indices.exists(index=AOSS_INDEX_NAME):
                    print(f"  Index verified after {(wait_attempt + 1) * 10}s")
                    break
            except Exception:
                pass
        else:
            print("  Index not yet verified, adding extra wait...")
            time.sleep(30)

    except ImportError:
        # Fall back to urllib-based index creation
        import urllib.request
        import urllib.error

        print("  opensearch-py not available, creating index via HTTP...")

        # Use SigV4 signing via botocore
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest

        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()

        index_body = json.dumps({
            "settings": {
                "index": {"knn": True}
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1024,
                        "method": {
                            "engine": "faiss",
                            "name": "hnsw",
                            "space_type": "l2",
                        },
                    },
                    "text": {"type": "text"},
                    "metadata": {"type": "text"},
                }
            },
        })

        url = f"{endpoint}/{AOSS_INDEX_NAME}"

        # Check if index exists
        try:
            check_req = AWSRequest(method="HEAD", url=url, headers={"Host": endpoint.replace("https://", "")})
            SigV4Auth(credentials, "aoss", REGION).add_auth(check_req)
            req = urllib.request.Request(url, method="HEAD", headers=dict(check_req.headers))
            urllib.request.urlopen(req)
            print(f"  Index exists: {AOSS_INDEX_NAME}")
            return
        except urllib.error.HTTPError as e:
            if e.code != 404:
                print(f"  Index check error: {e}")

        # Create index
        try:
            aws_req = AWSRequest(
                method="PUT",
                url=url,
                data=index_body,
                headers={
                    "Host": endpoint.replace("https://", ""),
                    "Content-Type": "application/json",
                },
            )
            SigV4Auth(credentials, "aoss", REGION).add_auth(aws_req)
            req = urllib.request.Request(
                url,
                data=index_body.encode("utf-8"),
                method="PUT",
                headers=dict(aws_req.headers),
            )
            urllib.request.urlopen(req)
            print(f"  Created vector index: {AOSS_INDEX_NAME}")

            # Wait for index to propagate
            print("  Waiting for index propagation in OpenSearch Serverless...")
            for wait_attempt in range(12):
                time.sleep(10)
                try:
                    check_req2 = AWSRequest(method="HEAD", url=url, headers={"Host": endpoint.replace("https://", "")})
                    SigV4Auth(credentials, "aoss", REGION).add_auth(check_req2)
                    req2 = urllib.request.Request(url, method="HEAD", headers=dict(check_req2.headers))
                    urllib.request.urlopen(req2)
                    print(f"  Index verified after {(wait_attempt + 1) * 10}s")
                    break
                except Exception:
                    pass
            else:
                print("  Index not yet verified, adding extra wait...")
                time.sleep(30)
        except Exception as e:
            print(f"  Index creation error (non-fatal): {e}")
            print("  Will retry KB creation with delay...")


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


def create_knowledge_base(role_arn, collection_arn):
    """Create Bedrock Knowledge Base with OpenSearch Serverless vector store."""
    existing_id = find_existing_kb()
    if existing_id:
        print(f"  KB exists: {KB_NAME} ({existing_id})")
        return existing_id

    # Retry KB creation — AOSS index may take time to become visible to Bedrock
    last_error = None
    for kb_attempt in range(5):
        try:
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
                        "collectionArn": collection_arn,
                        "vectorIndexName": AOSS_INDEX_NAME,
                        "fieldMapping": {
                            "vectorField": "embedding",
                            "textField": "text",
                            "metadataField": "metadata",
                        },
                    },
                },
            )
            last_error = None
            break
        except Exception as e:
            last_error = e
            if "no such index" in str(e) or "404" in str(e):
                wait_secs = 30 * (kb_attempt + 1)
                print(f"  Index not yet visible to Bedrock (attempt {kb_attempt + 1}/5), waiting {wait_secs}s...")
                time.sleep(wait_secs)
            else:
                raise

    if last_error:
        raise last_error

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
    print("\n[1/8] Creating S3 bucket for trial data...")
    create_trials_bucket()

    # Step 2: Upload trial data
    print("\n[2/8] Uploading trial data to S3...")
    count = upload_trial_data()
    if count == 0:
        print("  No trial data to upload. Running fetch_trials.py --local first...")
        import subprocess
        fetch_script = os.path.join(PROJECT_ROOT, "backend", "lambda", "fetch_trials.py")
        subprocess.run(["python", fetch_script, "--local"], check=True)
        count = upload_trial_data()

    # Step 3: Create IAM role
    print("\n[3/8] Setting up IAM role...")
    role_arn = get_or_create_kb_role()

    # Step 4: Create AOSS security policies
    print("\n[4/8] Creating OpenSearch Serverless security policies...")
    create_aoss_security_policies(role_arn)

    # Step 5: Create AOSS collection
    print("\n[5/8] Creating OpenSearch Serverless collection...")
    collection_arn, endpoint = get_or_create_aoss_collection()

    # Step 6: Create vector index
    print("\n[6/8] Creating vector index...")
    create_vector_index(endpoint)

    # Step 7: Create Knowledge Base
    print("\n[7/8] Creating Bedrock Knowledge Base...")
    kb_id = create_knowledge_base(role_arn, collection_arn)

    # Step 8: Create data source + sync
    print("\n[8/8] Creating S3 data source and starting sync...")
    ds_id = create_data_source(kb_id)
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
