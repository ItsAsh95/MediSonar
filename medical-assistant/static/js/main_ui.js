// medical-assistant/static/js/main_ui.js

document.addEventListener('DOMContentLoaded', () => {
    // --- THEME TOGGLE LOGIC ---
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = themeToggleBtn ? themeToggleBtn.querySelector('i') : null;
    const body = document.body;

    function applyTheme(theme) {
        if (!body || !themeIcon) return;
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
    if (savedTheme) applyTheme(savedTheme);
    else if (prefersDark) applyTheme('dark');
    else applyTheme('light');

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            body.classList.contains('dark-mode') ? applyTheme('light') : applyTheme('dark');
        });
    }

    // --- REGION SELECTOR LOGIC ---
    const countrySelect = document.getElementById('countrySelect');
    const stateSelect = document.getElementById('stateSelect');
    const regionSelectorContainer = document.getElementById('regionSelectorContainer');
    const finalUserRegionInput = document.getElementById('finalUserRegionInput');
    let countriesDataStore = [];

    async function fetchCountriesData() { /* ... same as previous version ... */ }
    function populateCountryDropdown() { /* ... same as previous version ... */ }
    function updateStateDropdown() { /* ... same as previous version ... */ }
    function updateFinalRegionInput() { /* ... same as previous version ... */ }
    
    if (countrySelect) countrySelect.addEventListener('change', () => { updateStateDropdown(); updateFinalRegionInput(); });
    if (stateSelect) stateSelect.addEventListener('change', updateFinalRegionInput);
    fetchCountriesData(); // Initialize

    window.toggleRegionSelector = function(show) { /* ... same as previous version ... */ };
    window.getSelectedRegion = function() { /* ... same as previous version ... */ };


    // --- MAIN UI MODE AND GREETING LOGIC ---
    const dynamicGreetingEl = document.getElementById('dynamicGreeting');
    const currentModeDisplayEl = document.getElementById('currentModeDisplay');
    const mainUserInput = document.getElementById('mainUserInput');
    const sidebarNavButtons = document.querySelectorAll('.sidebar-nav .nav-btn');

    // Define initial active mode. This will also be the key for history in MedicalMemory
    window.currentActiveChatMode = 'qna'; // 'qna', 'symptoms', 'report'

    const greetings = {
        qna: "Ask away! What medical questions do you have?",
        symptoms: "Let's analyze your symptoms. Please describe them and select your region below.",
        report: "Ready to analyze your report. Select your region, then type any comments and upload the file."
    };
    const placeholders = {
        qna: "Ask any medical question...",
        symptoms: "Describe your symptoms in detail (e.g., 'persistent headache for 3 days, mild fever')...",
        report: "Add any comments about your report, then upload the file..."
    };

    function updateUIForNewMode(newMode) {
        console.log("Switching UI to mode:", newMode);
        window.currentActiveChatMode = newMode;

        if (currentModeDisplayEl) currentModeDisplayEl.textContent = `Mode: ${newMode.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`;
        if (dynamicGreetingEl) dynamicGreetingEl.textContent = greetings[newMode] || "How can I assist?";
        if (mainUserInput) mainUserInput.placeholder = placeholders[newMode] || "Type your message...";

        // Toggle region selector visibility
        if (newMode === 'symptoms' || newMode === 'report') {
            if (window.toggleRegionSelector) window.toggleRegionSelector(true);
        } else {
            if (window.toggleRegionSelector) window.toggleRegionSelector(false);
        }

        // Load chat history for the new mode
        if (window.chatLogic && window.chatLogic.loadChatForMode) {
            window.chatLogic.loadChatForMode(newMode);
        }

        // Update active state for sidebar buttons
        sidebarNavButtons.forEach(btn => {
            if (btn.dataset.mainMode === newMode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
         // Auto-resize textarea for new placeholder
        if (mainUserInput) {
            mainUserInput.value = ''; // Clear input on mode switch
            mainUserInput.style.height = 'auto';
            mainUserInput.style.height = (mainUserInput.scrollHeight) + 'px';
        }
    }

    sidebarNavButtons.forEach(button => {
        button.addEventListener('click', function() {
            const mode = this.dataset.mainMode;
            if (mode.includes("placeholder")) { // For disabled/future tabs
                alert("This feature is coming soon!");
                return;
            }
            if (mode === "history_master_view") {
                if (window.chatLogic && window.chatLogic.showMasterHistoryModal) {
                    window.chatLogic.showMasterHistoryModal();
                }
            } else if (mode) {
                updateUIForNewMode(mode);
            }
        });
    });
    
    // Initialize UI for the default mode
    updateUIForNewMode(window.currentActiveChatMode);

    // Auto-resize for the main textarea
    if (mainUserInput) {
        mainUserInput.addEventListener('input', () => {
            mainUserInput.style.height = 'auto';
            mainUserInput.style.height = (Math.min(mainUserInput.scrollHeight, 150)) + 'px'; // Max height 150px
        });
    }
});