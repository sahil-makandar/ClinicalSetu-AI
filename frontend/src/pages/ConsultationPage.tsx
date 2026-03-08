import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Mic, MicOff, Send, Loader2, Stethoscope, Sparkles, User, Zap, FileText, UserCheck, FlaskConical, ChevronRight, Globe, Type, AudioLines, Bot, ArrowRight } from 'lucide-react';
import { sampleConsultations } from '../data/sampleConsultations';
import { processConsultation } from '../services/api';
import { startTranscription, isTranscribeConfigured, type TranscribeSession } from '../services/transcribeService';
import type { Consultation, ProcessingResult } from '../types';

interface Props {
  doctor: { id: string; name: string; speciality: string; hospital: string };
  consultation: Consultation | null;
  onResult: (result: ProcessingResult, consultation: Consultation) => void;
}

// Activity log messages — simulates real-time multi-agent orchestration trace
const agentActivityLog = [
  { agent: 'Supervisor', message: 'Received consultation narrative. Analyzing input...', delay: 0 },
  { agent: 'Supervisor', message: 'Routing to SOAPAgent for structured documentation.', delay: 2000 },
  { agent: 'SOAPAgent', message: 'Parsing clinical narrative...', delay: 3500 },
  { agent: 'SOAPAgent', message: 'Extracting subjective findings, vitals, assessment...', delay: 6000 },
  { agent: 'SOAPAgent', message: 'SOAP Note generated. Returning to Supervisor.', delay: 10000 },
  { agent: 'Supervisor', message: 'SOAP Note received. Dispatching to 3 specialist agents in parallel.', delay: 12000 },
  { agent: 'SummaryAgent', message: 'Creating patient-friendly summary from SOAP Note...', delay: 13000 },
  { agent: 'ReferralAgent', message: 'Generating discharge summary from SOAP Note...', delay: 13500 },
  { agent: 'TrialAgent', message: 'Extracting patient profile for trial matching...', delay: 14000 },
  { agent: 'SummaryAgent', message: 'Translating medical terms to plain language...', delay: 17000 },
  { agent: 'ReferralAgent', message: 'Drafting referral letter with urgency scoring...', delay: 18000 },
  { agent: 'TrialAgent', message: 'Matching against clinical trials database...', delay: 19000 },
  { agent: 'SummaryAgent', message: 'Patient summary complete.', delay: 21000 },
  { agent: 'ReferralAgent', message: 'Discharge summary + referral letter complete.', delay: 23000 },
  { agent: 'TrialAgent', message: 'Found matching trials. Computing confidence scores...', delay: 25000 },
  { agent: 'TrialAgent', message: 'Trial matching complete.', delay: 28000 },
  { agent: 'Supervisor', message: 'All agents complete. Assembling final results...', delay: 30000 },
];

const agentColors: Record<string, string> = {
  'Supervisor': 'text-indigo-600 bg-indigo-50 border-indigo-200/60',
  'SOAPAgent': 'text-teal-600 bg-teal-50 border-teal-200/60',
  'SummaryAgent': 'text-sky-600 bg-sky-50 border-sky-200/60',
  'ReferralAgent': 'text-amber-600 bg-amber-50 border-amber-200/60',
  'TrialAgent': 'text-violet-600 bg-violet-50 border-violet-200/60',
};

const agentIcons: Record<string, typeof Sparkles> = {
  'Supervisor': Zap,
  'SOAPAgent': Stethoscope,
  'SummaryAgent': UserCheck,
  'ReferralAgent': Send,
  'TrialAgent': FlaskConical,
};

const supportedLanguages = [
  { code: 'en-IN', label: 'English', short: 'EN' },
  { code: 'hi-IN', label: 'Hindi', short: 'HI' },
  { code: 'ta-IN', label: 'Tamil', short: 'TA' },
  { code: 'te-IN', label: 'Telugu', short: 'TE' },
  { code: 'mr-IN', label: 'Marathi', short: 'MR' },
  { code: 'bn-IN', label: 'Bengali', short: 'BN' },
  { code: 'kn-IN', label: 'Kannada', short: 'KN' },
  { code: 'gu-IN', label: 'Gujarati', short: 'GU' },
  { code: 'ml-IN', label: 'Malayalam', short: 'ML' },
];

