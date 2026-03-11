# autism_screening_app/services.py
# Core processing logic for behavioral screening
# Primary: MediaPipe FaceMesh + Pose
# Fallback: OpenCV heuristics if MediaPipe unavailable

import uuid
import json
import os
import base64
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import cv2

# --- Attempt to import MediaPipe (primary), fallback to OpenCV heuristics ---
try:
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    MEDIAPIPE_AVAILABLE = True
    print("AUTISM_SCREENING: MediaPipe loaded successfully (primary mode).")
except (ImportError, AttributeError) as e:
    MEDIAPIPE_AVAILABLE = False
    print(f"AUTISM_SCREENING: MediaPipe not usable ({e}) — using OpenCV fallback mode.")

# --- ML Model ---
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# --- Paths ---
APP_BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_BASE_DIR / "data"
SESSION_STORE_PATH = DATA_DIR / "autism_sessions.json"

# --- Ensure data directory exists ---
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ===========================================================================
# SESSION MANAGEMENT — dict in memory + JSON persistence
# ===========================================================================

_sessions: Dict[str, Dict[str, Any]] = {}


def _load_sessions_from_disk():
    """Load persisted sessions from JSON file on startup."""
    global _sessions
    if SESSION_STORE_PATH.exists():
        try:
            with open(SESSION_STORE_PATH, "r") as f:
                _sessions = json.load(f)
            logger.info(f"AUTISM_SCREENING: Loaded {len(_sessions)} sessions from disk.")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"AUTISM_SCREENING: Could not load sessions file: {e}")
            _sessions = {}
    else:
        _sessions = {}


def _save_sessions_to_disk():
    """Persist current sessions to JSON file."""
    try:
        with open(SESSION_STORE_PATH, "w") as f:
            json.dump(_sessions, f, indent=2, default=str)
    except IOError as e:
        logger.warning(f"AUTISM_SCREENING: Could not save sessions file: {e}")


# Load on module import
_load_sessions_from_disk()


def create_session(participant_id: Optional[str] = None) -> str:
    """Create a new screening session and return its ID."""
    session_id = str(uuid.uuid4())[:8]
    _sessions[session_id] = {
        "participant_id": participant_id,
        "created_at": datetime.now().isoformat(),
        "frames": {
            "eye_gaze": [],
            "facial_expression": [],
            "head_movement": [],
            "reaction_stimulus": []
        },
        "analysis": None,
        "report": None
    }
    _save_sessions_to_disk()
    logger.info(f"AUTISM_SCREENING: Session {session_id} created.")
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a session by ID."""
    return _sessions.get(session_id)


# ===========================================================================
# FRAME DECODING
# ===========================================================================

def decode_frame(frame_base64: str) -> Optional[np.ndarray]:
    """Decode a base64-encoded image frame to a numpy array (BGR)."""
    try:
        # Strip data URL prefix if present
        if "," in frame_base64:
            frame_base64 = frame_base64.split(",", 1)[1]
        img_bytes = base64.b64decode(frame_base64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        logger.error(f"AUTISM_SCREENING: Frame decode error: {e}")
        return None


# ===========================================================================
# MEDIAPIPE PROCESSORS (PRIMARY)
# ===========================================================================

# Reusable MediaPipe instances (lazy init)
_face_mesh_instance = None
_pose_instance = None


def _get_face_mesh():
    """Lazy-initialize MediaPipe FaceMesh."""
    global _face_mesh_instance
    if _face_mesh_instance is None and MEDIAPIPE_AVAILABLE:
        _face_mesh_instance = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    return _face_mesh_instance


def _get_pose():
    """Lazy-initialize MediaPipe Pose."""
    global _pose_instance
    if _pose_instance is None and MEDIAPIPE_AVAILABLE:
        _pose_instance = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    return _pose_instance


def _process_eye_gaze_mediapipe(frame: np.ndarray, stimulus_pos: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Process eye gaze using MediaPipe FaceMesh."""
    result = {
        "face_detected": False, "gaze_x": None, "gaze_y": None,
        "gaze_fixation": None, "blink_detected": None
    }
    face_mesh = _get_face_mesh()
    if face_mesh is None:
        return result

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_results = face_mesh.process(rgb)

    if not mp_results.multi_face_landmarks:
        return result

    result["face_detected"] = True
    landmarks = mp_results.multi_face_landmarks[0].landmark
    h, w = frame.shape[:2]

    # --- Eye gaze estimation from iris landmarks ---
    # Left iris: 468-472, Right iris: 473-477 (refined landmarks)
    try:
        left_iris = landmarks[468]
        right_iris = landmarks[473]
        gaze_x = (left_iris.x + right_iris.x) / 2.0
        gaze_y = (left_iris.y + right_iris.y) / 2.0
        result["gaze_x"] = round(gaze_x, 4)
        result["gaze_y"] = round(gaze_y, 4)

        # Fixation: check if gaze is near stimulus position
        if stimulus_pos:
            dist = np.sqrt((gaze_x - stimulus_pos.get("x", 0.5)) ** 2 +
                           (gaze_y - stimulus_pos.get("y", 0.5)) ** 2)
            result["gaze_fixation"] = dist < 0.15
    except (IndexError, AttributeError):
        pass

    # --- Blink detection using EAR (Eye Aspect Ratio) ---
    try:
        # Left eye vertical: 159(top), 145(bottom); horizontal: 33(left), 133(right)
        left_top = landmarks[159]
        left_bottom = landmarks[145]
        left_left = landmarks[33]
        left_right = landmarks[133]
        vert = abs(left_top.y - left_bottom.y)
        horiz = abs(left_left.x - left_right.x)
        ear = vert / (horiz + 1e-6)
        result["blink_detected"] = ear < 0.045
    except (IndexError, AttributeError):
        pass

    return result


