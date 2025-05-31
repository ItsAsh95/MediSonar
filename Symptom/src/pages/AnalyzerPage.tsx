// Symptom/src/pages/AnalyzerPage.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, SubmitHandler } from 'react-hook-form';
import { PlusCircle, X, AlertTriangle, Activity } from 'lucide-react'; // Removed MapPin if not used for region
import { motion } from 'framer-motion';
import { useSymptom } from '../context/SymptomContext';
import SymptomList from '../components/SymptomList';
import symptomApi from '../services/api';
import type {SymptomInputForRequest, ReactAnalysisRequest, StoredAnalysis, BackendAnalysisResult } from '../types';

interface SymptomFormData {
  description: string;
  duration: string;
  severity: number;
}

const severityOptions = [
  { value: 1, label: 'Mild', color: 'bg-green-100 text-green-800', hoverColor: 'hover:bg-green-200' },
  { value: 2, label: 'Moderate', color: 'bg-yellow-100 text-yellow-800', hoverColor: 'hover:bg-yellow-200' },
  { value: 3, label: 'Severe', color: 'bg-red-100 text-red-800', hoverColor: 'hover:bg-red-200' },
];

// TODO: Replace MOCK_COUNTRIES and MOCK_STATES with actual data fetching and state management
const MOCK_COUNTRIES = [{ name: "United States", code: "US" }, { name: "India", code: "IN" }];
const MOCK_STATES: { [key: string]: string[] } = {
  "US": ["California", "New York"],
  "IN": ["Maharashtra", "Delhi"]
};

