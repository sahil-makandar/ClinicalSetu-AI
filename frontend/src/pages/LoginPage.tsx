import { useState } from 'react';
import { Shield, Activity, Stethoscope, Sparkles, ArrowRight, Mail, Lock, User, Phone, KeyRound } from 'lucide-react';
import { demoDoctors } from '../data/sampleConsultations';

type LoginMode = 'select' | 'sso' | 'email';
type UserType = 'doctor' | 'patient';

interface Props {
  onLogin: (doctor: { id: string; name: string; speciality: string; hospital: string }) => void;
  onPatientLogin?: (phone: string) => void;
}

export default function LoginPage({ onLogin, onPatientLogin }: Props) {
  const [loginMode, setLoginMode] = useState<LoginMode>('select');
  const [userType, setUserType] = useState<UserType>('doctor');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);

  const handleEmailLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (userType === 'doctor') {
      if (email === 'doctor@clinicalsetu.in' && password === 'demo123') {
        onLogin(demoDoctors[0]);
      } else {
        setError('Invalid credentials. Try doctor@clinicalsetu.in / demo123');
      }
    } else {
      if (email === 'patient@clinicalsetu.in' && password === 'demo123') {
        onPatientLogin?.(phone || '+919876543210');
      } else {
        setError('Invalid credentials. Try patient@clinicalsetu.in / demo123');
      }
    }
  };

  const handleSSOLogin = (provider: string) => {
    // Mock SSO - in production this would redirect to OAuth
    if (userType === 'doctor') {
      onLogin(demoDoctors[provider === 'google' ? 0 : 1]);
    } else {
      onPatientLogin?.(phone || '+919876543210');
    }
  };

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
            Transform clinical narratives into structured documentation with AI-powered intelligence. One input, five outputs.
          </p>

          {/* Feature Pills */}
          <div className="space-y-3">
            {[
              { icon: '📋', label: 'SOAP Notes', desc: 'Structured clinical documentation' },
              { icon: '👤', label: 'Patient Summaries', desc: 'Plain-language visit reports' },
              { icon: '📨', label: 'Referral Letters', desc: 'Specialist referrals with urgency' },
              { icon: '📄', label: 'Discharge Summaries', desc: 'Formal visit/discharge documents' },
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

          {/* User Type Toggle */}
          <div className="flex bg-slate-100 rounded-xl p-1 mb-6">
            <button
              onClick={() => { setUserType('doctor'); setLoginMode('select'); setError(''); }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                userType === 'doctor' ? 'bg-white text-medical-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Stethoscope className="w-4 h-4" />
              Doctor Portal
            </button>
            <button
              onClick={() => { setUserType('patient'); setLoginMode('sso'); setError(''); setOtpSent(false); setOtp(''); }}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                userType === 'patient' ? 'bg-white text-medical-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <User className="w-4 h-4" />
              Patient Portal
            </button>
          </div>

          {/* Welcome */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              {userType === 'doctor' ? 'Welcome back, Doctor' : 'Patient Portal'}
            </h2>
            <p className="text-slate-500 mt-1.5 text-sm">
              {userType === 'doctor'
                ? 'Select a profile or sign in to access the clinical workspace'
                : 'Sign in with your phone number to view visit summaries'}
            </p>
          </div>

          {/* Doctor Quick Select (only for doctors) */}
          {userType === 'doctor' && loginMode === 'select' && (
            <>
              <div className="space-y-3 mb-5">
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
              <div className="flex items-center gap-3 mb-5">
                <div className="flex-1 h-px bg-slate-200" />
                <span className="text-xs text-slate-400 font-medium">or sign in with</span>
                <div className="flex-1 h-px bg-slate-200" />
              </div>
            </>
          )}

          {/* Patient Phone+OTP Login */}
          {userType === 'patient' && (
            <div className="space-y-4 mb-5">
              {!otpSent ? (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1.5">Phone Number</label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="tel"
                        value={phone}
                        onChange={(e) => { setPhone(e.target.value); setError(''); }}
                        placeholder="+91 98765 43210"
                        className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 bg-white focus:border-medical-400 focus:outline-none text-sm transition-colors"
                      />
                    </div>
                  </div>
                  {error && (
                    <p className="text-xs text-rose-600 bg-rose-50 px-3 py-2 rounded-lg border border-rose-200/60">{error}</p>
                  )}
                  <button
                    onClick={() => {
                      if (!phone.trim()) { setError('Please enter your phone number'); return; }
                      setOtpSent(true);
                      setError('');
                    }}
                    className="w-full py-3 rounded-xl text-white font-semibold text-sm transition-all cursor-pointer shadow-md shadow-medical-600/20 hover:shadow-lg"
                    style={{ background: 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)' }}
                  >
                    Send OTP
                  </button>
                  <p className="text-xs text-slate-400 text-center">
                    Demo: enter any phone number (e.g. <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">+919876543210</code>)
                  </p>
                </>
              ) : (
                <>
                  <div className="text-center mb-2">
                    <p className="text-sm text-slate-600">OTP sent to <strong>{phone}</strong></p>
                    <button onClick={() => { setOtpSent(false); setOtp(''); }} className="text-xs text-medical-600 hover:underline cursor-pointer mt-1">Change number</button>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1.5">Enter OTP</label>
                    <div className="relative">
                      <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="text"
                        value={otp}
                        onChange={(e) => { setOtp(e.target.value); setError(''); }}
                        placeholder="1234"
                        maxLength={4}
                        className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 bg-white focus:border-medical-400 focus:outline-none text-sm transition-colors text-center tracking-[0.5em] font-mono text-lg"
                      />
                    </div>
                  </div>
                  {error && (
                    <p className="text-xs text-rose-600 bg-rose-50 px-3 py-2 rounded-lg border border-rose-200/60">{error}</p>
                  )}
                  <button
                    onClick={() => {
                      if (otp === '1234') {
                        onPatientLogin?.(phone);
                      } else {
                        setError('Invalid OTP. Try 1234');
                      }
                    }}
                    className="w-full py-3 rounded-xl text-white font-semibold text-sm transition-all cursor-pointer shadow-md shadow-medical-600/20 hover:shadow-lg"
                    style={{ background: 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)' }}
                  >
                    Verify & Sign In
                  </button>
                  <p className="text-xs text-slate-400 text-center">
                    Demo OTP: <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">1234</code>
                  </p>
                </>
              )}
            </div>
          )}

          {/* Doctor SSO Buttons */}
          {userType === 'doctor' && (loginMode === 'select' || loginMode === 'sso') && (
            <div className="space-y-2.5 mb-4">
              <button
                onClick={() => handleSSOLogin('google')}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 transition-all cursor-pointer"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                <span className="text-sm font-medium text-slate-700">Continue with Google</span>
              </button>
              <button
                onClick={() => handleSSOLogin('microsoft')}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 transition-all cursor-pointer"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <rect x="1" y="1" width="10" height="10" fill="#F25022"/>
                  <rect x="13" y="1" width="10" height="10" fill="#7FBA00"/>
                  <rect x="1" y="13" width="10" height="10" fill="#00A4EF"/>
                  <rect x="13" y="13" width="10" height="10" fill="#FFB900"/>
                </svg>
                <span className="text-sm font-medium text-slate-700">Continue with Microsoft</span>
              </button>

              <div className="flex items-center gap-3 my-3">
                <div className="flex-1 h-px bg-slate-200" />
                <span className="text-xs text-slate-400 font-medium">or</span>
                <div className="flex-1 h-px bg-slate-200" />
              </div>

              {loginMode === 'sso' ? (
                <button
                  onClick={() => setLoginMode('email')}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border-2 border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 transition-all cursor-pointer"
                >
                  <Mail className="w-4 h-4 text-slate-500" />
                  <span className="text-sm font-medium text-slate-700">Sign in with Email</span>
                </button>
              ) : (
                <button
                  onClick={() => setLoginMode('email')}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-500 hover:text-slate-700 transition-all cursor-pointer"
                >
                  <Mail className="w-4 h-4" />
                  Sign in with Email
                </button>
              )}
            </div>
          )}

          {/* Doctor Email Login Form */}
          {userType === 'doctor' && loginMode === 'email' && (
            <form onSubmit={handleEmailLogin} className="space-y-4 mb-5">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="doctor@clinicalsetu.in"
                    className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 bg-white focus:border-medical-400 focus:outline-none text-sm transition-colors"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="demo123"
                    className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 bg-white focus:border-medical-400 focus:outline-none text-sm transition-colors"
                    required
                  />
                </div>
              </div>
              {error && (
                <p className="text-xs text-rose-600 bg-rose-50 px-3 py-2 rounded-lg border border-rose-200/60">{error}</p>
              )}
              <button
                type="submit"
                className="w-full py-3 rounded-xl text-white font-semibold text-sm transition-all cursor-pointer shadow-md shadow-medical-600/20 hover:shadow-lg"
                style={{ background: 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)' }}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setLoginMode('select')}
                className="w-full text-sm text-slate-500 hover:text-slate-700 py-2 cursor-pointer"
              >
                Back to other sign-in options
              </button>
              <p className="text-xs text-slate-400 text-center">
                Demo: <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">doctor@clinicalsetu.in</code> / <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">demo123</code>
              </p>
            </form>
          )}

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
