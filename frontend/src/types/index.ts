export interface Patient {
  name: string;
  age: number;
  gender: string;
  patient_id: string;
  phone?: string;
}

export interface Doctor {
  name: string;
  speciality: string;
  hospital: string;
}

export interface Consultation {
  id: string;
  patient: Patient;
  doctor: Doctor;
  consultation_text: string;
  referral_reason: string | null;
  specialist_type: string | null;
}

export interface SOAPNote {
  subjective: {
    chief_complaint: string;
    history_of_present_illness: string;
    review_of_systems: {
      relevant_positives: string[];
      relevant_negatives: string[];
    };
    past_medical_history: string[];
    medications: string[];
    allergies: string[];
  };
  objective: {
    vitals: Record<string, string>;
    physical_exam: {
      general: string;
      systems_examined: Array<{ system: string; findings: string }>;
    };
    investigations: string[];
  };
  assessment: {
    primary_diagnosis: string;
    secondary_diagnoses: string[];
    clinical_reasoning: string;
  };
  plan: {
    medications_prescribed: Array<{
      name: string;
      dosage: string;
      frequency: string;
      duration: string;
    }>;
    investigations_ordered: string[];
    procedures_planned: string[];
    referrals: string[];
    follow_up: string;
    patient_education: string[];
  };
  confidence_scores: {
    subjective: number;
    objective: number;
    assessment: number;
    plan: number;
  };
  flags: string[];
}

export interface PatientSummary {
  greeting: string;
  visit_summary: string;
  what_the_doctor_found: string;
  your_diagnosis: string;
  your_treatment_plan: {
    medications: Array<{
      name: string;
      what_its_for: string;
      how_to_take: string;
      important_notes: string;
    }>;
    lifestyle_advice: string[];
    tests_ordered: Array<{
      test_name: string;
      why_needed: string;
    }>;
  };
  follow_up: {
    next_appointment: string;
    what_to_bring: string[];
  };
  warning_signs: string[];
  questions_to_ask: string[];
  disclaimer: string;
}

export interface ReferralLetter {
  referral_letter: {
    date: string;
    to: string;
    from: string;
    patient_summary: {
      demographics: string;
      presenting_complaint: string;
    };
    reason_for_referral: string;
    relevant_history: {
      current_condition: string;
      relevant_past_history: string[];
      current_medications: string[];
      allergies: string;
    };
    investigations: {
      completed: string[];
      pending: string[];
      recommended_before_visit: string[];
    };
    clinical_questions: string[];
    urgency: {
      level: string;
      reasoning: string;
    };
    patient_preparation_checklist: string[];
  } | null;
  message?: string;
  confidence_score: number;
  flags?: string[];
}

export interface DischargeSummary {
  discharge_summary: {
    header: {
      facility: string;
      patient_name: string;
      age_gender: string;
      date_of_visit: string;
      attending_physician: string;
      visit_type: string;
    };
    chief_complaint: string;
    history_of_present_illness: string;
    past_medical_history: string;
    examination_findings: string;
    investigations: {
      completed: string[];
      ordered: string[];
    };
    diagnosis: {
      primary: string;
      secondary: string[];
    };
    treatment_given: {
      medications: Array<{
        name: string;
        dosage: string;
        duration: string;
        instructions: string;
      }>;
      procedures: string[];
      advice: string[];
    };
    condition_at_discharge: string;
    follow_up_plan: {
      next_visit: string;
      investigations_before_visit: string[];
      referrals: string[];
      emergency_instructions: string;
    };
    doctor_signature: {
      name: string;
      designation: string;
      date: string;
    };
  };
  confidence_score: number;
  disclaimer: string;
}

export interface TrialMatch {
  trial_id: string;
  trial_title: string;
  trial_phase: string;
  sponsor: string;
  enrollment_status: string;
  matched_criteria: Array<{
    criterion: string;
    patient_value: string;
    required_value: string;
    match: boolean;
  }>;
  unmatched_criteria: Array<{
    criterion: string;
    patient_value: string;
    required_value: string;
    match: boolean;
  }>;
  missing_information: string[];
  confidence_score: number;
  locations: string[];
  contact_info?: string;
}

export interface TrialMatches {
  patient_profile_extracted: Record<string, unknown>;
  trial_matches: TrialMatch[];
  summary: string;
  disclaimer: string;
}

export interface Visit {
  consultation_id: string;
  visit_date: string;
  patient_name: string;
  patient_age: number;
  patient_gender: string;
  doctor_name: string;
  doctor_speciality: string;
  hospital: string;
  diagnosis: string;
  patient_summary: PatientSummary;
  medications: Array<{ name: string; how: string }>;
  follow_up: string;
  warning_signs: string[];
}

export interface ProcessingStep {
  step: string;
  duration_ms: number;
  model: string;
  status: string;
}

export interface ProcessingResult {
  soap_note: SOAPNote;
  patient_summary: PatientSummary;
  referral_letter: ReferralLetter;
  discharge_summary?: DischargeSummary;
  trial_matches: TrialMatches;
  processing_steps: ProcessingStep[];
  agent_summary?: string;
  metadata: {
    total_processing_time_ms: number;
    model_used: string;
    consultation_id: string;
    patient_id: string;
    disclaimer: string;
    version: string;
    architecture?: string;
    agent_id?: string;
    agent_alias_id?: string;
    session_id?: string;
    tools_called?: number;
    agents_invoked?: number;
    fallback_reason?: string;
  };
}