const AnalyzerPage = () => {
  const navigate = useNavigate();
  const { currentSymptoms, addSymptom, clearSymptoms, analysisHistory, setCurrentAnalysisResult, saveAnalysisToHistory } = useSymptom();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiErrorMessage, setApiErrorMessage] = useState<string | null>(null);

  const [selectedCountry, setSelectedCountry] = useState<string>("");
  const [selectedState, setSelectedState] = useState<string>("");
  const [availableStates, setAvailableStates] = useState<string[]>([]);

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<SymptomFormData>({
    defaultValues: { severity: 1 }
  });
  const watchedSeverity = Number(watch("severity"));

  useEffect(() => {
    setCurrentAnalysisResult(null);
  }, [setCurrentAnalysisResult]);

  useEffect(() => {
    if (selectedCountry) {
      setAvailableStates(MOCK_STATES[selectedCountry] || []);
      setSelectedState("");
    } else {
      setAvailableStates([]);
      setSelectedState("");
    }
  }, [selectedCountry]);

  const onSymptomFormSubmit: SubmitHandler<SymptomFormData> = (data) => {
    addSymptom({
      description: data.description,
      duration: data.duration,
      severity: Number(data.severity),
    });
    reset({ description: '', duration: '', severity: 1 });
  };

  const handleAnalyzeSymptoms = async () => {
    if (currentSymptoms.length === 0) {
      setApiErrorMessage('Please add at least one symptom before analyzing.');
      return;
    }
    setIsSubmitting(true);
    setApiErrorMessage(null);

    const symptomsForApi: SymptomInputForRequest[] = currentSymptoms.map(({ id, ...restSymptomData }) => restSymptomData);
    
    let userRegionForApi: string | undefined = undefined;
    const countryObject = MOCK_COUNTRIES.find(c => c.code === selectedCountry);
    const countryName = countryObject ? countryObject.name : selectedCountry;

    if (selectedCountry) {
        userRegionForApi = selectedState && selectedState !== "" ? `${selectedState}, ${countryName}` : countryName;
    }

    let historyContextString = "";
    if (analysisHistory && analysisHistory.length > 0) {
        const recentAnalyses = analysisHistory.slice(0, 2);
        historyContextString = "User's recent symptom analysis history (for context):\n";
        recentAnalyses.forEach(analysis => {
            if(analysis && analysis.result){
                historyContextString += `- Date: ${new Date(analysis.date).toLocaleDateString()}, Symptoms: ${analysis.symptoms.map(s => s.description).join(', ')}, Potential Conditions: ${analysis.result.possible_conditions.map(c => c.name).join(', ') || 'N/A'}\n`;
            }
        });
    }

    const requestPayload: ReactAnalysisRequest = {
      symptoms: symptomsForApi,
      user_region: userRegionForApi,
      history_context_string: historyContextString.trim() || undefined
    };

    try {
      const backendAnalysisResult: BackendAnalysisResult = await symptomApi.analyzeSymptomsReact(requestPayload);
      
      const newStoredAnalysis: StoredAnalysis = {
        id: backendAnalysisResult.id,
        date: backendAnalysisResult.date,
        symptoms: [...currentSymptoms], 
        result: backendAnalysisResult 
      };
      
      setCurrentAnalysisResult(backendAnalysisResult);
      saveAnalysisToHistory(newStoredAnalysis);        
      
      setIsSubmitting(false);
      navigate('/results');

    } catch (error) {
      setIsSubmitting(false);
      const message = error instanceof Error ? error.message : 'An unknown error occurred during analysis.';
      setApiErrorMessage(message);
      console.error("Symptom analysis API call failed:", error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 md:px-0">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Symptom Analyzer</h1>
        <p className="text-gray-600 mb-6">Add your symptoms one by one, then click "Analyze Symptoms".</p>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-3">Your Region (Optional for refined results)</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-1">Country</label>
                    <select id="country" value={selectedCountry} onChange={(e) => setSelectedCountry(e.target.value)} className="input w-full">
                        <option value="">-- Select Country --</option>
                        {MOCK_COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
                    </select>
                </div>
                <div>
                    <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">State/Province</label>
                    <select id="state" value={selectedState} onChange={(e) => setSelectedState(e.target.value)} className="input w-full" disabled={!selectedCountry || availableStates.length === 0}>
                        <option value="">-- Select State --</option>
                        {availableStates.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                </div>
            </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-8">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
            <h2 className="text-lg font-medium text-gray-900">Enter Your Symptoms</h2>
            <p className="text-sm text-gray-600 mt-1">
              Provide detailed information about each symptom you're experiencing.
            </p>
          </div>
          <div className="p-6">
            <form onSubmit={handleSubmit(onSymptomFormSubmit)} className="space-y-6">
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">Symptom Description</label>
                <input id="description" type="text" placeholder="e.g., Headache, fever, cough"
                  className={`input w-full ${errors.description ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-primary-500'}`}
                  {...register('description', { required: 'Symptom description is required' })} />
                {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>}
              </div>
              <div>
                <label htmlFor="duration" className="block text-sm font-medium text-gray-700 mb-1">Duration</label>
                <input id="duration" type="text" placeholder="e.g., 2 days, 1 week, few hours"
                  className={`input w-full ${errors.duration ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-primary-500'}`}
                  {...register('duration', { required: 'Duration is required' })} />
                {errors.duration && <p className="mt-1 text-sm text-red-600">{errors.duration.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Severity</label>
                <div className="grid grid-cols-3 gap-3">
                  {severityOptions.map((option) => (
                    <label key={option.value}
                      className={`flex items-center justify-center p-3 rounded-md border cursor-pointer transition-all 
                                  ${watchedSeverity === option.value ? `ring-2 ring-primary-500 border-primary-500 ${option.color}` : `border-gray-200 ${option.color.replace('text-', 'hover:text-opacity-80 ').replace('bg-','hover:bg-opacity-75 ')} ${option.hoverColor}`} `}>
                      <input type="radio" value={option.value} className="sr-only"
                        {...register('severity', { required: 'Severity is required', valueAsNumber: true })} />
                      <span>{option.label}</span>
                    </label>
                  ))}
                </div>
                {errors.severity && <p className="mt-1 text-sm text-red-600">{errors.severity.message}</p>}
              </div>
              <div>
                <button type="submit" className="btn bg-gray-100 text-gray-800 hover:bg-gray-200 border border-gray-300">
                  <PlusCircle size={20} className="mr-2" /> Add Symptom
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-8">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Your Added Symptoms</h2>
              <p className="text-sm text-gray-600 mt-1">
                {currentSymptoms.length === 0 ? 'Add at least one symptom to proceed.' : `${currentSymptoms.length} symptom(s) added`}
              </p>
            </div>
            {currentSymptoms.length > 0 && (
              <button type="button" onClick={() => clearSymptoms()}
                className="text-sm text-gray-500 hover:text-red-600 flex items-center">
                <X size={16} className="mr-1" /> Clear All
              </button>
            )}
          </div>
          <div className="p-6">
            <SymptomList />
            {apiErrorMessage && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start">
                <AlertTriangle size={20} className="text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-600">{apiErrorMessage}</p>
              </div>
            )}
            <div className="mt-6 flex flex-col sm:flex-row sm:justify-end gap-4">
              <button type="button" onClick={() => navigate('/')}
                className="btn bg-white border border-gray-300 text-gray-700 hover:bg-gray-50">
                Cancel & Back to Main App
              </button>
              <button type="button" onClick={handleAnalyzeSymptoms}
                disabled={currentSymptoms.length === 0 || isSubmitting}
                className="btn btn-primary">
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Analyzing...
                  </>
                ) : ( <><Activity size={20} className="mr-2" />Analyze Symptoms</> )}
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AnalyzerPage;