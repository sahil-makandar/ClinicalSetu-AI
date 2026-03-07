"""
ClinicalSetu - Clinical Trial Data Fetcher
Fetches recruiting clinical trials in India from ClinicalTrials.gov v2 API.

Runs as:
  1. AWS Lambda (triggered by EventBridge daily) — uploads to S3, triggers KB sync
  2. Local script — saves to data/trials/ for development

Features:
  - Incremental sync: only fetches trials updated since last sync
  - Deduplication: skips trials already in S3 with same lastUpdateDate
  - Multiple condition queries to cover common Indian healthcare needs
  - Triggers Bedrock Knowledge Base data sync after new data

Usage:
  python backend/lambda/fetch_trials.py --test        # Fetch 1 trial, print it
  python backend/lambda/fetch_trials.py --local        # Save to data/trials/
  python backend/lambda/fetch_trials.py --local --test # Test locally

Environment variables (Lambda mode):
  TRIALS_BUCKET       - S3 bucket for trial data
  KNOWLEDGE_BASE_ID   - Bedrock Knowledge Base ID
  DATA_SOURCE_ID      - Bedrock KB data source ID
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# Conditions to search for — covers common Indian healthcare needs
SEARCH_CONDITIONS = [
    "diabetes",
    "hypertension",
    "asthma",
    "tuberculosis",
    "cancer",
    "heart failure",
    "lupus",
    "COPD",
    "migraine",
    "rheumatoid arthritis",
    "Alzheimer",
    "chronic kidney disease",
    "dengue",
    "malaria",
    "typhoid",
]

# India center point coordinates for geo filter
INDIA_LAT = 20.5937
INDIA_LON = 78.9629
INDIA_RADIUS_KM = 2000

API_BASE = "https://clinicaltrials.gov/api/v2/studies"
PAGE_SIZE = 20


def fetch_studies(condition, last_sync_date=None, page_size=PAGE_SIZE, max_pages=5):
    """Fetch recruiting studies from ClinicalTrials.gov v2 API for a condition."""
    all_studies = []
    next_page_token = None

    for page in range(max_pages):
        params = {
            "query.cond": condition,
            "filter.overallStatus": "RECRUITING",
            "filter.geo": f"distance({INDIA_LAT},{INDIA_LON},{INDIA_RADIUS_KM}km)",
            "pageSize": str(page_size),
            "format": "json",
        }

        if last_sync_date:
            params["filter.advanced"] = f"AREA[LastUpdatePostDate]RANGE[{last_sync_date},MAX]"

        if next_page_token:
            params["pageToken"] = next_page_token

        url = f"{API_BASE}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ClinicalSetu/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  API error for '{condition}': {e}")
            break

        studies = data.get("studies", [])
        if not studies:
            break

        all_studies.extend(studies)
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return all_studies


def parse_study(study):
    """Convert ClinicalTrials.gov API response to our schema."""
    proto = study.get("protocolSection", {})
    ident = proto.get("identificationModule", {})
    status = proto.get("statusModule", {})
    sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
    desc = proto.get("descriptionModule", {})
    conditions_mod = proto.get("conditionsModule", {})
    design = proto.get("designModule", {})
    eligibility = proto.get("eligibilityModule", {})
    contacts_locations = proto.get("contactsLocationsModule", {})

    nct_id = ident.get("nctId", "")
    if not nct_id:
        return None

    # Extract phase
    phases = design.get("designInfo", {}).get("allocation", "")
    phase_list = design.get("phases", [])
    phase = ", ".join(phase_list) if phase_list else "Not specified"
    if phase == "NA":
        phase = "Not Applicable"

    # Extract sponsor
    lead_sponsor = sponsor_mod.get("leadSponsor", {})
    sponsor_name = lead_sponsor.get("name", "Unknown")

    # Extract locations (India only)
    locations = []
    for loc in contacts_locations.get("locations", []):
        if loc.get("country", "").lower() == "india":
            facility = loc.get("facility", "")
            city = loc.get("city", "")
            if facility:
                locations.append(f"{facility}, {city}" if city else facility)

    # Extract contact info
    contact_info = ""
    central_contacts = contacts_locations.get("centralContacts", [])
    if central_contacts:
        c = central_contacts[0]
        name = c.get("name", "")
        email = c.get("email", "")
        contact_info = f"{name}, {email}" if email else name

    # Parse eligibility criteria text
    elig_text = eligibility.get("eligibilityCriteria", "")
    min_age = eligibility.get("minimumAge", "")
    max_age = eligibility.get("maximumAge", "")
    sex = eligibility.get("sex", "ALL")

    # Parse age values
    def parse_age(age_str):
        if not age_str:
            return None
        try:
            return int(age_str.split()[0])
        except (ValueError, IndexError):
            return None

    age_min = parse_age(min_age)
    age_max = parse_age(max_age)

    # Split eligibility into inclusion/exclusion
    inclusion_text = ""
    exclusion_list = []
    if "Exclusion Criteria:" in elig_text:
        parts = elig_text.split("Exclusion Criteria:")
        inclusion_text = parts[0].replace("Inclusion Criteria:", "").strip()
        exclusion_raw = parts[1].strip()
        exclusion_list = [
            line.strip().lstrip("0123456789.-) ").strip()
            for line in exclusion_raw.split("\n")
            if line.strip() and not line.strip().startswith("Exclusion")
        ]
        exclusion_list = [e for e in exclusion_list if len(e) > 3]
    elif "Inclusion Criteria:" in elig_text:
        inclusion_text = elig_text.replace("Inclusion Criteria:", "").strip()

    # Extract inclusion additional criteria
    inclusion_additional = [
        line.strip().lstrip("0123456789.-) ").strip()
        for line in inclusion_text.split("\n")
        if line.strip() and len(line.strip()) > 3
    ]
    inclusion_additional = [i for i in inclusion_additional if len(i) > 3][:10]

    # Get conditions
    conditions = conditions_mod.get("conditions", [])

    # Get last update date
    last_update = status.get("lastUpdatePostDateStruct", {}).get("date", "")

    return {
        "trial_id": nct_id,
        "title": ident.get("briefTitle", ident.get("officialTitle", "")),
        "phase": phase,
        "sponsor": sponsor_name,
        "status": status.get("overallStatus", "RECRUITING"),
        "conditions": conditions,
        "inclusion_criteria": {
            "age_min": age_min or 18,
            "age_max": age_max or 99,
            "gender": "All" if sex == "ALL" else sex.title(),
            "diagnosis": conditions[0] if conditions else "Not specified",
            "additional": inclusion_additional[:6],
        },
        "exclusion_criteria": exclusion_list[:8],
        "locations": locations[:5],
        "contact": contact_info,
        "summary": desc.get("briefSummary", ""),
        "last_updated": last_update,
    }


def get_last_sync_date(bucket=None, s3_client=None):
    """Read last sync timestamp from S3 or return None for first run."""
    if bucket and s3_client:
        try:
            resp = s3_client.get_object(Bucket=bucket, Key="sync_metadata.json")
            metadata = json.loads(resp["Body"].read().decode("utf-8"))
            return metadata.get("last_sync_date")
        except Exception:
            return None
    return None


def save_sync_metadata(bucket, s3_client, trial_count):
    """Update sync metadata in S3."""
    metadata = {
        "last_sync_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "last_sync_iso": datetime.now(timezone.utc).isoformat(),
        "trials_synced": trial_count,
    }
    s3_client.put_object(
        Bucket=bucket,
        Key="sync_metadata.json",
        Body=json.dumps(metadata, indent=2),
        ContentType="application/json",
    )


def fetch_all_trials(last_sync_date=None, test_mode=False):
    """Fetch trials across all conditions. Returns dict of nct_id -> trial."""
    trials = {}
    conditions = SEARCH_CONDITIONS[:1] if test_mode else SEARCH_CONDITIONS
    page_size = 1 if test_mode else PAGE_SIZE
    max_pages = 1 if test_mode else 5

    for condition in conditions:
        print(f"  Fetching: {condition}...")
        studies = fetch_studies(condition, last_sync_date, page_size, max_pages)
        for study in studies:
            parsed = parse_study(study)
            if parsed and parsed["trial_id"] not in trials:
                trials[parsed["trial_id"]] = parsed

    print(f"  Total unique trials: {len(trials)}")
    return trials


def run_local(test_mode=False):
    """Run locally — save trials to data/trials/."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    trials_dir = os.path.join(project_root, "data", "trials")
    os.makedirs(trials_dir, exist_ok=True)

    print(f"Fetching clinical trials from ClinicalTrials.gov...")
    trials = fetch_all_trials(test_mode=test_mode)

    if test_mode and trials:
        first = next(iter(trials.values()))
        print(f"\n--- Test Result ---")
        print(json.dumps(first, indent=2))
        print(f"--- API working! ---\n")

    new_count = 0
    for nct_id, trial in trials.items():
        filepath = os.path.join(trials_dir, f"{nct_id}.json")
        # Skip if file exists with same last_updated date
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if existing.get("last_updated") == trial.get("last_updated"):
                    continue
            except Exception:
                pass

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trial, f, indent=2, ensure_ascii=False)
        new_count += 1

    print(f"Saved {new_count} new/updated trials to {trials_dir}")
    print(f"Total trials in directory: {len(os.listdir(trials_dir))}")
    return trials


