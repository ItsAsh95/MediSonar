import { X } from 'lucide-react';
import { useSymptom } from '../context/SymptomContext';
import { motion } from 'framer-motion';

const SymptomList = () => {
  const { currentSymptoms, removeSymptom } = useSymptom();

  const getSeverityLabel = (severity: number) => {
    switch (severity) {
      case 1:
        return { label: 'Mild', color: 'bg-green-100 text-green-800' };
      case 2:
        return { label: 'Moderate', color: 'bg-yellow-100 text-yellow-800' };
      case 3:
        return { label: 'Severe', color: 'bg-red-100 text-red-800' };
      default:
        return { label: 'Unknown', color: 'bg-gray-100 text-gray-800' };
    }
  };

  if (currentSymptoms.length === 0) {
    return (
      <div className="text-center py-6">
        <p className="text-gray-500 italic">No symptoms added yet.</p>
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {currentSymptoms.map((symptom) => {
        const severity = getSeverityLabel(symptom.severity);
        
        return (
          <motion.li
            key={symptom.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-start justify-between p-4 bg-gray-50 rounded-lg border border-gray-200"
          >
            <div className="flex-1">
              <div className="flex items-center mb-1">
                <span className={`text-xs font-medium px-2.5 py-0.5 rounded ${severity.color} mr-2`}>
                  {severity.label}
                </span>
                <span className="text-sm text-gray-500">
                  Duration: {symptom.duration}
                </span>
              </div>
              <p className="text-gray-900 font-medium">{symptom.description}</p>
            </div>
            <button
              type="button"
              onClick={() => removeSymptom(symptom.id)}
              className="ml-2 p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
              aria-label="Remove symptom"
            >
              <X className="h-4 w-4" />
            </button>
          </motion.li>
        );
      })}
    </ul>
  );
};

export default SymptomList;