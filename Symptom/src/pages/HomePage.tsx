import { Link } from 'react-router-dom';
import { Activity, Shield, Clock, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

const HomePage = () => {
  return (
    <div className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="relative">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="space-y-6"
            >
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight">
                AI-Powered Symptom Analysis for Better Health Decisions
              </h1>
              <p className="text-xl text-gray-600 max-w-lg">
                Describe your symptoms and receive AI-generated insights to help you understand 
                potential causes and next steps.
              </p>
              <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
                <Link to="/analyze" className="btn btn-primary py-3 px-8 text-base">
                  Start Symptom Analysis
                </Link>
                <Link to="/history" className="btn bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 py-3 px-8 text-base">
                  View History
                </Link>
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="relative"
            >
              <div className="bg-gradient-to-br from-primary-500 to-secondary-500 rounded-2xl p-1">
                <div className="bg-white rounded-xl p-6 md:p-8">
                  <div className="space-y-6">
                    <div className="flex items-center space-x-4">
                      <div className="bg-primary-100 rounded-full p-3">
                        <Activity className="h-6 w-6 text-primary-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">MediScan Analysis</h3>
                        <p className="text-sm text-gray-500">AI-powered health insights</p>
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                        <h4 className="font-medium text-gray-900 mb-2">Symptoms</h4>
                        <ul className="space-y-2 text-sm">
                          <li className="flex items-center space-x-2">
                            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">Moderate</span>
                            <span>Persistent headache (3 days)</span>
                          </li>
                          <li className="flex items-center space-x-2">
                            <span className="bg-amber-100 text-amber-800 text-xs font-medium px-2.5 py-0.5 rounded">Mild</span>
                            <span>Fatigue</span>
                          </li>
                          <li className="flex items-center space-x-2">
                            <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded">Severe</span>
                            <span>Nausea</span>
                          </li>
                        </ul>
                      </div>
                      
                      <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                        <h4 className="font-medium text-gray-900 mb-2">Possible Conditions</h4>
                        <div className="space-y-3">
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm font-medium">Migraine</span>
                              <span className="text-xs text-gray-500">78%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className="bg-primary-600 h-2 rounded-full" style={{ width: '78%' }}></div>
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm font-medium">Dehydration</span>
                              <span className="text-xs text-gray-500">45%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div className="bg-primary-600 h-2 rounded-full" style={{ width: '45%' }}></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-500">This is a sample analysis</span>
                      <Link to="/analyze" className="text-primary-600 text-sm font-medium flex items-center hover:text-primary-700">
                        Try now <ArrowRight className="ml-1 h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-gray-50 py-12 rounded-2xl">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">How MediScan Works</h2>
            <p className="mt-4 text-xl text-gray-600 max-w-2xl mx-auto">
              Our AI-powered symptom analyzer helps you understand your health concerns in three simple steps.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: <Activity className="h-10 w-10 text-primary-600" />,
                title: 'Describe Your Symptoms',
                description: 'Enter detailed information about your symptoms, including duration, severity, and any relevant context.',
              },
              {
                icon: <Shield className="h-10 w-10 text-primary-600" />,
                title: 'AI Analysis',
                description: 'Our advanced AI powered by Perplexity Sonar Pro analyzes your symptoms and provides potential explanations.',
              },
              {
                icon: <Clock className="h-10 w-10 text-primary-600" />,
                title: 'Get Insights Instantly',
                description: 'Receive immediate insights about possible conditions and recommendations for next steps.',
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center"
              >
                <div className="flex justify-center mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-2xl overflow-hidden">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-12 md:py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-white mb-6">
              Ready to understand your symptoms?
            </h2>
            <p className="text-xl text-primary-100 max-w-2xl mx-auto mb-8">
              Get started with our AI-powered symptom analyzer and receive personalized health insights.
            </p>
            <Link 
              to="/analyze" 
              className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-primary-700 bg-white hover:bg-primary-50 transition-colors"
            >
              Start Analyzing Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="max-w-4xl mx-auto px-4">
        <div className="border border-amber-200 bg-amber-50 rounded-lg p-4">
          <h3 className="text-amber-800 font-medium text-lg mb-2">Important Health Disclaimer</h3>
          <p className="text-amber-700 text-sm">
            MediScan is designed to provide information and is not a substitute for professional medical advice, 
            diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider 
            with any questions you may have regarding a medical condition. Never disregard professional medical 
            advice or delay in seeking it because of something you have read on this website.
          </p>
        </div>
      </section>
    </div>
  );
};

export default HomePage;