# autism_screening_app/models.py
# Pydantic models for request/response schemas
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class TestType(str, Enum):
    """Types of behavioral tests available."""
    EYE_GAZE = "eye_gaze"
    FACIAL_EXPRESSION = "facial_expression"
    HEAD_MOVEMENT = "head_movement"
    REACTION_STIMULUS = "reaction_stimulus"


class ScreeningLevel(str, Enum):
    """Screening result classification levels."""
    LOW = "Low likelihood"
    MODERATE = "Moderate likelihood"
    HIGH = "High likelihood"


# --- Request Models ---

class StartSessionRequest(BaseModel):
    """Request to start a new screening session."""
    participant_id: Optional[str] = Field(None, description="Optional participant identifier")


class FrameData(BaseModel):
    """A single webcam frame sent for processing."""
    session_id: str = Field(..., description="Active session identifier")
    frame_base64: str = Field(..., description="Base64-encoded image frame from webcam")
    test_type: TestType = Field(..., description="Which behavioral test is active")
    timestamp: float = Field(..., description="Client-side timestamp in ms")
    stimulus_position: Optional[Dict[str, float]] = Field(None, description="Position of on-screen stimulus (x, y) for gaze tracking")
    target_emotion: Optional[str] = Field(None, description="Target emotion for expression test")


class AnalyzeSessionRequest(BaseModel):
    """Request to analyze a completed session."""
    session_id: str = Field(..., description="Session to analyze")


# --- Response Models ---

class SessionResponse(BaseModel):
    """Response when a session is started."""
    session_id: str
    message: str = "Session started successfully"


class FrameResult(BaseModel):
    """Results from processing a single frame."""
    session_id: str
    test_type: TestType
    frame_index: int
    face_detected: bool = False
    # Eye gaze data
    gaze_x: Optional[float] = None
    gaze_y: Optional[float] = None
    gaze_fixation: Optional[bool] = None
    blink_detected: Optional[bool] = None
    # Facial expression data
    detected_emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    expression_match: Optional[bool] = None
    # Head movement data
    head_pitch: Optional[float] = None
    head_yaw: Optional[float] = None
    head_roll: Optional[float] = None
    repetitive_motion: Optional[bool] = None
    # Reaction data
    reaction_time_ms: Optional[float] = None
    gaze_shift_detected: Optional[bool] = None
    engagement_level: Optional[float] = None
    message: str = ""


class BehavioralFeatures(BaseModel):
    """Extracted behavioral features from a session."""
    blink_rate: float = Field(0.0, description="Blinks per minute")
    gaze_fixation_time: float = Field(0.0, description="Average fixation duration in seconds")
    emotion_variability: float = Field(0.0, description="Standard deviation of emotion scores")
    head_motion_variance: float = Field(0.0, description="Variance of head movement angles")
    reaction_time: float = Field(0.0, description="Average reaction time in ms")
    engagement_score: float = Field(0.0, description="Overall engagement level 0-1")


class SessionAnalysis(BaseModel):
    """Full analysis of a screening session."""
    session_id: str
    features: BehavioralFeatures
    screening_level: ScreeningLevel
    screening_score: float = Field(..., description="Numeric score 0-100")
    confidence: float = Field(..., description="Model confidence 0-1")
    disclaimer: str = "This tool is not a medical diagnostic system. It provides behavioral screening indicators only."


class ChartDataPoint(BaseModel):
    """A single data point for chart visualization."""
    label: str
    value: float


class ScreeningReport(BaseModel):
    """Complete screening report with visualization data."""
    session_id: str
    analysis: SessionAnalysis
    emotion_distribution: List[ChartDataPoint] = []
    reaction_times: List[ChartDataPoint] = []
    head_movement_data: List[ChartDataPoint] = []
    gaze_heatmap_data: List[Dict[str, float]] = []
    test_summary: Dict[str, Any] = {}
    timestamp: str = ""
    disclaimer: str = "This tool is not a medical diagnostic system. It provides behavioral screening indicators only."
