from typing import Dict, Any, List, Optional 
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, Annotated

from .models import ChatMessageInput, ChatMessageOutput, FileInformation
from ..utils.ai_handler import AIInteractionHandler
from ..utils.medical_memory import MedicalMemory
# from ..config import settings # Not directly needed here if AIHandler uses it

router = APIRouter()

ai_handler = AIInteractionHandler()
memory_handler = MedicalMemory() # Single persistent user

@router.post("/chat", response_model=ChatMessageOutput)
async def handle_chat_message(
    message: Annotated[Optional[str], Form()] = None,
    mode: Annotated[str, Form()] = "qna",
    user_region: Annotated[Optional[str], Form()] = None,
    upload_file: Annotated[Optional[UploadFile], File()] = None # Key for file upload
):
    file_info_model: Optional[FileInformation] = None
    input_message = message
    
    if upload_file:
        if upload_file.size > 10 * 1024 * 1024: # 10MB limit
            raise HTTPException(status_code=413, detail="File too large. Max 10MB.")
        
        # Read file content as bytes, then base64 encode
        contents_bytes = await upload_file.read()
        import base64
        content_base64 = base64.b64encode(contents_bytes).decode('utf-8')
        
        file_info_model = FileInformation(
            name=upload_file.filename,
            type=upload_file.content_type,
            size=upload_file.size, # FastAPI gives size in UploadFile
            content_base64=content_base64
        )
        await upload_file.close()
        print(f"File received: {file_info_model.name}, Type: {file_info_model.type}, Size: {file_info_model.size}")
        if not input_message: # If only file is uploaded, make a default message
            input_message = f"Please analyze the uploaded file: {file_info_model.name}"


    if not input_message and not file_info_model: # If still no message and no file
        raise HTTPException(status_code=400, detail="No message or file provided.")

    # Use a Pydantic model for consistent input to AI handler, even if built from Form data
    chat_input = ChatMessageInput(
        message=input_message,
        mode=mode,
        user_region=user_region,
        file_info=file_info_model
    )

    history_context = memory_handler.get_relevant_history_for_query()
    response_data_dict: Dict[str, Any] = {}

    try:
        if chat_input.mode == "qna":
            response_data_dict = await ai_handler.get_general_qna_answer(
                chat_input.message, history_context, chat_input.file_info.model_dump() if chat_input.file_info else None
            )
        elif chat_input.mode == "personal_symptoms":
            if not chat_input.message: raise HTTPException(status_code=400, detail="Symptom description is required.")
            response_data_dict = await ai_handler.analyze_personal_symptoms(
                chat_input.message, history_context, chat_input.user_region
            )
        elif chat_input.mode == "personal_report_upload":
            if not chat_input.file_info: raise HTTPException(status_code=400, detail="File upload is required for report analysis.")
            response_data_dict = await ai_handler.analyze_uploaded_personal_report(
                chat_input.file_info.model_dump(), history_context, chat_input.user_region
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {chat_input.mode}")

        # Ensure all fields for ChatMessageOutput are present, defaulting if necessary
        final_output_data = {
            "answer": response_data_dict.get("answer", "No specific answer generated."),
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

        # Save to conversation history
        memory_handler.add_to_conversation_history(
            user_message=chat_input.message, # Original user text message
            ai_response=response_output.answer,
            mode=chat_input.mode,
            file_name=chat_input.file_info.name if chat_input.file_info else None
        )
        
        # Update medical history if relevant info extracted
        if response_data_dict.get("extracted_medical_info"):
            memory_handler.update_medical_history(response_data_dict["extracted_medical_info"])
            
        return response_output

    except HTTPException as e: # Re-raise HTTPExceptions
        raise e
    except Exception as e:
        print(f"Error in /chat endpoint: {e.__class__.__name__} - {str(e)}")
        import traceback
        traceback.print_exc() # For detailed server logs
        # Return a ChatMessageOutput compatible error
        return ChatMessageOutput(answer="Sorry, an unexpected server error occurred.", error=str(e))


@router.get("/history")
async def get_history():
    conv_history = memory_handler.get_conversation_history()
    med_history = memory_handler.get_medical_history()
    return {
        "conversation_history": conv_history,
        "medical_history": med_history
    }

@router.post("/history/clear")
async def clear_history():
    memory_handler.clear_all_history()
    return {"message": "All history has been cleared."}