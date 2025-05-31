// Symptom/src/pages/ResultsPage.tsx
import { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { AlertCircle, ArrowLeft, CheckCircle2, Printer, ExternalLink } from 'lucide-react';
import { motion } from 'framer-motion';
import { useSymptom } from '../context/SymptomContext';
import type { SymptomInputForRequest, BackendAnalysisResult } from '../types'; // Using SymptomInputForRequest for echoed symptoms

const getSeverityLabelStyle = (severity: number | undefined) => {
    if (typeof severity === 'undefined') return { label: 'N/A', color: 'bg-gray-100 text-gray-800' };
    switch (severity) {
      case 1: return { label: 'Mild', color: 'bg-green-100 text-green-700' };
      case 2: return { label: 'Moderate', color: 'bg-yellow-100 text-yellow-700' };
      case 3: return { label: 'Severe', color: 'bg-red-100 text-red-700' };
      default: return { label: 'Unknown', color: 'bg-gray-100 text-gray-700' };
    }
};

const ResultsPage = () => {
  const navigate = useNavigate();
  const { currentAnalysisResult } = useSymptom(); 
  
  const analysisToDisplay: BackendAnalysisResult | null = currentAnalysisResult;
  // Symptoms displayed are those echoed back by the backend, which are of type SymptomInputForRequest[]
  const symptomsForThisAnalysis: SymptomInputForRequest[] = analysisToDisplay?.symptoms || [];

  useEffect(() => {
    if (!analysisToDisplay) {
      console.warn("ResultsPage: No currentAnalysisResult found, redirecting to /analyze.");
      navigate('/analyze');
    }
  }, [analysisToDisplay, navigate]);

  if (!analysisToDisplay) {
    return (
      <div className="max-w-4xl mx-auto text-center py-16 px-4">
        <AlertCircle size={48} className="text-amber-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Loading Analysis Results...</h2>
        <p className="text-gray-600 mb-8">
          If you are seeing this for more than a few seconds, please try starting a new analysis.
        </p>
        <button onClick={() => navigate('/analyze')} className="btn btn-primary">
          Start New Analysis
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 md:px-0">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Symptom Analysis Results</h1>
            <p className="text-gray-600">
              Analysis ID: {analysisToDisplay.id} (Generated: {new Date(analysisToDisplay.date).toLocaleString()})
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <button onClick={() => window.print()}
              className="btn bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300 flex-shrink-0">
              <Printer size={16} className="mr-2" /> Print Results
            </button>
             <Link to="/analyze" className="btn bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 flex-shrink-0">
                <ArrowLeft size={16} className="mr-2" /> New Analysis
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden mb-8">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
            <h2 className="text-xl font-semibold text-gray-800">Your Reported Symptoms</h2>
          </div>
          <div className="p-6">
            {symptomsForThisAnalysis.length > 0 ? (
              <ul className="space-y-3">
                {symptomsForThisAnalysis.map((symptom, index) => {
                  const severityInfo = getSeverityLabelStyle(symptom.severity);
                  return (
                    <li key={`symptom-display-${index}`}
                      className="flex items-start p-3 bg-gray-100 rounded-lg border border-gray-200">
                      <div className="flex-grow">
                        <div className="flex items-center mb-1 flex-wrap">
                          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${severityInfo.color} mr-2 mb-1 sm:mb-0`}>
                            {severityInfo.label}
                          </span>
                          <span className="text-sm text-gray-600">Duration: {symptom.duration}</span>
                        </div>
                        <p className="text-gray-800 font-medium">{symptom.description}</p>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : <p className="text-gray-500 italic">No symptoms were reported for this analysis.</p>}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden mb-8">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
            <h2 className="text-xl font-semibold text-gray-800">Possible Conditions</h2>
            <p className="text-sm text-gray-600 mt-1">
              Based on your symptoms, these conditions might be relevant. This is not a diagnosis.
            </p>
          </div>
          <div className="p-6">
            {analysisToDisplay.possible_conditions && analysisToDisplay.possible_conditions.length > 0 ? (
                <div className="space-y-6">
                {analysisToDisplay.possible_conditions.map((condition, index) => (
                    <motion.div key={condition.name + index}
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: index * 0.1 }}
                    className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                    <div className="bg-gray-100 p-4 border-b border-gray-200">
                        <div className="flex justify-between items-center">
                        <h3 className="font-semibold text-lg text-gray-800">{condition.name}</h3>
                        <div className="flex items-center">
                            <span className="text-sm text-gray-600 mr-2">
                            Match: {Math.round(condition.probability * 100)}%
                            </span>
                            <div className="w-24 bg-gray-300 rounded-full h-2.5">
                            <div
                                className="bg-primary-600 h-2.5 rounded-full"
                                style={{ width: `${Math.max(0, Math.min(100, condition.probability * 100))}%` }}
                            ></div>
                            </div>
                        </div>
                        </div>
                    </div>
                    <div className="p-4">
                        <p className="text-sm text-gray-700 mb-3">{condition.description}</p>
                        <div className="bg-blue-50 p-3 rounded-md border border-blue-200">
                        <div className="flex items-start">
                            <CheckCircle2 size={20} className="text-blue-500 mr-2 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-blue-700">
                            <span className="font-medium">Recommendation:</span> {condition.recommendation}
                            </p>
                        </div>
                        </div>
                    </div>
                    </motion.div>
                ))}
                </div>
            ) : <p className="text-gray-500 italic p-4">No specific conditions were identified by the AI for further consideration based on the provided symptoms.</p>}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden mb-8">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4"><h2 className="text-xl font-semibold text-gray-800">General Advice</h2></div>
          <div className="p-6">
            <p className="text-gray-700 leading-relaxed">{analysisToDisplay.general_advice}</p>
            {analysisToDisplay.should_seek_medical_attention ? (
              <div className="mt-4 bg-red-50 border border-red-300 rounded-md p-4">
                <div className="flex items-start">
                  <AlertCircle size={20} className="text-red-600 mr-3 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-semibold text-red-800">Medical Attention Recommended</h3>
                    <p className="text-sm text-red-700 mt-1">
                      Based on your symptoms, we recommend seeking medical attention. This is not an emergency service - if you're experiencing a medical emergency, please call emergency services immediately or go to the nearest emergency room.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-4 bg-green-50 border border-green-300 rounded-md p-4">
                <div className="flex items-start">
                  <CheckCircle2 size={20} className="text-green-600 mr-3 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-semibold text-green-800">Self-Care Likely Sufficient For Now</h3>
                    <p className="text-sm text-green-700 mt-1">
                      Based on your symptoms, self-care measures are currently indicated. Monitor your symptoms closely. If they worsen, persist beyond a reasonable time, or new concerning symptoms develop, please consult with a healthcare professional.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {(analysisToDisplay.government_schemes && analysisToDisplay.government_schemes.length > 0) && (
             <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden mb-8">
                <div className="border-b border-gray-200 bg-gray-50 px-6 py-4"><h2 className="text-xl font-semibold text-gray-800">Relevant Government Schemes</h2></div>
                <div className="p-6"><ul className="list-disc pl-5 space-y-2">{analysisToDisplay.government_schemes.map(s => <li key={s.name} className="text-sm text-gray-700"><strong>{s.name}</strong>{s.region_specific ? ` (${s.region_specific})` : ''}: {s.description || 'No description available.'} {s.url ? <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline inline-flex items-center ml-1">Details <ExternalLink size={14} className="ml-1"/></a> : ''}</li>)}</ul></div>
             </div>
        )}
        {(analysisToDisplay.doctor_specialties_recommended && analysisToDisplay.doctor_specialties_recommended.length > 0) && (
             <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden mb-8">
                <div className="border-b border-gray-200 bg-gray-50 px-6 py-4"><h2 className="text-xl font-semibold text-gray-800">Recommended Doctor Specialties</h2></div>
                <div className="p-6"><ul className="list-disc pl-5 space-y-1">{analysisToDisplay.doctor_specialties_recommended.map(spec => <li key={spec} className="text-sm text-gray-700">{spec}</li>)}</ul></div>
             </div>
        )}

        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden mb-8">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4"><h2 className="text-xl font-semibold text-gray-800">Disclaimer</h2></div>
          <div className="p-6">
            <div className="bg-amber-50 border border-amber-300 rounded-md p-4">
              <div className="flex items-start">
                <AlertCircle size={20} className="text-amber-600 mr-3 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-amber-800">
                    The information provided by this AI tool is for informational purposes only and DOES NOT CONSTITUTE MEDICAL ADVICE. It should not be used for self-diagnosis or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay in seeking it because of something you have read or been told by this AI. If you think you may have a medical emergency, call your doctor or emergency services immediately.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-col sm:flex-row justify-center items-center gap-4">
            <Link to="/" className="btn bg-gray-600 hover:bg-gray-700 text-white px-6 py-3">
                <i className="fas fa-home mr-2"></i> Back to Main Assistant Home
            </Link>
        </div>
      </motion.div>
    </div>
  );
};

export default ResultsPage;