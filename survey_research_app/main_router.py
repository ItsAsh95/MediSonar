# medical-assistant/survey_research_app/main_router.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import FileResponse
from typing import Dict
import os
import json # For model_dump_json for logging if needed

# Use relative imports for schemas and services within this sub-app package
from .schemas import (
    SurveyResearchRequest, 
    SurveyReportResponse, 
    SurveyQuestionRequest, 
    SurveyAnswerResponse,
    ReportTypeEnum # Make sure ReportTypeEnum is imported
)
from .services import (
    conduct_deep_research as conduct_survey_deep_research, # Aliased to avoid name clash if main app has similar
    answer_follow_up_question as answer_survey_follow_up, # Aliased
    generate_report_id as generate_survey_report_id # Aliased
)

router = APIRouter(
    prefix="/survey-research", 
    tags=["Survey & Research Application"]
)

APP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_BASE_DIR, "static") # For this app's own static files

survey_generated_reports_cache: Dict[str, SurveyReportResponse] = {}

@router.post("/api/research", response_model=SurveyReportResponse)
async def create_survey_research_report_endpoint(research_request: SurveyResearchRequest):
    if not research_request.area1:
        raise HTTPException(status_code=400, detail="Area 1 (Primary Area) cannot be empty.")

    # Validation based on report_type from original app.py
    if research_request.report_type == ReportTypeEnum.COMPARE_AREAS and not research_request.area2:
        raise HTTPException(status_code=400, detail="Area 2 is required for comparison reports.")
    if research_request.report_type == ReportTypeEnum.DISEASE_FOCUS and not research_request.disease_focus:
        raise HTTPException(status_code=400, detail="Disease/Condition is required for disease focus reports.")

    print(f"SURVEY_APP: Received research request: {research_request.model_dump_json(indent=2)}")

    report_id_params = research_request.model_dump(exclude_none=True, exclude_defaults=False)
    report_id = generate_survey_report_id(report_id_params) # Use aliased function

    if report_id in survey_generated_reports_cache:
        print(f"SURVEY_APP: Returning cached report. ID: {report_id}")
        return survey_generated_reports_cache[report_id]

    try:
        # conduct_survey_deep_research is from this app's services.py
        # It should return a dictionary matching SurveyReportResponse fields
        report_dict_data = await conduct_survey_deep_research(research_request)
        
        # Ensure report_id in the response matches the one generated for caching
        # The conduct_survey_deep_research in your services.py should already include 'report_id'
        # If not, ensure it's added to report_dict_data before creating SurveyReportResponse
        if "report_id" not in report_dict_data or report_dict_data["report_id"] != report_id:
            report_dict_data["report_id"] = report_id # Ensure consistency

        response_model = SurveyReportResponse(**report_dict_data)
        survey_generated_reports_cache[report_id] = response_model
        print(f"SURVEY_APP: Research complete. Report ID: {response_model.report_id}, Area: {response_model.area_name}")
        return response_model
    except Exception as e:
        print(f"SURVEY_APP: Error during research for request '{research_request.model_dump_json()}': {e}")
        import traceback
        traceback.print_exc()
        # Consider if a more specific error from the service layer should be passed
        raise HTTPException(status_code=500, detail=f"Failed to conduct survey/research: {str(e)}")

@router.post("/api/ask", response_model=SurveyAnswerResponse)
async def ask_survey_follow_up_endpoint(question_request: SurveyQuestionRequest):
    report_id = question_request.report_id
    question = question_request.question.strip()
    report_context = question_request.report_context

    if not question:
        raise HTTPException(status_code=400, detail="Follow-up question cannot be empty.")
    
    if not report_context: # report_context is now required from frontend as per original app.py
        cached_report = survey_generated_reports_cache.get(report_id)
        if not cached_report or not cached_report.full_text_for_follow_up:
             raise HTTPException(status_code=400, detail="Report context is missing for follow-up and not found in cache.")
        report_context = cached_report.full_text_for_follow_up
        print(f"SURVEY_APP: Used cached report context for follow-up on report ID: {report_id}")
    
    print(f"SURVEY_APP: Received follow-up question: '{question}' for report ID: {report_id}")

    try:
        answer_text = await answer_survey_follow_up(question, report_context) # Use aliased function
        return SurveyAnswerResponse(answer=answer_text)
    except Exception as e:
        print(f"SURVEY_APP: Error answering follow-up question: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get survey follow-up answer: {str(e)}")

# Serve this sub-app's HTML frontend (index.html)
# Accessible at /survey-research/ due to router prefix
@router.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_survey_research_ui_root_endpoint(): # Renamed for clarity
    index_html_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_html_path):
        print(f"SURVEY_APP: UI File (index.html) not found at {index_html_path}")
        raise HTTPException(status_code=404, detail="Survey & Research App UI not found.")
    return FileResponse(index_html_path)

# If PERPLEXITY_DEEP_SEARCH/app.py had other routes (e.g., for other HTML pages), add them here.