// medical-assistant/advisories_app/static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    const locationInput = document.getElementById('locationInput');
    const getAdvisoriesBtn = document.getElementById('getAdvisoriesBtn');
    const advisoriesOutput = document.getElementById('advisoriesOutput');
    const resultsArea = document.getElementById('resultsArea');
    const loadingIndicator = document.getElementById('loading');
    const errorArea = document.getElementById('errorArea');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const htmlElement = document.documentElement; // Target <html> for data-theme
    const themeIcon = themeToggleBtn ? themeToggleBtn.querySelector('i') : null;
    const THEME_KEY = 'themePreferenceAdvisoryApp'; // Use app-specific key

    function applyTheme(theme) {
        if (theme === 'dark') {
            htmlElement.setAttribute('data-theme', 'dark');
            if (themeIcon) { themeIcon.classList.remove('fa-sun'); themeIcon.classList.add('fa-moon'); }
        } else {
            htmlElement.removeAttribute('data-theme');
            if (themeIcon) { themeIcon.classList.remove('fa-moon'); themeIcon.classList.add('fa-sun'); }
        }
    }

    function saveThemePreference(theme) { localStorage.setItem(THEME_KEY, theme); }

    function loadThemePreference() {
        const savedTheme = localStorage.getItem(THEME_KEY);
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (savedTheme) return savedTheme;
        if (prefersDarkScheme) return 'dark';
        return 'light';
    }

    if (themeToggleBtn) {
        const initialTheme = loadThemePreference();
        applyTheme(initialTheme);
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.hasAttribute('data-theme') ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            saveThemePreference(newTheme);
        });
    }
    
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
        if (!localStorage.getItem(THEME_KEY)) { // Only if no user preference set
            applyTheme(event.matches ? 'dark' : 'light');
        }
    });

    if(locationInput) locationInput.value = "California, United States"; // Default example
    if(resultsArea) resultsArea.classList.add('hidden');

    async function fetchAdvisories() {
        if (!locationInput || !getAdvisoriesBtn || !advisoriesOutput || !resultsArea || !loadingIndicator || !errorArea) {
            console.error("Advisory JS: One or more DOM elements not found.");
            return;
        }
        const location = locationInput.value.trim();
        if (!location) { displayError("Please enter a location (e.g., State, Country)."); return; }
        if (!location.includes(',')) { displayError("Please use the format 'State, Country'."); return; }

        loadingIndicator.classList.remove('hidden');
        resultsArea.classList.add('hidden');
        advisoriesOutput.textContent = '';
        errorArea.classList.add('hidden');
        getAdvisoriesBtn.disabled = true;

        try {
            // CORRECTED API URL for integrated app
            const response = await fetch('/advisories-app/api/advisories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ location: location }),
            });

            loadingIndicator.classList.add('hidden');

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: `HTTP error! Status: ${response.status}` }));
                throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
            }
            const data = await response.json();
            console.log("Advisories API Response Data:", data);

            if (data.advisories && data.advisories.trim() !== "") {
                advisoriesOutput.textContent = data.advisories;
                resultsArea.classList.remove('hidden');
            } else {
                advisoriesOutput.textContent = `No relevant official medical advisories were found for "${location}" in the last 30 days, or the AI response was empty.`;
                resultsArea.classList.remove('hidden');
            }
        } catch (error) {
            loadingIndicator.classList.add('hidden');
            console.error('Error fetching advisories:', error);
            displayError(`Failed to fetch advisories: ${error.message}`);
        } finally {
            if(getAdvisoriesBtn) getAdvisoriesBtn.disabled = false;
        }
    }

    function displayError(message) {
        if(errorArea && resultsArea) {
            errorArea.textContent = message;
            errorArea.classList.remove('hidden');
            resultsArea.classList.add('hidden');
        }
    }
    if(getAdvisoriesBtn) getAdvisoriesBtn.addEventListener('click', fetchAdvisories);
    if(locationInput) locationInput.addEventListener('keypress', (event) => { if (event.key === 'Enter') fetchAdvisories(); });
    
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) currentYearSpan.textContent = new Date().getFullYear();
});