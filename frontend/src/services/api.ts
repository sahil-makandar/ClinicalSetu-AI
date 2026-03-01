import axios from 'axios';
import type { Consultation, ProcessingResult } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 min timeout for Bedrock processing
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function processConsultation(consultation: Consultation): Promise<ProcessingResult> {
  const response = await api.post('/api/process', consultation);
  // Handle Lambda proxy response (body may be stringified)
  const data = typeof response.data.body === 'string'
    ? JSON.parse(response.data.body)
    : response.data;
  return data;
}

export default api;
