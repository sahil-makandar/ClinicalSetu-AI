import { useState } from 'react';
import {
  LogOut, User, FileText, Calendar, Clock, Shield, Stethoscope,
  Heart, Bell, ChevronRight, CheckCircle2, Sparkles, Activity
} from 'lucide-react';

interface Props {
  onLogout: () => void;
}

// Mock patient data for demo
const patientProfile = {
  name: 'Rajesh Kumar Sharma',
  age: 55,
  gender: 'Male',
  id: 'SYN-PT-10001',
  blood_group: 'B+',
  phone: '+91 98765 43210',
  conditions: ['Type 2 Diabetes Mellitus', 'Hypertension', 'Diabetic Neuropathy'],
};

const pastVisits = [
  {
    id: 'VISIT-001',
    date: '2026-02-28',
    doctor: 'Dr. Ananya Deshmukh',
    speciality: 'Internal Medicine',
    hospital: 'City General Hospital, Pune',
    diagnosis: 'T2DM with Peripheral Neuropathy - Follow-up',
    summary: 'Your diabetes numbers are a bit higher than we want them. The doctor has increased your sugar medicine (Glycomet GP 3) and added a new medicine (Pregabalin 75mg) to help with the tingling in your feet. You need blood tests before your next visit.',
    medications: [
      { name: 'Glycomet GP 3', how: 'Take once daily after breakfast' },
      { name: 'Pregabalin 75mg', how: 'Take at bedtime for foot tingling' },
      { name: 'Telmisartan 40mg', how: 'Continue once daily for blood pressure' },
    ],
    followUp: '6 weeks - bring blood test reports',
    warningSign: 'If you feel numbness spreading, sudden vision changes, or chest pain, visit the emergency department immediately.',
  },
  {
    id: 'VISIT-002',
    date: '2025-12-15',
    doctor: 'Dr. Suresh Nair',
    speciality: 'General Medicine',
    hospital: 'Apollo Clinic, Chennai',
    diagnosis: 'Routine Diabetes Follow-up',
    summary: 'Regular check-up. Sugar levels were better controlled. No changes to medication. Continue walking and dietary modifications.',
    medications: [
      { name: 'Glycomet GP 2', how: 'Take once daily after breakfast' },
      { name: 'Telmisartan 40mg', how: 'Continue once daily for blood pressure' },
    ],
    followUp: '3 months',
    warningSign: 'If blood sugar drops below 70 or you feel extremely dizzy, drink sugar water and contact your doctor.',
  },
];

