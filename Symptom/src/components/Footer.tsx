import { Link } from 'react-router-dom';
import { Activity} from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <Link to="/" className="flex items-center space-x-2 text-primary-600">
              <Activity className="h-6 w-6" />
              <span className="text-lg font-bold">MediScan</span>
            </Link>
            <p className="mt-2 text-sm text-gray-600 max-w-md">
              MediScan provides AI-powered symptom analysis to help you understand 
              your health concerns. Not a substitute for professional medical advice.
            </p>
          </div>
          
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">Quick Links</h3>
            <ul className="mt-4 space-y-2">
              <li>
                
                <Link to="/" className="text-sm text-gray-600 hover:text-primary-600">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/analyze" className="text-sm text-gray-600 hover:text-primary-600">
                  Symptom Analyzer
                </Link>
              </li>
              <li>
                <Link to="/history" className="text-sm text-gray-600 hover:text-primary-600">
                  History
                </Link>
                <li>
                  <a href="/" className="text-sm text-gray-600 hover:text-primary-600">
                    MediSonar
                  </a>
                </li>
              </li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">Disclaimer</h3>
            <p className="mt-4 text-sm text-gray-600">
              MediScan is not a medical device and is not intended to diagnose, 
              treat, cure or prevent any disease. Always consult with a qualified 
              healthcare provider for medical advice.
            </p>
          </div>
        </div>
        
        <div className="mt-8 border-t border-gray-200 pt-6 flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-gray-600"><b>
            
            © {currentYear} MediSonar. All rights reserved.
            </b>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;