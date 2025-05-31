import axios from 'axios';
import type { ReactSymptomAnalysisOutput, ReactAnalysisRequest } from '../types';
// This VITE_API_URL should be set in your React app's .env file (e.g., Symptom/.env.local)
// For example: VITE_API_URL=http://localhost:8000/api/v1
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'; 




const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // If your main FastAPI endpoint for /symptoms/analyze requires an API key via this header, add it.
    // Otherwise, remove or make conditional. For an internal app part, usually not needed.
    // 'X-API-Key': import.meta.env.VITE_SOME_INTERNAL_API_KEY, 
  },
});

export const analyzeSymptomsReact = async (
    data: ReactAnalysisRequest 
): Promise<ReactSymptomAnalysisOutput> => {
  try {
    const response = await apiClient.post<ReactSymptomAnalysisOutput>('/symptoms/analyze', data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      console.error("Symptom Analysis API Error - Response Data:", error.response.data);
      console.error("Symptom Analysis API Error - Response Status:", error.response.status);
      // Try to give a more specific error message from the backend if possible
      const detail = error.response.data?.detail || error.response.data?.message || `Failed to analyze symptoms. Status: ${error.response.status}`;
      throw new Error(String(detail));
    }
    console.error("Symptom Analysis Network/Unknown Error:", error);
    throw new Error('Failed to analyze symptoms due to a network issue or an unknown error.');
  }
};

export const checkApiHealthReact = async (): Promise<boolean> => {
  try {
    const response = await apiClient.get('/health'); 
    return response.data.status === 'healthy';
  } catch (error) {
    console.error("API Health Check Failed:", error);
    return false;
  }
};

export default {
  analyzeSymptomsReact,
  checkApiHealthReact,
};