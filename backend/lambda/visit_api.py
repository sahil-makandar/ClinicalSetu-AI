"""
ClinicalSetu - Visit Persistence API
Handles saving and retrieving patient visit records from DynamoDB.

Routes (dispatched by path):
  POST /api/save-visit      - Save a finalized consultation visit
  POST /api/patient-visits   - Fetch visits for a patient by phone number
"""

import json
import os
import time
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION_NAME", "us-east-1"))
VISITS_TABLE = os.environ.get("VISITS_TABLE", "clinicalsetu-visits-prod")


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return _cors(200, "")

    path = event.get("path", "")
    body = json.loads(event["body"]) if isinstance(event.get("body"), str) else event.get("body", {})

    if path.endswith("/save-visit"):
        return _save_visit(body)
    elif path.endswith("/patient-visits"):
        return _get_visits(body)
    elif path.endswith("/doctor-visits"):
        return _get_doctor_visits(body)
    else:
        return _cors(404, json.dumps({"error": "Not found"}))


def _save_visit(body):
    table = dynamodb.Table(VISITS_TABLE)

    phone = body.get("phone_number", "")
    hospital = body.get("hospital", "Unknown")
    consultation_id = body.get("consultation_id", "")
    visit_date = body.get("visit_date") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    if not phone:
        return _cors(400, json.dumps({"error": "phone_number is required"}))

    item = {
        "pk": f"HOSPITAL#{hospital}#PHONE#{phone}",
        "sk": f"VISIT#{visit_date}",
        "phone_number": phone,
        "visit_date": visit_date,
        "consultation_id": consultation_id,
        "patient_name": body.get("patient_name", ""),
        "patient_age": body.get("patient_age", 0),
        "patient_gender": body.get("patient_gender", ""),
        "patient_id": body.get("patient_id", ""),
        "doctor_name": body.get("doctor_name", ""),
        "doctor_speciality": body.get("doctor_speciality", ""),
        "hospital": hospital,
        "diagnosis": body.get("diagnosis", ""),
        "patient_summary": body.get("patient_summary", {}),
        "medications": body.get("medications", []),
        "follow_up": body.get("follow_up", ""),
        "warning_signs": body.get("warning_signs", []),
        "created_at": int(time.time()),
    }

    # Convert floats to Decimal for DynamoDB
    item = json.loads(json.dumps(item), parse_float=Decimal)
    table.put_item(Item=item)

    return _cors(200, json.dumps({"status": "saved", "consultation_id": consultation_id}))


def _get_visits(body):
    table = dynamodb.Table(VISITS_TABLE)
    phone = body.get("phone_number", "")

    if not phone:
        return _cors(400, json.dumps({"error": "phone_number is required"}))

    resp = table.query(
        IndexName="phone-index",
        KeyConditionExpression="phone_number = :ph",
        ExpressionAttributeValues={":ph": phone},
        ScanIndexForward=False,  # newest first
        Limit=20,
    )

    items = resp.get("Items", [])
    # Convert Decimal to float/int for JSON serialization
    return _cors(200, json.dumps(items, default=_decimal_default))


def _get_doctor_visits(body):
    table = dynamodb.Table(VISITS_TABLE)
    doctor_name = body.get("doctor_name", "")

    if not doctor_name:
        return _cors(400, json.dumps({"error": "doctor_name is required"}))

    resp = table.query(
        IndexName="doctor-index",
        KeyConditionExpression="doctor_name = :dn",
        ExpressionAttributeValues={":dn": doctor_name},
        ScanIndexForward=False,
        Limit=50,
    )

    items = resp.get("Items", [])
    return _cors(200, json.dumps(items, default=_decimal_default))


def _decimal_default(obj):
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _cors(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": body,
    }
