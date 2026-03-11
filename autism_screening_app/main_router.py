# autism_screening_app/main_router.py
# FastAPI router for the Autism Behavioral Screening module
# Follows the same pattern as advisories_app, disease_outbreak_app, etc.

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from .models import (
    StartSessionRequest, FrameData, AnalyzeSessionRequest,
    SessionResponse, FrameResult, SessionAnalysis, ScreeningReport,
    BehavioralFeatures, TestType, ScreeningLevel
)
from .services import (
    create_session,
    get_session,
    process_frame,
    analyze_session,
    generate_report
)

logger = logging.getLogger(__name__)

# --- APIRouter Instance ---
router = APIRouter(
    prefix="/autism-screening",
    tags=["Autism Behavioral Screening Application"]
)

# --- Path to this app's static files (frontend) ---
APP_BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_BASE_DIR / "static"


# ===========================================================================
# API ENDPOINTS
# ===========================================================================

@router.post("/api/start-session", response_model=SessionResponse)
async def start_session_endpoint(request: StartSessionRequest = StartSessionRequest()):
    """
    Start a new behavioral screening session.
    Returns a unique session ID to use for subsequent requests.
    """
    try:
        session_id = create_session(request.participant_id)
        logger.info(f"AUTISM_SCREENING: Session started: {session_id}")
        return SessionResponse(session_id=session_id, message="Session started successfully")
    except Exception as e:
        logger.error(f"AUTISM_SCREENING: Error starting session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/api/process-frame", response_model=FrameResult)
async def process_frame_endpoint(frame_data: FrameData):
    """
    Process a single webcam frame during a behavioral test.
    Analyzes the frame based on the active test type (eye_gaze, facial_expression,
    head_movement, reaction_stimulus).
    """
    session = get_session(frame_data.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found. Please start a new session.")

    try:
        result = process_frame(
            session_id=frame_data.session_id,
            frame_base64=frame_data.frame_base64,
            test_type=frame_data.test_type.value,
            timestamp=frame_data.timestamp,
            stimulus_position=frame_data.stimulus_position,
            target_emotion=frame_data.target_emotion
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return FrameResult(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AUTISM_SCREENING: Error processing frame: {e}")
        raise HTTPException(status_code=500, detail=f"Frame processing failed: {str(e)}")


@router.post("/api/analyze-session", response_model=SessionAnalysis)
async def analyze_session_endpoint(request: AnalyzeSessionRequest):
    """
    Analyze all collected behavioral data for a session.
    Extracts features and runs the ML screening model.
    Returns behavioral features, screening level, and confidence score.
    """
    session = get_session(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        analysis = analyze_session(request.session_id)
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])

        return SessionAnalysis(
            session_id=analysis["session_id"],
            features=BehavioralFeatures(**analysis["features"]),
            screening_level=ScreeningLevel(analysis["screening_level"]),
            screening_score=analysis["screening_score"],
            confidence=analysis["confidence"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AUTISM_SCREENING: Error analyzing session: {e}")
        raise HTTPException(status_code=500, detail=f"Session analysis failed: {str(e)}")


@router.get("/api/report/{session_id}", response_model=ScreeningReport)
async def get_report_endpoint(session_id: str):
    """
    Generate and return the full screening report for a session.
    Includes visualization data for charts: emotion distribution,
    reaction times, head movement, gaze heatmap, and final screening score.
    """
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        report = generate_report(session_id)
        if "error" in report:
            raise HTTPException(status_code=500, detail=report["error"])

        # Build response model from report dict
        return ScreeningReport(
            session_id=report["session_id"],
            analysis=SessionAnalysis(
                session_id=report["analysis"]["session_id"],
                features=BehavioralFeatures(**report["analysis"]["features"]),
                screening_level=ScreeningLevel(report["analysis"]["screening_level"]),
                screening_score=report["analysis"]["screening_score"],
                confidence=report["analysis"]["confidence"]
            ),
            emotion_distribution=report.get("emotion_distribution", []),
            reaction_times=report.get("reaction_times", []),
            head_movement_data=report.get("head_movement_data", []),
            gaze_heatmap_data=report.get("gaze_heatmap_data", []),
            test_summary=report.get("test_summary", {}),
            timestamp=report.get("timestamp", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AUTISM_SCREENING: Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


# ===========================================================================
# SERVE FRONTEND
# ===========================================================================

@router.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_autism_screening_ui():
    """Serve the autism screening frontend HTML page."""
    index_html_path = STATIC_DIR / "index.html"
    if not index_html_path.exists():
        raise HTTPException(status_code=404, detail="Autism Screening App UI (index.html) not found.")
    return FileResponse(index_html_path)
