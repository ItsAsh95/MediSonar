// Symptom/src/context/SymptomContext.tsx
import { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import type { SymptomUI, StoredAnalysis, BackendAnalysisResult } from '../types'; // Adjusted import

interface SymptomContextType {
  currentSymptoms: SymptomUI[];
  addSymptom: (symptomData: Omit<SymptomUI, 'id'>) => void;
  removeSymptom: (id: string) => void;
  clearSymptoms: () => void;
  analysisHistory: StoredAnalysis[];
  currentAnalysisResult: BackendAnalysisResult | null; // Stores the direct result from API for ResultsPage
  setCurrentAnalysisResult: (analysisResult: BackendAnalysisResult | null) => void;
  saveAnalysisToHistory: (analysisToSave: StoredAnalysis) => void; // Renamed for clarity
  getAnalysisById: (id: string) => StoredAnalysis | undefined;
}

const SymptomContext = createContext<SymptomContextType | undefined>(undefined);

const LOCAL_STORAGE_HISTORY_KEY = 'symptomAnalysisHistory';

export function SymptomProvider({ children }: { children: ReactNode }) {
  const [currentSymptoms, setCurrentSymptoms] = useState<SymptomUI[]>([]);
  // analysisHistory stores StoredAnalysis objects
  const [analysisHistory, setAnalysisHistory] = useState<StoredAnalysis[]>(() => {
    const storedHistory = localStorage.getItem(LOCAL_STORAGE_HISTORY_KEY);
    if (storedHistory) {
      try {
        return JSON.parse(storedHistory);
      } catch (e) {
        console.error("Failed to parse stored history:", e);
        localStorage.removeItem(LOCAL_STORAGE_HISTORY_KEY);
      }
    }
    return [];
  });

  // currentAnalysisResult stores the BackendAnalysisResult for the current analysis flow
  const [currentAnalysisResult, setCurrentAnalysisResult] = useState<BackendAnalysisResult | null>(null);

  useEffect(() => {
    // Persist history to localStorage whenever it changes
    localStorage.setItem(LOCAL_STORAGE_HISTORY_KEY, JSON.stringify(analysisHistory));
  }, [analysisHistory]);

  const addSymptom = (symptomData: Omit<SymptomUI, 'id'>) => {
    const newSymptom: SymptomUI = {
      ...symptomData,
      id: crypto.randomUUID(), // Generate unique ID for UI list key
    };
    setCurrentSymptoms(prevSymptoms => [...prevSymptoms, newSymptom]);
  };

  const removeSymptom = (id: string) => {
    setCurrentSymptoms(prevSymptoms => prevSymptoms.filter(symptom => symptom.id !== id));
  };

  const clearSymptoms = () => {
    setCurrentSymptoms([]);
  };

  const saveAnalysisToHistory = (analysisToSave: StoredAnalysis) => {
    // Prepend new analysis to history, ensuring no exact ID duplicates if backend ID is used
    setAnalysisHistory(prevHistory => {
        const existingIndex = prevHistory.findIndex(h => h.id === analysisToSave.id);
        if (existingIndex > -1) {
            // Optionally update if ID exists, or just keep newest, for now prepending
            console.warn(`Analysis with ID ${analysisToSave.id} already exists. Prepending new one.`);
        }
        return [analysisToSave, ...prevHistory.filter(h => h.id !== analysisToSave.id)].slice(0, 50); // Keep last 50
    });
  };

  const getAnalysisById = (id: string): StoredAnalysis | undefined => {
    return analysisHistory.find(analysis => analysis.id === id);
  };


  return (
    <SymptomContext.Provider
      value={{
        currentSymptoms,
        addSymptom,
        removeSymptom,
        clearSymptoms,
        analysisHistory,
        currentAnalysisResult,      // For ResultsPage to display
        setCurrentAnalysisResult,   // For AnalyzerPage to set after API call
        saveAnalysisToHistory,      // For AnalyzerPage to save the complete StoredAnalysis object
        getAnalysisById,
      }}
    >
      {children}
    </SymptomContext.Provider>
  );
}

export function useSymptom() {
  const context = useContext(SymptomContext);
  if (context === undefined) {
    throw new Error('useSymptom must be used within a SymptomProvider');
  }
  return context;
}