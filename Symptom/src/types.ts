// Symptom/src/types.ts
export interface SymptomInput { // Matches React Hook Form and FastAPI model
  id?: string; // Optional on input, assigned by context
  description: string;
  duration: string;
  severity: number; // 1, 2, or 3
}

export interface AISchemeInfo { // Matches FastAPI model
  name: string;
  region_specific?: string;
  description?: string;
  url?: string;
  source_info?: string;
}

export interface ReactConditionOutput { // Matches FastAPI model
  name: string;
  probability: number;
  description: string;
  recommendation: string;
}

// Structure for the main response from backend's /symptoms/analyze
export interface ReactSymptomAnalysisOutput {
  id: string;
  date: string;
  symptoms: SymptomInputForRequest[]; // Backend echoes back symptoms in this format
  possible_conditions: ReactConditionOutput[];
  general_advice: string;
  should_seek_medical_attention: boolean;
  government_schemes?: AISchemeInfo[];
  doctor_specialties_recommended?: string[];
}

// Request payload for the /symptoms/analyze endpoint
export interface ReactAnalysisRequest {
    symptoms: SymptomInputForRequest[];
    user_region?: string;
    history_context_string?: string;
}

// Symptom as defined in the form and context (can have client-side ID)
export interface SymptomUI extends SymptomInputForRequest {
  id: string; 
}

// Symptom structure for API request (matches backend Pydantic model)
export interface SymptomInputForRequest {
  description: string;
  duration: string;
  severity: number;
}

export interface BackendAnalysisResult {
  id: string; // Analysis ID from backend
  date: string; // ISO string from backend
  symptoms: SymptomInputForRequest[]; // Symptoms as echoed by backend
  possible_conditions: ReactConditionOutput[];
  general_advice: string;
  should_seek_medical_attention: boolean;
  government_schemes?: AISchemeInfo[];
  doctor_specialties_recommended?: string[];
}

export interface StoredAnalysis {
  id: string; // Can be client-generated for local history or backend ID
  date: string; // ISO string
  symptoms: SymptomUI[]; // Symptoms as entered by user (with UI ID)
  result: BackendAnalysisResult | null; // Null if analysis failed or not yet performed for some reason
}

export interface CountryDataForSPA {
    name: string; 
    states: string[]; 
}
