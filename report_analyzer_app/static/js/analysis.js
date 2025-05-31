document.addEventListener('DOMContentLoaded', () => {
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const errorMessageText = document.getElementById('errorMessageText');
    const tryAgainButton = document.getElementById('tryAgainButton');
    const analysisContent = document.getElementById('analysisContent');

    // Analysis Content Elements
    const analysisDate = document.getElementById('analysisDate');
    const reportFileName = document.getElementById('reportFileName');
    const overallStatusCard = document.getElementById('overallStatusCard');
    const overallStatusIcon = document.getElementById('overallStatusIcon');
    const overallStatusText = document.getElementById('overallStatusText');
    const overallNormalContent = document.getElementById('overallNormalContent');
    const overallNormalMessage = document.getElementById('overallNormalMessage');
    const overallSummaryMarkdown = document.getElementById('overallSummaryMarkdown');
    const overallAttentionContent = document.getElementById('overallAttentionContent');
    const overallAttentionSummaryMarkdown = document.getElementById('overallAttentionSummaryMarkdown');


    const parametersSection = document.getElementById('parametersSection');
    const parametersTableBody = document.getElementById('parametersTableBody');
    const noParametersMessage = document.getElementById('noParametersMessage');
    
    const abnormalitiesSection = document.getElementById('abnormalitiesSection');
    const abnormalitiesList = document.getElementById('abnormalitiesList');
    const noAbnormalitiesMessage = document.getElementById('noAbnormalitiesMessage');

    const recommendationsList = document.getElementById('recommendationsList');
    const followUpText = document.getElementById('followUpText');
    
    let analysisId = '';
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length > 0 && pathParts[pathParts.length - 2] === 'analysis') {
        analysisId = pathParts[pathParts.length - 1];
    }

    // Ported from React's AnalysisPage
    // This will use the structured_data directly from the server response.
    // The server's parse_structured_analysis now does the heavy lifting.
    // This client-side function primarily maps the server data to the UI.
    function processAndDisplayAnalysis(analysisResult) {
        // The server now provides `structured_data` directly, so we use that.
        // The old `processAnalysisText` from React is largely superseded by server-side parsing.
        // We just need to map the server's `AnalysisResult` and `StructuredAnalysis` to the UI.

        const structured = analysisResult.structured_data;
        if (!structured) {
            console.error("No structured_data found in analysis result from server.");
            showError("Analysis data is incomplete. Cannot display results.");
            return null; // Or throw error
        }

        // For client-side display purposes, let's determine overall display status
        // based on server's overall_status and abnormalities count
        let displayOverallStatus = 'normal';
        if (structured.overall_status === 'abnormal' || structured.overall_status === 'error') {
            displayOverallStatus = 'abnormal';
        } else if (structured.overall_status === 'nodata') {
            displayOverallStatus = 'nodata'; // Or handle as an error/special case
        }
        // React code also checked for keywords like 'attention_needed' in summary.
        // The server's overall_status should ideally capture this.
        // If client-side `processAnalysisText` was determining 'attention_needed' this is now less direct.
        // For now, we simplify: server's 'abnormal' means attention.
        
        // The client used 'overall_status: 'normal' | 'abnormal' | 'attention_needed';
        // Server provides 'normal' | 'abnormal' | 'nodata' | 'error'
        // We map this to what the UI expects for styling/content.

        let clientOverallStatus = 'normal'; // Default for UI
        if (structured.overall_status === 'abnormal' || 
            (structured.abnormalities && structured.abnormalities.length > 0)) {
            clientOverallStatus = 'abnormal'; // 'abnormal' or 'attention_needed' in React context
        } else if (structured.overall_status === 'error' || structured.overall_status === 'nodata') {
             clientOverallStatus = 'error'; // Special handling for UI
        }


        return {
            id: analysisResult.id,
            file_name: analysisResult.file_name,
            upload_date: analysisResult.upload_date,
            
            // Mapped from server's structured_data
            overall_status_display: clientOverallStatus, // This is for UI conditional rendering
            summary: structured.summary || "No summary provided.",
            parameters: structured.parameters || [],
            abnormalities: structured.abnormalities || [],
            recommendations: structured.recommendations || ['Regular follow-up as advised by healthcare provider.'],
            follow_up: analysisResult.follow_up_recommendations || structured.follow_up || 'Continue routine healthcare monitoring.'
        };
    }


    function getStatusIcon(status) {
        status = status ? status.toLowerCase() : 'unknown';
        switch (status) {
            case 'normal':
                return ICONS.CheckCircle('text-green-500');
            case 'abnormal':
                return ICONS.AlertTriangle('text-red-500');
            case 'borderline': // Server might not send 'borderline' in param.status, but good to have
                return ICONS.AlertCircle('text-yellow-500');
            default:
                return ICONS.Info('text-gray-500');
        }
    }

    function getSeverityClass(severity) {
        severity = severity ? severity.toLowerCase() : 'unknown';
        switch (severity) {
            case 'severe': return 'severity-severe';
            case 'moderate': return 'severity-moderate';
            case 'mild': return 'severity-mild';
            default: return 'severity-unknown';
        }
    }

    function renderAnalysis(processed) {
        analysisDate.textContent = `Analysis completed on ${new Date(processed.upload_date).toLocaleDateString()}`;
        reportFileName.textContent = `Report: ${processed.file_name}`;

        // Overall Status
        overallStatusCard.classList.remove('overall-status-normal', 'overall-status-abnormal', 'overall-status-attention');
        overallNormalContent.style.display = 'none';
        overallAttentionContent.style.display = 'none';

        if (processed.overall_status_display === 'normal') {
            overallStatusCard.classList.add('overall-status-normal');
            overallStatusIcon.innerHTML = ICONS.Shield('text-green-600');
            overallStatusText.textContent = 'All Parameters Normal';
            overallStatusText.className = 'text-2xl font-bold text-green-800';
            
            overallNormalContent.style.display = 'block';
            overallNormalMessage.textContent = 'Great news! Your medical report analysis suggests parameters within normal ranges or no significant abnormalities detected.';
            overallSummaryMarkdown.innerHTML = marked.parse(processed.summary || '*No summary provided.*');
        } else if (processed.overall_status_display === 'abnormal') { // Covers 'abnormal' and 'attention_needed'
            overallStatusCard.classList.add('overall-status-abnormal'); // Or a specific attention class if defined
            overallStatusIcon.innerHTML = ICONS.AlertTriangle('text-yellow-600'); // Yellow for attention
            overallStatusText.textContent = 'Attention Required';
            overallStatusText.className = 'text-2xl font-bold text-yellow-800';
            
            overallAttentionContent.style.display = 'block';
            overallAttentionSummaryMarkdown.innerHTML = marked.parse(processed.summary || '*Summary of findings requiring attention.*');
        } else { // nodata or error from server's perspective
             overallStatusCard.classList.add('overall-status-abnormal'); // Treat as attention/error for display
             overallStatusIcon.innerHTML = ICONS.AlertCircle('text-red-600');
             overallStatusText.textContent = 'Analysis Incomplete or Errored';
             overallStatusText.className = 'text-2xl font-bold text-red-800';
             overallAttentionContent.style.display = 'block';
             overallAttentionSummaryMarkdown.innerHTML = marked.parse(processed.summary || '*Could not fully process the report. Please review any available details or try again.*');
        }


        // Parameters
        parametersTableBody.innerHTML = ''; // Clear previous
        if (processed.parameters && processed.parameters.length > 0) {
            parametersSection.style.display = 'block';
            noParametersMessage.style.display = 'none';
            processed.parameters.forEach(param => {
                const row = parametersTableBody.insertRow();
                row.innerHTML = `
                    <td>${param.name}</td>
                    <td>${param.value}</td>
                    <td>${param.reference_range || 'Not specified'}</td>
                    <td class="status-icon">${getStatusIcon(param.status)}</td>
                `;
            });
        } else {
            parametersSection.style.display = 'block'; // Show section even if empty
            noParametersMessage.style.display = 'block';
        }

        // Abnormalities
        abnormalitiesList.innerHTML = ''; // Clear previous
        if (processed.abnormalities && processed.abnormalities.length > 0) {
            abnormalitiesSection.style.display = 'block';
            noAbnormalitiesMessage.style.display = 'none';
            processed.abnormalities.forEach(abnorm => {
                const div = document.createElement('div');
                div.className = `abnormality-item ${getSeverityClass(abnorm.estimated_severity)}`; // Server sends estimated_severity
                // React used 'parameter', 'finding', 'severity', 'recommendation'
                // Server sends 'parameter_name', 'description', 'estimated_severity', 'recommendation'
                div.innerHTML = `
                    <h4>${abnorm.estimated_severity || 'Unknown Severity'} - ${abnorm.parameter_name}</h4>
                    <p>${abnorm.description}</p>
                    ${abnorm.recommendation ? `<p class="recommendation">Recommendation: ${abnorm.recommendation}</p>` : ''}
                `;
                abnormalitiesList.appendChild(div);
            });
        } else {
            abnormalitiesSection.style.display = 'block'; // Show section
            noAbnormalitiesMessage.style.display = 'block';
        }

        // Recommendations
        recommendationsList.innerHTML = ''; // Clear previous
        (processed.recommendations || []).forEach(rec => {
            const li = document.createElement('li');
            li.innerHTML = `${ICONS.CheckCircle('text-green-500 mr-2 mt-0.5 flex-shrink-0')} <span class="text-sm text-gray-700">${rec}</span>`;
            recommendationsList.appendChild(li);
        });
        if (recommendationsList.children.length === 0) {
             const li = document.createElement('li');
             li.innerHTML = `<span class="text-sm text-gray-700">No specific recommendations provided beyond standard medical advice.</span>`;
             recommendationsList.appendChild(li);
        }


        // Follow-up
        followUpText.textContent = processed.follow_up;

        loadingState.style.display = 'none';
        errorState.style.display = 'none';
        analysisContent.style.display = 'block';
    }

    function showError(message) {
        loadingState.style.display = 'none';
        analysisContent.style.display = 'none';
        errorMessageText.textContent = message;
        errorState.style.display = 'block';
    }

    let pollCount = 0;
    const MAX_POLLS = 20; // Poll for 20 * 3 seconds = 1 minute
    const POLL_INTERVAL = 3000; // 3 seconds

    async function fetchAnalysis() {
        if (!analysisId) {
            showError('No analysis ID found in URL.');
            return;
        }

        loadingState.style.display = 'block';
        errorState.style.display = 'none';
        analysisContent.style.display = 'none';

        try {
            const result = await getAnalysisResults(analysisId);

            if (result.status === 'processing') {
                pollCount++;
                if (pollCount > MAX_POLLS) {
                    showError('Analysis is taking too long to process. Please check back later or contact support.');
                    // Optionally, stop polling and give a link to refresh manually
                    // tryAgainButton.onclick = () => window.location.reload(); 
                    return;
                }
                // Update loading message if needed
                loadingState.querySelector('p').textContent = `${result.detail || 'Still processing...'} (Attempt ${pollCount}/${MAX_POLLS})`;
                setTimeout(fetchAnalysis, POLL_INTERVAL); // Poll again
                return;
            }
            
            // If result is not 'processing', it should be the full analysis data or an error was thrown by getAnalysisResults
            const processedData = processAndDisplayAnalysis(result);
            if (processedData) {
                renderAnalysis(processedData);
            } else {
                // processAndDisplayAnalysis showed an error if it returned null
            }

        } catch (err) {
            console.error('Error fetching analysis:', err);
            showError(err.message || 'Failed to load analysis results. Please try again.');
        }
    }

    tryAgainButton.addEventListener('click', () => {
        pollCount = 0; // Reset poll count
        fetchAnalysis();
    });

    // Initial fetch
    fetchAnalysis();
});