import { useNavigate } from 'react-router-dom';
import { Plus, FileText, LogOut, Activity, Users, Clock, Stethoscope, ChevronRight, Search, Sparkles } from 'lucide-react';
import { sampleConsultations } from '../data/sampleConsultations';
import type { Consultation } from '../types';

interface Props {
  doctor: { id: string; name: string; speciality: string; hospital: string };
  onLogout: () => void;
  onSelectConsultation: (c: Consultation) => void;
}

export default function DashboardPage({ doctor, onLogout, onSelectConsultation }: Props) {
  const navigate = useNavigate();
  const doctorConsultations = sampleConsultations.filter(
    c => c.doctor.name === doctor.name
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200/60 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-medical-600 to-medical-500 text-white flex items-center justify-center shadow-md shadow-medical-600/20">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 tracking-tight">ClinicalSetu</h1>
              <p className="text-[10px] text-medical-600 font-semibold tracking-wider uppercase">AI Clinical Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block mr-2">
              <p className="text-sm font-semibold text-slate-900">{doctor.name}</p>
              <p className="text-xs text-slate-500">{doctor.speciality}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-medical-500 to-medical-600 text-white flex items-center justify-center text-sm font-bold">
              {doctor.name.split(' ').filter(n => n.startsWith('D') || n === doctor.name.split(' ').pop()).map(n => n[0]).join('').slice(0, 2)}
            </div>
            <button
              onClick={onLogout}
              className="p-2.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all cursor-pointer"
              title="Sign out"
            >
              <LogOut className="w-4.5 h-4.5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Banner */}
        <div className="relative overflow-hidden rounded-2xl mb-8 p-6 sm:p-8" style={{ background: 'linear-gradient(135deg, #042f2e 0%, #115e59 40%, #0f766e 70%, #0d9488 100%)' }}>
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-white/5 blur-3xl -translate-y-1/3 translate-x-1/3" />
          <div className="absolute bottom-0 left-1/3 w-48 h-48 rounded-full bg-teal-300/10 blur-2xl translate-y-1/2" />
          <div className="relative z-10">
            <p className="text-teal-200/70 text-sm font-medium mb-1">Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'},</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2">{doctor.name}</h2>
            <p className="text-teal-100/60 text-sm max-w-lg">{doctor.speciality} &middot; {doctor.hospital}</p>
            <button
              onClick={() => {
                onSelectConsultation(null as unknown as Consultation);
                navigate('/consultation');
              }}
              className="mt-5 inline-flex items-center gap-2 bg-white text-medical-700 px-5 py-2.5 rounded-xl font-semibold text-sm hover:bg-medical-50 transition-all duration-200 shadow-lg cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              New Consultation
            </button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 rounded-full bg-medical-50 -translate-y-1/2 translate-x-1/2" />
            <div className="relative flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-medical-50 text-medical-600 flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <p className="text-3xl font-bold text-slate-900">{doctorConsultations.length}</p>
                <p className="text-xs text-slate-500 font-medium">Sample Cases</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 rounded-full bg-emerald-50 -translate-y-1/2 translate-x-1/2" />
            <div className="relative flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <p className="text-3xl font-bold text-slate-900">4</p>
                <p className="text-xs text-slate-500 font-medium">AI Outputs / Visit</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 rounded-full bg-violet-50 -translate-y-1/2 translate-x-1/2" />
            <div className="relative flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <p className="text-3xl font-bold text-slate-900">0</p>
                <p className="text-xs text-slate-500 font-medium">Pending Reviews</p>
              </div>
            </div>
          </div>
        </div>

        {/* Section Header */}
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 tracking-tight">Sample Consultations</h3>
            <p className="text-sm text-slate-500 mt-0.5">Select a case to process with AI</p>
          </div>
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400 bg-white border border-slate-200/60 rounded-xl px-3 py-2">
            <Search className="w-3.5 h-3.5" />
            <span>{sampleConsultations.length} cases available</span>
          </div>
        </div>

        {/* Consultation Cards */}
        <div className="space-y-3">
          {sampleConsultations.map((consultation) => (
            <button
              key={consultation.id}
              onClick={() => {
                onSelectConsultation(consultation);
                navigate('/consultation');
              }}
              className="w-full group bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm hover:border-medical-300 hover:shadow-md hover:shadow-medical-500/5 transition-all duration-300 text-left cursor-pointer"
            >
              <div className="flex items-start gap-4">
                {/* Avatar */}
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-medical-100 to-medical-200 text-medical-700 flex items-center justify-center font-bold text-sm shrink-0">
                  {consultation.patient.name.split(' ').map(n => n[0]).slice(0, 2).join('')}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1.5">
                    <h3 className="font-semibold text-slate-900 text-sm">{consultation.patient.name}</h3>
                    <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-lg font-medium">
                      {consultation.patient.age}y &middot; {consultation.patient.gender}
                    </span>
                    {consultation.referral_reason && (
                      <span className="text-xs bg-amber-50 text-amber-700 border border-amber-200/60 px-2 py-0.5 rounded-lg font-medium">
                        Referral Needed
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-500 line-clamp-2 leading-relaxed">
                    {consultation.consultation_text.slice(0, 160)}...
                  </p>
                  <div className="flex items-center gap-3 mt-2.5">
                    <span className="flex items-center gap-1 text-xs text-slate-400">
                      <Users className="w-3 h-3" />
                      {consultation.doctor.name}
                    </span>
                    <span className="text-slate-300">&middot;</span>
                    <span className="flex items-center gap-1 text-xs text-slate-400">
                      <Clock className="w-3 h-3" />
                      {consultation.id}
                    </span>
                  </div>
                </div>

                <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-medical-500 group-hover:translate-x-1 transition-all duration-300 shrink-0 mt-2" />
              </div>
            </button>
          ))}
        </div>
      </main>
    </div>
  );
}
