import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Stethoscope, Calendar, Clock, MapPin, User, Pill, AlertTriangle, CalendarCheck, Edit3, FileText } from 'lucide-react';
import type { Visit, Consultation } from '../types';

interface Props {
  visit: Visit;
  doctor: { id: string; name: string; speciality: string; hospital: string };
  onEditConsultation: (c: Consultation) => void;
}

export default function VisitDetailPage({ visit, doctor, onEditConsultation }: Props) {
  const navigate = useNavigate();

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const formatTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  const summary = visit.patient_summary;
  const meds = summary?.your_treatment_plan?.medications || [];
  const lifestyle = summary?.your_treatment_plan?.lifestyle_advice || [];
  const tests = summary?.your_treatment_plan?.tests_ordered || [];
  const warnings = visit.warning_signs || summary?.warning_signs || [];
  const followUp = summary?.follow_up;

  const handleEdit = () => {
    const consultation: Consultation = {
      id: visit.consultation_id,
      patient: {
        name: visit.patient_name,
        age: visit.patient_age,
        gender: visit.patient_gender,
        patient_id: (visit as any).patient_id || '',
        phone: (visit as any).phone_number || '',
      },
      doctor: {
        name: visit.doctor_name || doctor.name,
        speciality: visit.doctor_speciality || doctor.speciality,
        hospital: visit.hospital || doctor.hospital,
      },
      consultation_text: '',
      referral_reason: null,
      specialist_type: null,
    };
    onEditConsultation(consultation);
    navigate('/consultation');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200/60 sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-4">
          <button onClick={() => navigate('/')} className="p-2 hover:bg-slate-100 rounded-xl transition-all cursor-pointer">
            <ArrowLeft className="w-5 h-5 text-slate-500" />
          </button>
          <div className="flex items-center gap-3 flex-1">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-medical-600 to-medical-500 text-white flex items-center justify-center shadow-md shadow-medical-600/20">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 tracking-tight">Visit Details</h1>
              <p className="text-xs text-slate-500">{visit.consultation_id}</p>
            </div>
          </div>
          <button
            onClick={handleEdit}
            className="inline-flex items-center gap-2 bg-medical-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-medical-700 transition-all cursor-pointer shadow-sm"
          >
            <Edit3 className="w-4 h-4" />
            Edit / Re-process
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Patient Info Card */}
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-100" style={{ background: 'linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 50%, #f0fdf4 100%)' }}>
            <div className="flex items-start gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-medical-500 to-medical-600 text-white flex items-center justify-center font-bold text-lg shadow-lg shadow-medical-600/20">
                {visit.patient_name?.split(' ').map(n => n[0]).slice(0, 2).join('') || '?'}
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-slate-900">{visit.patient_name}</h2>
                <div className="flex items-center gap-3 mt-1 flex-wrap">
                  <span className="text-sm text-slate-600">{visit.patient_age} years &middot; {visit.patient_gender}</span>
                  {(visit as any).phone_number && (
                    <span className="text-sm text-slate-500">{(visit as any).phone_number}</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="px-6 py-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-medical-50 text-medical-600 flex items-center justify-center">
                <Calendar className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Date</p>
                <p className="text-sm font-medium text-slate-800">{formatDate(visit.visit_date)}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Time</p>
                <p className="text-sm font-medium text-slate-800">{formatTime(visit.visit_date)}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                <MapPin className="w-4 h-4" />
              </div>
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Hospital</p>
                <p className="text-sm font-medium text-slate-800">{visit.hospital}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Diagnosis */}
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-3">
            <Stethoscope className="w-5 h-5 text-medical-600" />
            <h3 className="text-base font-bold text-slate-900">Diagnosis</h3>
          </div>
          <div className="bg-medical-50 border border-medical-200/50 rounded-xl px-4 py-3">
            <p className="text-sm font-semibold text-medical-800">{visit.diagnosis}</p>
          </div>
          {summary?.visit_summary && (
            <p className="text-sm text-slate-600 mt-3 leading-relaxed">{summary.visit_summary}</p>
          )}
          {summary?.what_the_doctor_found && (
            <div className="mt-3">
              <p className="text-xs text-slate-400 uppercase font-semibold mb-1">What the Doctor Found</p>
              <p className="text-sm text-slate-600 leading-relaxed">{summary.what_the_doctor_found}</p>
            </div>
          )}
        </div>

        {/* Doctor Info */}
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-3">
            <User className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">Attending Physician</h3>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-100 to-indigo-200 text-indigo-700 flex items-center justify-center font-bold text-sm">
              {(visit.doctor_name || doctor.name).split(' ').filter(n => n.startsWith('D') || n === (visit.doctor_name || doctor.name).split(' ').pop()).map(n => n[0]).join('').slice(0, 2)}
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">{visit.doctor_name || doctor.name}</p>
              <p className="text-xs text-slate-500">{visit.doctor_speciality || doctor.speciality}</p>
            </div>
          </div>
        </div>

        {/* Medications */}
        {meds.length > 0 && (
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4">
              <Pill className="w-5 h-5 text-emerald-600" />
              <h3 className="text-base font-bold text-slate-900">Medications</h3>
              <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-lg font-medium">{meds.length}</span>
            </div>
            <div className="space-y-3">
              {meds.map((med, i) => (
                <div key={i} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{med.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{med.what_its_for}</p>
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-3">
                    <span className="text-xs text-emerald-700 bg-emerald-50 px-2 py-1 rounded-lg">{med.how_to_take}</span>
                    {med.important_notes && (
                      <span className="text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded-lg">{med.important_notes}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tests Ordered */}
        {tests.length > 0 && (
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="w-5 h-5 text-sky-600" />
              <h3 className="text-base font-bold text-slate-900">Tests Ordered</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {tests.map((test, i) => (
                <div key={i} className="bg-sky-50/50 rounded-xl p-3 border border-sky-100">
                  <p className="text-sm font-medium text-slate-800">{test.test_name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{test.why_needed}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Lifestyle Advice */}
        {lifestyle.length > 0 && (
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6">
            <h3 className="text-base font-bold text-slate-900 mb-3">Lifestyle Advice</h3>
            <ul className="space-y-2">
              {lifestyle.map((advice, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-medical-500 mt-2 shrink-0" />
                  <span className="text-sm text-slate-600">{advice}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Follow-up */}
        {followUp && (
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-3">
              <CalendarCheck className="w-5 h-5 text-violet-600" />
              <h3 className="text-base font-bold text-slate-900">Follow-up</h3>
            </div>
            <div className="bg-violet-50 rounded-xl p-4 border border-violet-100">
              <p className="text-sm font-medium text-violet-800">{followUp.next_appointment}</p>
              {followUp.what_to_bring && followUp.what_to_bring.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs text-violet-600 font-semibold mb-1">What to bring:</p>
                  <ul className="space-y-1">
                    {followUp.what_to_bring.map((item, i) => (
                      <li key={i} className="text-xs text-violet-700 flex items-center gap-1.5">
                        <span className="w-1 h-1 rounded-full bg-violet-400" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Warning Signs */}
        {warnings.length > 0 && (
          <div className="bg-rose-50 rounded-2xl border border-rose-200 p-6">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
              <h3 className="text-base font-bold text-rose-900">Warning Signs — Seek Immediate Care</h3>
            </div>
            <ul className="space-y-2">
              {warnings.map((sign, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-2 shrink-0" />
                  <span className="text-sm text-rose-800">{typeof sign === 'string' ? sign : (sign as any).name || JSON.stringify(sign)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Disclaimer */}
        <div className="bg-amber-50 rounded-xl border border-amber-200 p-4">
          <p className="text-xs text-amber-700">
            This record was generated and verified by AI-assisted clinical documentation. Always follow direct medical advice from your physician.
          </p>
        </div>
      </main>
    </div>
  );
}
