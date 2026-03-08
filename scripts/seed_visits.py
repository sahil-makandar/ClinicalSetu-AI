"""
ClinicalSetu - Seed Synthetic Visit Data
Seeds DynamoDB VisitsTable with realistic synthetic consultation records.
Designed to run once during CI/CD deployment.

Usage:
  python scripts/seed_visits.py

Environment variables:
  VISITS_TABLE  - DynamoDB table name (default: clinicalsetu-visits-prod)
  AWS_REGION    - AWS region (default: us-east-1)
"""

import json
import os
import time
import boto3
from decimal import Decimal

VISITS_TABLE = os.environ.get("VISITS_TABLE", "clinicalsetu-visits-prod")
REGION = os.environ.get("AWS_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(VISITS_TABLE)

SEED_VISITS = [
    # --- Visit 1: Dr. Rojina Mallick sees Rajesh Kumar Sharma (Diabetes) ---
    {
        "phone_number": "+919876543210",
        "hospital": "City General Hospital, Kolkata, West Bengal",
        "consultation_id": "CONSULT-SEED-001",
        "visit_date": "2025-12-15T10:30:00Z",
        "patient_name": "Rajesh Kumar Sharma",
        "patient_age": 55,
        "patient_gender": "Male",
        "patient_id": "SYN-PT-10001",
        "doctor_name": "Dr. Rojina Mallick",
        "doctor_speciality": "Internal Medicine",
        "diagnosis": "Type 2 Diabetes Mellitus with Peripheral Neuropathy",
        "patient_summary": {
            "greeting": "Dear Rajesh,",
            "visit_summary": "You visited Dr. Rojina Mallick on 15th December 2025 for your diabetes follow-up. Your blood sugar levels have been higher than target, and you reported tingling in your feet.",
            "what_the_doctor_found": "Your blood pressure was slightly elevated at 138/86 mmHg. Your HbA1c is 8.2% which is above the target of 7%. There is reduced sensation in both feet suggesting early diabetic neuropathy.",
            "your_diagnosis": "Type 2 Diabetes Mellitus with early peripheral neuropathy and suboptimal sugar control.",
            "your_treatment_plan": {
                "medications": [
                    {"name": "Glycomet GP 3", "what_its_for": "To better control your blood sugar levels", "how_to_take": "One tablet after breakfast daily", "important_notes": "Take with meals to avoid stomach upset"},
                    {"name": "Pregabalin 75mg", "what_its_for": "To relieve the tingling and numbness in your feet", "how_to_take": "One tablet at bedtime", "important_notes": "May cause mild drowsiness initially"},
                    {"name": "Telmisartan 40mg", "what_its_for": "To control blood pressure", "how_to_take": "One tablet in the morning", "important_notes": "Continue as before"}
                ],
                "lifestyle_advice": [
                    "Walk for at least 30 minutes daily",
                    "Follow a diabetic diet — avoid sweets, white rice, and fried foods",
                    "Check your feet daily for any cuts or sores",
                    "Monitor fasting blood sugar at home twice a week"
                ],
                "tests_ordered": [
                    {"test_name": "Comprehensive Metabolic Panel", "why_needed": "To check kidney and liver function"},
                    {"test_name": "Lipid Profile", "why_needed": "To assess cholesterol levels"},
                    {"test_name": "Urine Microalbumin", "why_needed": "Early kidney damage screening"},
                    {"test_name": "HbA1c (repeat in 3 months)", "why_needed": "To track long-term sugar control"}
                ]
            },
            "follow_up": {
                "next_appointment": "6 weeks from now with Dr. Rojina Mallick",
                "what_to_bring": ["All blood test reports", "Home blood sugar readings diary", "List of all current medications"]
            },
            "warning_signs": [
                "Sudden vision changes or blurring",
                "Chest pain or difficulty breathing",
                "Severe numbness or weakness in legs",
                "Any non-healing wound on feet"
            ],
            "questions_to_ask": [],
            "disclaimer": "This summary is AI-generated for informational purposes. Always follow your doctor's direct advice."
        },
        "medications": [
            {"name": "Glycomet GP 3", "how": "One tablet after breakfast daily"},
            {"name": "Pregabalin 75mg", "how": "One tablet at bedtime"},
            {"name": "Telmisartan 40mg", "how": "One tablet in the morning"}
        ],
        "follow_up": "6 weeks from now with Dr. Rojina Mallick",
        "warning_signs": ["Sudden vision changes", "Chest pain", "Severe numbness in legs", "Non-healing foot wounds"]
    },
    # --- Visit 2: Dr. Sahil Makandar sees Rajesh (second opinion / General checkup) ---
    {
        "phone_number": "+919876543210",
        "hospital": "Apollo Clinic, Mapusa, Goa",
        "consultation_id": "CONSULT-SEED-002",
        "visit_date": "2026-01-22T14:15:00Z",
        "patient_name": "Rajesh Kumar Sharma",
        "patient_age": 55,
        "patient_gender": "Male",
        "patient_id": "SYN-PT-10001",
        "doctor_name": "Dr. Sahil Makandar",
        "doctor_speciality": "General Medicine",
        "diagnosis": "Chronic Gastritis with Vitamin D Deficiency",
        "patient_summary": {
            "greeting": "Dear Rajesh,",
            "visit_summary": "You visited Dr. Sahil Makandar on 22nd January 2026 with complaints of persistent acidity and fatigue. You mentioned feeling tired despite adequate sleep and having upper abdominal discomfort after meals for the past 3 weeks.",
            "what_the_doctor_found": "Your abdomen was mildly tender in the upper region. Blood tests revealed very low Vitamin D levels (12 ng/mL, normal >30). Your diabetes is currently managed but needs monitoring.",
            "your_diagnosis": "Chronic gastritis (stomach inflammation) and severe Vitamin D deficiency contributing to your fatigue.",
            "your_treatment_plan": {
                "medications": [
                    {"name": "Pantoprazole 40mg", "what_its_for": "To reduce stomach acid and heal gastritis", "how_to_take": "One tablet before breakfast on empty stomach", "important_notes": "Take 30 minutes before eating"},
                    {"name": "Vitamin D3 60000 IU", "what_its_for": "To correct your severe Vitamin D deficiency", "how_to_take": "One sachet weekly for 8 weeks", "important_notes": "Take with a fatty meal for better absorption"},
                    {"name": "Domperidone 10mg", "what_its_for": "To reduce nausea and improve digestion", "how_to_take": "One tablet before lunch and dinner", "important_notes": "Take for 2 weeks only"}
                ],
                "lifestyle_advice": [
                    "Eat smaller, more frequent meals",
                    "Avoid spicy, oily, and fried foods",
                    "Get 15 minutes of morning sunlight daily for natural Vitamin D",
                    "Avoid lying down immediately after eating"
                ],
                "tests_ordered": [
                    {"test_name": "H. Pylori Stool Antigen", "why_needed": "To rule out bacterial infection causing gastritis"},
                    {"test_name": "Vitamin D (repeat after 8 weeks)", "why_needed": "To check if levels have improved"}
                ]
            },
            "follow_up": {
                "next_appointment": "3 weeks with reports",
                "what_to_bring": ["H. Pylori test result", "Current medication list"]
            },
            "warning_signs": [
                "Blood in vomit or black colored stools",
                "Severe abdominal pain",
                "Persistent vomiting",
                "Unexplained weight loss"
            ],
            "questions_to_ask": [],
            "disclaimer": "This summary is AI-generated for informational purposes. Always follow your doctor's direct advice."
        },
        "medications": [
            {"name": "Pantoprazole 40mg", "how": "One tablet before breakfast"},
            {"name": "Vitamin D3 60000 IU", "how": "One sachet weekly for 8 weeks"},
            {"name": "Domperidone 10mg", "how": "Before lunch and dinner for 2 weeks"}
        ],
        "follow_up": "3 weeks with reports - Dr. Sahil Makandar",
        "warning_signs": ["Blood in vomit or black stools", "Severe abdominal pain", "Persistent vomiting"]
    },
    # --- Visit 3: Dr. Rojina Mallick sees Rajesh again (follow-up) ---
    {
        "phone_number": "+919876543210",
        "hospital": "City General Hospital, Kolkata, West Bengal",
        "consultation_id": "CONSULT-SEED-003",
        "visit_date": "2026-02-28T11:00:00Z",
        "patient_name": "Rajesh Kumar Sharma",
        "patient_age": 55,
        "patient_gender": "Male",
        "patient_id": "SYN-PT-10001",
        "doctor_name": "Dr. Rojina Mallick",
        "doctor_speciality": "Internal Medicine",
        "diagnosis": "Type 2 Diabetes Mellitus - Improved Control, Hypertension Stage 1",
        "patient_summary": {
            "greeting": "Dear Rajesh,",
            "visit_summary": "You visited Dr. Rojina Mallick on 28th February 2026 for your diabetes follow-up. Good news — your sugar control has improved! Your HbA1c has come down from 8.2% to 7.4%. The tingling in your feet has also reduced.",
            "what_the_doctor_found": "Blood pressure 134/82 mmHg — slightly better. Weight reduced by 2 kg to 80 kg. Foot sensation has improved with treatment. Kidney function tests are normal. Cholesterol is borderline high.",
            "your_diagnosis": "Type 2 Diabetes with improving control. Borderline high cholesterol. Blood pressure still needs monitoring.",
            "your_treatment_plan": {
                "medications": [
                    {"name": "Glycomet GP 3", "what_its_for": "Continue for diabetes control", "how_to_take": "One tablet after breakfast daily", "important_notes": "Continue same dose — working well"},
                    {"name": "Pregabalin 75mg", "what_its_for": "Continue for neuropathy", "how_to_take": "One tablet at bedtime", "important_notes": "Can reduce to alternate days if symptoms improve further"},
                    {"name": "Telmisartan 40mg", "what_its_for": "Blood pressure control", "how_to_take": "One tablet in the morning", "important_notes": "Continue as before"},
                    {"name": "Rosuvastatin 10mg", "what_its_for": "To lower cholesterol and protect heart", "how_to_take": "One tablet at bedtime", "important_notes": "Newly added — take regularly"}
                ],
                "lifestyle_advice": [
                    "Continue daily walking — increase to 45 minutes",
                    "Great progress on weight loss — keep going!",
                    "Add more fiber to diet — oats, dal, green vegetables",
                    "Limit salt intake to help blood pressure"
                ],
                "tests_ordered": [
                    {"test_name": "HbA1c (repeat in 3 months)", "why_needed": "To track continued improvement"},
                    {"test_name": "Lipid Profile (after 3 months on statin)", "why_needed": "To check cholesterol response to medication"}
                ]
            },
            "follow_up": {
                "next_appointment": "3 months with Dr. Rojina Mallick",
                "what_to_bring": ["HbA1c report", "Lipid profile report", "Blood sugar diary"]
            },
            "warning_signs": [
                "Any muscle pain or weakness (report immediately — may be statin side effect)",
                "Blood sugar below 70 mg/dL (signs of hypoglycemia)",
                "Return of severe tingling or numbness"
            ],
            "questions_to_ask": [],
            "disclaimer": "This summary is AI-generated for informational purposes. Always follow your doctor's direct advice."
        },
        "medications": [
            {"name": "Glycomet GP 3", "how": "One tablet after breakfast daily"},
            {"name": "Pregabalin 75mg", "how": "One tablet at bedtime"},
            {"name": "Telmisartan 40mg", "how": "One tablet in the morning"},
            {"name": "Rosuvastatin 10mg", "how": "One tablet at bedtime"}
        ],
        "follow_up": "3 months with Dr. Rojina Mallick",
        "warning_signs": ["Muscle pain/weakness", "Blood sugar below 70", "Return of severe tingling"]
    },
    # --- Visit 4: Dr. Rojina Mallick sees Sanjay Gupta (Migraine) ---
    {
        "phone_number": "+919876500001",
        "hospital": "City General Hospital, Kolkata, West Bengal",
        "consultation_id": "CONSULT-SEED-004",
        "visit_date": "2026-01-10T09:45:00Z",
        "patient_name": "Sanjay Gupta",
        "patient_age": 48,
        "patient_gender": "Male",
        "patient_id": "SYN-PT-10005",
        "doctor_name": "Dr. Rojina Mallick",
        "doctor_speciality": "Internal Medicine",
        "diagnosis": "Migraine without Aura, Stage 1 Hypertension",
        "patient_summary": {
            "greeting": "Dear Sanjay,",
            "visit_summary": "You visited Dr. Rojina Mallick on 10th January 2026 with a severe right-sided throbbing headache for 2 days, along with nausea and light sensitivity. This was triggered by work stress and skipping meals.",
            "what_the_doctor_found": "Your blood pressure was elevated at 148/94 mmHg. Neurological examination was completely normal — no concerning signs. This appears to be a migraine episode, and your blood pressure needs treatment.",
            "your_diagnosis": "Migraine without aura (recurring) and newly detected Stage 1 Hypertension.",
            "your_treatment_plan": {
                "medications": [
                    {"name": "Sumatriptan 50mg", "what_its_for": "To stop the current migraine attack", "how_to_take": "One tablet now, can repeat after 2 hours if needed", "important_notes": "Maximum 2 tablets in 24 hours"},
                    {"name": "Domperidone 10mg", "what_its_for": "To control nausea", "how_to_take": "One tablet when feeling nauseous", "important_notes": "Take before meals"},
                    {"name": "Propranolol 40mg", "what_its_for": "To prevent future migraines and control blood pressure", "how_to_take": "One tablet twice daily", "important_notes": "Do not stop suddenly — taper if needed"}
                ],
                "lifestyle_advice": [
                    "Never skip meals — eat at regular times",
                    "Practice stress management — deep breathing, short breaks",
                    "Sleep 7-8 hours regularly",
                    "Exercise for 30 minutes, 5 days a week",
                    "Reduce caffeine and screen time before bed"
                ],
                "tests_ordered": [
                    {"test_name": "Fasting Lipid Profile", "why_needed": "Heart risk assessment given age and hypertension"},
                    {"test_name": "Fasting Blood Sugar", "why_needed": "Screening for diabetes given family history"}
                ]
            },
            "follow_up": {
                "next_appointment": "2 weeks with Dr. Rojina Mallick",
                "what_to_bring": ["Blood test reports", "Blood pressure readings (check 3 times this week)", "Headache diary"]
            },
            "warning_signs": [
                "Sudden 'worst headache of your life'",
                "Weakness or numbness on one side",
                "Difficulty speaking or vision loss",
                "Headache with high fever and stiff neck"
            ],
            "questions_to_ask": [],
            "disclaimer": "This summary is AI-generated for informational purposes. Always follow your doctor's direct advice."
        },
        "medications": [
            {"name": "Sumatriptan 50mg", "how": "As needed for migraine attacks"},
            {"name": "Propranolol 40mg", "how": "One tablet twice daily"},
            {"name": "Domperidone 10mg", "how": "As needed for nausea"}
        ],
        "follow_up": "2 weeks with Dr. Rojina Mallick",
        "warning_signs": ["Worst headache of life", "One-sided weakness", "Vision loss", "Fever with stiff neck"]
    },
    # --- Visit 5: Dr. Sahil Makandar sees Priya Venkatesh (Lupus) ---
    {
        "phone_number": "+919876500002",
        "hospital": "Apollo Clinic, Mapusa, Goa",
        "consultation_id": "CONSULT-SEED-005",
        "visit_date": "2026-02-05T16:30:00Z",
        "patient_name": "Priya Venkatesh",
        "patient_age": 34,
        "patient_gender": "Female",
        "patient_id": "SYN-PT-10002",
        "doctor_name": "Dr. Sahil Makandar",
        "doctor_speciality": "General Medicine",
        "diagnosis": "Suspected Systemic Lupus Erythematosus (SLE)",
        "patient_summary": {
            "greeting": "Dear Priya,",
            "visit_summary": "You visited Dr. Sahil Makandar on 5th February 2026 with fatigue, joint pain in both hands for 3 months, and a butterfly-shaped rash on your cheeks. The doctor suspects an autoimmune condition called Lupus.",
            "what_the_doctor_found": "Butterfly rash on both cheeks, mild swelling of finger joints. Otherwise, heart and lungs are normal. Several blood tests have been ordered to confirm the diagnosis.",
            "your_diagnosis": "Suspected Systemic Lupus Erythematosus (SLE) — an autoimmune condition where the body's immune system attacks its own tissues.",
            "your_treatment_plan": {
                "medications": [
                    {"name": "Hydroxychloroquine 200mg", "what_its_for": "To control lupus activity and protect joints", "how_to_take": "One tablet twice daily with meals", "important_notes": "This is a long-term medication. Annual eye check-up needed."}
                ],
                "lifestyle_advice": [
                    "Apply SPF 50+ sunscreen every day, even on cloudy days",
                    "Avoid prolonged sun exposure — wear protective clothing",
                    "Get adequate rest — fatigue is common with lupus",
                    "Gentle exercise like swimming or yoga is beneficial"
                ],
                "tests_ordered": [
                    {"test_name": "ANA (Anti-Nuclear Antibody)", "why_needed": "Primary screening test for lupus"},
                    {"test_name": "Anti-dsDNA Antibodies", "why_needed": "Specific test for lupus"},
                    {"test_name": "Complement Levels C3, C4", "why_needed": "To check immune system activity"},
                    {"test_name": "CBC with Differential", "why_needed": "Check for blood cell abnormalities"},
                    {"test_name": "Urinalysis with Microscopy", "why_needed": "Check if kidneys are affected"}
                ]
            },
            "follow_up": {
                "next_appointment": "2 weeks with all reports",
                "what_to_bring": ["All blood test reports", "Urine test report", "Photos of rash if it changes"]
            },
            "warning_signs": [
                "High fever or severe fatigue",
                "Swelling of face, legs, or decreased urine",
                "Chest pain or difficulty breathing",
                "Worsening rash or new skin lesions"
            ],
            "questions_to_ask": [],
            "disclaimer": "This summary is AI-generated for informational purposes. Always follow your doctor's direct advice."
        },
        "medications": [
            {"name": "Hydroxychloroquine 200mg", "how": "One tablet twice daily with meals"}
        ],
        "follow_up": "2 weeks with reports - Dr. Sahil Makandar",
        "warning_signs": ["High fever", "Swelling of face/legs", "Chest pain", "Worsening rash"]
    },
    # --- Visit 6: Dr. Sahil Makandar sees Lakshmi Devi (Cognitive decline) ---
    {
        "phone_number": "+919876500003",
        "hospital": "Apollo Clinic, Mapusa, Goa",
        "consultation_id": "CONSULT-SEED-006",
        "visit_date": "2026-02-18T11:00:00Z",
        "patient_name": "Lakshmi Devi Agarwal",
        "patient_age": 70,
        "patient_gender": "Female",
        "patient_id": "SYN-PT-10006",
        "doctor_name": "Dr. Sahil Makandar",
        "doctor_speciality": "General Medicine",
        "diagnosis": "Early Alzheimer's Dementia (suspected)",
        "patient_summary": {
            "greeting": "Dear Lakshmi ji and family,",
            "visit_summary": "Lakshmi ji was brought by her son on 18th February 2026 for progressive memory problems over the past year. She has been forgetting recent conversations, misplacing things, and got lost in her neighborhood.",
            "what_the_doctor_found": "She is oriented to who she is but confused about dates and places. Memory test score was 20/30 indicating mild-to-moderate cognitive impairment. No weakness or walking problems.",
            "your_diagnosis": "Suspected early Alzheimer's dementia. Further tests and specialist evaluation needed to confirm.",
            "your_treatment_plan": {
                "medications": [
                    {"name": "Donepezil 5mg", "what_its_for": "To help improve memory and thinking ability", "how_to_take": "One tablet at bedtime", "important_notes": "May cause mild nausea initially — will improve in a few days"}
                ],
                "lifestyle_advice": [
                    "Keep her mentally active — puzzles, reading, conversations",
                    "Maintain a fixed daily routine",
                    "Ensure safety at home — remove trip hazards, keep doors locked",
                    "Encourage social interaction",
                    "Regular light exercise — morning walks with supervision"
                ],
                "tests_ordered": [
                    {"test_name": "MRI Brain with Volumetric Analysis", "why_needed": "To look for brain changes causing memory loss"},
                    {"test_name": "Vitamin B12 and Folate", "why_needed": "Deficiency can cause reversible memory problems"},
                    {"test_name": "Thyroid Function Tests", "why_needed": "Thyroid problems can affect memory"},
                    {"test_name": "Complete Blood Count", "why_needed": "General health check"}
                ]
            },
            "follow_up": {
                "next_appointment": "4 weeks with MRI and blood reports",
                "what_to_bring": ["MRI report and CD", "All blood reports", "List of daily difficulties observed by family"]
            },
            "warning_signs": [
                "Sudden confusion or major personality change",
                "Falls or difficulty walking",
                "Inability to recognize family members",
                "Wandering or getting lost repeatedly"
            ],
            "questions_to_ask": [],
            "disclaimer": "This summary is AI-generated for informational purposes. Always follow your doctor's direct advice."
        },
        "medications": [
            {"name": "Donepezil 5mg", "how": "One tablet at bedtime"}
        ],
        "follow_up": "4 weeks with reports - Dr. Sahil Makandar, Neurology referral pending",
        "warning_signs": ["Sudden confusion", "Falls or walking difficulty", "Cannot recognize family", "Wandering/getting lost"]
    },
]


def seed():
    """Insert seed visits into DynamoDB, skipping if already seeded."""
    # Check if already seeded by looking for first record
    try:
        resp = table.get_item(
            Key={
                "pk": f"HOSPITAL#{SEED_VISITS[0]['hospital']}#PHONE#{SEED_VISITS[0]['phone_number']}",
                "sk": f"VISIT#{SEED_VISITS[0]['visit_date']}"
            }
        )
        if resp.get("Item"):
            print("[Seed] Data already exists — skipping.")
            return
    except Exception:
        pass

    for visit in SEED_VISITS:
        phone = visit["phone_number"]
        hospital = visit["hospital"]
        visit_date = visit["visit_date"]

        item = {
            "pk": f"HOSPITAL#{hospital}#PHONE#{phone}",
            "sk": f"VISIT#{visit_date}",
            "phone_number": phone,
            "visit_date": visit_date,
            "consultation_id": visit["consultation_id"],
            "patient_name": visit["patient_name"],
            "patient_age": visit["patient_age"],
            "patient_gender": visit["patient_gender"],
            "patient_id": visit["patient_id"],
            "doctor_name": visit["doctor_name"],
            "doctor_speciality": visit["doctor_speciality"],
            "hospital": hospital,
            "diagnosis": visit["diagnosis"],
            "patient_summary": visit["patient_summary"],
            "medications": visit["medications"],
            "follow_up": visit["follow_up"],
            "warning_signs": visit["warning_signs"],
            "created_at": int(time.time()),
        }

        item = json.loads(json.dumps(item), parse_float=Decimal)
        table.put_item(Item=item)
        print(f"[Seed] Inserted: {visit['consultation_id']} - {visit['patient_name']} ({visit['doctor_name']})")

    print(f"[Seed] Done — {len(SEED_VISITS)} visits seeded.")


if __name__ == "__main__":
    seed()
