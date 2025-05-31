import httpx, html, json, re, datetime
from typing import Dict, Any, Optional, List

from ..config import settings 
from ..api.models import AISchemeInfo, AIDoctorRecommendation, AIGraphData

ExtractedMedicalInfo = Dict[str, Any]

class AIInteractionHandler:
    def __init__(self):
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = settings.PERPLEXITY_API_BASE_URL

        self.qna_model = settings.QNA_MODEL
        self.symptom_model = settings.SYMPTOM_MODEL       

        if not self.api_key:
            print("AIInteractionHandler: CRITICAL - PERPLEXITY_API_KEY is not set.")

    async def _call_perplexity_api(
        self,
        system_prompt: str,
        user_prompt: str,
        model_name: str,
        max_tokens: int = 2048,
        temperature: float = 0.3,   
    ) -> str:
        if not self.api_key:
            return "Error: API Key not configured on the server."

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
            
            # "top_p": 0.9,
            # "frequency_penalty": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        timeout_duration = 180.0 # Increased timeout slightly

        print(f"--- Sending Request to Perplexity (ai_handler) ---")
        print(f"Model: {model_name}")
        

        try:
            async with httpx.AsyncClient(timeout=timeout_duration) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                response_data = response.json()

            if response_data.get("choices") and response_data["choices"][0].get("message"):
                content = response_data["choices"][0]["message"]["content"].strip()
                # Log usage if needed for tracking: print(f"Usage: {response_data.get('usage')}")
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
            import traceback; traceback.print_exc()
            return f"Error: An unexpected error occurred: {str(e)}"

    def _strip_think_blocks(self, text_with_thoughts: str) -> str:
        """Removes <think>...</think> blocks from text, case-insensitive, handles newlines."""
        if not text_with_thoughts: return ""
        # More robust: find JSON block after the LAST </think> tag, or the first JSON block if no think tags
        last_think_end = text_with_thoughts.rfind("</think>")
        if last_think_end != -1:
            candidate_text = text_with_thoughts[last_think_end + len("</think>"):]
        else:
            candidate_text = text_with_thoughts
        
        # Try to extract ```json ... ``` block first
        match_json_block = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", candidate_text, re.IGNORECASE | re.DOTALL)
        if match_json_block:
            print("Found ```json block after stripping/considering <think> tags.")
            return match_json_block.group(1).strip()

        # If no ```json block, try to find a raw JSON object
        match_raw_json = re.search(r"^\s*(\{[\s\S]*\})\s*$", candidate_text.strip(), re.DOTALL)
        if match_raw_json:
            print("Found raw JSON object after stripping/considering <think> tags.")
            return match_raw_json.group(1).strip()
            
        # Fallback: general <think> stripping if specific JSON extraction failed
        print("No clear JSON block found after </think> or as raw JSON. Performing general <think> stripping on original text.")
        return re.sub(r"<think>.*?</think>", "", text_with_thoughts, flags=re.DOTALL | re.IGNORECASE).strip()

    def _parse_ai_response_to_structured_output(self, raw_response_text: str, mode: str, model_used: str) -> Dict[str, Any]:
        

        # Initialize output structure with safe defaults
        output = {
            "answer": "AI response processing failed or was empty.", # Safe default
            "answer_format": "markdown",
            "follow_up_questions": None, "disease_identification": None, "next_steps": None,
            "government_schemes": None, "doctor_recommendations": None, "graphs_data": None,
            "error": None, "file_processed_with_message": None, "extracted_medical_info": {}
        }

        if not raw_response_text or raw_response_text.strip() == "":
            output["answer"] = "Error: AI returned an empty response."
            output["error"] = "AI returned an empty response."
            print(f"Final Parsed Output (empty raw response): {output}")
            return output
            
        if raw_response_text.startswith("Error:"): # If _call_perplexity_api itself returned an error string
            output["answer"] = raw_response_text
            output["error"] = raw_response_text
            print(f"Final Parsed Output (API call error): {output}")
            return output

        # If we reach here, raw_response_text has content and is not an error from our HTTP call function
        cleaned_response_text = self._strip_think_blocks(raw_response_text)
        print(f"CLEANED RESPONSE (after <think> strip, first 500 chars): {cleaned_response_text[:500]}")

        if not cleaned_response_text.strip():
            output["answer"] = "AI response was empty after processing internal thoughts."
            output["error"] = "AI response empty post-processing."
            print(f"Final Parsed Output (empty after think strip): {output}")
            return output
        
        # Default answer is now the cleaned text, which will be overwritten if JSON parsing is successful for structured modes
        output["answer"] = cleaned_response_text 

        if mode in ["personal_symptoms", "personal_report_upload"]:
            try:
                json_candidate = cleaned_response_text
                if cleaned_response_text.strip().startswith("```json"):
                    # Extract content within ```json ... ```
                    match = re.search(r"```json\s*([\s\S]*?)\s*```", cleaned_response_text, re.IGNORECASE)
                    if match:
                        json_candidate = match.group(1).strip()
                    else: # Fallback if ```json is present but no closing ``` or malformed
                        json_candidate = cleaned_response_text.split("```json", 1)[1].strip()
                
                # Only attempt to parse if it looks like a JSON object
                if not (json_candidate.strip().startswith("{") and json_candidate.strip().endswith("}")):
                    print(f"Warning: Expected JSON for mode '{mode}' but received non-JSON like text after stripping thoughts. Content snippet: {json_candidate[:200]}")
                    # output["answer"] is already set to cleaned_response_text, which is appropriate here.
                    # We might set an error note if strict JSON was absolutely required.
                    # output["error"] = f"AI did not return the expected JSON structure for {mode}."
                    print(f"Final Parsed Output (non-JSON for structured mode): {output}")
                    return output 

                print(f"JSON CANDIDATE for mode '{mode}' (first 500 chars): {json_candidate[:500]}")
                data = json.loads(json_candidate)
                print(f"Successfully parsed JSON from AI response for mode '{mode}'.")
                
                # Map AI's JSON keys to our output structure
                output["answer"] = data.get("answer_markdown", cleaned_response_text) # Prioritize answer_markdown from JSON
                output["follow_up_questions"] = data.get("follow_up_questions_list")
                output["disease_identification"] = data.get("disease_identification_text")
                output["next_steps"] = data.get("next_steps_list")
                # Ensure list comprehensions handle None gracefully if a key is missing
                output["government_schemes"] = [AISchemeInfo(**s) for s in data.get("government_schemes_list", []) if isinstance(s, dict)]
                output["doctor_recommendations"] = [AIDoctorRecommendation(**dr) for dr in data.get("doctor_recommendations_list", []) if isinstance(dr, dict)]
                output["graphs_data"] = [AIGraphData(**gd) for gd in data.get("graphs_data_list", []) if isinstance(gd, dict)]
                output["extracted_medical_info"] = data.get("extracted_medical_info_dict", {})
                
                # If 'answer_markdown' was missing but other specific answer keys exist in JSON
                if output["answer"] == cleaned_response_text and data.get("summary"):
                    output["answer"] = data.get("summary")
                elif output["answer"] == cleaned_response_text and data.get("answer"): # Generic 'answer' key in JSON
                    output["answer"] = data.get("answer")


            except json.JSONDecodeError as e:
                print(f"JSON PARSE FAILED for mode '{mode}': {e}. Content snippet: {cleaned_response_text[:200]}")
                # output["answer"] is already cleaned_response_text, which is the best we can do.
                output["error"] = f"AI response for {mode} was not valid JSON (after cleaning attempts)."
            except Exception as e_parse: # Catch other potential errors during mapping
                print(f"Error mapping parsed JSON to output structure for mode '{mode}': {e_parse}")
                output["error"] = f"Error processing AI's structured response for {mode}."
        
        elif mode == "qna": # QnA mode specific parsing for sources and follow-ups
            # The variable 'cleaned_response_text' is already the primary content for QnA at this point.
            # We will parse sections from it.
            
            text_for_qna_parsing = cleaned_response_text
            parsed_qna_answer = text_for_qna_parsing # Start with everything
            final_follow_ups = None
            final_sources_text = None

            # 1. Extract "Further Exploration:"
            further_explore_marker = "Further Exploration:"
            match_fe = re.search(f"^(.*?){re.escape(further_explore_marker)}(.*)", text_for_qna_parsing, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if match_fe:
                text_before_fe = match_fe.group(1).strip()
                further_exploration_content = match_fe.group(2).strip()
                if further_exploration_content:
                    suggestions = [s.strip() for s in re.split(r'\s*\n\s*|\s*-\s*(?=[A-Z])|\s*\d+\.\s*|\s*\?\s*|\s*;\s*', further_exploration_content) if s.strip() and len(s) > 5]
                    final_follow_ups = suggestions[:2]
                text_for_qna_parsing = text_before_fe # Update text for next parsing step

            # 2. Extract "## Sources:"
            sources_marker = "## Sources:"
            match_sources = re.search(f"^(.*?){re.escape(sources_marker)}(.*)", text_for_qna_parsing, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if match_sources:
                parsed_qna_answer = match_sources.group(1).strip()
                final_sources_text = match_sources.group(2).strip()
            else: # No sources marker found, the remaining text is the answer
                parsed_qna_answer = text_for_qna_parsing.strip()

            output["answer"] = parsed_qna_answer
            if final_sources_text:
                output["answer"] += f"\n\n---\n**Sources:**\n{final_sources_text}"
            elif sources_marker.lower() in cleaned_response_text.lower(): # Marker was there but no content after
                output["answer"] += f"\n\n---\n**Sources:**\nGeneral medical knowledge."
            
            if final_follow_ups:
                output["follow_up_questions"] = final_follow_ups
        
        # Fallback if parsing left answer empty but cleaned_response_text had content
        if not output["answer"].strip() and cleaned_response_text.strip():
             output["answer"] = cleaned_response_text
             output["error"] = "Internal parsing logic resulted in empty answer; showing cleaned AI response."


        print(f"Final Parsed Output for mode '{mode}': Answer snippet: {str(output.get('answer'))[:100]}..., Error: {output.get('error')}")
        return output
    
    async def get_general_qna_answer(self, question: str, history_context: str, file_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        system_prompt = (
            "You are 'sonar-pro', an expert AI Medical Information Assistant. Your goal is to provide comprehensive, accurate, and well-structured answers to medical questions. "
            "Your response MUST adhere to the following structure and guidelines:\n\n"
            "1.  **MAIN ANSWER (Markdown):** Provide a detailed, in-depth explanation. Use Markdown for clarity: \n"
            "    *   Headings (e.g., `## Key Aspects`, `### Treatment Options`).\n"
            "    *   Bullet points (`* item`) or numbered lists for categorizing information.\n"
            "    *   Bold text (`**important**`) for emphasis on key terms or concepts.\n"
            "    *   If the question implies numerical data, trends, or comparisons that can be visualized, try to present this information. If you can generate data suitable for a simple chart (bar, line, pie), or a simple table, include it as part of your main answer text first, then provide the structured data for it (see point 4).\n\n"
            "2.  **FILE CONTEXT:** If a file is mentioned in the user prompt (name and type will be provided), assume its content is relevant to the question and you have access to it. Integrate information from the file into your answer if applicable and the question pertains to interpreting or discussing it.\n\n"
            "3.  **CITATIONS & SOURCES:** DO NOT use inline bracketed numerical citations like [1] or [2]. Instead, if you use specific information from identifiable sources, mention the source NATURALLY within the text (e.g., 'According to the World Health Organization...' or 'A 2023 study published in The Journal of Medicine indicated...'). At the VERY END of your entire response (after any chart/table data and before 'Further Exploration'), include a dedicated section titled '## Sources:' followed by a Markdown bulleted list of any primary web sources, specific medical references (like publication titles or official health organization names) you used. If your answer is based on general medical knowledge without specific external documents for this query, state 'General medical knowledge.' under this 'Sources:' heading.\n\n"
            "4.  **DATA FOR VISUALIZATION (Optional - JSON for Charts/Tables):** If your textual answer describes data suitable for a simple chart or table, provide the structured data for it *after* the main textual answer but *before* the 'Sources:' section. Format this as a JSON string within a special block: `CHART_TABLE_DATA_BLOCK_START` followed by the JSON string on new lines, and then `CHART_TABLE_DATA_BLOCK_END`. The JSON should be an object with a key 'visualizations', which is a list of objects. Each object can be a 'chart' or a 'table'.\n"
            "    *   **For Charts:** `{'type': 'chart', 'chart_type': 'bar'|'line'|'pie', 'title': 'Chart Title', 'data': {'labels': ['A', 'B'], 'datasets': [{'label': 'Series1', 'data': [10, 20]}]}}`\n"
            "    *   **For Tables:** `{'type': 'table', 'title': 'Table Title', 'headers': ['Col1', 'Col2'], 'rows': [['R1C1', 'R1C2'], ['R2C1', 'R2C2']]}` (The AI should try to render the table in Markdown in the main answer; this JSON is for potential structured use by the client if needed, but focus is on charts for `graphs_data` output field).\n"
            "    If no data for visualization is generated, omit this entire CHART_TABLE_DATA_BLOCK.\n\n"
            "5.  **RELATED TOPICS/FOLLOW-UP SUGGESTIONS:** After the 'Sources:' section, on a new line, suggest ONE or TWO closely related follow-up questions or topics the user might find interesting. Start this section EXACTLY with: 'Further Exploration: '. Example: 'Further Exploration: You might want to learn about the different types of diabetes medication.'\n\n"
            "SAFETY & SCOPE: Politely decline if the question is outside the medical domain, seeks a definitive diagnosis (which you cannot provide as an AI), or if you cannot provide a safe or accurate answer. If declining, explain briefly why.\n"
            "CONTEXT: Consider the user's provided history for contextual understanding but do not explicitly repeat the history in your answer."
        )

        user_prompt_parts = [f"Relevant User History (for context only):\n{history_context}\n"]
        if file_info:
            file_summary = f"The user has also uploaded a file relevant to their question: '{file_info['name']}' (Type: '{file_info['type']}'). Please consider its content when answering."
            if file_info.get('content_base64'):
                try:
                    import base64
                    decoded_content = base64.b64decode(file_info['content_base64']).decode('utf-8', errors='ignore')
                    max_text_chars = 12000 
                    if len(decoded_content) > max_text_chars:
                        decoded_content = decoded_content[:max_text_chars] + "\n... (File content truncated in prompt due to length)"
                    file_summary += f"\n\nHere is the text content of the file for your analysis:\n\"\"\"\n{decoded_content}\n\"\"\""
                except Exception as e:
                    print(f"QnA: Error decoding file for prompt: {e}")
                    file_summary += "\n(Note: Could not decode file content for inclusion in this prompt snippet.)"
            user_prompt_parts.append(file_summary)
        user_prompt_parts.append(f"\nUser's Question: {question}")
        user_prompt = "\n".join(user_prompt_parts)

        # Call the API
        api_response_content = await self._call_perplexity_api(
            system_prompt, user_prompt, self.qna_model,
            temperature=0.3, 
            max_tokens=3000 
        )
        
        # Initialize output structure
        output = {
            "answer": api_response_content, # Default to full API response if parsing fails or not applicable
            "answer_format": "markdown", 
            "follow_up_questions": None, 
            "graphs_data": None, 
            "error": None,
            "file_processed_with_message": file_info.get("name") if file_info else None
        }

        # If the API call itself returned an error string, set it and return
        if api_response_content.startswith("Error:"):
            output["error"] = api_response_content
            output["answer"] = api_response_content # Display the API error as the primary answer
            return output

        # Proceed with parsing only if the API call was successful
        cleaned_response = self._strip_think_blocks(api_response_content)
        if not cleaned_response.strip(): # If stripping thoughts left nothing
            output["answer"] = "AI response was empty after processing."
            output["error"] = "AI response empty post-processing."
            return output

        current_text_to_parse = cleaned_response
        parsed_charts_list = []
        
        # 1. Extract and remove Chart/Table Data Blocks
        # We'll build the main answer text by removing these blocks first
        answer_parts_for_main_text = []
        last_block_end_index = 0
        chart_block_start_marker = "CHART_TABLE_DATA_BLOCK_START"
        chart_block_end_marker = "CHART_TABLE_DATA_BLOCK_END"

        # Iteratively find all chart/table blocks
        for match in re.finditer(f"{re.escape(chart_block_start_marker)}(.*?){re.escape(chart_block_end_marker)}", current_text_to_parse, flags=re.DOTALL):
            answer_parts_for_main_text.append(current_text_to_parse[last_block_end_index:match.start()])
            last_block_end_index = match.end()
            
            json_str_content = match.group(1).strip()
            try:
                chart_table_data = json.loads(json_str_content)
                if chart_table_data.get("visualizations") and isinstance(chart_table_data["visualizations"], list):
                    for viz_item in chart_table_data["visualizations"]:
                        if viz_item.get("type") == "chart":
                            try:
                                chart_obj = AIGraphData(
                                    type=viz_item.get("chart_type", "bar").lower(),
                                    title=viz_item.get("title", "Chart"),
                                    labels=viz_item.get("data", {}).get("labels", []),
                                    datasets=viz_item.get("data", {}).get("datasets", [])
                                )
                                parsed_charts_list.append(chart_obj)
                            except Exception as e_pydantic: # Catch Pydantic validation error
                                print(f"Error validating chart data structure: {e_pydantic}. Item: {viz_item}")
                        elif viz_item.get("type") == "table":
                            # AI was prompted to include tables in main Markdown.
                            # This JSON is for potential future structured use, not directly appended to answer here.
                            print(f"Table JSON block found: {viz_item.get('title')}") 
            except json.JSONDecodeError as e:
                print(f"Error parsing CHART_TABLE_DATA_BLOCK JSON: {e}. Content: {json_str_content[:200]}")
                answer_parts_for_main_text.append(f"\n[System Note: A chart/table data block was malformed and could not be processed.]\n")

        answer_parts_for_main_text.append(current_text_to_parse[last_block_end_index:]) # Add text after the last block
        text_after_chart_parsing = "".join(answer_parts_for_main_text).strip()

        if parsed_charts_list:
            output["graphs_data"] = parsed_charts_list

        # 2. Extract Further Exploration (from text_after_chart_parsing)
        current_text_for_sources = text_after_chart_parsing
        further_explore_marker = "Further Exploration:"
        # Using regex for case-insensitive split and to capture content after the marker
        match_further_explore = re.search(f"{re.escape(further_explore_marker)}(.*)", text_after_chart_parsing, flags=re.IGNORECASE | re.DOTALL)
        if match_further_explore:
            current_text_for_sources = text_after_chart_parsing[:match_further_explore.start()].strip() # Text before "Further Exploration:"
            further_exploration_section = match_further_explore.group(1).strip()
            if further_exploration_section:
                # Simple split for suggestions. More robust parsing might be needed if format varies.
                suggestions = [s.strip() for s in re.split(r'\s*\n\s*|\s*-\s*(?=[A-Z])|\s*\d+\.\s*|\s*\?\s*|\s*;\s*', further_exploration_section) if s.strip() and len(s) > 5]
                output["follow_up_questions"] = suggestions[:2] # Take up to 2
                print(f"Extracted QnA follow-up suggestions: {output['follow_up_questions']}")

        # 3. Extract Sources and set final Main Answer (from current_text_for_sources)
        sources_marker = "## Sources:"
        final_answer_text = current_text_for_sources
        
        # Using regex for case-insensitive split for sources marker
        match_sources = re.search(f"({re.escape(sources_marker)})(.*)", current_text_for_sources, flags=re.IGNORECASE | re.DOTALL)
        if match_sources:
            final_answer_text = current_text_for_sources[:match_sources.start()].strip() # Text before "## Sources:"
            sources_section_content = match_sources.group(2).strip() # Text after "## Sources:"
            
            output["answer"] = final_answer_text
            if sources_section_content:
                output["answer"] += f"\n\n---\n**Sources:**\n{sources_section_content}"
            else: # Marker present, but no content after it
                output["answer"] += f"\n\n---\n**Sources:**\nGeneral medical knowledge."
        else:
            output["answer"] = final_answer_text # No "## Sources:" section found

        # Final check: if answer ended up empty but original cleaned_response had content
        if not output["answer"].strip() and cleaned_response.strip():
            print("Warning: QnA parsing resulted in empty answer; falling back to full cleaned response (minus chart JSON).")
            output["answer"] = text_after_chart_parsing # Use text that had chart JSONs removed
            # Re-attempt to parse follow-ups from this text_after_chart_parsing if they weren't caught
            if not output["follow_up_questions"] and further_explore_marker.lower() in text_after_chart_parsing.lower():
                 match_fe_fallback = re.search(f"{re.escape(further_explore_marker)}(.*)", text_after_chart_parsing, flags=re.IGNORECASE | re.DOTALL)
                 if match_fe_fallback and match_fe_fallback.group(1).strip():
                    suggestions_fallback = [s.strip() for s in re.split(r'\s*\n\s*|\s*-\s*(?=[A-Z])|\s*\d+\.\s*|\s*\?\s*|\s*;\s*', match_fe_fallback.group(1).strip()) if s.strip() and len(s) > 5]
                    output["follow_up_questions"] = suggestions_fallback[:2]

        return output

        # ... (analyze_personal_symptoms and analyze_uploaded_personal_report methods as refined in previous steps)
        # ... (_strip_think_blocks as before)
        # ... (_parse_ai_response_to_structured_output for symptoms/report as before)


    
    async def analyze_personal_symptoms(self, symptoms_description: str, history_context: str, user_region: Optional[str]) -> Dict[str, Any]:
        system_prompt = (
        "You are 'sonar-reasoning-pro', an AI Medical Symptom Analyzer. Your goal is to provide helpful, general information, not a definitive diagnosis. "
        "If the user's symptom description is brief or vague, your PRIORITY is to ask 2-4 specific, clarifying follow-up questions to gather more details. "
        "Otherwise, provide a preliminary analysis. "
        "CRITICAL OUTPUT FORMAT: Respond ONLY with a single, valid JSON object string. DO NOT use any conversational filler before or after the JSON. "
        "The JSON object MUST have a top-level key 'answer_markdown' (string: this is where your main conversational analysis, explanations, follow-up questions if any, and any direct advice in Markdown format should go). "
        "Other top-level keys in the JSON object must be: "
        "'follow_up_questions_list' (list of strings: EITHER your clarifying questions if initial info is vague, OR null/empty if providing analysis in 'answer_markdown'), "
        "'disease_identification_text' (string: very tentative, e.g., 'Symptoms could align with common viral infections or stress-related issues. This is not a diagnosis.'), "
        "'next_steps_list' (list of strings: e.g., 'monitor symptoms', 'consult a GP'), "
        "'government_schemes_list' (list of objects, each with 'name':string, 'description':string, 'region_specific':string (optional), 'source_info':string (optional) - provide 1-2 relevant schemes if user_region is given), "
        "'doctor_recommendations_list' (list of objects, each with 'specialty':string, 'reason':string (optional), 'source_info':string (optional) - suggest specialties if symptoms warrant medical attention), "
        "'extracted_medical_info_dict' (object: e.g., {'current_symptoms_list': ['headache', 'fatigue'], 'potential_conditions_discussed_list': ['viral infection', 'stress']}). "
        "If symptoms describe an immediate emergency, 'answer_markdown' MUST strongly advise seeking urgent medical care, and other JSON fields can be null or empty lists. "
        "Any internal thought process or planning MUST be enclosed in <think>Your thought here</think> tags. These <think> tags can be anywhere in your response string *before* the final JSON output, but the JSON itself must be clean."
         )
        user_prompt = (f"Relevant User History (for context):\n{history_context}\n\n"
            f"User's Stated Region: {user_region or 'Not Specified'}\n\n"
            f"User's Described Symptoms: {symptoms_description}\n\n"
            "Please provide your analysis ONLY as a single JSON object string with the specified keys. If the symptoms are too vague, prioritize asking follow-up questions within the JSON structure.")
        raw_response = await self._call_perplexity_api(system_prompt, user_prompt, self.symptom_model, max_tokens=3000)
        # Parsing logic will strip <think> then try to parse JSON
        parsed_output = self._parse_ai_response_to_structured_output(raw_response, "personal_symptoms", self.symptom_model)
        # Ensure the 'answer' field in the final dict gets the 'answer_markdown' from the parsed JSON
        if isinstance(parsed_output.get("answer"), dict) and "answer_markdown" in parsed_output["answer"]: # Check if full JSON was put in answer
            parsed_output["answer"] = parsed_output["answer"]["answer_markdown"]
        elif isinstance(parsed_output.get("extracted_medical_info"), dict) and parsed_output.get("answer_markdown"): # If keys were parsed correctly
            parsed_output["answer"] = parsed_output.pop("answer_markdown") # Use specific key for main answer
        return parsed_output
    

