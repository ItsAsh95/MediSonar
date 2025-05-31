import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css' // 
import { SymptomProvider } from './context/SymptomContext.tsx'; // Assuming path
import { BrowserRouter } from 'react-router-dom';


ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter basename="/symptom-analyzer"> 
      <SymptomProvider>
        <App />
      </SymptomProvider>
    </BrowserRouter>
  </React.StrictMode>,
)