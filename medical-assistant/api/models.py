from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class FileInformation(BaseModel):
    name: str
    type: str
    size: int
    content_base64: Optional[str] = None # Optional if file is just referenced by name/path

class ChatMessageInput(BaseModel):
    message: Optional[str] = None
    mode: str = Field(default="qna", description="qna, personal_symptoms, personal_report_upload")
    user_region: Optional[str] = None
    file_info: Optional[FileInformation] = None # For uploads
    # session_id: str # Removed, using single persistent user for now

class AISchemeInfo(BaseModel):
    name: str
    region_specific: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    source_info: Optional[str] = None # Added for consistency

class AIDoctorRecommendation(BaseModel):
    specialty: str
    reason: Optional[str] = None
    # Further details like name/contact would come from a Tab 2 integration, not directly from AI here

class AIGraphData(BaseModel):
    type: str # E.g., "bar", "line", "pie"
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]] # e.g., [{"label": "Blood Sugar", "data": [10,20]}]
    source: Optional[str] = None

class ChatMessageOutput(BaseModel):
    answer: str
    answer_format: str = Field(default="markdown", description="Format of the answer, e.g., markdown, text")
    follow_up_questions: Optional[List[str]] = None
    disease_identification: Optional[str] = None # Tentative, based on symptoms/report
    next_steps: Optional[List[str]] = None
    government_schemes: Optional[List[AISchemeInfo]] = None
    doctor_recommendations: Optional[List[AIDoctorRecommendation]] = None
    graphs_data: Optional[List[AIGraphData]] = None # Changed to List for multiple graphs
    error: Optional[str] = None
    # To aid frontend in knowing if file was processed with message:
    file_processed_with_message: Optional[str] = None # Name of the file included in this interaction

# --- Models for React Symptom Analyzer Integration ---
class ReactSymptomInput(BaseModel):
    description: str
    duration: str
    severity: int # Expecting 1, 2, or 3

class ReactAnalysisRequest(BaseModel):
    symptoms: List[ReactSymptomInput]
    user_region: Optional[str] = None # Add if React can send it
    history_context_string: Optional[str] = None # For SPA to send its history summary

class ReactConditionOutput(BaseModel):  
    name: str
    probability: float
    description: str
    recommendation: str

class ReactSymptomAnalysisOutput(BaseModel):
    id: str
    date: str # ISO format string
    symptoms: List[ReactSymptomInput]
    possible_conditions: List[ReactConditionOutput]
    general_advice: str
    should_seek_medical_attention: bool
    government_schemes: Optional[List[AISchemeInfo]] = None # Mirroring AISchemeInfo
    doctor_specialties_recommended: Optional[List[str]] = None # List of specialty strings