export default function ConsultationPage({ doctor, consultation, onResult }: Props) {
  const navigate = useNavigate();
  const [text, setText] = useState(consultation?.consultation_text || '');
  const [patientName, setPatientName] = useState(consultation?.patient.name || '');
  const [patientAge, setPatientAge] = useState(consultation?.patient.age?.toString() || '');
  const [patientGender, setPatientGender] = useState(consultation?.patient.gender || 'Male');
  const [patientPhone, setPatientPhone] = useState(consultation?.patient.phone || '');
  const [referralReason, setReferralReason] = useState(consultation?.referral_reason || '');
  const [specialistType, setSpecialistType] = useState(consultation?.specialist_type || '');
  const [isProcessing, setIsProcessing] = useState(false);
  const [visibleLogs, setVisibleLogs] = useState<number>(0);
  const [processingStartTime, setProcessingStartTime] = useState<number>(0);
  const [error, setError] = useState('');
  const logEndRef = useRef<HTMLDivElement>(null);
  const [isListening, setIsListening] = useState(false);
  const [inputMode, setInputMode] = useState<'voice' | 'text'>('voice');
  const [detectedLang, setDetectedLang] = useState('Auto-detect');
  const [audioLevel, setAudioLevel] = useState<number[]>(new Array(32).fill(5));
  const [interimText, setInterimText] = useState('');
  const transcribeSessionRef = useRef<TranscribeSession | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);
  const finalTranscriptRef = useRef<string>('');

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      if (transcribeSessionRef.current) { try { transcribeSessionRef.current.stop(); } catch {} }
    };
  }, []);

  // Auto-advance activity log entries based on their delay timings
  useEffect(() => {
    if (!isProcessing) return;
    const timers = agentActivityLog.map((entry, i) =>
      setTimeout(() => setVisibleLogs(prev => Math.max(prev, i + 1)), entry.delay)
    );
    return () => timers.forEach(clearTimeout);
  }, [isProcessing]);

  // Auto-scroll log to bottom when new entries appear
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [visibleLogs]);

  // Tick elapsed timer every second during processing
  const [, setTick] = useState(0);
  useEffect(() => {
    if (!isProcessing) return;
    const t = setInterval(() => setTick(v => v + 1), 1000);
    return () => clearInterval(t);
  }, [isProcessing]);

  // Audio visualizer - uses existing media stream from Transcribe
  const startAudioVisualizer = useCallback((stream: MediaStream) => {
    try {
      streamRef.current = stream;
      const ctx = new AudioContext();
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      src.connect(analyser);
      analyserRef.current = analyser;

      const updateBars = () => {
        const data = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(data);
        const bars = Array.from(data).slice(0, 32).map(v => Math.max(5, (v / 255) * 100));
        setAudioLevel(bars);
        animFrameRef.current = requestAnimationFrame(updateBars);
      };
      updateBars();
    } catch {
      // If visualizer fails, transcription still works
    }
  }, []);

  const stopAudioVisualizer = useCallback(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    setAudioLevel(new Array(32).fill(5));
  }, []);

  const handleLoadSample = (sample: Consultation) => {
    setText(sample.consultation_text);
    setPatientName(sample.patient.name);
    setPatientAge(sample.patient.age.toString());
    setPatientGender(sample.patient.gender);
    setReferralReason(sample.referral_reason || '');
    setSpecialistType(sample.specialist_type || '');
    setPatientPhone(sample.patient.phone || '+919876543210');
    setInputMode('text');
  };

  const toggleVoiceInput = async () => {
    if (isListening) {
      transcribeSessionRef.current?.stop();
      transcribeSessionRef.current = null;
      setIsListening(false);
      stopAudioVisualizer();
      return;
    }

    // Check if Transcribe Medical is configured; fall back to Web Speech API if not
    if (!isTranscribeConfigured()) {
      if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        setError('Voice input not available. Configure Amazon Transcribe Medical or use Chrome.');
        return;
      }
      // Fallback to Web Speech API for local development
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-IN';

      recognition.onresult = (event: any) => {
        let final = '';
        let interim = '';
        for (let i = 0; i < event.results.length; i++) {
          const t = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            final += t + ' ';
          } else {
            interim = t;
          }
        }
        if (final) setText(prev => (prev + ' ' + final).trim());
        setInterimText(interim);
      };

      recognition.onerror = (event: any) => {
        if (event.error !== 'no-speech') setError(`Voice recognition error: ${event.error}`);
      };

      recognition.onend = () => {
        setIsListening(false);
        setInterimText('');
        stopAudioVisualizer();
      };

      recognition.start();
      setIsListening(true);
      setDetectedLang('English (browser fallback)');
      // Get mic stream for visualizer
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        startAudioVisualizer(stream);
      } catch {}
      // Store stop fn
      transcribeSessionRef.current = {
        stop: () => { try { recognition.stop(); } catch {} },
        stream: new MediaStream(),
      };
      return;
    }

    // Amazon Transcribe Medical streaming
    try {
      finalTranscriptRef.current = text; // preserve existing text
      const session = await startTranscription(
        (transcript, isFinal) => {
          if (isFinal) {
            finalTranscriptRef.current = (finalTranscriptRef.current + ' ' + transcript).trim();
            setText(finalTranscriptRef.current);
            setInterimText('');
          } else {
            setInterimText(transcript);
          }
        },
        (errorMsg) => {
          setError(`Transcription error: ${errorMsg}`);
          setIsListening(false);
          stopAudioVisualizer();
        },
      );

      transcribeSessionRef.current = session;
      setIsListening(true);
      setDetectedLang('English (Medical)');
      startAudioVisualizer(session.stream);
    } catch (err: any) {
      setError(err.message || 'Failed to start Amazon Transcribe Medical');
    }
  };

  const handleProcess = async () => {
    if (!text.trim() || !patientName.trim() || !patientAge.trim() || !patientPhone.trim()) {
      setError('Please fill in the consultation text, patient details, and phone number.');
      return;
    }

    if (isListening) {
      transcribeSessionRef.current?.stop();
      transcribeSessionRef.current = null;
      setIsListening(false);
      stopAudioVisualizer();
    }

    setIsProcessing(true);
    setError('');
    setVisibleLogs(0);
    setProcessingStartTime(Date.now());

    const consultationData: Consultation = {
      id: consultation?.id || `CONSULT-${Date.now()}`,
      patient: {
        name: patientName,
        age: parseInt(patientAge),
        gender: patientGender,
        patient_id: consultation?.patient.patient_id || `SYN-PT-${Date.now()}`,
        phone: patientPhone,
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
      onResult(result, consultationData);
      navigate('/results');
    } catch (err: any) {
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
          {/* Mode Toggle */}
          <div className="ml-auto flex items-center bg-slate-100 rounded-xl p-1">
            <button
              onClick={() => setInputMode('voice')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                inputMode === 'voice' ? 'bg-white text-medical-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Mic className="w-3.5 h-3.5" />
              Voice
            </button>
            <button
              onClick={() => setInputMode('text')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                inputMode === 'text' ? 'bg-white text-medical-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Type className="w-3.5 h-3.5" />
              Text
            </button>
          </div>
        </div>
      </header>

      {/* Processing — Full-page inline view */}
      {isProcessing && (
        <div className="fixed inset-0 bg-slate-50 z-50 overflow-y-auto">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
            {/* Processing Header */}
            <div className="text-center mb-8">
              <div className="relative inline-flex items-center justify-center mb-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center shadow-xl shadow-indigo-500/20">
                  <Bot className="w-8 h-8 text-white" />
                </div>
                <span className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-400 border-3 border-white" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Multi-Agent AI Processing</h2>
              <p className="text-sm text-slate-500 mt-1">Supervisor coordinating 4 specialist agents</p>
              <div className="flex items-center justify-center gap-2 mt-3">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Live</span>
                <span className="text-slate-300 mx-1">&middot;</span>
                <span className="text-xs font-mono text-slate-400">
                  {((Date.now() - processingStartTime) / 1000).toFixed(0)}s elapsed
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              {/* Agent Progress Cards - Left */}
              <div className="lg:col-span-2 space-y-4">
                <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider px-1">Agent Status</h3>
                {(['Supervisor', 'SOAPAgent', 'SummaryAgent', 'ReferralAgent', 'TrialAgent'] as const).map((agent) => {
                  const Icon = agentIcons[agent] || Bot;
                  const colorClass = agentColors[agent] || 'text-slate-600 bg-slate-50 border-slate-200/60';
                  const agentLogs = agentActivityLog.filter(l => l.agent === agent);
                  const visibleAgentLogs = agentLogs.filter((_, i) => {
                    const globalIdx = agentActivityLog.indexOf(agentLogs[i]);
                    return globalIdx < visibleLogs;
                  });
                  const lastLog = visibleAgentLogs[visibleAgentLogs.length - 1];
                  const isDone = lastLog?.message.includes('complete') || lastLog?.message.includes('received');
                  const isActive = visibleAgentLogs.length > 0 && !isDone;

                  return (
                    <div
                      key={agent}
                      className={`bg-white rounded-xl border p-4 transition-all duration-500 ${
                        isActive ? 'border-indigo-200 shadow-md shadow-indigo-500/5' :
                        isDone ? 'border-emerald-200 bg-emerald-50/30' :
                        'border-slate-200/60 opacity-50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-9 h-9 rounded-lg flex items-center justify-center border ${colorClass}`}>
                          {isActive ? <Loader2 className="w-4 h-4 animate-spin" /> : <Icon className="w-4 h-4" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-slate-800">{agent}</span>
                            {isDone && <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">Done</span>}
                            {isActive && <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded animate-pulse">Active</span>}
                          </div>
                          <p className="text-xs text-slate-500 truncate mt-0.5">
                            {lastLog?.message || 'Waiting...'}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Activity Log - Right */}
              <div className="lg:col-span-3">
                <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider px-1 mb-4">Activity Log</h3>
                <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
                  <div className="h-[460px] overflow-y-auto px-4 py-3 space-y-1.5 bg-slate-50/30">
                    {agentActivityLog.slice(0, visibleLogs).map((entry, i) => {
                      const Icon = agentIcons[entry.agent] || Bot;
                      const colorClass = agentColors[entry.agent] || 'text-slate-600 bg-slate-50 border-slate-200/60';
                      const isLatest = i === visibleLogs - 1;
                      const elapsedSec = (entry.delay / 1000).toFixed(1);
                      return (
                        <div
                          key={i}
                          className={`flex items-start gap-2.5 px-3 py-2.5 rounded-lg transition-all duration-300 ${
                            isLatest ? 'bg-white border border-slate-200/60 shadow-sm' : ''
                          }`}
                          style={{ animation: isLatest ? 'fadeInUp 0.3s ease-out' : undefined }}
                        >
                          <div className={`w-7 h-7 rounded-md flex items-center justify-center shrink-0 mt-0.5 border ${colorClass}`}>
                            {isLatest ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Icon className="w-3.5 h-3.5" />}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className={`text-[10px] font-bold uppercase tracking-wider ${colorClass.split(' ')[0]}`}>
                                {entry.agent}
                              </span>
                              <span className="text-[10px] text-slate-300">{elapsedSec}s</span>
                            </div>
                            <p className={`text-xs leading-relaxed ${isLatest ? 'text-slate-700 font-medium' : 'text-slate-500'}`}>
                              {entry.message}
                            </p>
                          </div>
                          {(entry.message.includes('Routing') || entry.message.includes('Dispatching')) && (
                            <ArrowRight className="w-3.5 h-3.5 text-indigo-300 shrink-0 mt-1.5" />
                          )}
                        </div>
                      );
                    })}
                    {visibleLogs < agentActivityLog.length && (
                      <div className="flex items-center gap-2 px-3 py-2">
                        <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                        <span className="text-xs text-slate-400 animate-pulse">Processing...</span>
                      </div>
                    )}
                    <div ref={logEndRef} />
                  </div>

                  {/* Footer */}
                  <div className="px-5 py-3 border-t border-slate-100 bg-white flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <Zap className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Amazon Bedrock &middot; Nova Lite</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[10px] text-slate-400">5 outputs from 1 input</span>
                      <span className="text-[10px] font-mono text-slate-300">
                        {((Date.now() - processingStartTime) / 1000).toFixed(0)}s
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Patient context bar at bottom */}
            <div className="mt-6 bg-white rounded-xl border border-slate-200/60 px-5 py-3 flex items-center gap-4 text-xs text-slate-500">
              <span className="font-semibold text-slate-700">{patientName}</span>
              <span className="text-slate-300">|</span>
              <span>{patientAge}y &middot; {patientGender}</span>
              <span className="text-slate-300">|</span>
              <span>{doctor.name} &middot; {doctor.speciality}</span>
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

            {/* Voice Input Mode */}
            {inputMode === 'voice' && (
              <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
                {/* Voice Hero Area */}
                <div className="relative flex flex-col items-center justify-center py-10 px-6" style={{ background: 'linear-gradient(180deg, #f0fdfa 0%, #ffffff 100%)' }}>
                  {/* Language Detection Badge */}
                  <div className="flex items-center gap-2 mb-6">
                    <Globe className="w-3.5 h-3.5 text-medical-500" />
                    <span className="text-xs font-semibold text-medical-700 bg-medical-50 border border-medical-200/50 px-3 py-1 rounded-full">
                      {isListening ? `Detecting: ${detectedLang}` : 'Multi-language Auto-detect'}
                    </span>
                  </div>

                  {/* Waveform Visualizer */}
                  <div className="flex items-center justify-center gap-[3px] h-20 mb-6 w-full max-w-sm">
                    {audioLevel.map((level, i) => (
                      <div
                        key={i}
                        className={`w-[6px] rounded-full transition-all ${
                          isListening
                            ? 'bg-gradient-to-t from-medical-500 to-medical-300'
                            : 'bg-slate-200'
                        }`}
                        style={{
                          height: `${isListening ? level : 5}%`,
                          transitionDuration: isListening ? '80ms' : '300ms',
                          opacity: isListening ? 0.7 + (level / 300) : 0.4,
                        }}
                      />
                    ))}
                  </div>

                  {/* Big Mic Button */}
                  <button
                    onClick={toggleVoiceInput}
                    className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer ${
                      isListening
                        ? 'bg-rose-500 shadow-xl shadow-rose-500/30 scale-110'
                        : 'bg-gradient-to-br from-medical-600 to-medical-500 shadow-xl shadow-medical-600/30 hover:scale-105 hover:shadow-2xl hover:shadow-medical-600/40'
                    }`}
                  >
                    {/* Pulse rings when listening */}
                    {isListening && (
                      <>
                        <span className="absolute inset-0 rounded-full bg-rose-400 animate-ping opacity-20" />
                        <span className="absolute -inset-3 rounded-full border-2 border-rose-300 opacity-30 animate-pulse" />
                        <span className="absolute -inset-6 rounded-full border border-rose-200 opacity-20 animate-pulse" style={{ animationDelay: '0.5s' }} />
                      </>
                    )}
                    {isListening ? (
                      <MicOff className="w-10 h-10 text-white relative z-10" />
                    ) : (
                      <Mic className="w-10 h-10 text-white relative z-10" />
                    )}
                  </button>

                  <p className={`mt-5 text-sm font-medium ${isListening ? 'text-rose-600' : 'text-slate-500'}`}>
                    {isListening ? 'Tap to stop recording' : 'Tap to start recording'}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {isListening ? (
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                        Recording &middot; Amazon Transcribe Medical
                      </span>
                    ) : 'Powered by Amazon Transcribe Medical &middot; Clinical vocabulary optimized'}
                  </p>

                  {/* Supported Languages Grid */}
                  {!isListening && (
                    <div className="flex flex-wrap justify-center gap-1.5 mt-4">
                      {supportedLanguages.map(lang => (
                        <span key={lang.code} className="text-[10px] font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md">
                          {lang.label}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Live Transcript Area */}
                <div className="border-t border-slate-200/60 p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <AudioLines className="w-4 h-4 text-slate-400" />
                    <span className="text-xs font-semibold text-slate-600">Live Transcript</span>
                    {text && <span className="text-[10px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md ml-auto">{text.split(/\s+/).filter(Boolean).length} words</span>}
                  </div>
                  <div className="min-h-[120px] max-h-[200px] overflow-y-auto p-3 bg-slate-50/50 border border-slate-200 rounded-xl">
                    {text || interimText ? (
                      <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                        {text}
                        {interimText && <span className="text-slate-400 italic"> {interimText}</span>}
                      </p>
                    ) : (
                      <p className="text-sm text-slate-400 italic">
                        Your transcription will appear here in real-time...
                      </p>
                    )}
                  </div>
                  {text && (
                    <div className="flex items-center gap-2 mt-2">
                      <button
                        onClick={() => { setText(''); setInterimText(''); }}
                        className="text-xs text-slate-500 hover:text-rose-500 cursor-pointer px-2 py-1 rounded-lg hover:bg-rose-50 transition-all"
                      >
                        Clear
                      </button>
                      <button
                        onClick={() => setInputMode('text')}
                        className="text-xs text-slate-500 hover:text-medical-600 cursor-pointer px-2 py-1 rounded-lg hover:bg-medical-50 transition-all"
                      >
                        Edit as text
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Text Input Mode */}
            {inputMode === 'text' && (
              <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-400" />
                    <label className="text-sm font-semibold text-slate-700">Clinical Narrative</label>
                  </div>
                  <button
                    onClick={() => setInputMode('voice')}
                    className="flex items-center gap-1.5 text-xs px-3 py-2 rounded-xl font-medium transition-all cursor-pointer bg-slate-50 text-slate-600 border border-slate-200 hover:bg-medical-50 hover:text-medical-600 hover:border-medical-200"
                  >
                    <Mic className="w-3.5 h-3.5" />
                    Switch to Voice
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
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Globe className="w-3 h-3" /> Multi-language supported
                  </span>
                </div>
              </div>
            )}

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
                <div>
                  <label className="text-xs text-slate-500 font-medium block mb-1.5">Phone Number</label>
                  <input
                    type="tel"
                    value={patientPhone}
                    onChange={(e) => setPatientPhone(e.target.value)}
                    placeholder="+91 98765 43210"
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
                  { step: '1', text: 'Record or type your clinical narrative' },
                  { step: '2', text: 'AI auto-detects language & generates 5 outputs' },
                  { step: '3', text: 'Review, translate & edit each section' },
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
            <div className="rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
              <div className="px-5 py-3.5 bg-gradient-to-r from-indigo-50 to-violet-50 border-b border-indigo-100/60">
                <h3 className="text-sm font-bold text-indigo-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-500" />
                  AI Transparency
                </h3>
              </div>
              <div className="bg-white p-4 space-y-3">
                <div className="flex items-center gap-2 p-2.5 bg-indigo-50/50 rounded-xl border border-indigo-100/40">
                  <Zap className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                  <span className="text-[11px] font-semibold text-indigo-800">Multi-Agent Collaboration</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: 'Model', value: 'Nova Lite' },
                    { label: 'Fallback', value: 'Nova Micro' },
                    { label: 'Voice', value: 'Transcribe Medical' },
                    { label: 'Languages', value: '9 Indian' },
                    { label: 'Cache', value: 'DynamoDB 24h' },
                    { label: 'Data', value: 'Synthetic only' },
                  ].map((item) => (
                    <div key={item.label} className="text-center p-2 bg-slate-50 rounded-lg">
                      <p className="text-[10px] font-medium text-slate-400 uppercase">{item.label}</p>
                      <p className="text-[11px] font-semibold text-slate-700 mt-0.5">{item.value}</p>
                    </div>
                  ))}
                </div>
                <p className="text-[10px] text-slate-400 text-center pt-1">Supervisor + 4 Specialist Agents &middot; 5 outputs from 1 input</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
