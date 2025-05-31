// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    // Form elements
    const reportTypeRadios = document.querySelectorAll('input[name="reportType"]');
    const area1Input = document.getElementById('area1Input');
    const area1Label = document.getElementById('area1Label'); // For changing label text
    const area2Input = document.getElementById('area2Input');
    const diseaseFocusInput = document.getElementById('diseaseFocusInput');
    const timeRangeInput = document.getElementById('timeRangeInput');

    const area1Group = document.getElementById('area1Group');
    const area2Group = document.getElementById('area2Group');
    const diseaseFocusGroup = document.getElementById('diseaseFocusGroup');
    const diseaseFocusLabel = document.getElementById('diseaseFocusLabel');
    const diseaseFocusInfo = document.getElementById('diseaseFocusInfo');


    // UI elements
    const startResearchBtn = document.getElementById('startResearchBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessageDiv = document.getElementById('errorMessage');
    
    const reportSectionDiv = document.getElementById('reportSection');
    const reportAreaTitleH2 = document.getElementById('reportAreaTitle');
    const reportContentDiv = document.getElementById('reportContent');

    const followUpQuestionInput = document.getElementById('followUpQuestion');
    const askFollowUpBtn = document.getElementById('askFollowUpBtn');
    const followUpLoadingIndicator = document.getElementById('followUpLoadingIndicator');
    const followUpErrorMessageDiv = document.getElementById('followUpErrorMessage');
    const followUpAnswerDiv = document.getElementById('followUpAnswer');

    let currentReportData = null; 
    let chartInstances = []; 

    marked.setOptions({
        breaks: true, 
        gfm: true,    
        sanitize: false 
    });

    // --- Color Palette for Charts ---
    const baseColors = [
        { r: 26, g: 188, b: 156, a: 0.65 }, { r: 52, g: 152, b: 219, a: 0.65 }, // Teal, Blue
        { r: 155, g: 89, b: 182, a: 0.65 }, { r: 241, g: 196, b: 15, a: 0.75 }, // Purple, Yellow
        { r: 230, g: 126, b: 34, a: 0.65 }, { r: 231, g: 76, b: 60, a: 0.65 },  // Orange, Red
        { r: 46, g: 204, b: 113, a: 0.65 }, { r: 243, g: 156, b: 18, a: 0.75 }, // Green, Darker Orange
        { r: 52, g: 73, b: 94, a: 0.65 },   { r: 149, g: 165, b: 166, a: 0.65 },// Dark Blue-Gray, Mid Gray
        { r: 22, g: 160, b: 133, a: 0.65 }, { r: 41, g: 128, b: 185, a: 0.65 }, // Darker Teal, Darker Blue
        { r: 125, g: 60, b: 152, a: 0.65 }, { r: 211, g: 84, b: 0, a: 0.65 },   // Darker Purple, Burnt Orange
        { r: 189, g: 195, b: 199, a: 0.65 } // Light Gray (Concrete)
    ];

    function getRandomColor(isBorder = false, index = 0) {
        const colorObj = baseColors[index % baseColors.length];
        const alpha = isBorder ? '1' : (colorObj.a || '0.65').toString();
        return `rgba(${colorObj.r},${colorObj.g},${colorObj.b},${alpha})`;
    }

    function displayError(message, element = errorMessageDiv) {
        element.textContent = message;
        element.style.display = 'block';
    }

    function clearError(element = errorMessageDiv) {
        element.textContent = '';
        element.style.display = 'none';
    }
    
    function renderMarkdownToHtml(markdownText) {
        if (markdownText && typeof markdownText === 'string') {
            return marked.parse(markdownText);
        }
        return '<p><em>Content not available or in an unexpected format.</em></p>';
    }

    function getSelectedReportType() {
        for (const radio of reportTypeRadios) {
            if (radio.checked) {
                return radio.value;
            }
        }
        return 'comprehensive_single_area'; // Default
    }

    function updateFormVisibility() {
        const type = getSelectedReportType();
        
        area1Group.style.display = 'block'; 
        
        if (type === 'comprehensive_single_area') {
            area1Label.textContent = 'Area:';
            area2Group.style.display = 'none';
            diseaseFocusGroup.style.display = 'none';
            diseaseFocusInfo.style.display = 'none';
        } else if (type === 'compare_areas') {
            area1Label.textContent = 'Primary Area (Area 1):';
            area2Group.style.display = 'block';
            diseaseFocusGroup.style.display = 'block';
            diseaseFocusLabel.textContent = 'Optional: Focus comparison on specific Disease/Condition:';
            diseaseFocusInfo.style.display = 'block';

        } else if (type === 'disease_focus') {
            area1Label.textContent = 'Area for Disease Focus:';
            area2Group.style.display = 'none'; 
            diseaseFocusGroup.style.display = 'block';
            diseaseFocusLabel.textContent = 'Disease/Condition to Focus On:';
            diseaseFocusInfo.style.display = 'none';
        }
    }

    reportTypeRadios.forEach(radio => radio.addEventListener('change', updateFormVisibility));
    updateFormVisibility(); 

    startResearchBtn.addEventListener('click', async () => {
        const reportType = getSelectedReportType();
        const area1 = area1Input.value.trim();
        const area2 = area2Input.value.trim();
        const disease = diseaseFocusInput.value.trim();
        const timeRange = timeRangeInput.value.trim();

        if (!area1) {
            displayError('Area 1 (or Primary Area) cannot be empty.');
            return;
        }
        if (reportType === 'compare_areas' && !area2) {
            displayError('Area 2 cannot be empty for comparison reports.');
            return;
        }
        if (reportType === 'disease_focus' && !disease) {
            displayError('Disease/Condition cannot be empty for disease focus reports.');
            return;
        }

        const researchPayload = {
            report_type: reportType,
            area1: area1,
            area2: (reportType === 'compare_areas' && area2) ? area2 : null,
            disease_focus: ((reportType === 'disease_focus' || reportType === 'compare_areas') && disease) ? disease : null,
            time_range: timeRange || null
        };
        
        Object.keys(researchPayload).forEach(key => {
            if (researchPayload[key] === null || researchPayload[key] === '') {
                delete researchPayload[key]; 
            }
        });

        clearError();
        reportSectionDiv.style.display = 'none';
        reportContentDiv.innerHTML = '';
        chartInstances.forEach(chart => chart.destroy()); 
        chartInstances = [];
        followUpAnswerDiv.innerHTML = '';
        followUpQuestionInput.value = '';
        currentReportData = null;

        loadingIndicator.style.display = 'block';
        startResearchBtn.disabled = true;
        reportTypeRadios.forEach(radio => radio.disabled = true);
        [area1Input, area2Input, diseaseFocusInput, timeRangeInput].forEach(input => input.disabled = true);

        try {
             const response = await fetch('/survey-research/api/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(researchPayload) 
            });

            if (!response.ok) {
                let errorMsg = `HTTP error! Status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.detail || errorMsg;
                } catch (e) {
                    errorMsg = `${errorMsg} - ${response.statusText || 'Server error'}`;
                }
                throw new Error(errorMsg);
            }

            currentReportData = await response.json();
            displayReport(currentReportData);

        } catch (error) {
            console.error('Research error:', error);
            displayError(`Failed to generate health report: ${error.message}`);
            if (currentReportData && currentReportData.full_report_markdown && currentReportData.full_report_markdown.startsWith("Error:")) {
                 reportContentDiv.innerHTML = `<div class="report-subsection"><h3>Raw AI Error Details</h3><pre style="white-space: pre-wrap; word-wrap: break-word;">${currentReportData.full_report_markdown}</pre></div>`;
                 reportSectionDiv.style.display = 'block';
            }
        } finally {
            loadingIndicator.style.display = 'none';
            startResearchBtn.disabled = false;
            reportTypeRadios.forEach(radio => radio.disabled = false);
            [area1Input, area2Input, diseaseFocusInput, timeRangeInput].forEach(input => input.disabled = false);
        }
    });

    function displayReport(data) {
        if (!data || !data.area_name || typeof data.full_report_markdown !== 'string') {
            displayError("Received invalid report data from the server.");
            reportSectionDiv.style.display = 'none';
            return;
        }
        reportAreaTitleH2.textContent = `Health Analysis: ${data.area_name}`;
        
        chartInstances.forEach(chart => chart.destroy());
        chartInstances = [];
        reportContentDiv.innerHTML = '';

        if (data.full_report_markdown.startsWith("Error:")) {
            reportContentDiv.innerHTML = `<div class="report-subsection"><h3>Report Generation Error</h3><pre style="white-space: pre-wrap; word-wrap: break-word;">${data.full_report_markdown}</pre></div>`;
            reportSectionDiv.style.display = 'block';
            document.getElementById('followUpSection').style.display = 'none'; 
            return;
        } else {
            document.getElementById('followUpSection').style.display = 'block';
        }
        
        let markdownWithPlaceholders = data.full_report_markdown;
        const chartDataForRendering = []; 
        const chartDirectiveRegex = /CHART_DATA:\s*TYPE=(?<type>\w+)\s*TITLE="(?<title>[^"]+)"\s*LABELS=(?<labels>\[[^\]]*\])\s*DATA=(?<data>\[[^\]]*\])(?:\s*SOURCE="(?<source>[^"]+)")?/g;
        
        let match;
        let chartIndex = 0;
        let parsedChartsFromServer = data.charts || [];

        while ((match = chartDirectiveRegex.exec(data.full_report_markdown)) !== null) {
            const placeholderId = `chart-placeholder-${chartIndex}`;
            markdownWithPlaceholders = markdownWithPlaceholders.replace(match[0], `<div id="${placeholderId}" class="chart-render-target"></div>`);
            
            const parsedChart = parsedChartsFromServer[chartIndex]; 
            if (parsedChart) {
                 chartDataForRendering.push({ placeholderId, chartConfig: parsedChart });
            } else {
                console.warn(`Could not find server-parsed chart data for directive match index ${chartIndex}: ${match[0]}.`);
            }
            chartIndex++;
        }

        reportContentDiv.innerHTML = renderMarkdownToHtml(markdownWithPlaceholders);

        if (chartDataForRendering.length > 0) {
            chartDataForRendering.forEach((item, currentChartOverallIndex) => {
                const placeholderElement = document.getElementById(item.placeholderId);
                if (placeholderElement) {
                    const canvas = document.createElement('canvas');
                    canvas.id = `chart-canvas-${item.placeholderId.split('-').pop()}`; 
                    placeholderElement.appendChild(canvas);
                    
                    const ctx = canvas.getContext('2d');
                    try {
                        const chartConfig = item.chartConfig;
                        let chartTypeOption = chartConfig.type.toLowerCase() || 'bar';
                        let indexAxisValue = 'x'; // Default for vertical bar charts

                        if (chartTypeOption === 'horizontalbar') {
                            chartTypeOption = 'bar';        // Correct Chart.js type
                            indexAxisValue = 'y';     // Make it horizontal
                        }
                        // Optional: Add heuristics to make other bar charts horizontal if they have many labels
                        // else if (chartTypeOption === 'bar' && chartConfig.labels.length > 8) { // Example: if more than 8 labels, make it horizontal
                        //    indexAxisValue = 'y';
                        // }


                        const newChart = new Chart(ctx, {
                            type: chartTypeOption, 
                            data: {
                                labels: chartConfig.labels,
                                datasets: chartConfig.datasets.map((ds, datasetIndex) => {
                                    let bgColors;
                                    let borderColors;
                                    const currentChartTypeLower = chartTypeOption; // Use the potentially corrected type

                                    if (['pie', 'doughnut', 'polarArea'].includes(currentChartTypeLower)) {
                                        bgColors = ds.data.map((_, dataPointIndex) => 
                                            getRandomColor(false, currentChartOverallIndex * 10 + datasetIndex * 5 + dataPointIndex)
                                        );
                                        borderColors = '#fff';
                                    } else if (currentChartTypeLower === 'bar') { // Covers both vertical and horizontal
                                        if (chartConfig.datasets.length === 1) { // Single dataset bar chart, varied colors for bars
                                            bgColors = ds.data.map((_, dataPointIndex) => 
                                                getRandomColor(false, currentChartOverallIndex * 10 + dataPointIndex)
                                            );
                                            borderColors = bgColors.map(color => color.replace(/rgba\(([^,]+),([^,]+),([^,]+),[^)]+\)/, 'rgb($1,$2,$3)'));
                                        } else { // Multi-dataset bar chart, one color per dataset
                                            const colorBaseIndex = currentChartOverallIndex * 10 + datasetIndex;
                                            bgColors = getRandomColor(false, colorBaseIndex);
                                            borderColors = getRandomColor(true, colorBaseIndex);
                                        }
                                    }
                                    else { // line, radar, etc.
                                        const colorBaseIndex = currentChartOverallIndex * 10 + datasetIndex;
                                        bgColors = ds.backgroundColor || getRandomColor(false, colorBaseIndex);
                                        borderColors = ds.borderColor || getRandomColor(true, colorBaseIndex);
                                    }

                                    return {
                                        label: ds.label || chartConfig.title || `Dataset ${datasetIndex + 1}`,
                                        data: ds.data,
                                        backgroundColor: bgColors, 
                                        borderColor: borderColors,
                                        borderWidth: (['pie', 'doughnut', 'polarArea'].includes(currentChartTypeLower)) ? 2 : 1.5,
                                        tension: (currentChartTypeLower === 'line' || currentChartTypeLower === 'radar') ? 0.3 : 0,
                                        fill: (currentChartTypeLower === 'radar' && chartConfig.datasets.length === 1) ? 'origin' : 
                                              (currentChartTypeLower === 'line' && chartConfig.datasets.length === 1 && ds.data.length > 1) ? 'origin' : false,
                                    };
                                })
                            },
                            options: {
                                indexAxis: indexAxisValue, 
                                responsive: true,
                                maintainAspectRatio: true, 
                                aspectRatio: (chartTypeOption === 'pie' || chartTypeOption === 'doughnut') ? 1.5 : (indexAxisValue === 'y' ? 1.2 : 2), // Adjust aspect ratio for horizontal bars
                                animation: { duration: 600, easing: 'easeOutQuart' },
                                plugins: {
                                    title: {
                                        display: !!chartConfig.title,
                                        text: chartConfig.title,
                                        font: { size: 16, weight: 'bold' },
                                        padding: { top: 10, bottom: (chartConfig.source ? 5 : 20) }
                                    },
                                    subtitle: {
                                        display: !!chartConfig.source,
                                        text: chartConfig.source ? `Source: ${chartConfig.source}` : '',
                                        font: { size: 10, style: 'italic' },
                                        color: '#666',
                                        padding: { bottom: 15 }
                                    },
                                    legend: {
                                        display: chartConfig.datasets.length > 1 || ['pie', 'doughnut', 'polarArea'].includes(chartTypeOption),
                                        position: 'top',
                                        labels: { font: { size: 12 } }
                                    },
                                    tooltip: {
                                        enabled: true, 
                                        mode: 'index',
                                        intersect: false,
                                        callbacks: {
                                            label: function(context) {
                                                let label = '';
                                                const renderedChartType = context.chart.config.type; 
                                                
                                                if (['pie', 'doughnut', 'polarArea'].includes(renderedChartType)) {
                                                    label = context.label || '';
                                                } else {
                                                    label = context.dataset.label || '';
                                                }

                                                if (label) { label += ': '; }

                                                let value;
                                                if (context.chart.config.options.indexAxis === 'y') { 
                                                    if (context.parsed.x !== undefined) value = context.parsed.x;
                                                } else { 
                                                    if (context.parsed.y !== undefined) value = context.parsed.y;
                                                }
                                                
                                                if (value === undefined && context.parsed.r !== undefined) value = context.parsed.r;
                                                else if (value === undefined) value = context.parsed; 

                                                if (value !== null && value !== undefined) {
                                                    label += new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
                                                }
                                                return label;
                                            }
                                        }
                                    }
                                },
                                scales: (chartTypeOption === 'bar' || chartTypeOption === 'line' || chartTypeOption === 'scatter') ? {
                                    [indexAxisValue === 'y' ? 'x' : 'y']: { 
                                        beginAtZero: true,
                                        ticks: { font: { size: 11 }, callback: value => Number(value.toFixed(1)) },
                                        grid: { color: 'rgba(200, 200, 200, 0.2)' }
                                    },
                                    [indexAxisValue === 'y' ? 'y' : 'x']: { 
                                        ticks: { 
                                            font: { size: 11 }, 
                                            autoSkip: true, 
                                            maxTicksLimit: (indexAxisValue === 'y' ? (chartConfig.labels.length > 15 ? 15 : chartConfig.labels.length) : 10), // Allow more for horizontal
                                            maxRotation: (indexAxisValue === 'y' ? 0 : 45), // No rotation for y-axis labels
                                            minRotation: (indexAxisValue === 'y' ? 0 : 0)
                                        },
                                        grid: { display: false }
                                    }
                                } : chartTypeOption === 'radar' ? {
                                    r: {
                                        angleLines: { display: true, color: 'rgba(200, 200, 200, 0.2)' },
                                        suggestedMin: 0,
                                        pointLabels: { font: { size: 11 } },
                                        grid: { color: 'rgba(200, 200, 200, 0.2)' },
                                        ticks: { backdropColor: 'transparent', font: {size: 10}, callback: value => Number(value.toFixed(1)) }
                                    }
                                } : {} 
                            }
                        });
                        chartInstances.push(newChart);
                    } catch(e) {
                        console.error("Error rendering chart:", e, "Chart Config:", JSON.stringify(item.chartConfig, null, 2));
                        placeholderElement.innerHTML = `<p class="error-message">Could not render chart: ${item.chartConfig.title || 'Untitled Chart'}. Error: ${e.message}</p>`;
                    }
                } else {
                    console.warn(`Placeholder element ${item.placeholderId} not found in DOM after Markdown rendering.`);
                }
            });
        }
        
        reportSectionDiv.style.display = 'block';
    }
    
    askFollowUpBtn.addEventListener('click', async () => {
        const question = followUpQuestionInput.value.trim();
        if (!question) {
            displayError('Please enter a follow-up question.', followUpErrorMessageDiv);
            return;
        }
        if (!currentReportData || !currentReportData.report_id || !currentReportData.full_text_for_follow_up) {
            displayError('No report context available for follow-up. Please generate a report first.', followUpErrorMessageDiv);
            return;
        }

        clearError(followUpErrorMessageDiv);
        followUpAnswerDiv.innerHTML = '';
        followUpLoadingIndicator.style.display = 'block';
        askFollowUpBtn.disabled = true;
        followUpQuestionInput.disabled = true;

        try {
            const response = await fetch('/survey-research/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    report_id: currentReportData.report_id,
                    question: question,
                    report_context: currentReportData.full_text_for_follow_up 
                })
            });

            if (!response.ok) {
                let errorMsg = `HTTP error! Status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.detail || errorMsg;
                } catch (e) {
                     errorMsg = `${errorMsg} - ${response.statusText || 'Server error'}`;
                }
                throw new Error(errorMsg);
            }

            const answerData = await response.json();
            followUpAnswerDiv.innerHTML = renderMarkdownToHtml(answerData.answer);

        } catch (error) {
            console.error('Follow-up error:', error);
            displayError(`Failed to get answer: ${error.message}`, followUpErrorMessageDiv);
        } finally {
            followUpLoadingIndicator.style.display = 'none';
            askFollowUpBtn.disabled = false;
            followUpQuestionInput.disabled = false;
        }
    });
});