def lambda_handler(event=None, context=None):
    """Lambda entry point — triggered by EventBridge schedule."""
    import boto3

    bucket = os.environ.get("TRIALS_BUCKET", "")
    kb_id = os.environ.get("KNOWLEDGE_BASE_ID", "")
    ds_id = os.environ.get("DATA_SOURCE_ID", "")
    region = os.environ.get("AWS_REGION", "us-east-1")

    if not bucket:
        return {"statusCode": 400, "body": "TRIALS_BUCKET not set"}

    s3 = boto3.client("s3", region_name=region)

    # Get last sync date for incremental fetch
    last_sync = get_last_sync_date(bucket, s3)
    print(f"Last sync: {last_sync or 'FIRST RUN'}")

    # Fetch trials
    trials = fetch_all_trials(last_sync_date=last_sync)

    # Upload to S3
    new_count = 0
    for nct_id, trial in trials.items():
        key = f"trials/{nct_id}.json"

        # Check if already exists with same update date
        if last_sync:
            try:
                existing = s3.get_object(Bucket=bucket, Key=key)
                existing_data = json.loads(existing["Body"].read().decode("utf-8"))
                if existing_data.get("last_updated") == trial.get("last_updated"):
                    continue
            except s3.exceptions.NoSuchKey:
                pass
            except Exception:
                pass

        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(trial, indent=2, ensure_ascii=False),
            ContentType="application/json",
        )
        new_count += 1

    print(f"Uploaded {new_count} new/updated trials to s3://{bucket}/trials/")

    # Update sync metadata
    save_sync_metadata(bucket, s3, new_count)

    # Trigger KB data sync if new data was added
    if new_count > 0 and kb_id and ds_id:
        try:
            bedrock = boto3.client("bedrock-agent", region_name=region)
            bedrock.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
            )
            print(f"Started KB ingestion job for {kb_id}")
        except Exception as e:
            print(f"KB sync failed (non-fatal): {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "trials_fetched": len(trials),
            "trials_new_or_updated": new_count,
            "last_sync": last_sync,
        }),
    }


if __name__ == "__main__":
    test_mode = "--test" in sys.argv
    local_mode = "--local" in sys.argv

    if local_mode or not os.environ.get("TRIALS_BUCKET"):
        run_local(test_mode=test_mode)
    else:
        lambda_handler()
