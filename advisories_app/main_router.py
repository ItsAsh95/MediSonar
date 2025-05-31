# medical-assistant/advisories_app/main_router.py
import os
import httpx # Changed from requests to align with other async usage
import logging
import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv # For loading root .env
from pathlib import Path

# --- Load .env from the project root ---
# Assuming this file is .../medical-assistant/advisories_app/main_router.py
# Go up three levels for my_ai_medical_assistant/
PROJECT_ROOT_FOR_ENV = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT_FOR_ENV / '.env'


# Get config values directly
PERPLEXITY_API_KEY_ADVISORIES = os.getenv('PERPLEXITY_API_KEY')
MODEL_FOR_ADVISORIES_ROUTER = os.getenv('ADVISORY_APP_MODEL_NAME', "sonar-pro") # Default
API_BASE_URL_ADVISORIES = os.getenv('PERPLEXITY_API_BASE_URL', "https://api.perplexity.ai/chat/completions")

if not PERPLEXITY_API_KEY_ADVISORIES:
    print("ADVISORIES_ROUTER: CRITICAL - PERPLEXITY_API_KEY could not be loaded.")

logger = logging.getLogger(__name__) # Standard logging

# --- Pydantic Models (defined inline as in original app.py) ---
class AdvisoryRequest(BaseModel):
    location: str

class AdvisoryResponse(BaseModel):
    advisories: str

class ErrorResponse(BaseModel):
    error: str

# --- APIRouter Instance ---
router = APIRouter(
    prefix="/advisories-app",
    tags=["Health Advisories Application"]
)

# --- Path to this app's static files (frontend) ---
APP_BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_BASE_DIR / "static" # Assumes frontend files are in advisories_app/static/

# --- API Endpoint ---
@router.post("/api/advisories", response_model=AdvisoryResponse, responses={
    400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}, 503: {"model": ErrorResponse}
})
async def get_advisories_endpoint(payload: AdvisoryRequest): # Renamed from original get_advisories
    if not PERPLEXITY_API_KEY_ADVISORIES: # Check again inside endpoint
        logger.error("ADVISORIES_ROUTER: Perplexity API key not configured at request time.")
        raise HTTPException(status_code=500, detail="API key for advisory service not configured.")

    if not payload.location:
        raise HTTPException(status_code=400, detail="Location is required")

    try:
        state, country = map(str.strip, payload.location.split(','))
    except ValueError:
        raise HTTPException(status_code=400, detail="Location format should be 'State, Country'")

    prompt_text = f"""
    You are a specialized AI assistant tasked with finding official public health advisories.
    Your goal is to return the top 5 most relevant and current official medical advisories issued by government or public health authorities in the last 30 days for the location: {state}, {country}.
    These advisories should be related to public health, disease outbreaks, or specific health warnings for that region.
    Ensure advisories meet these criteria:
    1. Issued by governmental or official public health bodies.
    2. Dated or updated within the last 30 days from today.
    3. Presented as clear, summarized bullet points.
    4. For each advisory: Date of issue (or last update), Issuing Agency, A concise summary.
    5. Avoid duplication.
    6. Focus strictly on official advisories.
    If no official advisories are found, explicitly state:
    "No relevant official medical advisories were found for {state}, {country} in the last 30 days."
    Present findings as a numbered list. No introductory/concluding remarks beyond the list or "no advisories" statement.
    """

    perplexity_payload = {
        "model": MODEL_FOR_ADVISORIES_ROUTER,
        "messages": [
            {"role": "system", "content": "You are an expert assistant in public health advisories."},
            {"role": "user", "content": prompt_text}
        ],
        "max_tokens": 1000,
        "temperature": 0.2
    }
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY_ADVISORIES}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(API_BASE_URL_ADVISORIES, json=perplexity_payload, headers=headers)
            response.raise_for_status() 
        
        api_response_data = response.json()
        if api_response_data.get("choices") and len(api_response_data["choices"]) > 0:
            advisory_text = api_response_data["choices"][0]["message"]["content"].strip()
            return AdvisoryResponse(advisories=advisory_text)
        else:
            logger.error(f"ADVISORIES_ROUTER: Unexpected Perplexity API response structure: {api_response_data}")
            error_message = api_response_data.get("error", {}).get("message", "Unknown error structure from AI API")
            raise HTTPException(status_code=503, detail=f"Could not retrieve advisories. API response: {error_message}")

    except httpx.HTTPStatusError as e:
        logger.error(f"ADVISORIES_ROUTER: HTTP error calling Perplexity: {e.response.status_code} - {e.response.text[:200]}")
        # Try to parse error from Perplexity if available
        detail = f"Error from Perplexity API: Status {e.response.status_code}"
        try: detail_json = e.response.json(); detail = detail_json.get("error",{}).get("message", detail)
        except: pass
        raise HTTPException(status_code=e.response.status_code, detail=detail) # Use actual status code from Perplexity
    except httpx.RequestError as e:
        logger.error(f"ADVISORIES_ROUTER: Request error calling Perplexity: {e}")
        raise HTTPException(status_code=503, detail=f"Error communicating with Perplexity API: {str(e)}")
    except Exception as e_unexp:
        logger.error(f"ADVISORIES_ROUTER: An unexpected error occurred: {e_unexp}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching advisories.")


# --- Serve this sub-app's HTML frontend ---
@router.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_advisories_ui_root_endpoint(): # Renamed for clarity
    index_html_path = STATIC_DIR / "index.html"
    if not index_html_path.exists():
        raise HTTPException(status_code=404, detail="Advisories App UI (index.html) not found.")
    return FileResponse(index_html_path)