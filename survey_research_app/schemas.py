# schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum

class ReportTypeEnum(str, Enum):
    COMPREHENSIVE_SINGLE_AREA = "comprehensive_single_area"
    COMPARE_AREAS = "compare_areas"
    DISEASE_FOCUS = "disease_focus"

class SurveyResearchRequest(BaseModel):
    report_type: ReportTypeEnum = Field(default=ReportTypeEnum.COMPREHENSIVE_SINGLE_AREA, description="The type of report to generate.")
    area1: str = Field(..., description="Primary geographical area. For single area reports, this is the main subject. For comparisons, this is the first area.")
    area2: Optional[str] = Field(None, description="Second geographical area, used if report_type is 'compare_areas' or a disease focus comparison.")
    disease_focus: Optional[str] = Field(None, description="Specific disease or health condition to focus on, used if report_type is 'disease_focus'.")
    time_range: Optional[str] = Field(None, description="Optional time range for the data, e.g., '2020-2023', 'last 5 years'.")

class ChartDataset(BaseModel):
    label: str
    data: List[Union[int, float]]
    backgroundColor: Optional[Union[str, List[str]]] = None
    borderColor: Optional[Union[str, List[str]]] = None

class ChartData(BaseModel):
    type: str
    labels: List[str]
    datasets: List[ChartDataset]
    title: Optional[str] = None
    source: Optional[str] = None

class SurveyReportResponse(BaseModel):
    report_id: str
    area_name: str # This will be dynamically set based on the request, e.g., "Area X" or "Area X vs Area Y" or "Diabetes in Area X"
    full_report_markdown: str
    charts: List[ChartData] = []
    full_text_for_follow_up: str

class SurveyQuestionRequest(BaseModel):
    report_id: str
    question: str
    report_context: str

class SurveyAnswerResponse(BaseModel):
    answer: str