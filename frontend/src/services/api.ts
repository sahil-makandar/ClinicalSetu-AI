import axios from 'axios';
import type { Consultation, ProcessingResult } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 min — multi-agent orchestration can take time
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function processConsultation(consultation: Consultation): Promise<ProcessingResult> {
  // Always use multi-agent path — supervisor decides which agents to invoke
  // Falls back to monolithic internally if agent system is unavailable
  const response = await api.post('/api/process-agent', consultation);
  // Handle Lambda proxy response (body may be stringified)
  const data = typeof response.data.body === 'string'
    ? JSON.parse(response.data.body)
    : response.data;
  return data;
}

export async function translateSummary(summary: Record<string, unknown>, targetLanguage: string): Promise<Record<string, unknown>> {
  const response = await api.post('/api/translate', { summary, target_language: targetLanguage });
  const data = typeof response.data.body === 'string'
    ? JSON.parse(response.data.body)
    : response.data;
  return data.translated_summary || data;
}

export default api;
