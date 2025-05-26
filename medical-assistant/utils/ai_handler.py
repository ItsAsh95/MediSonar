
import httpx
import json
from typing import Dict, Any, Optional, List

from ..config import settings
from ..api.models import AISchemeInfo, AIDoctorRecommendation, AIGraphData # For type hints

# Placeholder for extracted medical information structure from AI
ExtractedMedicalInfo = Dict[str, Any] # e.g., {"symptoms_history": ["headache"], "new_diagnosis": "migraine"}

class AIInteractionHandler:
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = settings.PERPLEXITY_API_BASE_URL
        if not self.api_key:
            print("AIInteractionHandler: PERPLEXITY_API_KEY is not set. AI calls will fail.")

    async def _call_perplexity_api(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.5
    ) -> str:
        if not self.api_key:
            return "Error: API Key not configured."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"Calling Perplexity API. Model: {model}. User prompt length: {len(user_prompt)}")
        async with httpx.AsyncClient(timeout=120.0) as client: # 2 min timeout for chatty calls
            try:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                
                if response_data.get("choices") and response_data["choices"][0].get("message"):
                    content = response_data["choices"][0]["message"]["content"].strip()
                    print(f"Perplexity response length: {len(content)}")
                    return content
                else:
                    error_msg = response_data.get("error", {}).get("message", "Unknown API response format.")
                    print(f"API Error (model: {model}): {error_msg} Full response: {response_data}")
                    return f"Error: AI API returned an error: {error_msg}"
            except httpx.HTTPStatusError as http_err:
                error_content = http_err.response.text[:500] # Limit error detail length
                print(f"HTTP error (model: {model}): {http_err} - Details: {error_content}")
                return f"Error: AI API request failed (HTTP {http_err.response.status_code})."
            except httpx.TimeoutException:
                print(f"API request timed out for model {model}.")
                return "Error: The AI API request timed out."
            except Exception as e:
                print(f"Generic error in _call_perplexity_api (model: {model}): {e.__class__.__name__} - {str(e)[:200]}")
                return f"Error: An unexpected error occurred: {str(e)[:100]}"

    def _parse_structured_ai_response(self, raw_response_text: str) -> Dict[str, Any]:
        """
        Attempts to parse a structured JSON-like string from the AI.
        This is a placeholder and needs robust implementation based on how you prompt the AI.
        Ideally, prompt Perplexity to return a JSON string.
        """
        parsed_data = {"answer": raw_response_text, "answer_format": "markdown"} # Default
        try:
            # A common pattern is for AI to wrap JSON in ```json ... ```
            if "```json" in raw_response_text:
                json_str_match = raw_response_text.split("```json", 1)[1].split("```", 1)[0]
                data = json.loads(json_str_match.strip())
                print("Successfully parsed JSON block from AI response.")
                # Ensure all expected keys from ChatMessageOutput are mapped or defaulted
                parsed_data["answer"] = data.get("answer_markdown", data.get("summary", raw_response_text))
                parsed_data["follow_up_questions"] = data.get("follow_up_questions")
                parsed_data["disease_identification"] = data.get("disease_identification")
                parsed_data["next_steps"] = data.get("next_steps")
                parsed_data["government_schemes"] = [AISchemeInfo(**s) for s in data.get("government_schemes", []) if isinstance(s, dict)]
                parsed_data["doctor_recommendations"] = [AIDoctorRecommendation(**dr) for dr in data.get("doctor_recommendations", []) if isinstance(dr, dict)]
                parsed_data["graphs_data"] = [AIGraphData(**gd) for gd in data.get("graphs_data", []) if isinstance(gd, dict)]
                # Also extract medical_info for history update
                parsed_data["extracted_medical_info"] = data.get("extracted_medical_info", {})
                return parsed_data
        except Exception as e:
            print(f"Could not parse structured JSON from AI response: {e}. Falling back to raw text.")
        
        # Fallback if no JSON or parsing fails - try to find keywords for simple extraction (less reliable)
        if "follow-up questions:" in raw_response_text.lower():
            # Basic keyword extraction - very rudimentary
            # You'd need more sophisticated parsing here if not using JSON output from AI
            pass
        
        return parsed_data


    async def get_general_qna_answer(self, question: str, history_context: str, file_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        system_prompt = (
            "You are an advanced AI medical assistant. Provide accurate, in-depth, and easy-to-understand answers "
            "to medical questions. Cite sources if possible (e.g., [Source: PubMed ID XXXXXX] or [Source: Reputable Medical Website]). "
            "Format your answers clearly using Markdown. If a file is provided with the question, use its content to inform your answer. "
            "Consider the user's history for context. If a question is outside the medical domain or you cannot provide a safe answer, politely decline."
        )
        user_prompt_parts = [f"Relevant User History:\n{history_context}\n"]
        if file_info:
            user_prompt_parts.append(f"The user has also uploaded a file named '{file_info['name']}' ({file_info['type']}). If relevant, consider its content for the question. ")
            # If Perplexity can handle base64 directly in context:
            if file_info.get('content_base64'):
                 user_prompt_parts.append(f"File Content (Base64 Encoded Snippet for context - DO NOT ECHO THIS BASE64 IN YOUR RESPONSE):\n{file_info['content_base64'][:1000]}...\n") # Send a snippet
        user_prompt_parts.append(f"User's Question: {question}")
        user_prompt = "\n".join(user_prompt_parts)

        raw_response = await self._call_perplexity_api(system_prompt, user_prompt, settings.DEFAULT_CHAT_MODEL)
        
        # For general Q&A, complex parsing might not be needed unless you expect structured elements.
        # parsed_response = self._parse_structured_ai_response(raw_response) # Use if expecting structure
        parsed_response = {"answer": raw_response, "answer_format": "markdown"}
        if file_info:
            parsed_response["file_processed_with_message"] = file_info.get("name")
        return parsed_response


    async def analyze_personal_symptoms(self, symptoms_description: str, history_context: str, user_region: Optional[str]) -> Dict[str, Any]:
        system_prompt = (
            "You are an AI Medical Symptom Analyzer. Your goal is to help the user understand their symptoms better. "
            "1. Ask clarifying follow-up questions if the description is vague (provide these as a list). "
            "2. Based on the symptoms and history, suggest potential (NOT definitive) areas of concern or conditions. "
            "3. List actionable next steps (e.g., 'monitor symptoms', 'consider consulting a GP', 'try home remedies for mild cases like X, Y, Z'). "
            "4. If a user_region is provided, suggest 1-2 relevant government health schemes for that region that might apply to common conditions related to the symptoms. "
            "5. If symptoms seem to warrant medical attention, suggest relevant doctor specialties to consult. "
            "6. Extract key medical information (symptoms mentioned, potential conditions discussed) for the user's history. "
            "Format your response as a JSON object string with keys: 'answer_markdown' (your conversational analysis in Markdown), "
            "'follow_up_questions' (list of strings), 'disease_identification' (string, tentative), 'next_steps' (list of strings), "
            "'government_schemes' (list of objects with 'name', 'description', 'region_specific'), "
            "'doctor_recommendations' (list of objects with 'specialty', 'reason'), "
            "'extracted_medical_info' (object with keys like 'current_symptoms_list', 'potential_conditions_list'). "
            "Politely decline if symptoms are too vague for any meaningful analysis even after considering follow-ups, or if they indicate an immediate emergency (advise seeking urgent care)."
        )
        user_prompt = (
            f"Relevant User History:\n{history_context}\n\n"
            f"User's Region: {user_region or 'Not Specified'}\n\n"
            f"User's Symptoms: {symptoms_description}\n\n"
            "Please provide your analysis in the specified JSON format."
        )
        raw_response = await self._call_perplexity_api(system_prompt, user_prompt, settings.SYMPTOM_ANALYSIS_MODEL)
        return self._parse_structured_ai_response(raw_response)


    async def analyze_uploaded_personal_report(self, file_info: Dict[str, Any], history_context: str, user_region: Optional[str]) -> Dict[str, Any]:
        # This requires Perplexity to understand the file content.
        # Sending base64 directly in the prompt is experimental and depends on model capabilities.
        # A more robust solution might involve extracting text from PDF/images first if this fails.
        file_content_for_prompt = "No textual content could be extracted or file is not text-based."
        if file_info.get('content_base64'):
            # This is a big assumption: that the model can "read" base64 and interpret it as a document.
            # It's better to extract text if possible, but for now, trying with base64.
            # We'll tell the model it's base64.
            # Max prompt sizes are a concern here. Send only a part for large files if it's just context.
            # If the entire file needs to be analyzed, this approach has limits.
            # For true "analysis", the model needs the full content.
            # Let's assume for now file_info['content_base64'] is the *actual text* if it was pre-processed
            # or we are gambling on the model's ability.
            file_content_for_prompt = f"The following is the Base64 encoded content of the file named '{file_info['name']}'. Please analyze it as a medical report: \n{file_info.get('content_base64', '')}"
            # A better approach if file is large: "The user has uploaded a file named X. Assume its content is available to you for analysis."
            # Then, if Perplexity has a way to "attach" files to a session, use that. Otherwise, it must be in the prompt.
            # For a hackathon, sending a large base64 string in the prompt is risky due to token limits.

        system_prompt = (
            "You are an AI Medical Report Analyzer. The user has uploaded their medical report. "
            "1. Summarize the key findings from the report. "
            "2. Explain any abnormalities or values outside normal ranges in simple terms. "
            "3. Suggest potential implications or areas of concern based on the findings. "
            "4. Provide actionable advice: lifestyle changes, precautions, or if specialist consultation is needed. "
            "5. If a user_region is provided, suggest 1-2 relevant government health schemes. "
            "6. If specialist consultation is advised, mention relevant doctor specialties. "
            "7. Extract key medical information for history (e.g., report name, key abnormal values, diagnoses mentioned). "
            "Format your response as a JSON object string with keys: 'answer_markdown', 'disease_identification', 'next_steps', "
            "'government_schemes', 'doctor_recommendations', 'graphs_data' (if any trends or values can be plotted simply from THIS report), "
            "'extracted_medical_info' (object with 'report_name', 'key_findings_list', 'abnormal_values_dict'). "
            "If the file content is uninterpretable or not a medical report, state that clearly."
        )
        user_prompt = (
            f"Relevant User History:\n{history_context}\n\n"
            f"User's Region: {user_region or 'Not Specified'}\n\n"
            f"Uploaded File Name: {file_info['name']} (Type: {file_info['type']})\n\n"
            f"File Content to Analyze (or context):\n{file_content_for_prompt[:15000]}\n\n" # Truncate to avoid huge prompts if base64
            "Please provide your analysis of this medical report in the specified JSON format."
        )
        raw_response = await self._call_perplexity_api(system_prompt, user_prompt, settings.REPORT_ANALYSIS_MODEL, max_tokens=4000) # Allow longer response for reports
        parsed_response = self._parse_structured_ai_response(raw_response)
        parsed_response["file_processed_with_message"] = file_info.get("name")
        # Add report name to extracted_medical_info if not already there
        if "extracted_medical_info" in parsed_response and isinstance(parsed_response["extracted_medical_info"], dict):
            if "report_name" not in parsed_response["extracted_medical_info"]:
                 parsed_response["extracted_medical_info"]["report_name"] = file_info['name']
            if "reports_analyzed_info" not in parsed_response["extracted_medical_info"]: # For MedicalMemory
                 parsed_response["extracted_medical_info"]["reports_analyzed_info"] = [{"name": file_info['name'], "findings_summary_placeholder": "Summary..."}]


        return parsed_response