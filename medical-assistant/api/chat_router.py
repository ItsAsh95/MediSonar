from typing import Dict, Any, List, Optional, Annotated, get_args
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
import uuid
from datetime import datetime, timezone
from .models import ( # Use . for current package
    ChatMessageOutput, FileInformation, AISchemeInfo, AIDoctorRecommendation,
    ReactAnalysisRequest, ReactSymptomAnalysisOutput, ReactSymptomInput, ReactConditionOutput
)
from ..utils.ai_handler import AIInteractionHandler
from ..utils.medical_memory import MedicalMemory, ConversationMode

# from ..config import settings # Not directly needed here if AIHandler uses it

router = APIRouter()

ai_handler = AIInteractionHandler()
memory_handler = MedicalMemory() # Single persistent user, but manages modes internally

# --- Endpoint for React Symptom Analyzer ---
@router.post("/symptoms/analyze", response_model=ReactSymptomAnalysisOutput, tags=["Symptom Analyzer (React)"])
async def analyze_symptoms_for_react_app(request: ReactAnalysisRequest):
    if not request.symptoms:
        raise HTTPException(status_code=400, detail="At least one symptom is required for analysis.")

    symptoms_descriptions_list = []
    severity_map_display = {1: "Mild", 2: "Moderate", 3: "Severe"}
    for s_in in request.symptoms:
        s_desc = f"- {s_in.description} (Duration: {s_in.duration}, Severity: {severity_map_display.get(s_in.severity, 'Unknown')})"
        symptoms_descriptions_list.append(s_desc)
    symptoms_full_description_str = "\n".join(symptoms_descriptions_list) or "User submitted an empty symptom list."

    # For this specific integration, we might not have user_region from React app unless it's added.
    # History context can be generic or tied to a global user ID if you implement that later.
    history_context_for_symptoms = memory_handler.get_context_for_ai("symptoms") # Use symptoms-specific history

    # Call the AI handler's method meant for symptom analysis
    # This method is expected to return a dictionary that can be mapped to ChatMessageOutput,
    # so we need to adapt it to ReactSymptomAnalysisOutput.
    ai_handler_result_dict = await ai_handler.analyze_personal_symptoms(
        symptoms_description=symptoms_full_description_str,
        history_context=history_context_for_symptoms,
        user_region=None # TODO: Consider how React app might provide region, or use a global setting
    )

    if ai_handler_result_dict.get("error"):
        # Pass through AI handler's error or raise a new one
        error_detail = ai_handler_result_dict["error"]
        if "HTTP 400" in error_detail: # Specific check if it's a passthrough from Perplexity 400
             raise HTTPException(status_code=400, detail=f"AI backend issue: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

    # --- Transform ai_handler_result_dict to ReactSymptomAnalysisOutput ---
    # This is the critical mapping part.
    possible_conditions_for_react: List[ReactConditionOutput] = []
    # The ai_handler.analyze_personal_symptoms prompt asks for JSON with 'disease_identification_text'
    # and other lists. We need to see what Perplexity *actually* returns via logging.
    # For now, assume ai_handler_result_dict has a 'disease_identification' string and 'next_steps_list'.
    
    # Example: If ai_handler returns a list of potential conditions in its parsed output
    # This depends on how you refine the prompt for ai_handler.analyze_personal_symptoms to output multiple conditions
    # For now, let's use the example structure from your Symptom/backend/main.py if the AI doesn't give much structure
    # This part will need the MOST ATTENTION based on actual AI output from `sonar-reasoning-pro`
    
    ai_disease_id_text = ai_handler_result_dict.get("disease_identification") # From AI handler
    ai_next_steps = ai_handler_result_dict.get("next_steps_list", [])
    ai_main_answer = ai_handler_result_dict.get("answer", "General advice: Please consult a healthcare professional.")

    if ai_disease_id_text: # If AI gives a primary identification
        possible_conditions_for_react.append(ReactConditionOutput(
            name=ai_disease_id_text,
            probability=0.65, # Placeholder - AI should ideally provide this
            description=f"This is a potential area of concern based on the AI's analysis of your symptoms. This is not a definitive diagnosis. General advice from AI: {ai_main_answer}",
            recommendation=", ".join(ai_next_steps) if ai_next_steps else "Follow general advice or consult a doctor."
        ))
    else: # Fallback if AI doesn't give a clear disease_identification
        possible_conditions_for_react.extend([
            ReactConditionOutput(name="Condition A (Example)", probability=0.5, description="General symptoms may align.", recommendation="Monitor closely."),
            ReactConditionOutput(name="Condition B (Example)", probability=0.3, description="Another possibility to consider.", recommendation="Stay hydrated."),
        ])


    should_seek = False # Determine this based on AI's advice
    advice_lower = ai_main_answer.lower()
    if "consult a doctor" in advice_lower or "seek medical attention" in advice_lower or "gp" in advice_lower:
        should_seek = True
    if any("doctor" in (step or "").lower() or "medical attention" in (step or "").lower() for step in ai_next_steps):
        should_seek = True
    
    # Extract government schemes if provided by ai_handler
    gov_schemes_from_ai = ai_handler_result_dict.get("government_schemes") # This is List[AISchemeInfo]
    
    # Extract doctor specialties if provided
    doc_recs_from_ai = ai_handler_result_dict.get("doctor_recommendations") # List[AIDoctorRecommendation]
    specialties_recommended = [rec.specialty for rec in doc_recs_from_ai if rec.specialty] if doc_recs_from_ai else None


    response_for_react = ReactSymptomAnalysisOutput(
        id=str(uuid.uuid4()),
        date=datetime.now(timezone.utc).isoformat(),
        symptoms=request.symptoms,
        possible_conditions=possible_conditions_for_react,
        general_advice=ai_main_answer,
        should_seek_medical_attention=should_seek,
        government_schemes=gov_schemes_from_ai,
        doctor_specialties_recommended=specialties_recommended
    )
    
    # Save this interaction to main app's "symptoms" history
    memory_handler.add_to_conversation_history(
        mode="symptoms",
        user_message=f"Symptom Analysis (via React App): {symptoms_full_description_str}",
        ai_response=response_for_react.general_advice + " Possible conditions: " + ", ".join([c.name for c in response_for_react.possible_conditions]),
    )
    # Update medical summary based on what ai_handler extracted
    if ai_handler_result_dict.get("extracted_medical_info_dict"):
        extracted_info = ai_handler_result_dict["extracted_medical_info_dict"]
        # Ensure keys align with what update_medical_summary expects
        summary_update_data = {
            "current_symptoms_list": extracted_info.get("current_symptoms_list", [s.description for s in request.symptoms]),
            "potential_conditions_discussed_list": extracted_info.get("potential_conditions_discussed_list", [c.name for c in response_for_react.possible_conditions]),
        }
        memory_handler.update_medical_summary(summary_update_data)

    return response_for_react

@router.post("/chat", response_model=ChatMessageOutput)
async def handle_chat_message(
    message: Annotated[Optional[str], Form()] = None,
    mode_str: Annotated[str, Form()] = "qna", # Receive mode as string
    user_region: Annotated[Optional[str], Form()] = None,
    upload_file: Annotated[Optional[UploadFile], File()] = None
):
    current_mode: ConversationMode
    if mode_str not in get_args(ConversationMode): # Validate against Literal values
        raise HTTPException(status_code=400, detail=f"Invalid mode: '{mode_str}'. Must be one of {get_args(ConversationMode)}.")
    current_mode = mode_str # type: ignore

    file_info_model: Optional[FileInformation] = None
    input_message = message # User's text message
    
    if upload_file:
        if upload_file.size > 10 * 1024 * 1024: # 10MB limit
            raise HTTPException(status_code=413, detail="File too large. Max 10MB.")
        
        contents_bytes = await upload_file.read()
        import base64
        content_base64 = base64.b64encode(contents_bytes).decode('utf-8')
        
        file_info_model = FileInformation(
            name=upload_file.filename or "uploaded_file",
            type=upload_file.content_type or "application/octet-stream",
            size=len(contents_bytes), # Use actual byte length
            content_base64=content_base64
        )
        await upload_file.close()
        print(f"File received: {file_info_model.name}, Type: {file_info_model.type}, Size: {file_info_model.size}")
        if not input_message: # If only file is uploaded, make a default message for context
            input_message = f"Please analyze the uploaded file: {file_info_model.name}"

    if not input_message and not file_info_model:
        raise HTTPException(status_code=400, detail="No message or file provided.")

    # Use Pydantic model for consistent input to AI handler, built from Form data
    # This isn't strictly necessary here as we pass individual args, but good practice if AI handler expects a model
    # For now, we'll pass individual args as AI handler methods are defined that way
    file_info_model_dict = file_info_model.model_dump() if file_info_model else None

    history_context = memory_handler.get_context_for_ai(current_mode)
    response_data_dict: Dict[str, Any] = {}

    try:
        if current_mode == "qna":
            response_data_dict = await ai_handler.get_general_qna_answer(
                input_message or "User uploaded a file for context. Please see file details if relevant.", # Ensure some message
                history_context, 
                file_info_model_dict
            )
        elif current_mode == "personal_symptoms":
            if not input_message: 
                raise HTTPException(status_code=400, detail="Symptom description is required for this mode.")
            response_data_dict = await ai_handler.analyze_personal_symptoms(
                input_message, history_context, user_region
            )
        elif current_mode == "personal_report_upload":
            if not file_info_model_dict: 
                raise HTTPException(status_code=400, detail="File upload is required for report analysis mode.")
            response_data_dict = await ai_handler.analyze_uploaded_personal_report(
                file_info_model_dict, history_context, user_region
            )
        # No 'else' needed due to mode_str validation earlier

        # Ensure all fields for ChatMessageOutput are present, defaulting if necessary
        # The _parse_ai_response_to_structured_output in ai_handler should mostly handle this.
        # This is a final safety net.
        final_output_data = {
            "answer": response_data_dict.get("answer", "No specific answer generated by AI."),
            "answer_format": response_data_dict.get("answer_format", "markdown"),
            "follow_up_questions": response_data_dict.get("follow_up_questions"),
            "disease_identification": response_data_dict.get("disease_identification"),
            "next_steps": response_data_dict.get("next_steps"),
            "government_schemes": response_data_dict.get("government_schemes"),
            "doctor_recommendations": response_data_dict.get("doctor_recommendations"),
            "graphs_data": response_data_dict.get("graphs_data"),
            "error": response_data_dict.get("error"),
            "file_processed_with_message": response_data_dict.get("file_processed_with_message")
        }
        response_output = ChatMessageOutput(**final_output_data)

        # Save to conversation history for the specific mode
        memory_handler.add_to_conversation_history(
            mode=current_mode,
            user_message=input_message, 
            ai_response=response_output.answer, # Storing main answer text
            # To store the full AI JSON response for richer history display:
            # ai_response_full_obj=response_output.model_dump_json(), # Store full ChatMessageOutput as JSON string
            file_name=file_info_model.name if file_info_model else None
        )
        
        if current_mode in ["personal_symptoms", "personal_report_upload"] and response_data_dict.get("extracted_medical_info"):
            memory_handler.update_medical_summary(response_data_dict["extracted_medical_info"])
            
        return response_output

    except HTTPException as e:
        raise e # Re-raise HTTPExceptions from validation or AI handler
    except Exception as e:
        print(f"Critical Error in /chat endpoint processing mode '{current_mode}': {e.__class__.__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        return ChatMessageOutput(answer=f"Sorry, an unexpected server error occurred while processing your request for {current_mode}.", error=str(e))


@router.get("/history/{mode_str}", response_model=List[Dict[str, Any]])
async def get_mode_history_route(mode_str: str):
    current_mode: ConversationMode
    if mode_str not in get_args(ConversationMode):
        raise HTTPException(status_code=400, detail=f"Invalid mode for history: '{mode_str}'.")
    current_mode = mode_str #type: ignore
    return memory_handler.get_conversation_history(current_mode)

@router.get("/history/summary/all")
async def get_all_history_summary_route(): # Renamed to avoid conflict if class has same name
    conv_summary = memory_handler.get_all_conversations_summary()
    med_summary = memory_handler.get_medical_summary()
    return {
        "conversation_summaries": conv_summary,
        "medical_summary": med_summary
    }

@router.post("/history/clear/all")
async def clear_all_data_route(): # Renamed
    memory_handler.clear_all_user_data()
    return {"message": "All user data has been cleared."}