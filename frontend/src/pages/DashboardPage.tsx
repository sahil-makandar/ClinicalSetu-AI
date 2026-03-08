import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Plus, FileText, LogOut, Activity, Clock, Stethoscope, ChevronRight, Search, Sparkles, Loader2, AlertCircle, Calendar } from 'lucide-react';
import { fetchDoctorVisits } from '../services/api';
import type { Visit } from '../types';

interface Props {
  doctor: { id: string; name: string; speciality: string; hospital: string };
  onLogout: () => void;
  onSelectVisit: (visit: Visit) => void;
}

export default function DashboardPage({ doctor, onLogout, onSelectVisit }: Props) {
  const navigate = useNavigate();
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    fetchDoctorVisits(doctor.name)
      .then((data) => setVisits(data))
      .catch((err) => setError(err.message || 'Failed to load consultations'))
      .finally(() => setLoading(false));
  }, [doctor.name]);

  const filteredVisits = visits.filter((v) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      v.patient_name?.toLowerCase().includes(q) ||
      v.diagnosis?.toLowerCase().includes(q) ||
      v.consultation_id?.toLowerCase().includes(q) ||
      v.hospital?.toLowerCase().includes(q)
    );
  });

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
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
              onClick={() => navigate('/consultation')}
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
                <p className="text-3xl font-bold text-slate-900">{loading ? '-' : visits.length}</p>
                <p className="text-xs text-slate-500 font-medium">Consultations</p>
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
                <p className="text-3xl font-bold text-slate-900">5</p>
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
                <p className="text-3xl font-bold text-slate-900">{loading ? '-' : new Set(visits.map(v => v.patient_name)).size}</p>
                <p className="text-xs text-slate-500 font-medium">Unique Patients</p>
              </div>
            </div>
          </div>
        </div>

        {/* Section Header + Search */}
        <div className="flex items-center justify-between mb-5 gap-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 tracking-tight">Consultations</h3>
            <p className="text-sm text-slate-500 mt-0.5">Your patient visit records</p>
          </div>
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by patient, diagnosis..."
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200/60 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-medical-500/20 focus:border-medical-500 transition-all"
            />
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 text-medical-500 animate-spin mr-3" />
            <span className="text-sm text-slate-500">Loading consultations...</span>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-5 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-rose-800">Unable to load consultations</p>
              <p className="text-xs text-rose-600 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && visits.length === 0 && (
          <div className="text-center py-20">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-sm text-slate-500 font-medium">No consultations yet</p>
            <p className="text-xs text-slate-400 mt-1">Start a new consultation to see records here</p>
            <button
              onClick={() => navigate('/consultation')}
              className="mt-4 inline-flex items-center gap-2 bg-medical-600 text-white px-4 py-2 rounded-xl text-sm font-semibold hover:bg-medical-700 transition-all cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              New Consultation
            </button>
          </div>
        )}

        {/* No search results */}
        {!loading && !error && visits.length > 0 && filteredVisits.length === 0 && (
          <div className="text-center py-16">
            <Search className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-500">No consultations match "{searchQuery}"</p>
          </div>
        )}

        {/* Visit Cards */}
        <div className="space-y-3">
          {filteredVisits.map((visit) => (
            <button
              key={visit.consultation_id + visit.visit_date}
              onClick={() => {
                onSelectVisit(visit);
                navigate('/visit-detail');
              }}
              className="w-full group bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm hover:border-medical-300 hover:shadow-md hover:shadow-medical-500/5 transition-all duration-300 text-left cursor-pointer"
            >
              <div className="flex items-start gap-4">
                {/* Avatar */}
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-medical-100 to-medical-200 text-medical-700 flex items-center justify-center font-bold text-sm shrink-0">
                  {visit.patient_name?.split(' ').map(n => n[0]).slice(0, 2).join('') || '?'}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1.5">
                    <h3 className="font-semibold text-slate-900 text-sm">{visit.patient_name}</h3>
                    <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-lg font-medium">
                      {visit.patient_age}y &middot; {visit.patient_gender}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 font-medium mb-1">
                    {visit.diagnosis}
                  </p>
                  <div className="flex items-center gap-3 mt-2">
                    <span className="flex items-center gap-1 text-xs text-slate-400">
                      <Calendar className="w-3 h-3" />
                      {formatDate(visit.visit_date)}
                    </span>
                    <span className="text-slate-300">&middot;</span>
                    <span className="flex items-center gap-1 text-xs text-slate-400">
                      <Clock className="w-3 h-3" />
                      {formatTime(visit.visit_date)}
                    </span>
                    <span className="text-slate-300">&middot;</span>
                    <span className="text-xs text-slate-400">
                      {visit.consultation_id}
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
