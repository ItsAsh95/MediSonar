document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = themeToggleBtn.querySelector('i');
    const body = document.body;

    function applyTheme(theme) {
        if (theme === 'dark') {
            body.classList.add('dark-mode');
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        } else {
            body.classList.remove('dark-mode');
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
        localStorage.setItem('theme', theme);
    }

    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme) {
        applyTheme(savedTheme);
    } else if (prefersDark) {
        applyTheme('dark');
    } else {
        applyTheme('light'); // Default
    }

    themeToggleBtn.addEventListener('click', () => {
        if (body.classList.contains('dark-mode')) {
            applyTheme('light');
        } else {
            applyTheme('dark');
        }
    });

    // Sidebar mode switching
    const modeButtons = document.querySelectorAll('.mode-btn');
    const userRegionInputArea = document.getElementById('userRegionInputArea');
    const userInput = document.getElementById('userInput'); // Main chat input textarea

    let currentAppMode = 'qna'; // Default mode, exposed via window
    window.getCurrentAppMode = () => currentAppMode;

    modeButtons.forEach(button => {
        button.addEventListener('click', function() {
            modeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentAppMode = this.getAttribute('data-mode');
            window.chatLogic.clearFileOutputs(); // Clear graphs, etc. from chat_logic.js

            if (currentAppMode === 'personal_symptoms' || currentAppMode === 'personal_report_upload') {
                userRegionInputArea.style.display = 'block';
            } else {
                userRegionInputArea.style.display = 'none';
            }

            if (currentAppMode === 'personal_symptoms') {
                userInput.placeholder = "Describe your symptoms in detail...";
            } else if (currentAppMode === 'personal_report_upload') {
                userInput.placeholder = "Optionally, add comments about your lab report. Then upload the file.";
            } else { // qna
                userInput.placeholder = "Ask a medical question...";
            }
        });
    });

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto'; // Reset height
        userInput.style.height = (userInput.scrollHeight) + 'px'; // Set to scroll height
    });

    // Expose a global way to show user region input if needed by other modules
    window.showUserRegionInput = () => { userRegionInputArea.style.display = 'block'; };
    window.hideUserRegionInput = () => { userRegionInputArea.style.display = 'none'; };
    window.getUserRegion = () => document.getElementById('userRegionInput').value.trim();

});