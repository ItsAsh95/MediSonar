# MediSonar - AI Medical Suite

**MediSonar** is an intelligent, AI-powered health platform designed to be your comprehensive solution for navigating medical information and healthcare access. It integrates multiple specialized AI functionalities to provide users with in-depth medical Q&A, personal symptom analysis insights (via a dedicated SPA), detailed analysis of uploaded medical reports (via a dedicated app), regional health research capabilities, and access to current health advisories.

## Core Features

*   **AI Medical Q&A ("Ask Away"):** Get detailed, easy-to-understand answers to your medical questions. Powered by Perplexity's `sonar-pro` model, responses are structured with Markdown, aim for natural source citation, and suggest related topics for further exploration. Includes file upload capability to ask questions about a document.
*   **Symptom Analyzer (SPA):** A dedicated Single Page Application (built with React/Vite) for a focused symptom analysis experience. Users input symptoms, duration, and severity to receive AI-generated insights into potential conditions, general advice, and recommendations. This module uses Perplexity's `sonar-reasoning-pro` model via a FastAPI backend endpoint.
*   **Report Analysis (Dedicated App):** An integrated application for uploading medical reports (PDF, images, text). It uses AI (configurable, e.g., `sonar-pro` via OpenAI-compatible endpoint) to extract parameters, identify abnormalities, and provide a structured summary. Accessed via its own interface.
*   **Survey & Research (Dedicated App):** Powered by Perplexity's `sonar-deep-research`, this tool generates extensive reports on regional health landscapes, disease prevalence, healthcare systems, and government schemes based on user-defined areas and topics. Includes chart generation and follow-up Q&A on the generated report. Accessed via its own interface.
*   **Advisories in Effect (Dedicated App):** Fetches and displays the latest official public health advisories for a specified location using `sonar-pro`. Accessed via its own interface.
*   **Doctor Connect:** A module to find and get information about healthcare professionals (currently uses placeholder data, designed for future API/Database integration).
*   **Persistent User History (Main App):** The main chat assistant (Q&A, Symptoms initiated from main UI) maintains a history of interactions, saved locally in JSON files, to provide context for future AI responses. Each chat mode (Q&A, Symptoms) has its own distinct history thread within the main app. Sub-applications like the Report Analyzer manage their own history separately.
*   **Modern UI/UX:** Features a clean, responsive interface with light/dark mode support, clear presentation of information, and user-friendly controls.
*   **Downloadable Chat Transcripts:** Q&A/Symptom chat sessions from the main app can be downloaded as a PDF.

## Technology Stack

*   **Backend (Main App & Sub-App APIs):** Python, FastAPI, Uvicorn
*   **AI Models:** Perplexity AI (sonar-pro, sonar-reasoning-pro, sonar-deep-research) via API.
*   **Frontend (Main App Q&A UI & Static Sub-Apps):** HTML, CSS, JavaScript, Bootstrap (for modal), Chart.js, Marked.js, jsPDF, html2canvas.
*   **Frontend (Symptom Analyzer SPA):** React, Vite, TypeScript, Tailwind CSS, Axios, React Hook Form, Framer Motion.
*   **Data Storage (Main App History):** Local JSON files.
*   **File Processing (Report Analyzer):** Pillow, PyPDF2.

## Project Structure

The project is organized into a main FastAPI application (`medical-assistant`) which serves the primary chat interface and orchestrates access to other specialized applications/modules:

