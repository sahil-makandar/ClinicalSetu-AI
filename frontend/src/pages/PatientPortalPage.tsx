import { useState, useEffect } from 'react';
import {
  LogOut, User, FileText, Calendar, Clock, Shield, Stethoscope,
  Heart, ChevronRight, CheckCircle2, Sparkles, Activity, Loader2, RefreshCw
} from 'lucide-react';
import { fetchPatientVisits } from '../services/api';
import type { Visit } from '../types';

interface Props {
  onLogout: () => void;
  phone: string;
}

export default function PatientPortalPage({ onLogout, phone }: Props) {
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedVisit, setSelectedVisit] = useState<string | null>(null);

  const loadVisits = () => {
    setLoading(true);
    setError('');
    fetchPatientVisits(phone)
      .then((data) => {
        setVisits(data);
        if (data.length > 0) setSelectedVisit(data[0].consultation_id);
      })
      .catch((err) => {
        console.error('Failed to fetch visits:', err);
        setError('Unable to load visits. Please try again.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (phone) loadVisits();
  }, [phone]);

  const activeVisit = visits.find(v => v.consultation_id === selectedVisit);
  const patientName = visits.length > 0 ? visits[0].patient_name : 'Patient';
  const patientAge = visits.length > 0 ? visits[0].patient_age : 0;
  const patientGender = visits.length > 0 ? visits[0].patient_gender : '';

  // Extract conditions from all visits' diagnoses
  const conditions = [...new Set(visits.map(v => v.diagnosis).filter(Boolean))];

  // Extract patient summary fields safely
  const summary = activeVisit?.patient_summary;
  const summaryText = summary?.visit_summary || summary?.your_diagnosis || '';
  const meds = activeVisit?.medications?.length
    ? activeVisit.medications
    : summary?.your_treatment_plan?.medications?.map(m => ({
        name: m.name,
        how: m.how_to_take || `${m.what_its_for}`,
      })) || [];
  const followUp = activeVisit?.follow_up || summary?.follow_up?.next_appointment || '';
  const warningSign = activeVisit?.warning_signs?.join('. ') || summary?.warning_signs?.join('. ') || '';

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
              <span className="text-xs font-semibold text-medical-700">{patientName}</span>
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
            <strong>Patient Portal.</strong> This portal shows AI-generated summaries of your visits in simple language. Always follow your doctor's verbal instructions. These summaries are for reference only and do not replace medical advice.
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-medical-500 animate-spin mb-4" />
            <p className="text-sm text-slate-500">Loading your visits...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <p className="text-sm text-rose-600 mb-4">{error}</p>
            <button onClick={loadVisits} className="flex items-center gap-2 text-sm text-medical-600 hover:underline cursor-pointer">
              <RefreshCw className="w-4 h-4" /> Try again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && visits.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-16 h-16 rounded-2xl bg-medical-50 text-medical-400 flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-slate-700 mb-2">No Visits Yet</h3>
            <p className="text-sm text-slate-500 max-w-sm mx-auto text-center">
              Your doctor hasn't uploaded any visit summaries for this phone number yet. After your next consultation, your summary will appear here.
            </p>
            <button onClick={loadVisits} className="flex items-center gap-2 text-sm text-medical-600 hover:underline cursor-pointer mt-4">
              <RefreshCw className="w-4 h-4" /> Refresh
            </button>
          </div>
        )}

        {/* Main Content */}
        {!loading && !error && visits.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Profile + Visit List */}
            <div className="lg:col-span-1 space-y-5">
              {/* Patient Profile Card */}
              <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-medical-500 to-medical-600 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-medical-500/20">
                    {patientName.split(' ').map(n => n[0]).slice(0, 2).join('')}
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">{patientName}</h2>
                    <p className="text-xs text-slate-500 mt-0.5">{patientAge}y &middot; {patientGender}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{phone}</p>
                  </div>
                </div>
                {conditions.length > 0 && (
                  <div className="border-t border-slate-100 pt-3">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Diagnoses</p>
                    <div className="flex flex-wrap gap-1.5">
                      {conditions.map((c, i) => (
                        <span key={i} className="text-xs bg-medical-50 text-medical-700 border border-medical-200/40 px-2.5 py-1 rounded-lg font-medium">{c}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              {activeVisit && followUp && (
                <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-4">
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Reminders</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-medical-50/50 border border-medical-200/30 text-left">
                      <Heart className="w-4 h-4 text-medical-600 shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-slate-800">Follow-up: {followUp}</p>
                        <p className="text-xs text-slate-500">{activeVisit.doctor_name}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Past Visits */}
              <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Your Visits</h3>
                  <button onClick={loadVisits} className="p-1.5 hover:bg-slate-100 rounded-lg transition-all cursor-pointer" title="Refresh">
                    <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
                  </button>
                </div>
                <div className="space-y-2">
                  {visits.map((visit) => (
                    <button
                      key={visit.consultation_id}
                      onClick={() => setSelectedVisit(visit.consultation_id)}
                      className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-all cursor-pointer text-left ${
                        selectedVisit === visit.consultation_id
                          ? 'border-medical-400 bg-medical-50/50 shadow-sm'
                          : 'border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center shrink-0">
                        <Calendar className="w-4 h-4 text-slate-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-800 truncate">{visit.diagnosis || 'Consultation'}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{visit.doctor_name} &middot; {visit.visit_date?.split('T')[0]}</p>
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
                      <h2 className="text-lg font-bold text-slate-900 tracking-tight">{activeVisit.diagnosis || 'Consultation'}</h2>
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500">
                        <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {activeVisit.visit_date?.split('T')[0]}</span>
                        <span className="flex items-center gap-1"><Stethoscope className="w-3.5 h-3.5" /> {activeVisit.doctor_name}</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{activeVisit.hospital} &middot; {activeVisit.doctor_speciality}</p>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs bg-emerald-50 text-emerald-700 border border-emerald-200/60 px-3 py-1.5 rounded-xl font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Verified by Doctor
                    </div>
                  </div>

                  {/* Summary */}
                  {summaryText && (
                    <div className="bg-medical-50/50 border border-medical-200/30 rounded-xl p-5">
                      <h3 className="text-xs font-bold text-medical-700 uppercase tracking-wider mb-2">Your Visit Summary</h3>
                      <p className="text-sm text-medical-900 leading-relaxed">{summaryText}</p>
                    </div>
                  )}

                  {/* What the Doctor Found */}
                  {summary?.what_the_doctor_found && (
                    <div className="bg-slate-50/80 border border-slate-100 rounded-xl p-5">
                      <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">What the Doctor Found</h3>
                      <p className="text-sm text-slate-700 leading-relaxed">{summary.what_the_doctor_found}</p>
                    </div>
                  )}

                  {/* Medications */}
                  {meds.length > 0 && (
                    <div>
                      <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-medical-500" />
                        Your Medicines
                      </h3>
                      <div className="space-y-2.5">
                        {meds.map((med, i) => (
                          <div key={i} className="bg-slate-50/80 rounded-xl p-4 border border-slate-100">
                            <p className="text-sm font-semibold text-slate-900">{med.name}</p>
                            <p className="text-xs text-medical-700 mt-1 font-medium">{med.how}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Lifestyle Advice */}
                  {summary?.your_treatment_plan?.lifestyle_advice && summary.your_treatment_plan.lifestyle_advice.length > 0 && (
                    <div>
                      <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Lifestyle Advice</h3>
                      <ul className="space-y-1.5">
                        {summary.your_treatment_plan.lifestyle_advice.map((advice, i) => (
                          <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-medical-400 mt-1.5 shrink-0" />
                            {advice}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Follow-up */}
                  {followUp && (
                    <div className="bg-blue-50/80 border border-blue-200/60 rounded-xl p-4">
                      <h3 className="text-xs font-bold text-blue-700 uppercase tracking-wider mb-1.5 flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5" />
                        Next Visit
                      </h3>
                      <p className="text-sm text-blue-800 font-medium">{followUp}</p>
                    </div>
                  )}

                  {/* Warning Signs */}
                  {warningSign && (
                    <div className="bg-rose-50/80 border border-rose-200/60 rounded-xl p-4">
                      <h3 className="text-xs font-bold text-rose-700 uppercase tracking-wider mb-1.5 flex items-center gap-2">
                        <Shield className="w-3.5 h-3.5" />
                        When to Get Help Immediately
                      </h3>
                      <p className="text-sm text-rose-800 leading-relaxed">{warningSign}</p>
                    </div>
                  )}

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
        )}

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
