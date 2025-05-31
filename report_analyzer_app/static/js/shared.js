
const API_BASE_URL_REPORT_APP = '/report-analyzer'; 


const ICONS = {
    Loader2: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>`,
    FileText: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>`,
    AlertCircle: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    CheckCircle: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    Download: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
    AlertTriangle: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    Activity: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
    TrendingUp: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`,
    Info: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
    Shield: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
    Upload: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>`,
    File: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>`,
    X: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
    Heart: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
    Stethoscope: (className = '') => `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${className}"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/><circle cx="4" cy="10" r="2"/></svg>`,
};

function renderAllIcons() {
  
    const stethoscopeNav = document.getElementById('stethoscope-icon-nav');
    if (stethoscopeNav && ICONS.Stethoscope) stethoscopeNav.innerHTML = ICONS.Stethoscope('text-primary-500 h-8 w-8'); 

    const uploadIconMain = document.getElementById('upload-icon-main');
    if (uploadIconMain && ICONS.Upload) uploadIconMain.innerHTML = ICONS.Upload('h-12 w-12 text-primary-500');
    
    
    const fileIconPreview = document.getElementById('file-icon-preview');
    if (fileIconPreview && ICONS.File) fileIconPreview.innerHTML = ICONS.File('h-5 w-5 text-primary-500');

    const xIconRemove = document.getElementById('x-icon-remove');
    if (xIconRemove && ICONS.X) xIconRemove.innerHTML = ICONS.X('h-5 w-5');

    const loaderIconUpload = document.getElementById('loader-icon-upload');
    if (loaderIconUpload && ICONS.Loader2) loaderIconUpload.innerHTML = ICONS.Loader2('');

    const filetextIconFeature = document.getElementById('filetext-icon-feature');
    if (filetextIconFeature && ICONS.FileText) filetextIconFeature.innerHTML = ICONS.FileText('h-10 w-10 text-primary-500');

    const checkcircleIconFeature = document.getElementById('checkcircle-icon-feature');
    if (checkcircleIconFeature && ICONS.CheckCircle) checkcircleIconFeature.innerHTML = ICONS.CheckCircle('h-10 w-10 text-green-500');
    
    const alertcircleIconFeatureRec = document.getElementById('alertcircle-icon-feature-rec'); // Make sure ID is unique
    if (alertcircleIconFeatureRec && ICONS.AlertCircle) alertcircleIconFeatureRec.innerHTML = ICONS.AlertCircle('h-10 w-10 text-yellow-500'); // Changed to yellow

    const loaderIconAnalysis = document.getElementById('loader-icon-analysis');
    if (loaderIconAnalysis && ICONS.Loader2) loaderIconAnalysis.innerHTML = ICONS.Loader2('');

    const alertcircleIconError = document.getElementById('alertcircle-icon-error');
    if (alertcircleIconError && ICONS.AlertCircle) alertcircleIconError.innerHTML = ICONS.AlertCircle('');

    const activityIconParams = document.getElementById('activity-icon-params');
    if (activityIconParams && ICONS.Activity) activityIconParams.innerHTML = ICONS.Activity('h-6 w-6 text-gray-500');

    const alerttriangleIconAbnormal = document.getElementById('alerttriangle-icon-abnormal');
    if (alerttriangleIconAbnormal && ICONS.AlertTriangle) alerttriangleIconAbnormal.innerHTML = ICONS.AlertTriangle('h-6 w-6 text-red-500');

    const trendingupIconRecs = document.getElementById('trendingup-icon-recs');
    if (trendingupIconRecs && ICONS.TrendingUp) trendingupIconRecs.innerHTML = ICONS.TrendingUp('h-6 w-6 text-blue-500');

    const infoIconFollowup = document.getElementById('info-icon-followup');
    if (infoIconFollowup && ICONS.Info) infoIconFollowup.innerHTML = ICONS.Info('h-6 w-6 text-purple-500');

    const alertcircleIconDisclaimer = document.getElementById('alertcircle-icon-disclaimer');
    if (alertcircleIconDisclaimer && ICONS.AlertCircle) alertcircleIconDisclaimer.innerHTML = ICONS.AlertCircle('h-6 w-6 text-gray-400');
}


function setYear() {
    const yearSpans = document.querySelectorAll('#currentYear'); // Use querySelectorAll if multiple
    yearSpans.forEach(span => {
        if (span) span.textContent = new Date().getFullYear();
    });
}

// --- API Service Functions ---
async function uploadReport(file) {
    const formData = new FormData();
    formData.append('file', file);

    
    const response = await fetch(`${API_BASE_URL_REPORT_APP}/api/reports/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown upload error. Server might be down or endpoint incorrect.' }));
        console.error("Upload Report Error Data:", errorData);
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
}

async function getAnalysisResults(id) {
    
    const response = await fetch(`${API_BASE_URL_REPORT_APP}/api/reports/${id}`);

    if (response.status === 202) { 
        const data = await response.json().catch(() => ({ detail: 'Analysis is processing, but no detailed message was returned.'}));
        console.log("Analysis in progress (202):", data.detail);
        return { status: 'processing', detail: data.detail };
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error fetching analysis results.' }));
        console.error("Get Analysis Results Error Data:", errorData);
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json(); // This should be the full AnalysisResult
}

document.addEventListener('DOMContentLoaded', () => {
    setYear();
    if (typeof renderAllIcons === 'function') { // Ensure it's defined
        renderAllIcons(); 
    } else {
        console.warn("renderAllIcons function not found in shared.js. Icons might not display.");
    }
});