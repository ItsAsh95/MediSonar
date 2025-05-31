// medical-assistant/static/js/chat_logic.js

window.chatLogic = (() => { // IIFE to create a namespace

    // --- DOM Element References (from new UI structure in index.html) ---
    const mainUserInput = document.getElementById('mainUserInput');
    const mainSendBtn = document.getElementById('mainSendBtn');
    const activeChatWindow = document.getElementById('activeChatWindow'); // Main display area
    const mainFileUploadInput = document.getElementById('mainFileUpload');
    const filePreviewAreaMain = document.getElementById('filePreviewAreaMain');
    const filePreviewNameMain = document.getElementById('filePreviewNameMain');
    const removeFileBtnMain = document.getElementById('removeFileBtnMain');

    // Master History Modal Elements (assuming these IDs are on your modal)
    const masterHistoryModalEl = document.getElementById('masterHistoryModal'); // For Bootstrap JS
    const masterHistoryModalBody = document.getElementById('masterHistoryModalBody');
    const clearAllDataBtn = document.getElementById('clearAllDataBtn'); // In master history modal

    // Navbar button for PDF download
    const downloadChatPdfBtn = document.getElementById('downloadChatPdfBtn');

    let currentUploadedFileMain = null;
    let activeChartsDisplayed = {}; // Store charts per message ID: { messageId: [chartInstance, ...] }


    // --- Utility Functions ---
    function escapeHtml(unsafe) {
        if (unsafe === null || typeof unsafe === 'undefined') return '';
        return String(unsafe)
             .replace(/&/g, "&")
             .replace(/</g, "<")
             .replace(/>/g, ">")
             .replace(/"/g, "'")
             .replace(/'/g, "'");
    }

    function renderMarkdown(markdownText) {
        if (window.marked && typeof markdownText === 'string') {
            marked.setOptions({ breaks: true, gfm: true, sanitize: true });
            return marked.parse(markdownText);
        }
        // Fallback for plain text rendering with line breaks
        return `<p>${escapeHtml(markdownText || "").replace(/\n/g, '<br>')}</p>`;
    }

    // --- Helper functions for appending structured AI data to message content ---
    function appendFollowUpQuestions(parentDiv, questions) {
        if (!questions || !Array.isArray(questions) || questions.length === 0) return;
        const fupDiv = document.createElement('div');
        fupDiv.className = 'mt-2 ai-structured-info';
        fupDiv.innerHTML = `<strong>Follow-up Questions:</strong><ul>${questions.map(q => `<li>${escapeHtml(q)}</li>`).join('')}</ul>`;
        parentDiv.appendChild(fupDiv);
    }

    function appendSimpleInfo(parentDiv, title, text) {
        if (text === null || typeof text === 'undefined' || text === "") return;
        const infoDiv = document.createElement('div');
        infoDiv.className = 'mt-2 ai-structured-info';
        infoDiv.innerHTML = `<strong>${escapeHtml(title)}:</strong> ${renderMarkdown(text)}`;
        parentDiv.appendChild(infoDiv);
    }

    function appendList(parentDiv, title, items) {
        if (!items || !Array.isArray(items) || items.length === 0) return;
        const listDiv = document.createElement('div');
        listDiv.className = 'mt-2 ai-structured-info';
        listDiv.innerHTML = `<strong>${escapeHtml(title)}:</strong><ul>${items.map(item => `<li>${renderMarkdown(item)}</li>`).join('')}</ul>`;
        parentDiv.appendChild(listDiv);
    }

    function appendSchemes(parentDiv, schemes) {
        if (!schemes || !Array.isArray(schemes) || schemes.length === 0) return;
        const schemesDiv = document.createElement('div');
        schemesDiv.className = 'mt-2 ai-structured-info';
        let html = '<strong>Relevant Government Schemes:</strong><ul class="list-unstyled">';
        schemes.forEach(s => {
            if (s && s.name) { // Ensure scheme object and name exist
                html += `<li class="mb-1"><strong>${escapeHtml(s.name)}</strong> ${s.region_specific ? `(${escapeHtml(s.region_specific)})` : ''}: ${renderMarkdown(s.description || '')} ${s.url ? `<a href="${s.url}" target="_blank" rel="noopener noreferrer">[Details]</a>` : ''} ${s.source_info ? `<small class="text-muted d-block"><em>Source: ${escapeHtml(s.source_info)}</em></small>` : ''}</li>`;
            }
        });
        html += '</ul>';
        schemesDiv.innerHTML = html;
        parentDiv.appendChild(schemesDiv);
    }

    function appendDoctorRecommendations(parentDiv, doctors) {
        if (!doctors || !Array.isArray(doctors) || doctors.length === 0) return;
        const drDiv = document.createElement('div');
        drDiv.className = 'mt-2 ai-structured-info';
        let html = '<strong>Doctor Recommendations:</strong><ul class="list-unstyled">';
        doctors.forEach(dr => {
            if (dr && dr.specialty) { // Ensure doctor object and specialty exist
                html += `<li class="mb-1">Consult a <strong>${escapeHtml(dr.specialty)}</strong>. ${dr.reason ? `Reason: ${renderMarkdown(dr.reason)}` : ''} ${dr.source_info ? `<small class="text-muted d-block"><em>Source/Basis: ${escapeHtml(dr.source_info)}</em></small>` : ''}</li>`;
            }
        });
        html += '</ul>';
        drDiv.innerHTML = html;
        parentDiv.appendChild(drDiv);
    }

    // --- Chat Message Display Logic ---
    function addMessageToChat(messageData, sender, _currentModeForHistory, interactionId = null) { // _currentModeForHistory not directly used here but kept for signature if needed
        if (!activeChatWindow) { console.error("activeChatWindow element not found!"); return; }

        const messageTimestamp = messageData.timestamp || new Date().toISOString();
        const messageId = interactionId || `msg-${new Date(messageTimestamp).getTime()}-${Math.random().toString(36).substr(2, 9)}`;

        const messageOuterContainer = document.createElement('div');
        messageOuterContainer.classList.add('message-container', sender === 'user' ? 'user-message-outer' : 'ai-message-outer');
        messageOuterContainer.id = messageId;

        const messageDiv = document.createElement('div');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
        
        const avatar = document.createElement('div');
        avatar.classList.add('avatar', sender === 'user' ? 'user-avatar' : 'ai-avatar');
        avatar.innerHTML = `<i class="fas ${sender === 'user' ? 'fa-user-alt' : 'fa-robot'}"></i>`;

        const messageContentDiv = document.createElement('div');
        messageContentDiv.classList.add('message-content');
        
        let textContentForCopy = "";

        if (sender === 'ai') {
            textContentForCopy = messageData.answer || ""; // Raw answer text for copy
            if (messageData.answer_format === 'markdown' && messageData.answer) {
                messageContentDiv.innerHTML = renderMarkdown(messageData.answer);
            } else {
                messageContentDiv.textContent = messageData.answer || "Error: AI response was empty or unformatted.";
            }

            // Append structured data if available
            appendFollowUpQuestions(messageContentDiv, messageData.follow_up_questions);
            appendSimpleInfo(messageContentDiv, "Potential Identification", messageData.disease_identification);
            appendList(messageContentDiv, "Next Steps", messageData.next_steps);
            appendSchemes(messageContentDiv, messageData.government_schemes);
            appendDoctorRecommendations(messageContentDiv, messageData.doctor_recommendations);
            
            if (messageData.graphs_data && messageData.graphs_data.length > 0) {
                messageData.graphs_data.forEach(graph => displayGraph(graph, messageContentDiv, messageId));
            }
            if (messageData.file_processed_with_message) {
                 const fileProcessedP = document.createElement('p');
                 fileProcessedP.innerHTML = `<small class="text-muted mt-2 d-block"><i>Context included file: ${escapeHtml(messageData.file_processed_with_message)}</i></small>`;
                 messageContentDiv.appendChild(fileProcessedP);
            }

            // Add Copy button
            const controlsDiv = document.createElement('div');
            controlsDiv.className = 'ai-message-controls mt-2 text-right';
            const copyButton = document.createElement('button');
            copyButton.className = 'btn btn-xs btn-outline-secondary copy-btn';
            copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy Text';
            copyButton.title = "Copy AI's main response text";
            copyButton.setAttribute('aria-label', "Copy AI response");
            copyButton.addEventListener('click', (e) => {
                e.stopPropagation();
                navigator.clipboard.writeText(textContentForCopy).then(() => {
                    copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    setTimeout(() => { copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy Text'; }, 2000);
                }).catch(err => { 
                    console.error('Failed to copy text: ', err); 
                    alert('Failed to copy text. Your browser might not support this feature or permission was denied.'); 
                });
            });
            controlsDiv.appendChild(copyButton);
            // Append controls to messageContentDiv instead of messageDiv to keep it with the text
            messageContentDiv.appendChild(controlsDiv);

        } else { // User message
            messageContentDiv.textContent = messageData.text;
            textContentForCopy = messageData.text; // Not typically copied by user this way, but available
            if (messageData.fileName) {
                const fileInfoP = document.createElement('p');
                fileInfoP.innerHTML = `<small class="text-muted mt-1 d-block"><i>File attached: ${escapeHtml(messageData.fileName)}</i></small>`;
                messageContentDiv.appendChild(fileInfoP);
            }
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContentDiv);
        messageOuterContainer.appendChild(messageDiv);
        activeChatWindow.appendChild(messageOuterContainer);
        activeChatWindow.scrollTop = activeChatWindow.scrollHeight;
    }

    // --- Graph Display Logic ---
    function displayGraph(graphData, parentElementToAppendTo, messageId) {
        if (!parentElementToAppendTo) { console.error("Cannot display graph, parent element is null for message " + messageId); return; }
        if (!activeChartsDisplayed[messageId]) {
            activeChartsDisplayed[messageId] = [];
        }
        // Destroy previous charts *for this specific message* if re-rendering or updating
        activeChartsDisplayed[messageId].forEach(chart => chart.destroy());
        activeChartsDisplayed[messageId] = [];

        const chartWrapper = document.createElement('div');
        chartWrapper.className = 'chart-container mt-3 p-2 border rounded'; // Added some padding and border

        const titleEl = document.createElement('h6');
        titleEl.className = 'text-center mb-2'; // Center title
        titleEl.textContent = graphData.title || "Chart";
        chartWrapper.appendChild(titleEl);
        
        const canvasWrapper = document.createElement('div');
        canvasWrapper.className = 'chart-canvas-wrapper'; // Ensure this has CSS for height/width
        const canvas = document.createElement('canvas');
        canvasWrapper.appendChild(canvas);
        chartWrapper.appendChild(canvasWrapper);
        
        parentElementToAppendTo.appendChild(chartWrapper);

        try {
            const newChart = new Chart(canvas, {
                type: graphData.type.toLowerCase() || 'bar',
                data: {
                    labels: graphData.labels || [],
                    datasets: graphData.datasets || []
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, // Important for custom wrapper height
                    scales: { y: { beginAtZero: true } },
                    plugins: { legend: { display: (graphData.datasets && graphData.datasets.length > 1) } } // Show legend if multiple datasets
                }
            });
            activeChartsDisplayed[messageId].push(newChart);
        } catch (e) {
            console.error("Error creating chart:", e, "with data:", graphData);
            chartWrapper.innerHTML += "<p class='text-danger small mt-1'>Error rendering chart.</p>";
        }
        if (activeChatWindow) activeChatWindow.scrollTop = activeChatWindow.scrollHeight;
    }

    function clearAllDisplayedCharts() {
        for (const messageId in activeChartsDisplayed) {
            if (Array.isArray(activeChartsDisplayed[messageId])) {
                activeChartsDisplayed[messageId].forEach(chart => chart.destroy());
            }
        }
        activeChartsDisplayed = {};
    }
    
    // --- Loading Indicator Logic ---
    function addLoadingIndicator() {
        if (!activeChatWindow) return;
        const loadingOuter = document.createElement('div');
        loadingOuter.id = 'loading-indicator-outer';
        loadingOuter.classList.add('message-container', 'ai-message-outer');
        
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('ai-message', 'loading-indicator');

        const avatar = document.createElement('div');
        avatar.classList.add('avatar', 'ai-avatar');
        avatar.innerHTML = `<i class="fas fa-robot fa-spin"></i>`; // Spinning robot

        const content = document.createElement('div');
        content.classList.add('message-content');
        content.innerHTML = `<p><i>AI is thinking...</i></p>`;
        
        loadingDiv.appendChild(avatar);
        loadingDiv.appendChild(content);
        loadingOuter.appendChild(loadingDiv);
        activeChatWindow.appendChild(loadingOuter);
        activeChatWindow.scrollTop = activeChatWindow.scrollHeight;
    }

    function removeLoadingIndicator() {
        const loadingIndicator = document.getElementById('loading-indicator-outer');
        if (loadingIndicator) loadingIndicator.remove();
    }

    // --- Send Message Logic ---
    async function handleSendMessage() {
        if (!mainUserInput || !mainSendBtn) return; // Guard clause

        const messageText = mainUserInput.value.trim();
        const currentMode = window.currentActiveChatMode || 'qna'; // From main_ui.js
        let userRegion = null;

        if (currentMode === 'symptoms' || currentMode === 'report') {
            if (window.getSelectedRegion) userRegion = window.getSelectedRegion();
        }

        if (!messageText && !currentUploadedFileMain) return;
        
        addMessageToChat({ text: messageText, fileName: currentUploadedFileMain ? currentUploadedFileMain.name : null }, 'user', currentMode);
        mainUserInput.value = ''; 
        mainUserInput.style.height = 'auto'; // Reset textarea height

        addLoadingIndicator();

        const formData = new FormData();
        if (messageText) formData.append('message', messageText);
        formData.append('mode_str', currentMode); // Backend expects 'mode_str'
        if (userRegion) formData.append('user_region', userRegion);
        if (currentUploadedFileMain) {
            formData.append('upload_file', currentUploadedFileMain, currentUploadedFileMain.name);
        }

        try {
            const response = await fetch('/api/v1/chat', { method: 'POST', body: formData });
            removeLoadingIndicator();
            const data = await response.json(); // Expecting ChatMessageOutput schema

            if (response.ok) {
                addMessageToChat(data, 'ai', currentMode, data.id /* If backend sends an ID for the interaction */);
            } else {
                addMessageToChat({ answer: data.detail || data.error || 'An API error occurred.', answer_format: 'text' }, 'ai', currentMode);
            }
        } catch (error) {
            removeLoadingIndicator();
            console.error('Error sending message:', error);
            addMessageToChat({ answer: 'Could not connect to the server. Please try again later.', answer_format: 'text'}, 'ai', currentMode);
        } finally {
            if (currentUploadedFileMain) {
                currentUploadedFileMain = null; 
                if (mainFileUploadInput) mainFileUploadInput.value = null;
                if (filePreviewAreaMain) filePreviewAreaMain.style.display = 'none';
                if (filePreviewNameMain) filePreviewNameMain.textContent = '';
            }
        }
    }

    if (mainSendBtn) mainSendBtn.addEventListener('click', handleSendMessage);
    if (mainUserInput) {
        mainUserInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });
    }
    
    if (mainFileUploadInput) {
        mainFileUploadInput.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                currentUploadedFileMain = e.target.files[0];
                if (currentUploadedFileMain.size > 10 * 1024 * 1024) { // 10MB
                    alert("File is too large! Max 10MB.");
                    currentUploadedFileMain = null; mainFileUploadInput.value = "";
                    if(filePreviewAreaMain) filePreviewAreaMain.style.display = 'none'; return;
                }
                if(filePreviewNameMain) filePreviewNameMain.textContent = currentUploadedFileMain.name;
                if(filePreviewAreaMain) filePreviewAreaMain.style.display = 'block';
            }
        });
    }
    if (removeFileBtnMain) {
        removeFileBtnMain.addEventListener('click', () => {
            currentUploadedFileMain = null; if(mainFileUploadInput) mainFileUploadInput.value = null;
            if(filePreviewAreaMain) filePreviewAreaMain.style.display = 'none';
            if(filePreviewNameMain) filePreviewNameMain.textContent = '';
        });
    }

    // --- History Logic ---
    async function loadChatForModePublic(mode) {
        if (!activeChatWindow) return;
        activeChatWindow.innerHTML = ''; // Clear current chat
        clearAllDisplayedCharts();
        
        const loadingMsgId = `loading-history-${mode}`;
        addMessageToChat({ answer: `Loading ${mode.replace(/_/g, ' ')} history...`, answer_format: 'text', timestamp: new Date().toISOString()}, 'ai', mode, loadingMsgId);

        try {
            const response = await fetch(`/api/v1/history/${mode}`);
            const existingLoadingMsg = document.getElementById(loadingMsgId);
            if(existingLoadingMsg) existingLoadingMsg.remove();

            if (!response.ok) throw new Error(`Failed to fetch history for ${mode}. Status: ${response.status}`);
            const historyInteractions = await response.json();
            
            if (historyInteractions && historyInteractions.length > 0) {
                historyInteractions.forEach(interaction => {
                    let aiMessageDataForDisplay = { answer: interaction.ai_response, answer_format: 'markdown', timestamp: interaction.timestamp };
                    // If you start storing full ChatMessageOutput JSON string in history:
                    // if (interaction.ai_response_full_obj) { try { aiMessageDataForDisplay = JSON.parse(interaction.ai_response_full_obj); } catch(e){} }
                    
                    if (interaction.user_message || interaction.file_processed) {
                        addMessageToChat({ text: interaction.user_message, fileName: interaction.file_processed, timestamp: interaction.timestamp }, 'user', mode, interaction.id);
                    }
                    if (interaction.ai_response) { // Check if AI response exists
                        addMessageToChat(aiMessageDataForDisplay, 'ai', mode, interaction.id);
                    }
                });
            } else {
                addMessageToChat({ answer: `No history found for ${mode.replace(/_/g, ' ')} mode. Start a new conversation!`, answer_format: 'text', timestamp: new Date().toISOString()}, 'ai', mode);
            }
        } catch (error) {
            console.error(`Error loading history for ${mode}:`, error);
            const existingLoadingMsgOnError = document.getElementById(loadingMsgId);
            if(existingLoadingMsgOnError) existingLoadingMsgOnError.remove();
            addMessageToChat({ answer: `Could not load history for ${mode.replace(/_/g, ' ')}. Error: ${error.message}`, answer_format: 'text', timestamp: new Date().toISOString()}, 'ai', mode);
        }
    }
    
    async function showMasterHistoryModalPublic() {
        if (!masterHistoryModalBody || !masterHistoryModalEl) return;
        masterHistoryModalBody.innerHTML = '<p class="text-center p-3"><i>Loading all history... <i class="fas fa-spinner fa-spin"></i></i></p>';
        // Use Bootstrap's JS to show modal if it's not already shown by data-toggle
        // var modal = new bootstrap.Modal(masterHistoryModalEl); modal.show(); // For BS5
        $(masterHistoryModalEl).modal('show'); // For BS4 with jQuery

        try {
            const response = await fetch('/api/v1/history/summary/all');
            if (!response.ok) throw new Error("Failed to fetch master history summary.");
            const data = await response.json();
            
            let html = '';
            html += '<h5>Medical Summary</h5>';
            if (data.medical_summary && Object.keys(data.medical_summary).length > 0 && 
                (data.medical_summary.symptoms_log?.length || data.medical_summary.analyzed_reports_info?.length || data.medical_summary.key_diagnoses_mentioned?.length)) {
                html += '<dl class="row">';
                for (const key in data.medical_summary) {
                    const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    let value = data.medical_summary[key];
                    if (Array.isArray(value) && value.length > 0) {
                        if (key === "symptoms_log") {
                            value = value.map(s => `<li>${new Date(s.date).toLocaleDateString()}: ${escapeHtml(s.symptoms.join(', '))}${s.notes ? ` (${escapeHtml(s.notes)})` : ''}</li>`).join('');
                            value = `<ul>${value}</ul>`;
                        } else if (key === "analyzed_reports_info") {
                             value = value.map(r => `<li>${escapeHtml(r.name || "Report")} (${new Date(r.date_analyzed).toLocaleDateString()}) - ${escapeHtml(r.key_findings_summary || "Summary N/A")}</li>`).join('');
                             value = `<ul>${value}</ul>`;
                        } else {
                            value = value.map(v => escapeHtml(v)).join(', ');
                        }
                    } else if (typeof value !== 'object' && value) { // Simple value
                        value = escapeHtml(value);
                    } else { value = 'N/A'; }
                    if (value !== 'N/A' && (!Array.isArray(data.medical_summary[key]) || data.medical_summary[key].length > 0 ) ) { // Only display if there's content
                        html += `<dt class="col-sm-3">${escapeHtml(title)}</dt><dd class="col-sm-9">${value}</dd>`;
                    }
                }
                html += '</dl><hr/>';
            } else { html += '<p>No medical summary available.</p><hr/>'; }

            for (const mode in data.conversation_summaries) {
                html += `<h5>${mode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} Conversations</h5>`;
                const interactions = data.conversation_summaries[mode];
                if (interactions && interactions.length > 0) {
                    html += '<ul class="list-unstyled">';
                    interactions.slice().reverse().forEach(item => { // Newest first
                        const userMsgDisplay = item.user_message || (item.file_processed ? `<i>File: ${escapeHtml(item.file_processed)}</i>` : '<i>No text message</i>');
                        const aiRespDisplay = item.ai_response ? renderMarkdown(item.ai_response.substring(0, 150) + (item.ai_response.length > 150 ? '...' : '')) : '<i>No AI response.</i>';
                        html += `<li class="mb-2 p-2 border rounded">
                                   <small><strong>${new Date(item.timestamp).toLocaleString()}</strong></small><br/>
                                   <strong>You:</strong> ${escapeHtml(userMsgDisplay)}<br/>
                                   <strong>AI:</strong> ${aiRespDisplay}
                                 </li>`;
                    });
                    html += '</ul>';
                } else { html += '<p>No conversations in this mode.</p>'; }
                html += '<hr class="my-3"/>';
            }
            masterHistoryModalBody.innerHTML = html;
        } catch (e) { 
            masterHistoryModalBody.innerHTML = '<p class="text-danger text-center">Error loading history summary.</p>'; 
            console.error("Error loading master history:", e); 
        }
    }

    if (clearAllDataBtn) {
        clearAllDataBtn.addEventListener('click', async () => {
            if (confirm("Are you sure you want to clear ALL your data? This includes all chat histories and your medical summary. This action cannot be undone.")) {
                try {
                    const response = await fetch('/api/v1/history/clear/all', { method: 'POST' });
                    if (response.ok) {
                        $(masterHistoryModalEl).modal('hide'); // For BS4
                        if (window.currentActiveChatMode && window.chatLogic.loadChatForMode) {
                            loadChatForModePublic(window.currentActiveChatMode); // Reload current chat to show it's empty
                        }
                        // Add a message to the main chat window confirming clearance
                        if (activeChatWindow) addMessageToChat({ answer: "All your data has been successfully cleared.", answer_format: 'text'}, 'ai', window.currentActiveChatMode || 'qna');
                        alert("All your data has been cleared.");
                    } else { 
                        const errData = await response.json();
                        alert(`Failed to clear data. Server error: ${errData.detail || response.statusText}`); 
                    }
                } catch (e) { console.error("Error during clearAllData:", e); alert("Error clearing data. Network issue or server down."); }
            }
        });
    }
    
    // PDF Download Logic (Document Style)
    if (downloadChatPdfBtn) {
        downloadChatPdfBtn.addEventListener('click', async () => {
            if (typeof window.jspdf === 'undefined') { alert("PDF library not loaded."); return; }
            const { jsPDF } = window.jspdf;
            const activeMode = window.currentActiveChatMode || 'qna';

            addMessageToChat({ answer: "Preparing transcript for PDF generation...", answer_format: 'text'}, 'ai', activeMode);

            try {
                const response = await fetch(`/api/v1/history/${activeMode}`);
                if (!response.ok) throw new Error(`Failed to fetch history for ${activeMode} for PDF.`);
                const modeHistory = await response.json();

                if (!modeHistory || modeHistory.length === 0) {
                    alert(`No chat history found for ${activeMode} mode to download.`);
                    removeLoadingIndicator(); // Or find and remove the "Preparing..." message
                    return;
                }

                const pdf = new jsPDF({ orientation: 'p', unit: 'pt', format: 'a4' });
                const pageWidth = pdf.internal.pageSize.getWidth();
                const margin = 40;
                const maxLineWidth = pageWidth - 2 * margin;
                let yPosition = margin;
                const lineHeightFactor = 1.4; // Increased for better readability
                const smallFontSize = 9;
                const normalFontSize = 11;

                function addWrappedText(text, fontSize, isBold = false, isContinuation = false, indent = 0) {
                    if (yPosition > margin && !isContinuation) yPosition += (fontSize * 0.5); // Space before new block
                    
                    pdf.setFontSize(fontSize);
                    pdf.setFont(undefined, isBold ? 'bold' : 'normal');
                    
                    const lines = pdf.splitTextToSize(text || " ", maxLineWidth - indent); // text || " " to avoid error on null
                    lines.forEach(line => {
                        if (yPosition + fontSize > pdf.internal.pageSize.getHeight() - margin) {
                            pdf.addPage();
                            yPosition = margin;
                        }
                        pdf.text(line, margin + indent, yPosition);
                        yPosition += (fontSize * lineHeightFactor);
                    });
                }
                
                addWrappedText(`AI Medical Assistant - Chat Transcript`, 16, true);
                addWrappedText(`Mode: ${activeMode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`, 12);
                addWrappedText(`Generated: ${new Date().toLocaleString()}`, smallFontSize);
                yPosition += 20;

                modeHistory.forEach(interaction => {
                    const timestamp = new Date(interaction.timestamp).toLocaleString();
                    let userMsgDisplay = interaction.user_message || "";
                    if (interaction.file_processed) userMsgDisplay += ` (File: ${interaction.file_processed})`;
                    
                    if (userMsgDisplay.trim()) {
                        addWrappedText(`You (${timestamp}):`, smallFontSize, true);
                        addWrappedText(userMsgDisplay, normalFontSize, false, true);
                    }

                    if (interaction.ai_response) {
                        addWrappedText(`AI (${timestamp}):`, smallFontSize, true);
                        // For PDF, we use the raw answer. Markdown rendering to PDF is complex with jsPDF alone.
                        // This will print the markdown syntax. For rich text, would need html-to-pdf library or advanced jsPDF.
                        addWrappedText(interaction.ai_response, normalFontSize, false, true);
                    }
                    yPosition += normalFontSize * 0.5; // Space between interactions
                });

                const pdfTimestamp = new Date().toISOString().replace(/[:.]/g, '-');
                pdf.save(`Chat_Transcript_${activeMode}_${pdfTimestamp}.pdf`);
                addMessageToChat({ answer: "PDF transcript download initiated.", answer_format: 'text'}, 'ai', activeMode);

            } catch (error) {
                console.error("Error generating PDF:", error);
                addMessageToChat({ answer: "Sorry, an error occurred while generating the PDF transcript.", answer_format: 'text'}, 'ai', activeMode);
            }
        });
    }
    
    // Expose functions to global scope (via window.chatLogic)
    return {
        loadChatForMode: loadChatForModePublic,
        showMasterHistoryModal: showMasterHistoryModalPublic,
        // Any other functions main_ui.js might need to call
    };

})(); // End of IIFE