def _process_head_movement_mediapipe(frame: np.ndarray) -> Dict[str, Any]:
    """Process head movement using MediaPipe Pose."""
    result = {
        "face_detected": False, "head_pitch": None, "head_yaw": None,
        "head_roll": None, "repetitive_motion": None
    }
    pose = _get_pose()
    if pose is None:
        return result

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_results = pose.process(rgb)

    if not mp_results.pose_landmarks:
        return result

    result["face_detected"] = True
    lm = mp_results.pose_landmarks.landmark

    try:
        # Nose: 0, Left ear: 7, Right ear: 8, Left shoulder: 11, Right shoulder: 12
        nose = lm[0]
        left_ear = lm[7]
        right_ear = lm[8]
        left_shoulder = lm[11]
        right_shoulder = lm[12]

        # Yaw: horizontal difference between ears relative to nose
        yaw = (left_ear.x - right_ear.x)
        result["head_yaw"] = round(float(np.degrees(np.arctan2(yaw, 1.0))), 2)

        # Pitch: vertical relationship of nose to shoulders
        mid_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2.0
        pitch = nose.y - mid_shoulder_y
        result["head_pitch"] = round(float(np.degrees(np.arctan2(pitch, 1.0))), 2)

        # Roll: shoulder tilt
        roll = left_shoulder.y - right_shoulder.y
        result["head_roll"] = round(float(np.degrees(np.arctan2(roll, 1.0))), 2)
    except (IndexError, AttributeError):
        pass

    return result


# ===========================================================================
# OPENCV FALLBACK PROCESSORS
# ===========================================================================

# Haar cascades for face and eye detection (fallback)
_face_cascade = None
_eye_cascade = None


def _get_face_cascade():
    """Lazy-load OpenCV Haar cascade for face detection."""
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _face_cascade = cv2.CascadeClassifier(cascade_path)
        if _face_cascade.empty():
            # Try alternate cascade
            alt_path = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
            _face_cascade = cv2.CascadeClassifier(alt_path)
        print(f"AUTISM_SCREENING: Face cascade loaded, empty={_face_cascade.empty()}")
    return _face_cascade


