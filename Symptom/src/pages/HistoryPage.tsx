import { Link } from 'react-router-dom';
import { Clock, ArrowRight, Activity, AlertCircle } from 'lucide-react';
import { useSymptom } from '../context/SymptomContext';

const HistoryPage = () => {
  const { analysisHistory } = useSymptom();

  const formatDate = (dateString: string) => {
    const options: Intl.DateTimeFormatOptions = { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analysis History</h1>
          <p className="text-gray-600">
            View your past symptom analyses and results
          </p>
        </div>
        <Link
          to="/analyze"
          className="btn btn-primary"
        >
          <Activity className="h-4 w-4 mr-2" />
          New Analysis
        </Link>
      </div>

      {analysisHistory.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <div className="bg-gray-100 rounded-full p-3 inline-flex mx-auto mb-4">
            <Clock className="h-6 w-6 text-gray-500" />
          </div>
          <h2 className="text-xl font-medium text-gray-900 mb-2">No Analysis History</h2>
          <p className="text-gray-600 mb-6">
            You haven't analyzed any symptoms yet. Start your first analysis to track your health concerns.
          </p>
          <Link
            to="/analyze"
            className="btn btn-primary"
          >
            Start Your First Analysis
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {analysisHistory.map((analysis) => (
            <div
              key={analysis.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              <div className="border-b border-gray-200 bg-gray-50 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h2 className="text-lg font-medium text-gray-900">Analysis from {formatDate(analysis.date)}</h2>
                  <p className="text-sm text-gray-600">
                    {analysis.symptoms.length} symptom{analysis.symptoms.length !== 1 ? 's' : ''} reported
                  </p>
                </div>
                <Link
                  to="/results"
                  className="text-primary-600 text-sm font-medium flex items-center hover:text-primary-700"
                >
                  View Details <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>
              
              <div className="p-6">
                <div className="mb-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Reported Symptoms:</h3>
                  <div className="flex flex-wrap gap-2">
                    {analysis.symptoms.map((symptom) => (
                      <span
                        key={symptom.id}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        {symptom.description} ({symptom.duration})
                      </span>
                    ))}
                  </div>
                </div>
                
                {analysis.result && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Top Possible Conditions:</h3>
                    <div className="space-y-2">
                      {analysis.result.possible_conditions.slice(0, 2).map((condition) => (
                        <div key={condition.name} className="flex justify-between items-center">
                          <span className="text-sm">{condition.name}</span>
                          <div className="flex items-center">
                            <span className="text-xs text-gray-500 mr-2">
                              {Math.round(condition.probability * 100)}%
                            </span>
                            <div className="w-16 bg-gray-200 rounded-full h-1.5">
                              <div
                                className="bg-primary-600 h-1.5 rounded-full"
                                style={{ width: `${condition.probability * 100}%` }}
                                >
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {analysis.result.should_seek_medical_attention && (
                      <div className="mt-4 flex items-center text-red-600 text-sm">
                        <AlertCircle className="h-4 w-4 mr-1" />
                        Medical attention was recommended
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoryPage;