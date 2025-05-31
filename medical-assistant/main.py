from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os

from .api import chat_router
from .config import settings
# from .config import settings # Only if settings are needed at app level, e.g. for CORS origins

app = FastAPI(
    title="AI Medical Assistant",
    description="An AI-powered assistant for medical queries, symptom analysis, and report diagnostics.",
    version="0.1.0"
)

# CORS - Allow all for development, restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify ["http://localhost:8000"] if frontend is served on same
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine base directory for static and templates
# Assuming main.py is in 'medical-assistant' folder.
# If running uvicorn from project root: 'uvicorn medical-assistant.main:app'
# Then paths need to be relative to 'medical-assistant' or project root.
# For consistency when running from project root:
STATIC_DIR = os.path.join("medical-assistant", "static")
TEMPLATES_DIR = os.path.join("medical-assistant", "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(chat_router.router, prefix="/api/v1", tags=["Chat & Medical AI"])

@app.get("/")
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/doctor-connect", include_in_schema=False) # Add this new route
async def serve_doctor_connect_page(request: Request):
    return templates.TemplateResponse("doctorconnect.html", {"request": request})

# To run from my_ai_medical_assistant/ directory:
# uvicorn medical-assistant.main:app --reload --port 8000