def _get_eye_cascade():
    """Lazy-load OpenCV Haar cascade for eye detection."""
    global _eye_cascade
    if _eye_cascade is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_eye.xml"
        _eye_cascade = cv2.CascadeClassifier(cascade_path)
    return _eye_cascade


def _detect_face_opencv(frame: np.ndarray):
    """
    Robust face detection with histogram equalization and relaxed params.
    Returns list of (x, y, w, h) tuples and the preprocessed grayscale image.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Apply histogram equalization to normalize lighting
    gray = cv2.equalizeHist(gray)

    cascade = _get_face_cascade()
    # Use relaxed parameters: scaleFactor=1.1 (more thorough), minNeighbors=3 (less strict)
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=3,
        minSize=(60, 60),  # minimum face size
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    if len(faces) == 0:
        # Try even more relaxed as last resort
        faces = cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=2, minSize=(40, 40))

    return faces, gray


def _process_eye_gaze_opencv(frame: np.ndarray, stimulus_pos: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Fallback eye gaze estimation using OpenCV Haar cascades."""
    result = {
        "face_detected": False, "gaze_x": None, "gaze_y": None,
        "gaze_fixation": None, "blink_detected": None
    }
    faces, gray = _detect_face_opencv(frame)

    if len(faces) == 0:
        return result

    result["face_detected"] = True
    x, y, w, h = faces[0]
    face_center_x = (x + w / 2) / frame.shape[1]
    face_center_y = (y + h / 2) / frame.shape[0]
    result["gaze_x"] = round(face_center_x, 4)
    result["gaze_y"] = round(face_center_y, 4)

    if stimulus_pos:
        dist = np.sqrt((face_center_x - stimulus_pos.get("x", 0.5)) ** 2 +
                       (face_center_y - stimulus_pos.get("y", 0.5)) ** 2)
        result["gaze_fixation"] = dist < 0.25  # more lenient threshold

    # Blink detection using eye cascade
    eye_cascade = _get_eye_cascade()
    face_roi = gray[y:y + h, x:x + w]
    eyes = eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=3, minSize=(15, 15))
    # If fewer than 2 eyes detected, likely blinking
    result["blink_detected"] = len(eyes) < 2

    return result


def _process_head_movement_opencv(frame: np.ndarray) -> Dict[str, Any]:
    """Fallback head movement estimation using face position heuristics."""
    result = {
        "face_detected": False, "head_pitch": None, "head_yaw": None,
        "head_roll": None, "repetitive_motion": None
    }
    faces, gray = _detect_face_opencv(frame)

    if len(faces) == 0:
        return result

    result["face_detected"] = True
    x, y, w, h = faces[0]
    frame_h, frame_w = frame.shape[:2]
    center_x = (x + w / 2) / frame_w
    center_y = (y + h / 2) / frame_h

    # Estimate yaw from horizontal position (centered = 0)
    result["head_yaw"] = round((center_x - 0.5) * 60, 2)
    # Estimate pitch from vertical position (face center at ~0.4 from top is neutral)
    result["head_pitch"] = round((center_y - 0.4) * 40, 2)
    # Roll from face width/height ratio deviation (normal aspect ~0.8)
    aspect = w / (h + 1e-6)
    result["head_roll"] = round((aspect - 0.8) * 30, 2)

    return result


# ===========================================================================
# EMOTION DETECTION (simple heuristic — no DeepFace dependency)
# ===========================================================================

_EMOTIONS = ["happy", "sad", "angry", "surprised", "neutral"]


