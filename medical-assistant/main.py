from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

# --- CORRECTED IMPORTS FOR SUB-APPLICATION ROUTERS ---
# These are now treated as top-level packages accessible from the project root
from .api import chat_router as main_chat_api_router # This one is a sub-package of medical_assistant

import report_analyzer_app.main_router as report_analyzer_router
import survey_research_app.main_router as survey_research_router
import advisories_app.main_router as advisories_router
# Note: To make 'import report_analyzer_app.main_router' work,
# report_analyzer_app MUST have an __init__.py file. Same for others.

app = FastAPI(
    title="AI Medical Suite - Integrated Platform",
    description="Main application integrating Chat Assistant, Symptom Analyzer SPA, Report Analyzer, Survey & Research, and Health Advisories.",
    version="2.0.3" # Incremented version
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Define Base Directories ---
main_app_module_dir = os.path.dirname(os.path.abspath(__file__)) # medical-assistant/
project_root_dir = os.path.dirname(main_app_module_dir)          # my_ai_medical_assistant/

# --- Static Files & Templates for the MAIN WRAPPER APP (QnA Chat UI) ---
main_app_static_on_disk = os.path.join(main_app_module_dir, "static")
main_app_templates_on_disk = os.path.join(main_app_module_dir, "templates")
app.mount("/static", StaticFiles(directory=main_app_static_on_disk), name="static")
templates = Jinja2Templates(directory=main_app_templates_on_disk)

# --- Symptom Analyzer SPA (React App) ---
# Path relative to where uvicorn runs (project_root_dir)
symptom_spa_dist_on_disk = os.path.join(project_root_dir, "medical-assistant", "static", "symptom_analyzer_spa")
symptom_spa_assets_on_disk = os.path.join(symptom_spa_dist_on_disk, "assets")
# ... (Static mount for symptom_spa_assets as before) ...
if os.path.exists(symptom_spa_assets_on_disk) and os.path.isdir(symptom_spa_assets_on_disk):
    app.mount("/symptom-analyzer/assets", StaticFiles(directory=symptom_spa_assets_on_disk), name="symptom_spa_assets")
else:
    print(f"WARNING: Symptom Analyzer SPA assets directory not found: {symptom_spa_assets_on_disk}")

# --- Mount Static Directories for HTML Frontends of Sub-Applications ---
# Paths are now relative to project_root_dir since sub-app folders are siblings to medical-assistant
report_app_static_on_disk = os.path.join(project_root_dir, "report_analyzer_app", "static")
if os.path.exists(report_app_static_on_disk) and os.path.isdir(report_app_static_on_disk):
    app.mount("/report-analyzer-static", StaticFiles(directory=report_app_static_on_disk), name="static_report_app")
else:
    print(f"WARNING: Report Analyzer App static directory not found: {report_app_static_on_disk}")

survey_app_static_on_disk = os.path.join(project_root_dir, "survey_research_app", "static")
if os.path.exists(survey_app_static_on_disk) and os.path.isdir(survey_app_static_on_disk):
    app.mount("/survey-research-static", StaticFiles(directory=survey_app_static_on_disk), name="static_survey_app")
else:
    print(f"WARNING: Survey & Research App static directory not found: {survey_app_static_on_disk}")

advisories_app_static_on_disk = os.path.join(project_root_dir, "advisories_app", "static")
if os.path.exists(advisories_app_static_on_disk) and os.path.isdir(advisories_app_static_on_disk):
    app.mount("/advisories-static", StaticFiles(directory=advisories_app_static_on_disk), name="static_advisories_app")
else:
    print(f"WARNING: Advisories App static directory not found: {advisories_app_static_on_disk}")

# --- Include API Routers ---
app.include_router(main_chat_api_router.router, prefix="/api/v1") # This router is inside medical_assistant package
app.include_router(report_analyzer_router.router)      # Imported as top-level
app.include_router(survey_research_router.router)   # Imported as top-level
app.include_router(advisories_router.router)        # Imported as top-level

# --- HTML Page Serving for Main Wrapper App ---
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/doctor-connect", response_class=HTMLResponse, include_in_schema=False)
async def serve_doctor_connect_page(request: Request):
    return templates.TemplateResponse("doctorconnect.html", {"request": request})

# --- HTML Page Serving for Sub-Applications ---
@app.get("/report-analyzer", response_class=FileResponse, include_in_schema=False)
@app.get("/report-analyzer/", response_class=FileResponse, include_in_schema=False)
async def serve_report_analyzer_frontend():
    file_path = os.path.join(report_app_static_on_disk, "index.html")
    if os.path.exists(file_path): return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Report Analyzer App UI not found.")

@app.get("/survey-research", response_class=FileResponse, include_in_schema=False)
@app.get("/survey-research/", response_class=FileResponse, include_in_schema=False)
async def serve_survey_research_frontend():
    file_path = os.path.join(survey_app_static_on_disk, "index.html")
    if os.path.exists(file_path): return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Survey & Research App UI not found.")

@app.get("/advisories", response_class=FileResponse, include_in_schema=False)
@app.get("/advisories/", response_class=FileResponse, include_in_schema=False)
async def serve_advisories_frontend():
    file_path = os.path.join(advisories_app_static_on_disk, "index.html")
    if os.path.exists(file_path): return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Advisories App UI not found.")

# --- Catch-all routes for the Symptom Analyzer React SPA ---
@app.get("/symptom-analyzer/{rest_of_path:path}")
async def serve_symptom_analyzer_spa_paths(request: Request, rest_of_path: str):
    spa_index_file = os.path.join(symptom_spa_dist_on_disk, "index.html")
    if os.path.exists(spa_index_file): return FileResponse(spa_index_file)
    raise HTTPException(status_code=404, detail="Symptom Analyzer resource not found.")

@app.get("/about", response_class=HTMLResponse, include_in_schema=False)
async def serve_about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/symptom-analyzer")
@app.get("/symptom-analyzer/")
async def serve_symptom_analyzer_spa_base(request: Request):
    spa_index_file = os.path.join(symptom_spa_dist_on_disk, "index.html")
    if os.path.exists(spa_index_file): return FileResponse(spa_index_file)
    raise HTTPException(status_code=404, detail="Symptom Analyzer application not found.")

@app.get("/api/v1/health", tags=["Main App Health"])
async def health_check():
    return {"status": "healthy", "application": "Main AI Medical Suite"}

# To run (from my_ai_medical_assistant/ directory):
# uvicorn medical-assistant.main:app --reload --port 8000