export default function PatientPortalPage({ onLogout }: Props) {
  const [selectedVisit, setSelectedVisit] = useState<string | null>(null);
  const activeVisit = pastVisits.find(v => v.id === selectedVisit);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200/60 sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-medical-500 to-medical-600 flex items-center justify-center">
              <Stethoscope className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 tracking-tight">ClinicalSetu</h1>
              <p className="text-[10px] text-medical-600 font-semibold tracking-wide uppercase">Patient Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-medical-50 px-3 py-1.5 rounded-xl border border-medical-200/40">
              <User className="w-3.5 h-3.5 text-medical-600" />
              <span className="text-xs font-semibold text-medical-700">{patientProfile.name}</span>
            </div>
            <button onClick={onLogout} className="p-2 hover:bg-slate-100 rounded-xl transition-all cursor-pointer" title="Logout">
              <LogOut className="w-4 h-4 text-slate-500" />
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Disclaimer */}
        <div className="flex items-start gap-3 p-4 bg-amber-50/80 border border-amber-200/60 rounded-xl mb-6">
          <Shield className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <p className="text-xs text-amber-800 leading-relaxed">
            <strong>Patient Portal (Prototype).</strong> This portal shows AI-generated summaries of your visits in simple language. Always follow your doctor's verbal instructions. These summaries are for reference only and do not replace medical advice.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Profile + Visit List */}
          <div className="lg:col-span-1 space-y-5">
            {/* Patient Profile Card */}
            <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-medical-500 to-medical-600 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-medical-500/20">
                  {patientProfile.name.split(' ').map(n => n[0]).slice(0, 2).join('')}
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">{patientProfile.name}</h2>
                  <p className="text-xs text-slate-500 mt-0.5">{patientProfile.age}y &middot; {patientProfile.gender} &middot; {patientProfile.blood_group}</p>
                  <p className="text-xs text-slate-400 mt-0.5">ID: {patientProfile.id}</p>
                </div>
              </div>
              <div className="border-t border-slate-100 pt-3">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Active Conditions</p>
                <div className="flex flex-wrap gap-1.5">
                  {patientProfile.conditions.map((c, i) => (
                    <span key={i} className="text-xs bg-medical-50 text-medical-700 border border-medical-200/40 px-2.5 py-1 rounded-lg font-medium">{c}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full flex items-center gap-3 p-3 rounded-xl bg-medical-50/50 border border-medical-200/30 hover:bg-medical-50 transition-all cursor-pointer text-left">
                  <Bell className="w-4 h-4 text-medical-600" />
                  <div>
                    <p className="text-sm font-medium text-slate-800">Upcoming: Follow-up in 6 weeks</p>
                    <p className="text-xs text-slate-500">Dr. Ananya Deshmukh</p>
                  </div>
                </button>
                <button className="w-full flex items-center gap-3 p-3 rounded-xl bg-rose-50/50 border border-rose-200/30 hover:bg-rose-50 transition-all cursor-pointer text-left">
                  <Heart className="w-4 h-4 text-rose-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-800">Pending: Blood tests ordered</p>
                    <p className="text-xs text-slate-500">HbA1c, Lipid profile, Urine microalbumin</p>
                  </div>
                </button>
              </div>
            </div>

            {/* Past Visits */}
            <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Your Visits</h3>
              <div className="space-y-2">
                {pastVisits.map((visit) => (
                  <button
                    key={visit.id}
                    onClick={() => setSelectedVisit(visit.id)}
                    className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-all cursor-pointer text-left ${
                      selectedVisit === visit.id
                        ? 'border-medical-400 bg-medical-50/50 shadow-sm'
                        : 'border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center shrink-0">
                      <Calendar className="w-4 h-4 text-slate-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800 truncate">{visit.diagnosis}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{visit.doctor} &middot; {visit.date}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-300 shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Visit Detail */}
          <div className="lg:col-span-2">
            {activeVisit ? (
              <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6 sm:p-8 space-y-6">
                {/* Visit Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 tracking-tight">{activeVisit.diagnosis}</h2>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500">
                      <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {activeVisit.date}</span>
                      <span className="flex items-center gap-1"><Stethoscope className="w-3.5 h-3.5" /> {activeVisit.doctor}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{activeVisit.hospital}</p>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs bg-emerald-50 text-emerald-700 border border-emerald-200/60 px-3 py-1.5 rounded-xl font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Verified by Doctor
                  </div>
                </div>

                {/* Summary */}
                <div className="bg-medical-50/50 border border-medical-200/30 rounded-xl p-5">
                  <h3 className="text-xs font-bold text-medical-700 uppercase tracking-wider mb-2">Your Visit Summary</h3>
                  <p className="text-sm text-medical-900 leading-relaxed">{activeVisit.summary}</p>
                </div>

                {/* Medications */}
                <div>
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-medical-500" />
                    Your Medicines
                  </h3>
                  <div className="space-y-2.5">
                    {activeVisit.medications.map((med, i) => (
                      <div key={i} className="bg-slate-50/80 rounded-xl p-4 border border-slate-100">
                        <p className="text-sm font-semibold text-slate-900">{med.name}</p>
                        <p className="text-xs text-medical-700 mt-1 font-medium">{med.how}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Follow-up */}
                <div className="bg-blue-50/80 border border-blue-200/60 rounded-xl p-4">
                  <h3 className="text-xs font-bold text-blue-700 uppercase tracking-wider mb-1.5 flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5" />
                    Next Visit
                  </h3>
                  <p className="text-sm text-blue-800 font-medium">{activeVisit.followUp}</p>
                </div>

                {/* Warning Signs */}
                <div className="bg-rose-50/80 border border-rose-200/60 rounded-xl p-4">
                  <h3 className="text-xs font-bold text-rose-700 uppercase tracking-wider mb-1.5 flex items-center gap-2">
                    <Shield className="w-3.5 h-3.5" />
                    When to Get Help Immediately
                  </h3>
                  <p className="text-sm text-rose-800 leading-relaxed">{activeVisit.warningSign}</p>
                </div>

                {/* Disclaimer */}
                <p className="text-xs text-slate-400 italic border-t border-slate-100 pt-4">
                  This summary was generated by AI based on your doctor's notes. Always follow your doctor's verbal instructions. If you have questions, contact your doctor's office.
                </p>
              </div>
            ) : (
              <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-12 text-center">
                <div className="w-16 h-16 rounded-2xl bg-medical-50 text-medical-400 flex items-center justify-center mx-auto mb-4">
                  <FileText className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-bold text-slate-700 mb-2">Select a Visit</h3>
                <p className="text-sm text-slate-500 max-w-sm mx-auto">
                  Choose a past visit from the list to view your doctor-approved summary in simple language.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-slate-200/60">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-medical-400" />
              <span>Powered by Amazon Bedrock &middot; ClinicalSetu</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Activity className="w-3 h-3 text-medical-400" />
              <span>AI for Bharat Hackathon 2026</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
