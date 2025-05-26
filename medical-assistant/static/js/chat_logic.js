// Ensure main_ui.js is loaded first if depending on its window variables
window.chatLogic = (() => { // IIFE to create a namespace
    const userInput = document.getElementById('userInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const chatWindow = document.getElementById('chat-window');
    const fileUploadInput = document.getElementById('fileUploadInput');
    const filePreviewArea = document.getElementById('file-preview-area');
    const filePreviewName = document.getElementById('file-preview-name');
    const removeFileBtn = document.getElementById('remove-file-btn');

    const viewHistoryBtn = document.getElementById('viewHistoryBtn');
    const historyModalBody = document.getElementById('historyModalBody');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const downloadChatPdfBtn = document.getElementById('downloadChatPdfBtn');

    let currentUploadedFile = null;
    let activeCharts = []; // To keep track of Chart.js instances

function escapeHtml(unsafe) {
    if (unsafe === null || typeof unsafe === 'undefined') return '';
    return String(unsafe)
         .replace(/&/g, "&")   // Correct: & to &
         .replace(/</g, "<")    // Correct: < to <
         .replace(/>/g, ">")    // Correct: > to >
         .replace(/"/g, "'")  // Correct: " to "
         .replace(/'/g, "'"); // Correct: ' to ' (or ')
}
    
    function renderMarkdown(markdownText) {
        if (window.marked) {
            // Configure marked to handle newlines as <br> for chat-like appearance
            // and to sanitize HTML to prevent XSS if AI includes it (though it shouldn't for MD)
            marked.setOptions({
                breaks: true,
                gfm: true,
                sanitize: true // Basic sanitization
            });
            return marked.parse(markdownText || "");
        }
        return `<p>${escapeHtml(markdownText).replace(/\n/g, '<br>')}</p>`; // Fallback
    }


    function addMessageToChat(messageData, sender) {
        const messageOuterContainer = document.createElement('div');
        messageOuterContainer.classList.add('message-container', sender === 'user' ? 'user-message-outer' : 'ai-message-outer');

        const messageDiv = document.createElement('div');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
        
        const avatar = document.createElement('div');
        avatar.classList.add('avatar', sender === 'user' ? 'user-avatar' : 'ai-avatar');
        avatar.innerHTML = `<i class="fas ${sender === 'user' ? 'fa-user' : 'fa-robot'}"></i>`;

        const messageContentDiv = document.createElement('div');
        messageContentDiv.classList.add('message-content');

        if (sender === 'ai') {
            // If AI response has a specific format like markdown
            if (messageData.answer_format === 'markdown') {
                messageContentDiv.innerHTML = renderMarkdown(messageData.answer);
            } else {
                messageContentDiv.textContent = messageData.answer || "Could not process the request.";
            }
            // Handle other structured data from AI
            if (messageData.follow_up_questions && messageData.follow_up_questions.length > 0) {
                appendFollowUpQuestions(messageContentDiv, messageData.follow_up_questions);
            }
            if (messageData.disease_identification) {
                appendSimpleInfo(messageContentDiv, "Potential Identification", messageData.disease_identification);
            }
            if (messageData.next_steps && messageData.next_steps.length > 0) {
                appendList(messageContentDiv, "Next Steps", messageData.next_steps);
            }
            if (messageData.government_schemes && messageData.government_schemes.length > 0) {
                appendSchemes(messageContentDiv, messageData.government_schemes);
            }
            if (messageData.doctor_recommendations && messageData.doctor_recommendations.length > 0) {
                appendDoctorRecommendations(messageContentDiv, messageData.doctor_recommendations);
            }
            if (messageData.graphs_data && messageData.graphs_data.length > 0) {
                messageData.graphs_data.forEach(graph => displayGraph(graph, messageOuterContainer)); // Append graph to its message
            }
             if (messageData.file_processed_with_message) {
                appendSimpleInfo(messageContentDiv, "Related File", messageData.file_processed_with_message);
            }

        } else { // User message
            messageContentDiv.textContent = messageData.text;
            if (messageData.fileName) {
                const fileInfoP = document.createElement('p');
                fileInfoP.innerHTML = `<small><i>File attached: ${escapeHtml(messageData.fileName)}</i></small>`;
                messageContentDiv.appendChild(fileInfoP);
            }
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContentDiv);
        messageOuterContainer.appendChild(messageDiv);
        chatWindow.appendChild(messageOuterContainer);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function appendFollowUpQuestions(parentDiv, questions) {
        const fupDiv = document.createElement('div');
        fupDiv.className = 'mt-2';
        fupDiv.innerHTML = `<strong>Follow-up Questions:</strong><ul>${questions.map(q => `<li>${escapeHtml(q)}</li>`).join('')}</ul>`;
        parentDiv.appendChild(fupDiv);
    }
    function appendSimpleInfo(parentDiv, title, text) {
        const infoDiv = document.createElement('div');
        infoDiv.className = 'mt-2';
        infoDiv.innerHTML = `<strong>${escapeHtml(title)}:</strong> ${renderMarkdown(text)}`;
        parentDiv.appendChild(infoDiv);
    }
    function appendList(parentDiv, title, items) {
        const listDiv = document.createElement('div');
        listDiv.className = 'mt-2';
        listDiv.innerHTML = `<strong>${escapeHtml(title)}:</strong><ul>${items.map(item => `<li>${renderMarkdown(item)}</li>`).join('')}</ul>`;
        parentDiv.appendChild(listDiv);
    }
    function appendSchemes(parentDiv, schemes) {
         const schemesDiv = document.createElement('div');
        schemesDiv.className = 'mt-2';
        let html = '<strong>Relevant Government Schemes:</strong><ul class="list-unstyled">';
        schemes.forEach(s => {
            html += `<li><strong>${escapeHtml(s.name)}</strong> ${s.region_specific ? `(${escapeHtml(s.region_specific)})` : ''}: ${renderMarkdown(s.description || '')} ${s.url ? `<a href="${s.url}" target="_blank">[Link]</a>` : ''}</li>`;
        });
        html += '</ul>';
        schemesDiv.innerHTML = html;
        parentDiv.appendChild(schemesDiv);
    }
    function appendDoctorRecommendations(parentDiv, doctors) {
        const drDiv = document.createElement('div');
        drDiv.className = 'mt-2';
        let html = '<strong>Doctor Recommendations:</strong><ul class="list-unstyled">';
        doctors.forEach(dr => {
            html += `<li>Consult a <strong>${escapeHtml(dr.specialty)}</strong>. ${dr.reason ? `Reason: ${renderMarkdown(dr.reason)}` : ''}</li>`;
        });
        html += '</ul>';
        drDiv.innerHTML = html;
        parentDiv.appendChild(drDiv);
    }


    function displayGraph(graphData, messageContainer) {
        // Destroy existing charts before creating new ones to prevent memory leaks
        activeCharts.forEach(chart => chart.destroy());
        activeCharts = [];

        const chartWrapper = document.createElement('div');
        chartWrapper.className = 'chart-container mt-2'; // Added to message

        const titleEl = document.createElement('h5');
        titleEl.textContent = graphData.title || "Chart";
        chartWrapper.appendChild(titleEl);
        
        const canvasWrapper = document.createElement('div');
        canvasWrapper.className = 'chart-canvas-wrapper';
        const canvas = document.createElement('canvas');
        canvasWrapper.appendChild(canvas);
        chartWrapper.appendChild(canvasWrapper);
        
        messageContainer.appendChild(chartWrapper); // Append chart to the specific AI message container

        try {
            const newChart = new Chart(canvas, {
                type: graphData.type.toLowerCase() || 'bar',
                data: {
                    labels: graphData.labels || [],
                    datasets: graphData.datasets || [] // Expects [{"label": "Series 1", "data": [1,2,3]}]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    },
                    plugins: {
                        title: { display: false, text: graphData.title } // Title is above canvas
                    }
                }
            });
            activeCharts.push(newChart);
        } catch (e) {
            console.error("Error creating chart:", e, "with data:", graphData);
            chartWrapper.innerHTML += "<p class='text-danger'>Error rendering chart.</p>";
        }
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
    
    // Public function to clear graphs (called on mode change)
    function clearFileOutputsPublic() {
        activeCharts.forEach(chart => chart.destroy());
        activeCharts = [];
        // Could also clear other dynamic outputs here if they are not part of messages
    }


    function addLoadingIndicator() {
        const loadingOuter = document.createElement('div');
        loadingOuter.id = 'loading-indicator-outer';
        loadingOuter.classList.add('message-container', 'ai-message-outer');
        
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('ai-message', 'loading-indicator');

        const avatar = document.createElement('div');
        avatar.classList.add('avatar', 'ai-avatar');
        avatar.innerHTML = `<i class="fas fa-robot"></i>`;

        const content = document.createElement('div');
        content.classList.add('message-content');
        content.innerHTML = `<p><i>AI is thinking... <i class="fas fa-spinner fa-spin"></i></i></p>`;
        
        loadingDiv.appendChild(avatar);
        loadingDiv.appendChild(content);
        loadingOuter.appendChild(loadingDiv);
        chatWindow.appendChild(loadingOuter);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function removeLoadingIndicator() {
        const loadingIndicator = document.getElementById('loading-indicator-outer');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }

    async function handleSendMessage() {
        const messageText = userInput.value.trim();
        const currentMode = window.getCurrentAppMode ? window.getCurrentAppMode() : 'qna';
        const userRegion = window.getUserRegion ? window.getUserRegion() : null;

        if (!messageText && !currentUploadedFile) {
            // alert('Please type a message or upload a file.'); // Or handle more gracefully
            return;
        }
        
        // Add user message to chat
        addMessageToChat({ text: messageText, fileName: currentUploadedFile ? currentUploadedFile.name : null }, 'user');
        
        userInput.value = ''; // Clear input field
        userInput.style.height = 'auto'; // Reset textarea height

        addLoadingIndicator();

        const formData = new FormData();
        if (messageText) formData.append('message', messageText);
        formData.append('mode', currentMode);
        if (userRegion && (currentMode === 'personal_symptoms' || currentMode === 'personal_report_upload')) {
            formData.append('user_region', userRegion);
        }
        if (currentUploadedFile) {
            formData.append('upload_file', currentUploadedFile, currentUploadedFile.name);
        }

        try {
            const response = await fetch('/api/v1/chat', {
                method: 'POST',
                body: formData // FormData handles multipart/form-data
            });
            
            removeLoadingIndicator();
            const data = await response.json(); // Expecting ChatMessageOutput

            if (response.ok) {
                addMessageToChat(data, 'ai'); // data is ChatMessageOutput
            } else {
                addMessageToChat({ answer: data.detail || data.error || 'An error occurred.', answer_format: 'text' }, 'ai');
            }
        } catch (error) {
            removeLoadingIndicator();
            console.error('Error sending message:', error);
            addMessageToChat({ answer: 'Could not connect to the server. Please try again later.', answer_format: 'text'}, 'ai');
        } finally {
            // Clear file after sending, regardless of success/failure
            if (currentUploadedFile) {
                currentUploadedFile = null;
                fileUploadInput.value = null; // Reset file input
                filePreviewArea.style.display = 'none';
            }
        }
    }

    sendMessageBtn.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) { // Send on Enter, new line on Shift+Enter
            e.preventDefault(); // Prevent default Enter behavior (newline)
            handleSendMessage();
        }
    });

    fileUploadInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            currentUploadedFile = e.target.files[0];
            if (currentUploadedFile.size > 10 * 1024 * 1024) { // 10MB
                alert("File is too large! Max 10MB.");
                currentUploadedFile = null;
                fileUploadInput.value = ""; // Reset
                filePreviewArea.style.display = 'none';
                return;
            }
            filePreviewName.textContent = currentUploadedFile.name;
            filePreviewArea.style.display = 'block';
        }
    });

    removeFileBtn.addEventListener('click', () => {
        currentUploadedFile = null;
        fileUploadInput.value = null; // Reset file input
        filePreviewArea.style.display = 'none';
    });

    // --- History Modal Logic ---
    async function loadHistory() {
        try {
            const response = await fetch('/api/v1/history');
            const historyData = await response.json(); // {conversation_history: [], medical_history: {}}
            
            historyModalBody.innerHTML = ''; 

            let html = '<h4>Conversation History</h4>';
            if (historyData.conversation_history && historyData.conversation_history.length > 0) {
                html += '<ul class="list-unstyled">';
                // Newest first
                historyData.conversation_history.slice().reverse().forEach(item => {
                    const userMsgDisplay = item.user_message || (item.file_processed ? `<i>File: ${escapeHtml(item.file_processed)}</i>` : '<i>No text message</i>');
                    html += `<li class="mb-2 p-2 border rounded">
                                <small><strong>${new Date(item.timestamp).toLocaleString()} - Mode: ${escapeHtml(item.mode)}</strong></small><br/>
                                <strong>You:</strong> ${userMsgDisplay}<br/>
                                <strong>AI:</strong> ${renderMarkdown(item.ai_response)}
                             </li>`;
                });
                html += '</ul>';
            } else {
                html += '<p>No conversation history found.</p>';
            }

            html += '<h4 class="mt-4">Medical Summary</h4>';
            if (historyData.medical_history && Object.keys(historyData.medical_history).length > 0) {
                html += '<dl class="row">';
                for (const key in historyData.medical_history) {
                    const title = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    let value = historyData.medical_history[key];
                    if (Array.isArray(value)) {
                        if (key === "reports_analyzed_info" && value.length > 0 && typeof value[0] === 'object') {
                             value = value.map(v => `${escapeHtml(v.name || "Report")} (${escapeHtml(v.findings_summary_placeholder || "No summary")})`).join(', ');
                        } else {
                            value = value.map(v => escapeHtml(v)).join(', ');
                        }
                    } else {
                        value = escapeHtml(value);
                    }
                    html += `<dt class="col-sm-4">${escapeHtml(title)}</dt><dd class="col-sm-8">${value || 'N/A'}</dd>`;
                }
                html += '</dl>';
            } else {
                html += '<p>No medical summary found.</p>';
            }
            historyModalBody.innerHTML = html;

        } catch (error) {
            console.error("Error loading history:", error);
            historyModalBody.innerHTML = '<p class="text-danger">Error loading history. Please try again.</p>';
        }
    }

    viewHistoryBtn.addEventListener('click', () => {
        loadHistory();
        $('#historyModal').modal('show');
    });

    clearHistoryBtn.addEventListener('click', async () => {
        if (confirm("Are you sure you want to clear ALL your history? This cannot be undone.")) {
            try {
                const response = await fetch('/api/v1/history/clear', { method: 'POST' });
                if (response.ok) {
                    addMessageToChat({ answer: "Your history has been cleared.", answer_format: 'text' }, 'ai');
                    $('#historyModal').modal('hide');
                    // Optionally, clear the current chat window too
                    // chatWindow.innerHTML = '<div class="ai-message">Hello! History cleared. How can I help you?</div>';
                } else {
                    alert("Failed to clear history. Server error.");
                }
            } catch (error) {
                console.error("Error clearing history:", error);
                alert("Error clearing history. Network issue or server down.");
            }
        }
    });

    // --- PDF Download Logic ---
    downloadChatPdfBtn.addEventListener('click', async () => {
        if (typeof window.jspdf === 'undefined' || typeof window.html2canvas === 'undefined') {
            alert("PDF generation library not loaded. Please refresh.");
            return;
        }
        const { jsPDF } = window.jspdf;
        const chatContainer = document.getElementById('chat-window');
        if (!chatContainer.hasChildNodes()) {
            alert("Chat is empty, nothing to download.");
            return;
        }

        addMessageToChat({ answer: "Generating PDF, please wait...", answer_format: 'text'}, 'ai');

        try {
            // Temporarily make chat window very tall to capture all content
            // This is a common workaround for html2canvas limitations with scrollable content.
            // It can be glitchy with very complex layouts.
            const originalHeight = chatContainer.style.height;
            const originalOverflow = chatContainer.style.overflowY;
            chatContainer.style.height = 'auto'; 
            chatContainer.style.overflowY = 'visible'; // Allow it to expand fully
            
            // Brief delay to allow DOM to re-render if height change causes reflow
            await new Promise(resolve => setTimeout(resolve, 300));


            const canvas = await html2canvas(chatContainer, {
                scale: 2, // Increase scale for better quality
                useCORS: true, // If you have external images/icons
                logging: false, // Reduce console noise
                onclone: (document) => { // Modify cloned document if needed
                    // Example: ensure dark mode styles are applied if active for capture
                    if (document.body.classList.contains('dark-mode')) {
                         document.getElementById('chat-window').style.backgroundColor = getComputedStyle(document.body).getPropertyValue('--card-bg-color');
                         // Add more specific style overrides for capture if needed
                    }
                }
            });
            
            // Restore original styles
            chatContainer.style.height = originalHeight;
            chatContainer.style.overflowY = originalOverflow;

            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF({
                orientation: 'p',
                unit: 'pt', // points
                format: 'a4'
            });

            const imgProps = pdf.getImageProperties(imgData);
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();
            
            // Calculate the height the image will take up in the PDF once scaled to fit width
            const imgHeight = (imgProps.height * pdfWidth) / imgProps.width;
            let heightLeft = imgHeight;
            let position = 15; // Top margin

            pdf.addImage(imgData, 'PNG', 15, position, pdfWidth - 30, imgHeight); // -30 for L/R margins
            heightLeft -= (pdfHeight - 30); // -30 for T/B margins

            while (heightLeft >= 0) {
                position = heightLeft - imgHeight + 15; // Adjust position for next page
                pdf.addPage();
                pdf.addImage(imgData, 'PNG', 15, position, pdfWidth - 30, imgHeight);
                heightLeft -= (pdfHeight - 30);
            }
            
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            pdf.save(`AI_Medical_Chat_${timestamp}.pdf`);
            addMessageToChat({ answer: "PDF download initiated.", answer_format: 'text'}, 'ai');

        } catch (error) {
            console.error("Error generating PDF:", error);
            addMessageToChat({ answer: "Sorry, an error occurred while generating the PDF.", answer_format: 'text'}, 'ai');
             // Restore original styles in case of error
            chatContainer.style.height = originalHeight;
            chatContainer.style.overflowY = originalOverflow;
        }
    });
    
    return { // Expose functions if needed by other scripts (e.g., main_ui.js)
        clearFileOutputs: clearFileOutputsPublic
    };

})(); // End of IIFE for chatLogic namespace