def _detect_emotion_heuristic(frame: np.ndarray) -> Tuple[str, float]:
    """
    Simple emotion estimation based on face brightness and texture.
    Returns (emotion_label, confidence).
    In production, swap this with DeepFace or FER.
    """
    faces, gray = _detect_face_opencv(frame)

    if len(faces) == 0:
        return "neutral", 0.0

    x, y, w, h = faces[0]
    face_roi = gray[y:y + h, x:x + w]

    if face_roi.size == 0:
        return "neutral", 0.0

    # Use simple statistics as proxy features
    mean_val = float(np.mean(face_roi))
    std_val = float(np.std(face_roi))
    laplacian_var = float(cv2.Laplacian(face_roi, cv2.CV_64F).var())

    # Map features to emotions heuristically
    # Adjusted thresholds for equalized images (brighter overall)
    if laplacian_var > 400 and std_val > 45:
        return "surprised", round(min(0.5 + laplacian_var / 2000, 0.9), 2)
    elif mean_val > 130 and std_val > 35:
        return "happy", round(min(0.4 + mean_val / 400, 0.85), 2)
    elif mean_val < 110 and std_val < 35:
        return "sad", round(min(0.3 + (130 - mean_val) / 200, 0.8), 2)
    elif std_val > 50:
        return "angry", round(min(0.3 + std_val / 150, 0.75), 2)
    else:
        return "neutral", round(0.5, 2)


# ===========================================================================
# UNIFIED FRAME PROCESSOR
# ===========================================================================

