import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Mic, MicOff, Send, Loader2, Stethoscope, Sparkles, User, Zap, FileText, UserCheck, FlaskConical, ChevronRight } from 'lucide-react';
import { sampleConsultations } from '../data/sampleConsultations';
import { processConsultation } from '../services/api';
import type { Consultation, ProcessingResult } from '../types';

interface Props {
  doctor: { id: string; name: string; speciality: string; hospital: string };
  consultation: Consultation | null;
  onResult: (result: ProcessingResult, consultation: Consultation) => void;
}

const processingSteps = [
  { label: 'Analyzing clinical narrative...', icon: FileText },
  { label: 'Generating SOAP Note...', icon: Stethoscope },
  { label: 'Creating Patient Summary...', icon: UserCheck },
  { label: 'Drafting Referral Letter...', icon: Send },
  { label: 'Matching Clinical Trials...', icon: FlaskConical },
  { label: 'Validating outputs...', icon: Sparkles },
];

export default function ConsultationPage({ doctor, consultation, onResult }: Props) {
  const navigate = useNavigate();
  const [text, setText] = useState(consultation?.consultation_text || '');
  const [patientName, setPatientName] = useState(consultation?.patient.name || '');
  const [patientAge, setPatientAge] = useState(consultation?.patient.age?.toString() || '');
  const [patientGender, setPatientGender] = useState(consultation?.patient.gender || 'Male');
  const [referralReason, setReferralReason] = useState(consultation?.referral_reason || '');
  const [specialistType, setSpecialistType] = useState(consultation?.specialist_type || '');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState('');
  const [isListening, setIsListening] = useState(false);

  const handleLoadSample = (sample: Consultation) => {
    setText(sample.consultation_text);
    setPatientName(sample.patient.name);
    setPatientAge(sample.patient.age.toString());
    setPatientGender(sample.patient.gender);
    setReferralReason(sample.referral_reason || '');
    setSpecialistType(sample.specialist_type || '');
  };

  const toggleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Voice input is not supported in this browser. Please use Chrome.');
      return;
    }
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (isListening) {
      setIsListening(false);
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';
    recognition.onresult = (event: any) => {
      let transcript = '';
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setText(prev => prev + ' ' + transcript);
    };
    recognition.onend = () => setIsListening(false);
    recognition.start();
    setIsListening(true);
  };

  const handleProcess = async () => {
    if (!text.trim() || !patientName.trim() || !patientAge.trim()) {
      setError('Please fill in the consultation text and patient details.');
      return;
    }

    setIsProcessing(true);
    setError('');
    setCurrentStep(0);

    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < processingSteps.length - 1) return prev + 1;
        return prev;
      });
    }, 3000);

    const consultationData: Consultation = {
      id: consultation?.id || `CONSULT-${Date.now()}`,
      patient: {
        name: patientName,
        age: parseInt(patientAge),
        gender: patientGender,
        patient_id: consultation?.patient.patient_id || `SYN-PT-${Date.now()}`,
      },
      doctor: {
        name: doctor.name,
        speciality: doctor.speciality,
        hospital: doctor.hospital,
      },
      consultation_text: text,
      referral_reason: referralReason || null,
      specialist_type: specialistType || null,
    };

    try {
      const result = await processConsultation(consultationData);
      clearInterval(stepInterval);
      onResult(result, consultationData);
      navigate('/results');
    } catch (err: any) {
      clearInterval(stepInterval);
      setIsProcessing(false);
      setError(
        err.response?.data?.error ||
        err.message ||
        'Failed to process consultation. Please check the API connection and try again.'
      );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-slate-200/60 sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-4">
          <button onClick={() => navigate('/')} className="p-2 hover:bg-slate-100 rounded-xl transition-all cursor-pointer">
            <ArrowLeft className="w-5 h-5 text-slate-500" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-medical-600 to-medical-500 text-white flex items-center justify-center shadow-md shadow-medical-600/20">
              <Stethoscope className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 tracking-tight">New Consultation</h1>
              <p className="text-xs text-slate-500">{doctor.name} &middot; {doctor.speciality}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Processing Overlay */}
      {isProcessing && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-50 flex items-center justify-center">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mx-4 shadow-2xl border border-slate-200/60">
            <div className="text-center mb-8">
              <div className="relative inline-flex items-center justify-center w-20 h-20 mb-5">
                <div className="absolute inset-0 rounded-full bg-medical-100 animate-ping opacity-20" />
                <div className="absolute inset-2 rounded-full bg-medical-50" />
                <Sparkles className="w-8 h-8 text-medical-600 relative z-10 animate-pulse-soft" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">AI Processing</h2>
              <p className="text-sm text-slate-500 mt-1">Generating 4 clinical outputs from your narrative</p>
            </div>

            <div className="space-y-2.5">
              {processingSteps.map((step, i) => {
                const Icon = step.icon;
                return (
                  <div key={i} className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-500 ${
                    i < currentStep ? 'bg-emerald-50' : i === currentStep ? 'bg-medical-50 border border-medical-200/60' : 'bg-slate-50'
                  }`}>
                    {i < currentStep ? (
                      <div className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                      </div>
                    ) : i === currentStep ? (
                      <div className="w-7 h-7 rounded-full bg-medical-100 text-medical-600 flex items-center justify-center">
                        <Loader2 className="w-4 h-4 animate-spin" />
                      </div>
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center">
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                    )}
                    <span className={`text-sm font-medium ${
                      i < currentStep ? 'text-emerald-700' : i === currentStep ? 'text-medical-700' : 'text-slate-400'
                    }`}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>

            <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-center gap-2 text-xs text-slate-400">
              <Zap className="w-3.5 h-3.5 text-medical-400" />
              <span>Powered by Amazon Bedrock Agent (Claude 3 Sonnet)</span>
            </div>
          </div>
        </div>
      )}

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Input Area */}
          <div className="lg:col-span-2 space-y-5">
            {/* Sample Cases */}
            <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="w-4 h-4 text-medical-500" />
                <p className="text-sm font-semibold text-slate-700">Quick Load</p>
                <span className="text-xs text-slate-400 ml-1">Select a sample case</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {sampleConsultations.slice(0, 5).map((sample) => (
                  <button
                    key={sample.id}
                    onClick={() => handleLoadSample(sample)}
                    className="group text-xs bg-medical-50 text-medical-700 pl-3 pr-2.5 py-2 rounded-xl hover:bg-medical-100 border border-medical-200/40 hover:border-medical-300 transition-all duration-200 cursor-pointer flex items-center gap-1.5"
                  >
                    {sample.patient.name.split(' ')[0]} ({sample.patient.age}y)
                    <ChevronRight className="w-3 h-3 text-medical-400 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                ))}
              </div>
            </div>

            {/* Text Input */}
            <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-400" />
                  <label className="text-sm font-semibold text-slate-700">Clinical Narrative</label>
                </div>
                <button
                  onClick={toggleVoiceInput}
                  className={`flex items-center gap-1.5 text-xs px-3 py-2 rounded-xl font-medium transition-all cursor-pointer ${
                    isListening
                      ? 'bg-rose-50 text-rose-600 border border-rose-200 animate-pulse-soft'
                      : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-medical-50 hover:text-medical-600 hover:border-medical-200'
                  }`}
                >
                  {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
                  {isListening ? 'Stop Recording' : 'Voice Input'}
                </button>
              </div>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Enter the clinical consultation narrative here...&#10;&#10;Describe the patient's presentation, examination findings, assessment, and plan as you would during a consultation."
                className="w-full h-72 p-4 bg-slate-50/50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-medical-500/20 focus:border-medical-500 focus:bg-white resize-none transition-all duration-200 leading-relaxed"
              />
              <div className="flex items-center justify-between mt-2.5">
                <span className="text-xs text-slate-400 font-medium">{text.length} characters</span>
                {isListening && (
                  <span className="text-xs text-rose-500 flex items-center gap-1.5 font-medium">
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                    Listening (en-IN)...
                  </span>
                )}
              </div>
            </div>

            {/* Referral Section */}
            <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
              <div className="flex items-center gap-2 mb-3">
                <Send className="w-4 h-4 text-slate-400" />
                <label className="text-sm font-semibold text-slate-700">Referral</label>
                <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-lg">Optional</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input
                  type="text"
                  value={referralReason}
                  onChange={(e) => setReferralReason(e.target.value)}
                  placeholder="Reason for referral..."
                  className="w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-medical-500/20 focus:border-medical-500 focus:bg-white transition-all duration-200"
                />
                <input
                  type="text"
                  value={specialistType}
                  onChange={(e) => setSpecialistType(e.target.value)}
                  placeholder="Specialist type (e.g., Cardiology)..."
                  className="w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-medical-500/20 focus:border-medical-500 focus:bg-white transition-all duration-200"
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-start gap-3">
                <div className="w-5 h-5 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center shrink-0 mt-0.5">!</div>
                <p className="text-sm text-rose-700">{error}</p>
              </div>
            )}

            {/* Process Button */}
            <button
              onClick={handleProcess}
              disabled={isProcessing || !text.trim()}
              className="w-full flex items-center justify-center gap-2.5 py-4 rounded-2xl font-semibold text-sm transition-all duration-300 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-white shadow-lg shadow-medical-600/20 hover:shadow-xl hover:shadow-medical-600/30"
              style={{ background: 'linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%)' }}
            >
              <Sparkles className="w-5 h-5" />
              Process with AI
            </button>
          </div>

          {/* Sidebar - Patient Context */}
          <div className="space-y-5">
            <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
              <div className="flex items-center gap-2 mb-4">
                <User className="w-4 h-4 text-medical-500" />
                <h3 className="text-sm font-semibold text-slate-700">Patient Details</h3>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-slate-500 font-medium block mb-1.5">Patient Name</label>
                  <input
                    type="text"
                    value={patientName}
                    onChange={(e) => setPatientName(e.target.value)}
                    placeholder="Full name"
                    className="w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-medical-500/20 focus:border-medical-500 focus:bg-white transition-all duration-200"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-slate-500 font-medium block mb-1.5">Age</label>
                    <input
                      type="number"
                      value={patientAge}
                      onChange={(e) => setPatientAge(e.target.value)}
                      placeholder="Age"
                      className="w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-medical-500/20 focus:border-medical-500 focus:bg-white transition-all duration-200"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 font-medium block mb-1.5">Gender</label>
                    <select
                      value={patientGender}
                      onChange={(e) => setPatientGender(e.target.value)}
                      className="w-full px-3.5 py-2.5 bg-slate-50/50 border border-slate-200 rounded-xl text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-medical-500/20 focus:border-medical-500 focus:bg-white transition-all duration-200"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* How it works */}
            <div className="rounded-2xl border border-medical-200/40 p-5 overflow-hidden" style={{ background: 'linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 50%, #f0fdf4 100%)' }}>
              <h3 className="text-sm font-bold text-medical-900 mb-4">How it works</h3>
              <div className="space-y-3">
                {[
                  { step: '1', text: 'Enter your clinical narrative' },
                  { step: '2', text: 'AI Agent generates 4 structured outputs' },
                  { step: '3', text: 'Review and edit each section' },
                  { step: '4', text: 'Approve and finalize documentation' },
                ].map((item) => (
                  <div key={item.step} className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-lg bg-medical-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
                      {item.step}
                    </div>
                    <p className="text-xs text-medical-800 font-medium leading-relaxed pt-0.5">{item.text}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Transparency */}
            <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
              <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-medical-500" />
                AI Transparency
              </h3>
              <div className="space-y-2.5">
                {[
                  { label: 'Architecture', value: 'Bedrock Agent + Tool Use' },
                  { label: 'Model', value: 'Claude 3 Sonnet' },
                  { label: 'Trial Search', value: 'RAG via Knowledge Bases' },
                  { label: 'Outputs', value: 'SOAP, Summary, Referral, Trials' },
                  { label: 'Data', value: 'Synthetic only (no real PHI)' },
                ].map((item) => (
                  <div key={item.label} className="flex items-start gap-2">
                    <span className="text-xs font-semibold text-slate-500 w-20 shrink-0">{item.label}</span>
                    <span className="text-xs text-slate-600">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
