import { Shield, Activity, Stethoscope, Sparkles, ArrowRight } from 'lucide-react';
import { demoDoctors } from '../data/sampleConsultations';

interface Props {
  onLogin: (doctor: { id: string; name: string; speciality: string; hospital: string }) => void;
}

export default function LoginPage({ onLogin }: Props) {
  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Hero */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #042f2e 0%, #115e59 40%, #0f766e 70%, #0d9488 100%)' }}>
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-64 h-64 rounded-full bg-white/20 blur-3xl animate-float" />
          <div className="absolute bottom-32 right-16 w-80 h-80 rounded-full bg-teal-300/20 blur-3xl" style={{ animationDelay: '3s', animation: 'float 8s ease-in-out infinite' }} />
          <div className="absolute top-1/2 left-1/3 w-40 h-40 rounded-full bg-emerald-400/10 blur-2xl" style={{ animationDelay: '1.5s', animation: 'float 7s ease-in-out infinite' }} />
        </div>

        <div className="relative z-10 flex flex-col justify-center px-16 py-12">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-sm flex items-center justify-center border border-white/20">
              <Stethoscope className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">ClinicalSetu</h1>
              <p className="text-teal-200/80 text-xs font-medium tracking-wide uppercase">AI Clinical Intelligence</p>
            </div>
          </div>

          <h2 className="text-4xl font-bold text-white leading-tight mb-4">
            Capture Once.<br />
            <span className="text-teal-200">Reuse Responsibly.</span>
          </h2>
          <p className="text-teal-100/70 text-base leading-relaxed max-w-md mb-10">
            Transform clinical narratives into structured documentation with AI-powered intelligence. One input, four outputs.
          </p>

          {/* Feature Pills */}
          <div className="space-y-3">
            {[
              { icon: '📋', label: 'SOAP Notes', desc: 'Structured clinical documentation' },
              { icon: '👤', label: 'Patient Summaries', desc: 'Plain-language visit reports' },
              { icon: '📨', label: 'Referral Letters', desc: 'Specialist referrals with urgency' },
              { icon: '🔬', label: 'Trial Matching', desc: 'RAG-powered clinical trial search' },
            ].map((f, i) => (
              <div key={i} className="flex items-center gap-4 bg-white/8 backdrop-blur-sm rounded-xl px-4 py-3 border border-white/10">
                <span className="text-xl">{f.icon}</span>
                <div>
                  <p className="text-white text-sm font-semibold">{f.label}</p>
                  <p className="text-teal-200/60 text-xs">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel - Login */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 bg-gradient-to-br from-slate-50 via-white to-medical-50/30">
        <div className="max-w-md w-full">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-medical-600 text-white mb-3">
              <Stethoscope className="w-7 h-7" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">ClinicalSetu</h1>
            <p className="text-medical-600 text-xs font-semibold tracking-wide uppercase mt-1">AI Clinical Intelligence</p>
          </div>

          {/* Welcome */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Welcome back</h2>
            <p className="text-slate-500 mt-1.5">Select a doctor profile to explore the prototype</p>
          </div>

          {/* Doctor Profiles */}
          <div className="space-y-3 mb-6">
            {demoDoctors.map((doc) => (
              <button
                key={doc.id}
                onClick={() => onLogin(doc)}
                className="w-full group flex items-center gap-4 p-4 rounded-2xl border-2 border-slate-100 bg-white hover:border-medical-400 hover:shadow-lg hover:shadow-medical-500/10 transition-all duration-300 text-left cursor-pointer"
              >
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-medical-500 to-medical-600 text-white flex items-center justify-center font-bold text-base shrink-0 shadow-md shadow-medical-500/20">
                  {doc.avatar}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-900 text-base">{doc.name}</p>
                  <p className="text-sm text-slate-500 mt-0.5">{doc.speciality}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{doc.hospital}</p>
                </div>
                <ArrowRight className="w-5 h-5 text-slate-300 group-hover:text-medical-500 group-hover:translate-x-1 transition-all duration-300 shrink-0" />
              </button>
            ))}
          </div>

          {/* Disclaimer */}
          <div className="p-4 bg-amber-50/80 border border-amber-200/60 rounded-xl backdrop-blur-sm">
            <div className="flex gap-3">
              <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-amber-800 mb-1">Prototype Disclaimer</p>
                <p className="text-xs text-amber-700/80 leading-relaxed">
                  Uses <strong>synthetic data only</strong>. No real patient information is processed. All AI outputs require clinician validation before use.
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-medical-400" />
                <span>Powered by Amazon Bedrock</span>
              </div>
              <span>Team Sahrova</span>
            </div>
            <div className="flex items-center justify-center gap-2 mt-3">
              <Activity className="w-3 h-3 text-medical-400" />
              <span className="text-xs text-slate-400">AI for Bharat Hackathon 2026</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