*   `my_ai_medical_assistant/`
    *   `.env`: **(CRITICAL)** Stores API keys and model configurations. Must be created manually.
    *   `medical-assistant/`: Core files for the main FastAPI application and integrated sub-app routers.
        *   `main.py`: Main FastAPI app instance, mounts static files and includes all routers.
        *   `config.py`: Loads `.env` and provides settings.
        *   `api/`: Router and models for the main chat assistant's Q&A/Symptom modes.
        *   `utils/`: AI handler and memory management for the main chat assistant.
        *   `report_analyzer_app/`: Contains `main_router.py` (with all its Python logic) and `static/` (frontend HTML, CSS, JS) for the Report Analyzer.
        *   `survey_research_app/`: Contains `main_router.py`, `schemas.py`, `services.py`, and `static/` for the Survey & Research tool.
        *   `advisories_app/`: Contains `main_router.py` (with all its Python logic) and `static/` for the Advisories tool.
        *   `static/`: Assets for the main Q&A UI, and the build output for the Symptom Analyzer React SPA (`symptom_analyzer_spa/`).
        *   `templates/`: Jinja2 HTML templates for the main Q&A UI (`index.html`), Doctor Connect (`doctorconnect.html`), and About page (`about.html`).
    *   *(Original sub-app development folders like `REPORT/`, `PERPLEXITY_DEEP_SEARCH/`, `ADVISORY/`, `Symptom/` are separate from this integrated deployment structure).*

## Setup and Running Locally

1.  **Clone the Repository (if applicable):**
    ```bash
    git clone <your-repo-url>
    cd my_ai_medical_assistant
    ```

2.  **Create and Activate a Python Virtual Environment:**
    (Python 3.10+ recommended)
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate    # On Windows
    ```

3.  **Install Python Dependencies:**
    All Python dependencies for the main app and all integrated sub-apps are listed in `medical-assistant/requirements.txt`.
    ```bash
    pip install -r medical-assistant/requirements.txt
    ```

4.  **Create and Configure `.env` File:**
    *   In the project root directory (`my_ai_medical_assistant/`), create a file named `.env`.
    *   Add your API keys and any model name overrides:
        ```env
        PERPLEXITY_API_KEY=your_actual_perplexity_api_key_here
        APP_SECRET_KEY=generate_a_very_strong_random_secret_key_here

        # Optional: Override default model names (see medical-assistant/config.py for defaults)
        # PERPLEXITY_QNA_MODEL="sonar-pro"
        # PERPLEXITY_SYMPTOM_MODEL="sonar-reasoning-pro"
        # REPORT_APP_AI_MODEL="sonar-pro" 
        # SURVEY_APP_MODEL_NAME="sonar-deep-research"
        # ADVISORY_APP_MODEL_NAME="sonar-pro"
        ```
    *   Generate `APP_SECRET_KEY` with: `python -c "import secrets; print(secrets.token_hex(32))"`

5.  **Build the Symptom Analyzer React SPA (if using it and not just the built files):**
    *   Navigate to your original `Symptom/` directory.
    *   Install Node.js dependencies: `npm install` (or `yarn install`).
    *   Create a `.env` or `.env.local` file inside `Symptom/` with:
        `VITE_API_URL=http://localhost:8000/api/v1`
    *   Build the SPA: `npm run build` (or `yarn build`).
    *   Copy the entire contents of the generated `Symptom/dist/` folder into `my_ai_medical_assistant/medical-assistant/static/symptom_analyzer_spa/`.

6.  **Run the FastAPI Application:**
    *   Ensure you are in the project root directory (`my_ai_medical_assistant/`).
    *   Execute:
        ```bash
        uvicorn medical-assistant.main:app --reload --port 8000
        ```

7.  **Access the Application:**
    *   Main Assistant UI: `http://localhost:8000/`
    *   Symptom Analyzer SPA: `http://localhost:8000/symptom-analyzer/`
    *   Report Analysis App: `http://localhost:8000/report-analyzer/`
    *   Doctor Connect: `http://localhost:8000/doctor-connect`
    *   Survey & Research App: `http://localhost:8000/survey-research/`
    *   Advisories App: `http://localhost:8000/advisories/`
    *   About MediSonar: `http://localhost:8000/about`

## Further Development

*   Refine AI prompts for optimal accuracy across all modules.
*   Enhance error handling and user feedback mechanisms.
*   Develop user authentication for personalization and secure data.
*   Expand data visualization capabilities.
