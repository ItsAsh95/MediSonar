import httpx
import json
from typing import Dict, Any, Optional, List

from ..config import settings  # Relative import: .. means "go up one directory"
from ..api.models import AISchemeInfo, AIDoctorRecommendation, AIGraphData # .. then into api

# Placeholder for extracted medical information structure from AI
ExtractedMedicalInfo = Dict[str, Any]

class AIInteractionHandler:
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = settings.PERPLEXITY_API_BASE_URL

        # VERIFY THESE MODEL NAMES WITH PERPLEXITY DOCUMENTATION FOR YOUR API KEY
        self.qna_model = settings.DEFAULT_CHAT_MODEL # e.g., "sonar-small-chat" or "sonar-medium-chat"
        self.symptom_model = settings.SYMPTOM_ANALYSIS_MODEL # e.g., "sonar-medium-chat"
        self.personal_report_model = settings.REPORT_ANALYSIS_MODEL # e.g., "sonar-medium-chat" or a model good with context

        if not self.api_key:
            print("AIInteractionHandler: CRITICAL - PERPLEXITY_API_KEY is not set.")

    async def _call_perplexity_api(
        self,
        system_prompt: str,
        user_prompt: str,
        model_name: str,
        max_tokens: int = 2048, # Default, can be overridden
        temperature: float = 0.5 # Default, can be overridden
    ) -> str: # Returns the raw content string from the AI
        if not self.api_key:
            return "Error: API Key not configured on the server."

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        payload = {"model": model_name, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        timeout_duration = 120.0 # 2 minutes, adjust if needed for certain tasks

        # Debug logging (similar to services.py)
        print(f"--- Sending Request to Perplexity (ai_handler) ---")
        print(f"Model: {model_name}")
        # Avoid logging full payload in production if it contains sensitive prompt data
        # For debugging, this is fine:
        # print(f"Payload: {json.dumps(payload, indent=2)}")


        try:
            async with httpx.AsyncClient(timeout=timeout_duration) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
                response_data = response.json()

            if response_data.get("choices") and response_data["choices"][0].get("message"):
                content = response_data["choices"][0]["message"]["content"].strip()
                print(f"Raw response received from {model_name} (length: {len(content)} chars).")
                return content
            else:
                error_msg = response_data.get("error", {}).get("message", "Unknown API response format.")
                print(f"API Error (model: {model_name}): {error_msg} Full response: {json.dumps(response_data, indent=2)}")
                return f"Error: AI API returned an error: {error_msg}"
        except httpx.HTTPStatusError as http_err:
            error_content = "Unknown error"
            try:
                error_details = http_err.response.json()
                error_content = error_details.get("error", {}).get("message", http_err.response.text[:200])
            except json.JSONDecodeError:
                error_content = http_err.response.text[:200]
            print(f"HTTP error (model: {model_name}): {http_err} - Details: {error_content}")
            return f"Error: AI API request failed (HTTP {http_err.response.status_code}). Details: {error_content}"
        except httpx.TimeoutException:
            print(f"API request timed out for model {model_name} after {timeout_duration}s.")
            return "Error: The AI API request timed out. Please try again later."
        except httpx.RequestError as req_err:
            print(f"Request error (model: {model_name}): {req_err}")
            return f"Error: AI API request failed due to a network issue: {str(req_err)}"
        except Exception as e:
            print(f"Generic error in _call_perplexity_api (model: {model_name}): {e.__class__.__name__} - {e}")
            import traceback; traceback.print_exc() # For server logs
            return f"Error: An unexpected error occurred: {str(e)}"

    def _parse_ai_response_to_structured_output(self, raw_response_text: str, mode: str) -> Dict[str, Any]:
        """
        Attempts to parse AI's response into the ChatMessageOutput structure.
        If AI is prompted for JSON, it tries to parse JSON. Otherwise, it sets the answer field.
        """
        output = { # Defaults matching ChatMessageOutput Pydantic model
            "answer": "Could not understand AI response.", "answer_format": "markdown",
            "follow_up_questions": None, "disease_identification": None, "next_steps": None,
            "government_schemes": None, "doctor_recommendations": None, "graphs_data": None,
            "error": None, "file_processed_with_message": None, "extracted_medical_info": {}
        }

        if raw_response_text.startswith("Error:"):
            output["answer"] = raw_response_text
            output["error"] = raw_response_text
            return output

        try:
            # Check if the response is intended to be JSON (e.g., from symptom or report analysis modes)
            # A common pattern is AI wrapping JSON in ```json ... ``` or just returning a JSON string.
            json_candidate = raw_response_text
            if raw_response_text.strip().startswith("```json"):
                json_candidate = raw_response_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif raw_response_text.strip().startswith("{") and raw_response_text.strip().endswith("}"):
                json_candidate = raw_response_text.strip()

            data = json.loads(json_candidate)
            print("Successfully parsed JSON from AI response.")
            
            # Map known keys from AI's JSON to our ChatMessageOutput structure
            output["answer"] = data.get("answer_markdown", data.get("summary", "AI provided structured data but no primary answer text."))
            output["follow_up_questions"] = data.get("follow_up_questions")
            output["disease_identification"] = data.get("disease_identification")
            output["next_steps"] = data.get("next_steps")
            output["government_schemes"] = [AISchemeInfo(**s) for s in data.get("government_schemes", []) if isinstance(s, dict)]
            output["doctor_recommendations"] = [AIDoctorRecommendation(**dr) for dr in data.get("doctor_recommendations", []) if isinstance(dr, dict)]
            output["graphs_data"] = [AIGraphData(**gd) for gd in data.get("graphs_data", []) if isinstance(gd, dict)]
            output["extracted_medical_info"] = data.get("extracted_medical_info", {})
            
            # If answer_markdown was not present, but a general 'answer' or 'response' key is
            if output["answer"] == "AI provided structured data but no primary answer text.":
                if data.get("answer"): output["answer"] = data.get("answer")
                elif data.get("response"): output["answer"] = data.get("response")


        except json.JSONDecodeError:
            print(f"AI response for mode '{mode}' was not valid JSON. Treating as markdown/text.")
            output["answer"] = raw_response_text # Default to the whole text as answer
        except Exception as e:
            print(f"Error parsing AI response structure: {e}. Using raw text.")
            output["answer"] = raw_response_text
            output["error"] = f"Error processing AI response structure: {str(e)}"
            
        return output

    async def get_general_qna_answer(self, question: str, history_context: str, file_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        system_prompt = (
            "You are an AI Medical Assistant. Provide accurate, in-depth, and easy-to-understand answers to medical questions. "
            "Format your main answer using Markdown for clarity (e.g., use headings, lists, bold text where appropriate). "
            "If a file is provided with the question, its name and type will be mentioned. Assume you have access to its content if relevant, and incorporate it into your answer if applicable. "
            "Politely decline to answer if the question is outside the medical domain, seeks a definitive diagnosis (which you cannot provide), or if you cannot provide a safe or accurate answer. "
            "Consider the user's relevant history for context."
        )
        user_prompt_parts = [f"Relevant User History (for context only, do not repeat it in your answer):\n{history_context}\n"]
        if file_info:
            user_prompt_parts.append(f"The user has also uploaded a file: '{file_info['name']}' (Type: '{file_info['type']}'). If this file is relevant to the question, please consider its content. For example, if the question is about interpreting this file. Assume the file content is available to you if you need it.\n")
            # Note: Actually sending file content for QnA mode needs careful consideration of token limits.
            # For now, we're just informing the AI about the file. If it needs the content, it would have to be explicitly provided.
            # For a simple QnA, we assume the question is about the file, not requiring full file analysis here.
        user_prompt_parts.append(f"User's Question: {question}")
        user_prompt = "\n".join(user_prompt_parts)

        raw_response = await self._call_perplexity_api(system_prompt, user_prompt, self.qna_model)
        
        # General Q&A typically doesn't return complex structured JSON unless specifically prompted for it.
        output = self._parse_ai_response_to_structured_output(raw_response, "qna")
        if file_info:
            output["file_processed_with_message"] = file_info.get("name")
        return output


    async def analyze_personal_symptoms(self, symptoms_description: str, history_context: str, user_region: Optional[str]) -> Dict[str, Any]:
        system_prompt = (
            "You are an AI Medical Symptom Analyzer. Your goal is to provide helpful, general information, not a diagnosis. "
            "Based on the user's symptoms, history, and region: "
            "1. Identify potential areas of concern or common conditions that *might* be related (be very clear this is not a diagnosis). "
            "2. Suggest 2-3 clarifying follow-up questions the user could consider. "
            "3. List actionable, general next steps (e.g., 'monitor symptoms closely', 'consider consulting a General Practitioner', 'try general home care for mild symptoms like rest and hydration'). "
            "4. If user_region is provided, list 1-2 relevant public health schemes or resources in that region that *could* be helpful for common conditions (do not imply the user has these conditions). "
            "5. If symptoms seem to strongly suggest needing medical attention, recommend consulting specific doctor specialties. "
            "6. Prepare a small summary of key medical information derived from this interaction for the user's record. "
            "IMPORTANT: Respond ONLY with a single, valid JSON object string. The JSON object should have these top-level keys: "
            "'answer_markdown' (string: your conversational analysis and explanation in Markdown), "
            "'follow_up_questions' (list of strings), "
            "'disease_identification' (string: very tentative, e.g., 'Could be related to viral infections or stress. Not a diagnosis.'), "
            "'next_steps' (list of strings), "
            "'government_schemes' (list of objects, each with 'name':string, 'description':string, 'region_specific':string (optional, e.g., 'National' or state name)), "
            "'doctor_recommendations' (list of objects, each with 'specialty':string, 'reason':string (optional)), "
            "'extracted_medical_info' (object: e.g., {'current_symptoms_list': ['headache', 'fatigue'], 'potential_conditions_discussed_list': ['viral infection', 'stress']}). "
            "If symptoms are too vague or indicate an emergency, the 'answer_markdown' should advise seeking appropriate medical attention immediately and other JSON fields can be null or empty lists."
        )
        user_prompt = (
            f"Relevant User History (for context):\n{history_context}\n\n"
            f"User's Stated Region: {user_region or 'Not Specified'}\n\n"
            f"User's Described Symptoms: {symptoms_description}\n\n"
            "Please provide your analysis ONLY as a single JSON object string with the specified keys."
        )
        raw_response = await self._call_perplexity_api(system_prompt, user_prompt, self.symptom_model, max_tokens=3000) # Allow more tokens for JSON
        return self._parse_ai_response_to_structured_output(raw_response, "personal_symptoms")


    async def analyze_uploaded_personal_report(self, file_info: Dict[str, Any], history_context: str, user_region: Optional[str]) -> Dict[str, Any]:
        # This assumes Perplexity can analyze the content if provided.
        # For large files, sending full base64 is problematic.
        # A better long-term solution for large files would be an API that accepts file IDs after upload,
        # or a model specifically fine-tuned for document QA with a mechanism to provide the document.
        # For now, we'll send the base64 content and explicitly tell the AI it's base64.
        
        file_content_prompt_segment = "User did not provide file content, or it could not be processed."
        if file_info.get('content_base64'):
            # Truncate if too long to prevent exceeding token limits in the prompt itself.
            # This is a major limitation if the whole document needs analysis.
            # Perplexity models have context windows (e.g., 4k, 8k, 32k tokens).
            # Base64 is ~33% larger than original binary. Text is ~1 token per 4 chars.
            # Example: 100KB text is ~25k tokens. Its base64 is ~133KB.
            # Max reasonable base64 string length in prompt might be only a few thousand chars.
            max_b64_chars_in_prompt = 10000 # Arbitrary limit for prompt, roughly 2.5k tokens for base64 itself
            b64_content = file_info['content_base64']
            if len(b64_content) > max_b64_chars_in_prompt:
                b64_snippet = b64_content[:max_b64_chars_in_prompt] + "... (content truncated)"
                file_content_prompt_segment = (
                    f"The following is a TRUNCATED Base64 encoded snippet of the file content for context. "
                    f"The full file cannot be included due to length constraints. Analyze based on this snippet if possible, "
                    f"or indicate if full content is needed and cannot be processed this way:\n{b64_snippet}"
                )
            else:
                file_content_prompt_segment = (
                    f"The following is the Base64 encoded content of the uploaded file. "
                    f"Please analyze it as a medical report:\n{b64_content}"
                )
        
        system_prompt = (
            "You are an AI Medical Report Analyzer. The user has uploaded their medical report. "
            "Your task is to analyze the provided content. "
            "1. Summarize key findings. Explain abnormalities or values outside normal ranges in simple terms. "
            "2. Suggest potential implications. "
            "3. Provide actionable advice (lifestyle, precautions, specialist consultation). "
            "4. If user_region is provided, list 1-2 relevant government health schemes. "
            "5. If specialist consultation is advised, mention relevant doctor specialties. "
            "6. Note any data that could be plotted (e.g., a series of lab values over time, if present *in this single report*) and provide it if simple. "
            "7. Prepare a summary for the user's medical record. "
            "IMPORTANT: Respond ONLY with a single, valid JSON object string. The JSON object should have these top-level keys: "
            "'answer_markdown' (string: your detailed analysis in Markdown), "
            "'disease_identification' (string: tentative findings, e.g., 'Elevated liver enzymes noted.'), "
            "'next_steps' (list of strings), "
            "'government_schemes' (list of objects: 'name', 'description', 'region_specific'), "
            "'doctor_recommendations' (list of objects: 'specialty', 'reason'), "
            "'graphs_data' (list of graph objects: 'type', 'title', 'labels', 'datasets' (list of {'label':string, 'data':list_of_numbers})), "
            "'extracted_medical_info' (object: 'report_name', 'key_findings_list', 'abnormal_values_dict', 'potential_diagnoses_mentioned_list'). "
            "If the file content is uninterpretable, not a medical report, or too truncated for meaningful analysis, state that in 'answer_markdown'."
        )
        user_prompt = (
            f"Relevant User History (for context):\n{history_context}\n\n"
            f"User's Stated Region: {user_region or 'Not Specified'}\n\n"
            f"Uploaded File Information: Name='{file_info['name']}', Type='{file_info['type']}', Size (bytes)='{file_info['size']}'.\n\n"
            f"File Content Context:\n{file_content_prompt_segment}\n\n"
            "Please provide your analysis of this medical report ONLY as a single JSON object string with the specified keys."
        )

        # This task might require a model with a larger context window and more tokens for the response.
        raw_response = await self._call_perplexity_api(system_prompt, user_prompt, self.personal_report_model, max_tokens=3500, temperature=0.3)
        parsed_response = self._parse_ai_response_to_structured_output(raw_response, "personal_report_upload")
        
        parsed_response["file_processed_with_message"] = file_info.get("name")
        # Ensure extracted_medical_info has report name
        if isinstance(parsed_response.get("extracted_medical_info"), dict):
            parsed_response["extracted_medical_info"]["report_name"] = file_info['name']
            # For MedicalMemory to store structured report info:
            parsed_response["extracted_medical_info"]["reports_analyzed_info"] = [{
                "name": file_info['name'],
                "findings_summary_placeholder": parsed_response.get("answer", "Analysis performed.")[:100] # Brief summary
            }]
        else: # Initialize if missing
            parsed_response["extracted_medical_info"] = {
                "report_name": file_info['name'],
                "reports_analyzed_info": [{"name": file_info['name'], "findings_summary_placeholder": "Analysis performed."[:100]}]
            }
            
        return parsed_response