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

The project is architected as a **unified, multi-component FastAPI application**. The central `medical-assistant` application serves as the primary orchestrator, managing the core chat interface while seamlessly integrating and serving several specialized sub-applications. All components are designed to run under a single server process for a cohesive user experience.

*   `MediSonar/` **(Project Root)**
    *   `.env`: **(CRITICAL - Must be created manually)** Stores all API keys (`PERPLEXITY_API_KEY`) and other environment-specific configurations for the entire suite of applications.
    *   `.github/`: Contains community health files for the repository like pull request templates and codes of conduct.
    *   `LICENSE.txt` & `README.md`: Project license and this informational document.
    *   `medical-assistant/`: The core FastAPI application that acts as the central orchestrator and serves the main Q&A chat UI.
        *   `main.py`: The main FastAPI app instance that mounts all static directories and includes all API routers from itself and the sub-applications. **This is the single entry point to run the entire project.**
        *   `config.py`: Loads the root `.env` file and provides a shared `settings` object for all parts of the application.
        *   `requirements.txt`: A consolidated list of all Python dependencies for the entire project.
        *   `api/`: Contains the `chat_router.py` and Pydantic `models.py` for the main chat assistant's functionalities (Q&A).
        *   `utils/`: Contains core utilities for the main chat assistant, including `ai_handler.py` (for Perplexity API interactions) and `medical_memory.py` (for persistent history management).
        *   `data/`: Stores persistent JSON files for the main chat assistant's conversation history and medical summary.
        *   `templates/`: Jinja2 HTML templates for the main wrapper UI (`index.html`) and the "Doctor Connect" page.
        *   `static/`: Contains static assets (CSS, JS, images) for the main wrapper UI and, importantly, the pre-built static output of the React Symptom Analyzer SPA inside `symptom_analyzer_spa/`.
    *   `Symptom/`: **(Source Code - Not Deployed Directly)** The source code for the standalone React/Vite/Tailwind-based Symptom Analyzer SPA. The `npm run build` command generates the deployable static files inside `medical-assistant/static/symptom_analyzer_spa/`.
    *   `report_analyzer_app/`: The complete "Medical Report Analyzer" sub-application module.
        *   `main_router.py`: Contains the FastAPI `APIRouter` with all API endpoints and HTML-serving routes for this specific app.
        *   Contains its own `static/` directory for its unique HTML, CSS, and JS frontend.
        *   Contains its own `uploads_report_app/` and `results_report_app/` for file management, keeping it self-contained within the main project.
    *   `survey_research_app/`: The complete "Survey & Research" sub-application module.
        *   `main_router.py`: The `APIRouter` for its API and frontend-serving logic.
        *   `schemas.py` & `services.py`: Contains its specific Pydantic models and business logic for generating in-depth health reports.
        *   `static/`: Contains the HTML, CSS, and JS frontend for this tool.
    *   `advisories_app/`: The complete "Advisories in Effect" sub-application module.
        *   `main_router.py`: The `APIRouter` for its API and frontend-serving logic.
        *   `static/`: Contains the simple HTML, CSS, and JS frontend for fetching and displaying advisories.

## Setup and Running Locally

1.  **Clone the Repository (if applicable):**
    ```bash
    git clone https://github.com/ItsAsh95/MediSonar.git
    cd MediSonar
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
    *   In the project root directory (`MediSonar/`), create a file named `.env`.
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
    *   Copy the entire contents of the generated `Symptom/dist/` folder into `MediSonar/medical-assistant/static/symptom_analyzer_spa/`.

6.  **Run the FastAPI Application:**
    *   Ensure you are in the project root directory (`MediSonar/`).
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

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.

You may freely use, modify, and share this project for personal or non-commercial purposes, provided that proper attribution is given to the author. Commercial use requires prior written consent.

Full license text is available in the [LICENSE](./LICENSE.txt) file.

This project also makes use of third-party services, including the Perplexity SONAR API. Use of these services is subject to their own terms of service as detailed in the [Third-Party Notices](.github/THIRD_PARTY_NOTICE.md).

