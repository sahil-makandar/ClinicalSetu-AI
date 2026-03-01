import type { Consultation } from '../types';

export const sampleConsultations: Consultation[] = [
  {
    id: "CONSULT-001",
    patient: { name: "Rajesh Kumar Sharma", age: 55, gender: "Male", patient_id: "SYN-PT-10001" },
    doctor: { name: "Dr. Ananya Deshmukh", speciality: "Internal Medicine", hospital: "City General Hospital, Pune" },
    consultation_text: "Patient Rajesh Kumar Sharma, 55-year-old male, comes for a follow-up visit for his diabetes management. He was diagnosed with Type 2 Diabetes Mellitus about 3 years ago. He reports his fasting blood sugar at home has been running between 140-160 mg/dL over the past month. He says he has been taking Glycomet GP 2 regularly but admits to being irregular with his evening walk. He complains of occasional tingling in both feet for the past 2 weeks, worse at night. No visual disturbances. He also mentions feeling more tired than usual. He has a history of hypertension controlled on Telmisartan 40mg daily. No chest pain, no breathlessness. Family history of diabetes in mother. On examination, BP is 138/86 mmHg, pulse 78/min regular, weight 82 kg. BMI calculated at 28.4. Foot examination shows diminished sensation to monofilament testing in both feet, dorsalis pedis pulses palpable bilaterally. Rest of the systemic examination is unremarkable. HbA1c from last month was 8.2%. I'm going to increase his Glycomet GP to the GP 3 formulation, add Tab Pregabalin 75mg at bedtime for the neuropathy symptoms, and order a comprehensive metabolic panel, lipid profile, urine microalbumin, and a repeat HbA1c in 3 months. I've also advised strict dietary control and at least 30 minutes of walking daily. I want to refer him to an ophthalmologist for a diabetic retinopathy screening since it hasn't been done in over a year. Follow up in 6 weeks.",
    referral_reason: "Diabetic retinopathy screening - not done in over 1 year",
    specialist_type: "Ophthalmology"
  },
  {
    id: "CONSULT-002",
    patient: { name: "Priya Venkatesh", age: 34, gender: "Female", patient_id: "SYN-PT-10002" },
    doctor: { name: "Dr. Suresh Nair", speciality: "General Medicine", hospital: "Apollo Clinic, Chennai" },
    consultation_text: "Priya Venkatesh, 34-year-old female, presents with complaints of persistent fatigue and joint pain for the past 3 months. She describes the fatigue as overwhelming, not relieved by rest, and affecting her work as a software engineer. Joint pain is primarily in the small joints of both hands, especially the proximal interphalangeal joints and metacarpophalangeal joints, with morning stiffness lasting about 45 minutes. She also reports a butterfly-shaped rash on her cheeks that worsens with sun exposure, which appeared about 2 months ago. She has noticed some hair thinning recently. No fever, no oral ulcers, no Raynaud's phenomenon. She has no significant past medical history. She is not on any regular medications. No known allergies. On examination, she appears fatigued. BP 118/76 mmHg, pulse 82/min, temp 37.1°C. Malar rash noted on both cheeks. Mild synovitis of the PIP and MCP joints bilaterally, no deformity. No lymphadenopathy. Chest clear, heart sounds normal. I'm suspecting Systemic Lupus Erythematosus and have ordered ANA, anti-dsDNA antibodies, complement levels C3 and C4, CBC with differential, ESR, CRP, urinalysis with microscopy, and serum creatinine. I've advised her to use sunscreen SPF 50+ and avoid prolonged sun exposure. Starting her on Hydroxychloroquine 200mg twice daily. Referring to Rheumatology for further evaluation and confirmation. Follow up in 2 weeks with reports.",
    referral_reason: "Suspected Systemic Lupus Erythematosus - needs rheumatological evaluation and confirmation",
    specialist_type: "Rheumatology"
  },
  {
    id: "CONSULT-003",
    patient: { name: "Arjun Reddy Patil", age: 62, gender: "Male", patient_id: "SYN-PT-10003" },
    doctor: { name: "Dr. Meera Joshi", speciality: "Pulmonology", hospital: "Government District Hospital, Hyderabad" },
    consultation_text: "Arjun Reddy Patil, 62-year-old male, retired auto-rickshaw driver, comes with complaints of progressive breathlessness on exertion for the past 6 months, now getting breathless even walking to the bathroom. He has a chronic productive cough with whitish sputum, occasionally yellowish, for the past 2 years. He is a heavy smoker, about 30 pack-years, and quit smoking only 6 months ago. He also reports weight loss of about 5 kg in the past 3 months without any change in appetite. He had pulmonary tuberculosis 15 years ago, completed DOTS treatment. No hemoptysis. No chest pain. No fever currently. He has no other comorbidities. On examination, he is thin built, BMI 19.2, appears breathless at rest. SpO2 is 91% on room air, respiratory rate 22/min, BP 126/80 mmHg. Chest examination shows bilateral wheezing with prolonged expiratory phase, reduced air entry in the right upper zone. No clubbing. Spirometry done today shows FEV1 of 42% predicted, FEV1/FVC ratio 0.58, indicating severe obstructive pattern with no significant bronchodilator reversibility. Chest X-ray shows hyperinflated lungs with a suspicious opacity in the right upper lobe measuring about 2.5 cm. Given his history and findings, I am diagnosing him with severe COPD, GOLD Stage 3. The right upper lobe opacity is concerning and needs further evaluation. Starting him on Tiotropium 18 mcg inhaler once daily, Budesonide-Formoterol 200/6 mcg inhaler twice daily, and SOS Salbutamol inhaler. Ordering a HRCT chest urgently, sputum for AFB and cytology, and CBC. Referring to Oncology for evaluation of the lung opacity. Follow up in 1 week with CT report.",
    referral_reason: "Suspicious right upper lobe opacity 2.5 cm on chest X-ray - needs CT evaluation and oncological assessment",
    specialist_type: "Oncology"
  },
  {
    id: "CONSULT-005",
    patient: { name: "Sanjay Gupta", age: 48, gender: "Male", patient_id: "SYN-PT-10005" },
    doctor: { name: "Dr. Ananya Deshmukh", speciality: "Internal Medicine", hospital: "City General Hospital, Pune" },
    consultation_text: "Sanjay Gupta, 48-year-old male, businessman, comes with acute onset severe headache for 2 days. He describes it as a throbbing pain, predominantly right-sided, associated with nausea and sensitivity to light. Pain is 8/10 in severity. He has had similar episodes in the past, about 2-3 times a year, usually triggered by stress or skipped meals. This episode started after a particularly stressful week at work and he missed lunch yesterday. He took Combiflam but no relief. He also mentions his blood pressure readings at home have been slightly elevated, around 140-145/90-92 mmHg, and he is currently not on any antihypertensive medication. He has a family history of hypertension and his father had a stroke at age 60. No visual aura, no weakness, no speech difficulties, no neck stiffness, no fever. On examination, he is in moderate distress due to headache. BP 148/94 mmHg, pulse 86/min, afebrile. Neurological examination is completely normal - cranial nerves intact, no focal deficits, no papilledema on fundoscopy, no meningeal signs. I am diagnosing this as a migraine without aura. Also noting Stage 1 hypertension that needs treatment. For the acute migraine, prescribing Tab Sumatriptan 50mg now and can repeat after 2 hours if needed, Tab Domperidone 10mg for nausea. For prevention given his frequency, starting Tab Propranolol 40mg twice daily which will also help with his blood pressure. Advising lifestyle modifications - regular meals, stress management, adequate sleep, regular exercise. Ordering basic blood work including fasting lipid profile and blood sugar given his age, family history, and newly detected hypertension. Follow up in 2 weeks.",
    referral_reason: null,
    specialist_type: null
  },
  {
    id: "CONSULT-006",
    patient: { name: "Lakshmi Devi Agarwal", age: 70, gender: "Female", patient_id: "SYN-PT-10006" },
    doctor: { name: "Dr. Suresh Nair", speciality: "General Medicine", hospital: "Apollo Clinic, Chennai" },
    consultation_text: "Lakshmi Devi Agarwal, 70-year-old female, retired school teacher, brought by her son with complaints of progressive memory loss over the past 1 year. The son reports she has been forgetting recent conversations, misplacing things frequently, repeating questions, and getting confused about the day of the week. She got lost in her own neighborhood last month. She has also become increasingly withdrawn and less interested in her usual activities like reading and watching television. Sleep is disturbed with frequent nighttime awakenings. She has a history of well-controlled hypertension on Amlodipine 5mg, hypothyroidism on Thyronorm 50mcg, and osteoarthritis of both knees. Her husband passed away 2 years ago. No history of falls, no urinary incontinence, no visual or auditory hallucinations, no personality changes. On examination, she is oriented to person but not fully to time and place. BP 134/78 mmHg, pulse 72/min. Mini Mental State Examination score is 20/30, with deficits mainly in recall, attention, and orientation. Cranial nerves are intact, no focal neurological deficits, gait is normal. I am considering early Alzheimer's dementia versus vascular cognitive impairment. Ordering MRI brain with volumetric analysis, complete blood count, metabolic panel, vitamin B12 levels, folate levels, thyroid function tests to rule out reversible causes. Starting Tab Donepezil 5mg once at bedtime. Referring to Neurology for comprehensive cognitive assessment and further evaluation. Follow up in 4 weeks with reports.",
    referral_reason: "Progressive cognitive decline - needs comprehensive neurocognitive assessment and MRI-guided evaluation for dementia",
    specialist_type: "Neurology"
  }
];

export const demoDoctors = [
  {
    id: "DOC-001",
    name: "Dr. Ananya Deshmukh",
    speciality: "Internal Medicine",
    hospital: "City General Hospital, Pune",
    avatar: "AD"
  },
  {
    id: "DOC-002",
    name: "Dr. Suresh Nair",
    speciality: "General Medicine",
    hospital: "Apollo Clinic, Chennai",
    avatar: "SN"
  }
];