def process_frame(session_id: str, frame_base64: str, test_type: str,
                  timestamp: float, stimulus_position: Optional[Dict[str, float]] = None,
                  target_emotion: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a single webcam frame for the given test type.
    Uses MediaPipe if available, otherwise falls back to OpenCV.
    """
    session = get_session(session_id)
    if session is None:
        return {"error": "Session not found", "face_detected": False}

    frame = decode_frame(frame_base64)
    if frame is None:
        return {"error": "Could not decode frame", "face_detected": False}

    frame_index = len(session["frames"].get(test_type, []))
    result = {
        "session_id": session_id,
        "test_type": test_type,
        "frame_index": frame_index,
        "face_detected": False,
        "message": ""
    }

    # --- Route to appropriate processor ---
    if test_type == "eye_gaze":
        if MEDIAPIPE_AVAILABLE:
            data = _process_eye_gaze_mediapipe(frame, stimulus_position)
        else:
            data = _process_eye_gaze_opencv(frame, stimulus_position)
        result.update(data)
        result["message"] = "Tracking gaze" if data["face_detected"] else "No face detected"

    elif test_type == "facial_expression":
        # Use heuristic emotion detection
        emotion, confidence = _detect_emotion_heuristic(frame)
        faces, gray = _detect_face_opencv(frame)
        result["face_detected"] = len(faces) > 0
        result["detected_emotion"] = emotion
        result["emotion_confidence"] = confidence
        result["expression_match"] = (emotion == target_emotion) if target_emotion else None
        result["message"] = f"Detected: {emotion}" if result["face_detected"] else "No face detected"

    elif test_type == "head_movement":
        if MEDIAPIPE_AVAILABLE:
            data = _process_head_movement_mediapipe(frame)
        else:
            data = _process_head_movement_opencv(frame)
        result.update(data)
        result["message"] = "Tracking head" if data["face_detected"] else "No face detected"

    elif test_type == "reaction_stimulus":
        # Reaction test: detect face presence + gaze shift
        if MEDIAPIPE_AVAILABLE:
            gaze_data = _process_eye_gaze_mediapipe(frame, stimulus_position)
        else:
            gaze_data = _process_eye_gaze_opencv(frame, stimulus_position)
        result["face_detected"] = gaze_data["face_detected"]
        result["gaze_x"] = gaze_data.get("gaze_x")
        result["gaze_y"] = gaze_data.get("gaze_y")
        result["gaze_shift_detected"] = gaze_data.get("gaze_fixation", False)
        # Engagement: based on face detection consistency
        result["engagement_level"] = 0.8 if gaze_data["face_detected"] else 0.2
        result["message"] = "Measuring reaction" if gaze_data["face_detected"] else "No face detected"

    # --- Store frame result in session ---
    # Only store serializable summary (not the full frame)
    frame_summary = {
        "frame_index": frame_index,
        "timestamp": timestamp,
        "face_detected": result.get("face_detected", False),
        "gaze_x": result.get("gaze_x"),
        "gaze_y": result.get("gaze_y"),
        "gaze_fixation": result.get("gaze_fixation"),
        "blink_detected": result.get("blink_detected"),
        "detected_emotion": result.get("detected_emotion"),
        "emotion_confidence": result.get("emotion_confidence"),
        "expression_match": result.get("expression_match"),
        "head_pitch": result.get("head_pitch"),
        "head_yaw": result.get("head_yaw"),
        "head_roll": result.get("head_roll"),
        "engagement_level": result.get("engagement_level"),
        "gaze_shift_detected": result.get("gaze_shift_detected")
    }

    if test_type in session["frames"]:
        session["frames"][test_type].append(frame_summary)
    else:
        session["frames"][test_type] = [frame_summary]

    # Persist periodically (every 10 frames to avoid I/O bottleneck)
    if frame_index % 10 == 0:
        _save_sessions_to_disk()

    return result


# ===========================================================================
# FEATURE EXTRACTION
# ===========================================================================

def extract_behavioral_features(session_id: str) -> Dict[str, float]:
    """
    Extract aggregate behavioral features from all test frames in a session.
    Returns dict with: blink_rate, gaze_fixation_time, emotion_variability,
    head_motion_variance, reaction_time, engagement_score.
    """
    session = get_session(session_id)
    if session is None:
        return {}

    frames = session["frames"]
    features = {}

    # --- Blink rate (from eye_gaze frames) ---
    gaze_frames = frames.get("eye_gaze", [])
    if gaze_frames:
        blinks = sum(1 for f in gaze_frames if f.get("blink_detected"))
        # Estimate duration from timestamps
        if len(gaze_frames) >= 2:
            duration_sec = (gaze_frames[-1]["timestamp"] - gaze_frames[0]["timestamp"]) / 1000.0
            duration_min = max(duration_sec / 60.0, 0.01)
        else:
            duration_min = 0.5  # default
        features["blink_rate"] = round(blinks / duration_min, 2)

        # Gaze fixation time (proportion of frames with fixation)
        fixations = sum(1 for f in gaze_frames if f.get("gaze_fixation"))
        features["gaze_fixation_time"] = round(fixations / max(len(gaze_frames), 1), 4)
    else:
        features["blink_rate"] = 15.0  # normal average
        features["gaze_fixation_time"] = 0.5

    # --- Emotion variability (from facial expression frames) ---
    expr_frames = frames.get("facial_expression", [])
    if expr_frames:
        confidences = [f.get("emotion_confidence", 0) for f in expr_frames if f.get("emotion_confidence") is not None]
        features["emotion_variability"] = round(float(np.std(confidences)) if confidences else 0.0, 4)
    else:
        features["emotion_variability"] = 0.3

    # --- Head motion variance (from head movement frames) ---
    head_frames = frames.get("head_movement", [])
    if head_frames:
        pitches = [f.get("head_pitch", 0) for f in head_frames if f.get("head_pitch") is not None]
        yaws = [f.get("head_yaw", 0) for f in head_frames if f.get("head_yaw") is not None]
        rolls = [f.get("head_roll", 0) for f in head_frames if f.get("head_roll") is not None]
        all_angles = pitches + yaws + rolls
        features["head_motion_variance"] = round(float(np.var(all_angles)) if all_angles else 0.0, 4)
    else:
        features["head_motion_variance"] = 5.0

    # --- Reaction time (from reaction stimulus frames) ---
    react_frames = frames.get("reaction_stimulus", [])
    if react_frames:
        # Average time between stimulus appearance and gaze shift detection
        reaction_times = []
        for i, f in enumerate(react_frames):
            if f.get("gaze_shift_detected") and i > 0:
                dt = f["timestamp"] - react_frames[i - 1]["timestamp"]
                if 0 < dt < 5000:  # sanity check
                    reaction_times.append(dt)
        features["reaction_time"] = round(float(np.mean(reaction_times)) if reaction_times else 500.0, 2)
    else:
        features["reaction_time"] = 500.0

    # --- Engagement score (from all frames with face detection) ---
    all_frames = []
    for test_frames in frames.values():
        all_frames.extend(test_frames)
    if all_frames:
        face_detected_count = sum(1 for f in all_frames if f.get("face_detected"))
        features["engagement_score"] = round(face_detected_count / max(len(all_frames), 1), 4)
    else:
        features["engagement_score"] = 0.5

    return features


# ===========================================================================
# ML SCREENING MODEL
# ===========================================================================

_screening_model = None
_scaler = None


def _train_screening_model():
    """
    Train a RandomForestClassifier on synthetic behavioral feature data.
    In production, replace with real training data.
    """
    global _screening_model, _scaler
    np.random.seed(42)

    # Synthetic training data: 300 samples across 3 classes
    n_samples = 100
    # Features: blink_rate, gaze_fixation_time, emotion_variability,
    #           head_motion_variance, reaction_time, engagement_score

    # Class 0: Low likelihood (typical behavior)
    low = np.column_stack([
        np.random.normal(15, 3, n_samples),      # blink_rate ~15/min
        np.random.normal(0.7, 0.1, n_samples),    # gaze_fixation ~0.7
        np.random.normal(0.3, 0.05, n_samples),   # emotion_variability ~0.3
        np.random.normal(5, 2, n_samples),         # head_motion_variance ~5
        np.random.normal(350, 80, n_samples),      # reaction_time ~350ms
        np.random.normal(0.85, 0.05, n_samples)    # engagement ~0.85
    ])

    # Class 1: Moderate likelihood
    moderate = np.column_stack([
        np.random.normal(10, 4, n_samples),
        np.random.normal(0.4, 0.15, n_samples),
        np.random.normal(0.15, 0.06, n_samples),
        np.random.normal(15, 5, n_samples),
        np.random.normal(600, 150, n_samples),
        np.random.normal(0.6, 0.1, n_samples)
    ])

    # Class 2: High likelihood
    high = np.column_stack([
        np.random.normal(6, 3, n_samples),
        np.random.normal(0.2, 0.1, n_samples),
        np.random.normal(0.08, 0.04, n_samples),
        np.random.normal(30, 10, n_samples),
        np.random.normal(900, 200, n_samples),
        np.random.normal(0.35, 0.12, n_samples)
    ])

    X = np.vstack([low, moderate, high])
    y = np.array([0] * n_samples + [1] * n_samples + [2] * n_samples)

    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)

    _screening_model = RandomForestClassifier(
        n_estimators=100, max_depth=8, random_state=42
    )
    _screening_model.fit(X_scaled, y)
    logger.info("AUTISM_SCREENING: Screening model trained on synthetic data.")


def predict_screening(features: Dict[str, float]) -> Dict[str, Any]:
    """
    Run the screening model on extracted features.
    Returns: screening_level, screening_score (0-100), confidence.
    """
    global _screening_model, _scaler
    if _screening_model is None:
        _train_screening_model()

    feature_vector = np.array([[
        features.get("blink_rate", 15),
        features.get("gaze_fixation_time", 0.5),
        features.get("emotion_variability", 0.3),
        features.get("head_motion_variance", 5),
        features.get("reaction_time", 500),
        features.get("engagement_score", 0.5)
    ]])

    X_scaled = _scaler.transform(feature_vector)
    prediction = _screening_model.predict(X_scaled)[0]
    probabilities = _screening_model.predict_proba(X_scaled)[0]

    level_map = {0: "Low likelihood", 1: "Moderate likelihood", 2: "High likelihood"}
    screening_level = level_map.get(prediction, "Low likelihood")

    # Screening score: weighted probability → 0-100 scale
    screening_score = round(probabilities[1] * 50 + probabilities[2] * 100, 1)
    screening_score = max(0, min(100, screening_score))

    confidence = round(float(max(probabilities)), 3)

    return {
        "screening_level": screening_level,
        "screening_score": screening_score,
        "confidence": confidence
    }


# ===========================================================================
# SESSION ANALYSIS
# ===========================================================================

def analyze_session(session_id: str) -> Dict[str, Any]:
    """
    Analyze a complete session: extract features → run ML model → return analysis.
    """
    session = get_session(session_id)
    if session is None:
        return {"error": "Session not found"}

    features = extract_behavioral_features(session_id)
    prediction = predict_screening(features)

    analysis = {
        "session_id": session_id,
        "features": features,
        "screening_level": prediction["screening_level"],
        "screening_score": prediction["screening_score"],
        "confidence": prediction["confidence"],
        "disclaimer": "This tool is not a medical diagnostic system. It provides behavioral screening indicators only."
    }

    # Store analysis in session
    session["analysis"] = analysis
    _save_sessions_to_disk()

    return analysis


# ===========================================================================
# REPORT GENERATION
# ===========================================================================

def generate_report(session_id: str) -> Dict[str, Any]:
    """
    Generate a full screening report with visualization data.
    """
    session = get_session(session_id)
    if session is None:
        return {"error": "Session not found"}

    # Ensure analysis has been run
    analysis = session.get("analysis")
    if analysis is None:
        analysis = analyze_session(session_id)
        if "error" in analysis:
            return analysis

    frames = session["frames"]

    # --- Emotion distribution ---
    emotion_counts: Dict[str, int] = {}
    for f in frames.get("facial_expression", []):
        em = f.get("detected_emotion", "neutral")
        emotion_counts[em] = emotion_counts.get(em, 0) + 1
    emotion_distribution = [
        {"label": k, "value": v} for k, v in emotion_counts.items()
    ]

    # --- Reaction times ---
    reaction_times = []
    react_frames = frames.get("reaction_stimulus", [])
    for i, f in enumerate(react_frames):
        if f.get("gaze_shift_detected") and i > 0:
            dt = f["timestamp"] - react_frames[i - 1]["timestamp"]
            if 0 < dt < 5000:
                reaction_times.append({"label": f"Trial {len(reaction_times) + 1}", "value": round(dt, 1)})

    # --- Head movement data ---
    head_movement_data = []
    for f in frames.get("head_movement", []):
        if f.get("head_pitch") is not None:
            head_movement_data.append({
                "label": f"Frame {f['frame_index']}",
                "value": round(abs(f.get("head_pitch", 0)) + abs(f.get("head_yaw", 0)) + abs(f.get("head_roll", 0)), 2)
            })

    # --- Gaze heatmap data ---
    gaze_heatmap = []
    for f in frames.get("eye_gaze", []):
        if f.get("gaze_x") is not None and f.get("gaze_y") is not None:
            gaze_heatmap.append({
                "x": f["gaze_x"],
                "y": f["gaze_y"],
                "intensity": 1.0 if f.get("gaze_fixation") else 0.5
            })

    # --- Test summary ---
    test_summary = {}
    for test_name, test_frames in frames.items():
        total = len(test_frames)
        detected = sum(1 for f in test_frames if f.get("face_detected"))
        test_summary[test_name] = {
            "total_frames": total,
            "face_detected_frames": detected,
            "detection_rate": round(detected / max(total, 1), 3)
        }

    report = {
        "session_id": session_id,
        "analysis": analysis,
        "emotion_distribution": emotion_distribution,
        "reaction_times": reaction_times,
        "head_movement_data": head_movement_data,
        "gaze_heatmap_data": gaze_heatmap,
        "test_summary": test_summary,
        "timestamp": datetime.now().isoformat(),
        "disclaimer": "This tool is not a medical diagnostic system. It provides behavioral screening indicators only."
    }

    # Store report in session
    session["report"] = report
    _save_sessions_to_disk()

    return report
