from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json

from .api import chat_router
from .config import settings
# from .config import settings # Only if settings are needed at app level, e.g. for CORS origins

app = FastAPI(
    title="MediConnect",
    description="An AI-powered assistant for medical queries, symptom analysis, and report diagnostics.",
    version="0.1.0"
)

# CORS - Allow all for development, restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Serve the main static files (CSS, JS for your main app)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Serve React Symptom Analyzer SPA ---
# 1. Mount the static assets for the SPA
SYMPTOM_ANALYZER_SPA_DIR = os.path.join(STATIC_DIR, "symptom_analyzer_spa")
app.mount("/symptom-analyzer/assets", StaticFiles(directory=os.path.join(SYMPTOM_ANALYZER_SPA_DIR, "assets")), name="symptom_spa_assets")

# 2. Catch-all route for the SPA - must be defined AFTER specific API routes
#    and AFTER the static mount for its assets.
@app.get("/symptom-analyzer/{rest_of_path:path}")
async def serve_symptom_analyzer_spa_paths(request: Request, rest_of_path: str):
    spa_index_file = os.path.join(SYMPTOM_ANALYZER_SPA_DIR, "index.html")
    if os.path.exists(spa_index_file):
        return FileResponse(spa_index_file)
    raise HTTPException(status_code=404, detail="Symptom Analyzer SPA not found.")

@app.get("/symptom-analyzer") # Route for the base SPA path
async def serve_symptom_analyzer_spa_base(request: Request):
    spa_index_file = os.path.join(SYMPTOM_ANALYZER_SPA_DIR, "index.html")
    if os.path.exists(spa_index_file):
        return FileResponse(spa_index_file)
    raise HTTPException(status_code=404, detail="Symptom Analyzer SPA not found.")

# --- Your existing API router and main app routes ---
from .api import chat_router # Make sure this import is correct
app.include_router(chat_router.router, prefix="/api/v1") # API routes first

@app.get("/", include_in_schema=False)
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/doctor-connect", include_in_schema=False)
async def serve_doctor_connect_page(request: Request):
    return templates.TemplateResponse("doctorconnect.html", {"request": request})

# Health check endpoint (good for testing if API is up)
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


# Startup event to clear history files if you want a clean slate on every server boot
# If you want history to persist across server restarts, comment out/remove this.
# @app.on_event("startup")
# async def startup_event_clear_history():
#     print("INFO: Application startup. Clearing persistent history files for a fresh session.")
#     # Initialize memory_handler to access file paths and user_id
#     temp_memory_handler = MedicalMemory() # Uses class defaults for paths
#     user_id_for_init = temp_memory_handler.user_id

#     default_conv_structure = {user_id_for_init: {"qna": [], "symptoms": [], "report": []}}
#     try:
#         with open(CONVERSATIONS_FILE, 'w') as f:
#             json.dump(default_conv_structure, f, indent=4)
#         print(f"INFO: Cleared and re-initialized {CONVERSATIONS_FILE}")
#     except Exception as e:
#         print(f"ERROR: Could not clear/re-initialize {CONVERSATIONS_FILE}: {e}")
    
#     default_med_summary = {
#         user_id_for_init: {
#             "symptoms_log": [], "analyzed_reports_info": [], "key_diagnoses_mentioned": [],
#             "allergies": [], "medications_log": []
#         }
#     }
#     try:
#         with open(MEDICAL_SUMMARY_FILE, 'w') as f:
#             json.dump(default_med_summary, f, indent=4)
#         print(f"INFO: Cleared and re-initialized {MEDICAL_SUMMARY_FILE}")
#     except Exception as e:
#         print(f"ERROR: Could not clear/re-initialize {MEDICAL_SUMMARY_FILE}: {e}")