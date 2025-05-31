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
             .replace(/&/g, "&") // Corrected escape for ampersand
             .replace(/</g, "<")
             .replace(/>/g, ">")
             .replace(/"/g, "'")
             .replace(/'/g, "'");
    }

    function renderMarkdown(markdownText) {
        if (window.marked && typeof markdownText === 'string') {
            marked.setOptions({ breaks: true, gfm: true, sanitize: true }); // sanitize is important
            return marked.parse(markdownText);
        }
        // Fallback for plain text rendering with line breaks
        return `<p>${escapeHtml(markdownText || "").replace(/\n/g, '<br>')}</p>`;
    }

    // --- Helper functions for appending structured AI data to message content ---
    function appendFollowUpQuestions(parentDiv, questions) {
        if (!questions || !Array.isArray(questions) || questions.length === 0) return;
        const fupDiv = document.createElement('div');
        fupDiv.className = 'mt-2 ai-structured-info follow-up-questions'; // Added specific class
        fupDiv.innerHTML = `<strong>Follow-up Questions:</strong><ul>${questions.map(q => `<li>${escapeHtml(q)}</li>`).join('')}</ul>`;
        parentDiv.appendChild(fupDiv);
    }

    function appendSimpleInfo(parentDiv, title, text) {
        if (text === null || typeof text === 'undefined' || text === "") return;
        const infoDiv = document.createElement('div');
        infoDiv.className = 'mt-2 ai-structured-info simple-info'; // Added specific class
        infoDiv.innerHTML = `<strong>${escapeHtml(title)}:</strong> ${renderMarkdown(text)}`;
        parentDiv.appendChild(infoDiv);
    }

    function appendList(parentDiv, title, items) {
        if (!items || !Array.isArray(items) || items.length === 0) return;
        const listDiv = document.createElement('div');
        listDiv.className = 'mt-2 ai-structured-info item-list'; // Added specific class
        listDiv.innerHTML = `<strong>${escapeHtml(title)}:</strong><ul>${items.map(item => `<li>${renderMarkdown(item)}</li>`).join('')}</ul>`;
        parentDiv.appendChild(listDiv);
    }

    function appendSchemes(parentDiv, schemes) {
        if (!schemes || !Array.isArray(schemes) || schemes.length === 0) return;
        const schemesDiv = document.createElement('div');
        schemesDiv.className = 'mt-2 ai-structured-info government-schemes'; // Added specific class
        let html = '<strong>Relevant Government Schemes:</strong><ul class="list-unstyled">';
        schemes.forEach(s => {
            if (s && s.name) {
                html += `<li class="mb-1 scheme-item"><strong>${escapeHtml(s.name)}</strong> ${s.region_specific ? `(${escapeHtml(s.region_specific)})` : ''}: ${renderMarkdown(s.description || '')} ${s.url ? `<a href="${s.url}" target="_blank" rel="noopener noreferrer" class="scheme-link">[Details]</a>` : ''} ${s.source_info ? `<small class="text-muted d-block scheme-source"><em>Source: ${escapeHtml(s.source_info)}</em></small>` : ''}</li>`;
            }
        });
        html += '</ul>';
        schemesDiv.innerHTML = html;
        parentDiv.appendChild(schemesDiv);
    }

    function appendDoctorRecommendations(parentDiv, doctors) {
        if (!doctors || !Array.isArray(doctors) || doctors.length === 0) return;
        const drDiv = document.createElement('div');
        drDiv.className = 'mt-2 ai-structured-info doctor-recommendations'; // Added specific class
        let html = '<strong>Doctor Recommendations:</strong><ul class="list-unstyled">';
        doctors.forEach(dr => {
            if (dr && dr.specialty) {
                html += `<li class="mb-1 doctor-item">Consult a <strong>${escapeHtml(dr.specialty)}</strong>. ${dr.reason ? `Reason: ${renderMarkdown(dr.reason)}` : ''} ${dr.source_info ? `<small class="text-muted d-block doctor-source"><em>Source/Basis: ${escapeHtml(dr.source_info)}</em></small>` : ''}</li>`;
            }
        });
        html += '</ul>';
        drDiv.innerHTML = html;
        parentDiv.appendChild(drDiv);
    }

    // --- Chat Message Display Logic ---
    function addMessageToChat(messageData, sender, _currentModeForHistory, interactionId = null) {
        if (!activeChatWindow) { console.error("activeChatWindow element not found!"); return; }

        const messageTimestamp = messageData.timestamp || new Date().toISOString();
        const messageId = interactionId || `msg-${new Date(messageTimestamp).getTime()}-${Math.random().toString(36).substr(2, 9)}`;

        const messageOuterContainer = document.createElement('div');
        messageOuterContainer.classList.add('message-container', sender === 'user' ? 'user-message-outer' : 'ai-message-outer');
        messageOuterContainer.id = messageId;

        const messageDiv = document.createElement('div'); // This div is less styled now, avatar and content are direct children of outer.
        // messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message'); // Class not used directly on messageDiv for new structure

        const avatar = document.createElement('div');
        avatar.classList.add('avatar', sender === 'user' ? 'user-avatar' : 'ai-avatar');
        // Updated AI icon to fa-brain
        avatar.innerHTML = `<i class="fas ${sender === 'user' ? 'fa-user-alt' : 'fa-brain'}"></i>`;


        const messageContentDiv = document.createElement('div');
        messageContentDiv.classList.add('message-content');

        let textContentForCopy = "";

        if (sender === 'ai') {
            textContentForCopy = messageData.answer || "";
            if (messageData.answer_format === 'markdown' && messageData.answer) {
                messageContentDiv.innerHTML = renderMarkdown(messageData.answer);
            } else {
                messageContentDiv.textContent = messageData.answer || "Error: AI response was empty or unformatted.";
            }

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
                 fileProcessedP.innerHTML = `<small class="text-muted mt-2 d-block file-processed-info"><i>Context included file: ${escapeHtml(messageData.file_processed_with_message)}</i></small>`;
                 messageContentDiv.appendChild(fileProcessedP);
            }

            const controlsDiv = document.createElement('div');
            controlsDiv.className = 'ai-message-controls mt-2 text-right';
            const copyButton = document.createElement('button');
            copyButton.className = 'btn btn-xs copy-btn'; // Removed btn-outline-secondary for custom styling
            copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy'; // Shortened text
            copyButton.title = "Copy AI's main response text";
            copyButton.setAttribute('aria-label', "Copy AI response");
            copyButton.addEventListener('click', (e) => {
                e.stopPropagation();
                navigator.clipboard.writeText(textContentForCopy).then(() => {
                    copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    setTimeout(() => { copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy'; }, 2000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                    alert('Failed to copy text. Your browser might not support this feature or permission was denied.');
                });
            });
            controlsDiv.appendChild(copyButton);
            messageContentDiv.appendChild(controlsDiv);

        } else { // User message
            messageContentDiv.textContent = messageData.text;
            textContentForCopy = messageData.text;
            if (messageData.fileName) {
                const fileInfoP = document.createElement('p');
                fileInfoP.innerHTML = `<small class="text-muted mt-1 d-block file-attached-info"><i>File attached: ${escapeHtml(messageData.fileName)}</i></small>`;
                messageContentDiv.appendChild(fileInfoP);
            }
        }

        // New structure: avatar and messageContentDiv are direct children of messageOuterContainer
        messageOuterContainer.appendChild(avatar);
        messageOuterContainer.appendChild(messageContentDiv);
        // messageOuterContainer.appendChild(messageDiv); // Old structure if messageDiv was wrapper

        activeChatWindow.appendChild(messageOuterContainer);
        activeChatWindow.scrollTop = activeChatWindow.scrollHeight;
    }

    // --- Graph Display Logic ---
    function displayGraph(graphData, parentElementToAppendTo, messageId) {
        if (!parentElementToAppendTo) { console.error("Cannot display graph, parent element is null for message " + messageId); return; }
        if (!activeChartsDisplayed[messageId]) {
            activeChartsDisplayed[messageId] = [];
        }
        activeChartsDisplayed[messageId].forEach(chart => chart.destroy());
        activeChartsDisplayed[messageId] = [];

        const chartWrapper = document.createElement('div');
        chartWrapper.className = 'chart-container mt-3 p-2 border rounded bg-light'; // Added bg-light for better contrast

        const titleEl = document.createElement('h6');
        titleEl.className = 'text-center mb-2 chart-title'; // Added class
        titleEl.textContent = graphData.title || "Chart";
        chartWrapper.appendChild(titleEl);

        const canvasWrapper = document.createElement('div');
        canvasWrapper.className = 'chart-canvas-wrapper';
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
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true, ticks: { color: 'var(--text-color)' } }, x: { ticks: { color: 'var(--text-color)' } } }, // Themed ticks
                    plugins: { legend: { display: (graphData.datasets && graphData.datasets.length > 1), labels: { color: 'var(--text-color)' } } } // Themed legend
                }
            });
            activeChartsDisplayed[messageId].push(newChart);
        } catch (e) {
            console.error("Error creating chart:", e, "with data:", graphData);
            chartWrapper.innerHTML += "<p class='text-danger small mt-1 chart-error-message'>Error rendering chart.</p>";
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

        const avatar = document.createElement('div');
        avatar.classList.add('avatar', 'ai-avatar');
        // Updated loading icon to fa-spinner fa-spin
        avatar.innerHTML = `<i class="fas fa-spinner fa-spin"></i>`;

        const content = document.createElement('div');
        content.classList.add('message-content', 'loading-message-content'); // Added specific class
        content.innerHTML = `<p><i>AI is thinking...</i></p>`;

        loadingOuter.appendChild(avatar);
        loadingOuter.appendChild(content);
        activeChatWindow.appendChild(loadingOuter);
        activeChatWindow.scrollTop = activeChatWindow.scrollHeight;
    }

    function removeLoadingIndicator() {
        const loadingIndicator = document.getElementById('loading-indicator-outer');
        if (loadingIndicator) loadingIndicator.remove();
    }

    // --- Send Message Logic ---
    async function handleSendMessage() {
        if (!mainUserInput || !mainSendBtn) return;

        const messageText = mainUserInput.value.trim();
        const currentMode = window.currentActiveChatMode || 'qna';
        let userRegion = null;

        if (currentMode === 'symptoms' || currentMode === 'report') {
            if (window.getSelectedRegion) userRegion = window.getSelectedRegion();
        }

        if (!messageText && !currentUploadedFileMain) return;

        addMessageToChat({ text: messageText, fileName: currentUploadedFileMain ? currentUploadedFileMain.name : null }, 'user', currentMode);
        mainUserInput.value = '';
        mainUserInput.style.height = 'auto';

        addLoadingIndicator();

        const formData = new FormData();
        if (messageText) formData.append('message', messageText);
        formData.append('mode_str', currentMode);
        if (userRegion) formData.append('user_region', userRegion);
        if (currentUploadedFileMain) {
            formData.append('upload_file', currentUploadedFileMain, currentUploadedFileMain.name);
        }

        try {
            const response = await fetch('/api/v1/chat', { method: 'POST', body: formData });
            removeLoadingIndicator();
            const data = await response.json();

            if (response.ok) {
                addMessageToChat(data, 'ai', currentMode, data.id);
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
        activeChatWindow.innerHTML = '';
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

                    if (interaction.user_message || interaction.file_processed) {
                        addMessageToChat({ text: interaction.user_message, fileName: interaction.file_processed, timestamp: interaction.timestamp }, 'user', mode, interaction.id);
                    }
                    if (interaction.ai_response) {
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
        $(masterHistoryModalEl).modal('show');

        try {
            const response = await fetch('/api/v1/history/summary/all');
            if (!response.ok) throw new Error("Failed to fetch master history summary.");
            const data = await response.json();

            let html = '';
            html += '<h5>Medical Summary</h5>';
            if (data.medical_summary && Object.keys(data.medical_summary).length > 0 &&
                (data.medical_summary.symptoms_log?.length || data.medical_summary.analyzed_reports_info?.length || data.medical_summary.key_diagnoses_mentioned?.length)) {
                html += '<dl class="row medical-summary-dl">'; // Added class
                for (const key in data.medical_summary) {
                    const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    let value = data.medical_summary[key];
                    if (Array.isArray(value) && value.length > 0) {
                        if (key === "symptoms_log") {
                            value = value.map(s => `<li>${new Date(s.date).toLocaleDateString()}: ${escapeHtml(s.symptoms.join(', '))}${s.notes ? ` (${escapeHtml(s.notes)})` : ''}</li>`).join('');
                            value = `<ul class="symptoms-log-list">${value}</ul>`; // Added class
                        } else if (key === "analyzed_reports_info") {
                             value = value.map(r => `<li>${escapeHtml(r.name || "Report")} (${new Date(r.date_analyzed).toLocaleDateString()}) - ${escapeHtml(r.key_findings_summary || "Summary N/A")}</li>`).join('');
                             value = `<ul class="analyzed-reports-list">${value}</ul>`; // Added class
                        } else {
                            value = value.map(v => escapeHtml(v)).join(', ');
                        }
                    } else if (typeof value !== 'object' && value) {
                        value = escapeHtml(value);
                    } else { value = 'N/A'; }
                    if (value !== 'N/A' && (!Array.isArray(data.medical_summary[key]) || data.medical_summary[key].length > 0 ) ) {
                        html += `<dt class="col-sm-3">${escapeHtml(title)}</dt><dd class="col-sm-9">${value}</dd>`;
                    }
                }
                html += '</dl><hr class="my-4"/>'; // Increased hr margin
            } else { html += '<p>No medical summary available.</p><hr class="my-4"/>'; }

            for (const mode in data.conversation_summaries) {
                html += `<h5>${mode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} Conversations</h5>`;
                const interactions = data.conversation_summaries[mode];
                if (interactions && interactions.length > 0) {
                    html += '<ul class="list-unstyled conversation-summary-list">'; // Added class
                    interactions.slice().reverse().forEach(item => {
                        const userMsgDisplay = item.user_message || (item.file_processed ? `<i>File: ${escapeHtml(item.file_processed)}</i>` : '<i>No text message</i>');
                        const aiRespDisplay = item.ai_response ? renderMarkdown(item.ai_response.substring(0, 150) + (item.ai_response.length > 150 ? '...' : '')) : '<i>No AI response.</i>';
                        html += `<li class="mb-3 p-3 border rounded history-item">
                                   <small class="d-block text-muted mb-1"><strong>${new Date(item.timestamp).toLocaleString()}</strong></small>
                                   <div class="history-user-msg"><strong>You:</strong> ${escapeHtml(userMsgDisplay)}</div>
                                   <div class="history-ai-msg mt-1"><strong>AI:</strong> ${aiRespDisplay}</div>
                                 </li>`;
                    });
                    html += '</ul>';
                } else { html += '<p>No conversations in this mode.</p>'; }
                html += '<hr class="my-4"/>';
            }
            masterHistoryModalBody.innerHTML = html;
        } catch (e) {
            masterHistoryModalBody.innerHTML = '<p class="text-danger text-center p-3">Error loading history summary.</p>';
            console.error("Error loading master history:", e);
        }
    }

    if (clearAllDataBtn) {
        clearAllDataBtn.addEventListener('click', async () => {
            if (confirm("Are you sure you want to clear ALL your data? This includes all chat histories and your medical summary. This action cannot be undone.")) {
                try {
                    const response = await fetch('/api/v1/history/clear/all', { method: 'POST' });
                    if (response.ok) {
                        $(masterHistoryModalEl).modal('hide');
                        if (window.currentActiveChatMode && window.chatLogic.loadChatForMode) {
                            loadChatForModePublic(window.currentActiveChatMode);
                        }
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

    // PDF Download Logic
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

                const loadingMsgElement = activeChatWindow.querySelector('.message-content p:contains("Preparing transcript")');
                if (loadingMsgElement && loadingMsgElement.closest('.message-container')) {
                    loadingMsgElement.closest('.message-container').remove();
                }


                if (!modeHistory || modeHistory.length === 0) {
                    alert(`No chat history found for ${activeMode} mode to download.`);
                    return;
                }

                const pdf = new jsPDF({ orientation: 'p', unit: 'pt', format: 'a4' });
                pdf.setFont("Helvetica", "sans-serif"); // Set a base font

                const pageWidth = pdf.internal.pageSize.getWidth();
                const margin = 40;
                const maxLineWidth = pageWidth - 2 * margin;
                let yPosition = margin;
                const lineHeightFactor = 1.5;
                const smallFontSize = 9;
                const normalFontSize = 11;
                const titleFontSize = 16;

                function addWrappedText(text, fontSize, isBold = false, isItalic = false, indent = 0, color = [0,0,0]) {
                    if (yPosition > margin && !isItalic) yPosition += (fontSize * 0.4); // Space before new block, unless it's continuation like italic part

                    pdf.setFontSize(fontSize);
                    pdf.setFont(undefined, isBold ? (isItalic ? 'bolditalic' : 'bold') : (isItalic ? 'italic' : 'normal'));
                    pdf.setTextColor(color[0], color[1], color[2]);

                    const lines = pdf.splitTextToSize(text || " ", maxLineWidth - indent);
                    lines.forEach(line => {
                        if (yPosition + fontSize > pdf.internal.pageSize.getHeight() - margin) {
                            pdf.addPage();
                            yPosition = margin;
                        }
                        pdf.text(line, margin + indent, yPosition);
                        yPosition += (fontSize * lineHeightFactor);
                    });
                }

                addWrappedText(`MediSonar - Chat Transcript`, titleFontSize, true, false, 0, [41,121,255]); // Primary color title
                addWrappedText(`Mode: ${activeMode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`, normalFontSize + 1, false);
                addWrappedText(`Generated: ${new Date().toLocaleString()}`, smallFontSize, false, true, 0, [100,100,100]); // Italic, gray
                yPosition += 20;

                modeHistory.forEach(interaction => {
                    const timestamp = new Date(interaction.timestamp).toLocaleString();
                    let userMsgDisplay = interaction.user_message || "";

                    if (userMsgDisplay.trim()) {
                        addWrappedText(`You (${timestamp}):`, smallFontSize, true, false, 0, [0,123,255]); // User label in blue
                        addWrappedText(userMsgDisplay, normalFontSize);
                        if (interaction.file_processed) {
                            addWrappedText(`(File: ${interaction.file_processed})`, smallFontSize, false, true, 15, [100,100,100]); // Indented file info
                        }
                    }

                    if (interaction.ai_response) {
                        addWrappedText(`AI (${timestamp}):`, smallFontSize, true, false, 0, [50,50,50]); // AI label in dark gray
                        // For PDF, using raw answer; Markdown to PDF is complex with jsPDF alone.
                        addWrappedText(interaction.ai_response, normalFontSize);
                    }
                    yPosition += normalFontSize * 0.6; // Space between interactions
                });

                const pdfTimestamp = new Date().toISOString().replace(/[:.]/g, '-');
                pdf.save(`MediSonar_Transcript_${activeMode}_${pdfTimestamp}.pdf`);
                addMessageToChat({ answer: "PDF transcript download initiated.", answer_format: 'text'}, 'ai', activeMode);

            } catch (error) {
                console.error("Error generating PDF:", error);
                addMessageToChat({ answer: "Sorry, an error occurred while generating the PDF transcript.", answer_format: 'text'}, 'ai', activeMode);
            }
        });
    }

    return {
        loadChatForMode: loadChatForModePublic,
        showMasterHistoryModal: showMasterHistoryModalPublic,
    };

})();