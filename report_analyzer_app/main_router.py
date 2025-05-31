from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse # To serve index.html at root
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
import os
import shutil
import uuid
import json
import re 
from openai import OpenAI 
from pydantic import BaseModel
from PIL import Image 
import PyPDF2 
import base64 

PROJECT_ROOT_FOR_ENV = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT_FOR_ENV / '.env'

# --- App Setup ---
app = FastAPI(title="Medical Report Analysis", version="2.3")

router = APIRouter(
    prefix="/report-analyzer", 
    tags=["Medical Report Analyzer Application (Integrated)"]
)

APP_BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = APP_BASE_DIR / "uploads_report_app" # Namespaced
RESULTS_DIR = APP_BASE_DIR / "results_report_app" # Namespaced
STATIC_DIR = APP_BASE_DIR / "static" # For this app's HTML, CSS, JS

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)



API_KEY: str = os.getenv('PERPLEXITY_API_KEY')



# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


# In-memory database for demo purposes
analysis_results: Dict[str, Dict[str, Any]] = {}

# --- Pydantic Models (Your existing models) ---
class Parameter(BaseModel):
    name: str
    value: str
    reference_range: Optional[str] = "N/A"
    status: Optional[str] = "unknown" # React code uses 'normal', 'abnormal', 'borderline'
    significance: Optional[str] = None

class Abnormality(BaseModel):
    parameter_name: str # React uses 'parameter'
    description: str    # React uses 'finding'
    observed_value: Optional[str] = "N/A" # Not directly in React's ProcessedAnalysis but good to have
    estimated_severity: Optional[str] = "unknown" # React uses 'severity' ('mild', 'moderate', 'severe')
    recommendation: Optional[str] = "Consult healthcare provider." # React has this

class StructuredAnalysis(BaseModel):
    overall_status: str 
    summary: str        
    parameters: List[Parameter]
    abnormalities: List[Abnormality]
    recommendations: List[str] 
    follow_up: str             
    other_details: Optional[List[str]] = None

class AnalysisResult(BaseModel):
    id: str
    file_name: str
    upload_date: str
    summary: str
    detailed_analysis: str 
    structured_data: Optional[StructuredAnalysis] = None
    follow_up_recommendations: Optional[str] = None

OPENAI_COMPATIBLE_API_KEY_FOR_REPORTS = os.getenv('PERPLEXITY_API_KEY') 
OPENAI_COMPATIBLE_BASE_URL_FOR_REPORTS = os.getenv('PERPLEXITY_API_BASE_URL', "https://api.perplexity.ai/chat/completions")
MODEL_FOR_REPORTS_ROUTER_SVC = os.getenv('REPORT_APP_AI_MODEL', "sonar-pro")

openai_client_for_reports = None



# --- File Processing Functions (Your existing functions: extract_text_from_file, image_to_base64_data_uri) ---
def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Extract text from files - skip OCR for images.
    Returns actual text for text/pdf, or special marker strings for images/errors.
    """
    print(f"DEBUG: EXTRACT: Processing file: {file_path}, type: {file_type}")
    try:
        file_extension = file_type.lower()
        if file_extension not in ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif', 'webp']:
            if not os.path.exists(file_path):
                print(f"ERROR: EXTRACT: File does not exist: {file_path}")
                return f"ERROR:FILE_NOT_FOUND:{file_path}"

        if file_extension == 'pdf':
            if not os.path.exists(file_path): 
                print(f"ERROR: EXTRACT: PDF file does not exist: {file_path}")
                return f"ERROR:FILE_NOT_FOUND:{file_path}"
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                if not pdf_reader.pages:
                    print(f"DEBUG: EXTRACT: PDF file {file_path} has no pages or is empty.")
                    return "" 
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text: text_parts.append(page_text)
                result = "\n".join(text_parts).strip()
                print(f"DEBUG: EXTRACT: PDF extracted {len(result)} characters")
                return result
        
        elif file_extension in ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif', 'webp']:
            print(f"DEBUG: EXTRACT: Image file detected ({file_extension}) - will use AI vision")
            if not os.path.exists(file_path):
                print(f"ERROR: EXTRACT: Image file does not exist: {file_path}")
                return f"ERROR:IMAGE_FILE_NOT_FOUND:{file_path}"
            try:
                with Image.open(file_path) as img: img.verify() 
            except Exception as img_error:
                print(f"ERROR: EXTRACT: Cannot open or verify image: {img_error}")
                return f"ERROR:INVALID_IMAGE:{file_path}:{str(img_error)}"
            return f"IMAGE_FILE:{file_path}"
        
        elif file_extension in ['txt', 'rtf', 'md', 'csv', 'json', 'xml', 'html', 'py', 'js', 'css']:
            print(f"DEBUG: EXTRACT: Text-based file ({file_extension})")
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
            for enc in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=enc) as file: content = file.read().strip()
                    print(f"DEBUG: EXTRACT: Text file extracted {len(content)} characters using {enc}")
                    return content
                except UnicodeDecodeError: print(f"DEBUG: EXTRACT: Failed to decode {file_path} with {enc}")
                except Exception as e_read: print(f"ERROR: EXTRACT: Error reading text file {file_path} with {enc}: {e_read}")
            print(f"ERROR: EXTRACT: Could not decode text file {file_path} with any attempted encoding.")
            return f"ERROR:TEXT_FILE_DECODE_ERROR:{file_path}"

        else: 
            print(f"DEBUG: EXTRACT: Attempting to read unknown format '{file_extension}' as text")
            if not os.path.exists(file_path):
                 print(f"ERROR: EXTRACT: Unknown file does not exist: {file_path}")
                 return f"ERROR:FILE_NOT_FOUND:{file_path}"
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file: result = file.read().strip()
                print(f"DEBUG: EXTRACT: Unknown format extracted {len(result)} characters (UTF-8, errors ignored)")
                return result
            except Exception as e_unknown:
                print(f"ERROR: EXTRACT: Could not read unknown file {file_path} as text: {str(e_unknown)}")
                return f"ERROR:UNKNOWN_FILE_READ_ERROR:{file_path}:{str(e_unknown)}"
    except Exception as e_general:
        print(f"ERROR: EXTRACT: General exception for {file_path}, type {file_type}: {str(e_general)}")
        return f"ERROR:GENERAL_EXTRACTION_ERROR:{str(e_general)}"

def image_to_base64_data_uri(image_path: str) -> str | None:
    try:
        image_extension = os.path.splitext(image_path)[1].lower().lstrip('.')
        if image_extension == "jpg": image_format = "jpeg"
        elif image_extension in ["png", "jpeg", "gif", "webp"]: image_format = image_extension
        else:
            print(f"WARN: IMAGE_ENCODE: Unknown image extension '{image_extension}'. Using it directly.")
            image_format = image_extension
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/{image_format};base64,{encoded_string}"
    except FileNotFoundError: print(f"ERROR: IMAGE_ENCODE: Image file not found: {image_path}"); return None
    except Exception as e: print(f"ERROR: IMAGE_ENCODE: Could not encode image {image_path} to base64: {str(e)}"); return None


# --- AI Interaction and Parsing (Your existing functions: parse_structured_analysis, analyze_report_with_ai) ---
def parse_structured_analysis(ai_response: str) -> StructuredAnalysis:
    """
    Parses AI response that is expected to have specific headings for different sections.
    """
    print("DEBUG: PARSE_NL_SECTIONS: Attempting to parse AI response with new section headings.")
    
    summary_text = "Summary not provided or section not found."
    parameters_list: List[Parameter] = []
    abnormalities_list: List[Abnormality] = []
    recommendations_list: List[str] = ["Consult healthcare provider."]
    follow_up_text = "Follow standard medical advice."
    other_details_list: List[str] = []
    overall_status_text = 'unknown'

    summary_match = re.search(r'GENERAL_SUMMARY:(.*?)(?=IDENTIFIED_PARAMETERS:|OBSERVED_ABNORMALITIES:|GENERAL_RECOMMENDATIONS:|$)', ai_response, re.IGNORECASE | re.DOTALL)
    if summary_match:
        extracted_summary = summary_match.group(1).strip()
        if extracted_summary: summary_text = extracted_summary

    param_section_match = re.search(r'IDENTIFIED_PARAMETERS:(.*?)(?=OBSERVED_ABNORMALITIES:|GENERAL_SUMMARY:|GENERAL_RECOMMENDATIONS:|$)', ai_response, re.IGNORECASE | re.DOTALL)
    if param_section_match:
        param_section_text = param_section_match.group(1).strip()
        param_line_pattern = re.compile(
            r'^\s*[-*]?\s*'                                                                
            r'(?P<name>[A-Za-z][A-Za-z0-9\s/\-().%μLmkIU/dLgmnp]*?):\s*'                        
            r'(?P<value>[0-9.,<>]+\s*[\w/%μLmkIU/dLgmnp]*)'                                    
            r'(?:\s*\((?P<ref_info>[^)]*)\))?'                                                 
            r'(?:\s*-\s*(?P<status_text>[A-Za-z\s]+))?',                                       
            re.IGNORECASE
        )
        for line in param_section_text.split('\n'):
            line = line.strip(); 
            if not line: continue
            match = param_line_pattern.match(line)
            if match:
                data = match.groupdict(); name = data['name'].strip()
                if name.lower() == "reference":
                    other_details_list.append(f"Skipped 'Reference' as param name (NL Parse): {line}"); continue
                value_str = data['value'].strip()
                ref_range_str = "N/A"; raw_ref_info = data.get('ref_info')
                if raw_ref_info:
                    raw_ref_info = raw_ref_info.strip()
                    ref_match_prefix = re.match(r'(?:Reference Range|Reference|Normal):\s*(.*)', raw_ref_info, re.IGNORECASE)
                    if ref_match_prefix: ref_range_str = ref_match_prefix.group(1).strip()
                    elif raw_ref_info: ref_range_str = raw_ref_info
                    if not ref_range_str or ref_range_str.lower() in ["not specified", "na", "n/a", ""]: ref_range_str = "Not specified"
                
                current_status = "unknown"; raw_status_text = data.get('status_text')
                if raw_status_text:
                    status_text_cleaned = raw_status_text.strip().lower()
                    if any(s in status_text_cleaned for s in ['high', 'low', 'abnormal', 'elevated', 'decreased', 'positive', 'critical', 'outside range', 'out of range']): current_status = 'abnormal'
                    elif 'borderline' in status_text_cleaned: current_status = 'borderline'
                    elif 'normal' in status_text_cleaned or 'within range' in status_text_cleaned : current_status = 'normal'
                
                if current_status in ["unknown", "normal"] and ref_range_str not in ["N/A", "Not specified"]:
                    try: 
                        val_numeric_match = re.match(r'([<>]?\s*[0-9.]+)', value_str)
                        if val_numeric_match:
                            val_num_part = val_numeric_match.group(1); is_less_than = '<' in val_num_part; is_greater_than = '>' in val_num_part
                            val_float = float(val_num_part.replace('<','').replace('>','').strip())
                            range_parts_match = re.match(r'([0-9.]+)\s*-\s*([0-9.]+)', ref_range_str)
                            if range_parts_match:
                                low_ref, high_ref = float(range_parts_match.group(1)), float(range_parts_match.group(2))
                                if (not is_less_than and val_float < low_ref) or (not is_greater_than and val_float > high_ref): current_status = 'abnormal'
                                elif current_status == "unknown": current_status = 'normal'
                    except ValueError: pass
                parameters_list.append(Parameter(name=name, value=value_str, reference_range=ref_range_str, status=current_status))
            elif not (line.lower().strip() == "reference" or line.lower().strip() == "reference:"):
                if line.strip(): other_details_list.append(f"Unmatched in IDENTIFIED_PARAMETERS: {line}")
    else:
        print("WARN: PARSE_NL_SECTIONS: IDENTIFIED_PARAMETERS section not found.")

    abnorm_section_match = re.search(r'OBSERVED_ABNORMALITIES:(.*?)(?=GENERAL_SUMMARY:|GENERAL_RECOMMENDATIONS:|$)', ai_response, re.IGNORECASE | re.DOTALL)
    if abnorm_section_match:
        abnorm_text = abnorm_section_match.group(1).strip()
        potential_abnorm_entries = abnorm_text.split('\n') 
        for entry_raw in potential_abnorm_entries:
            entry = entry_raw.strip()
            if not entry: continue
            if entry.startswith(('-', '*')): entry = entry[1:].strip() 

            match_param_colon = re.match(r'([A-Za-z][A-Za-z0-9\s/\-()]{2,})\s*:\s*(.+)', entry)
            match_param_is = re.match(r'([A-Za-z][A-Za-z0-9\s/\-()]{2,})\s+(?:is|are|shows|was|were)\s+(.+)', entry, re.IGNORECASE)
            
            param_name = None; description = None; recommendation_text = "Consult healthcare provider for detailed evaluation." # Default

            if match_param_colon:
                param_name = match_param_colon.group(1).strip()
                description = match_param_colon.group(2).strip()
            elif match_param_is:
                param_name = match_param_is.group(1).strip()
                description = match_param_is.group(2).strip()
            else: 
                if len(entry) > 10: 
                    param_name = "General Observation"
                    description = entry
                else:
                    other_details_list.append(f"Unparsed short line in OBSERVED_ABNORMALITIES: {entry}")
                    continue
            
            if param_name and param_name.lower() == "reference": continue 

            severity = "unknown"; observed_value_str = "N/A"
            desc_lower = description.lower()
            if "severe" in desc_lower or "significantly" in desc_lower or "markedly" in desc_lower: severity = "severe"
            elif "moderate" in desc_lower: severity = "moderate"
            elif "mild" in desc_lower or "slight" in desc_lower: severity = "mild"

            obs_val_match = re.search(r'([<>]?\s*[0-9.,]+\s*[\w/%μLmkIU/dLgmnp]+)', description)
            if obs_val_match: observed_value_str = obs_val_match.group(1).strip()
            
            # Try to extract recommendation if present in the description
            rec_match = re.search(r'(?:Recommendation|Suggests|Consider|Advise[ds]?):\s*(.+)', description, re.IGNORECASE)
            if rec_match:
                recommendation_text = rec_match.group(1).strip()
                # Remove the recommendation part from the main description
                description = description.split(rec_match.group(0))[0].strip()


            cleaned_description = description
            cleaned_description = re.sub(r'\.\s*This indicates.*$', '.', cleaned_description, flags=re.IGNORECASE) 
            cleaned_description = re.sub(r'\s*\((mild|moderate|severe|unknown|low|high|abnormal|normal)\)', '', cleaned_description, flags=re.IGNORECASE).strip()
            if not cleaned_description.endswith('.'): cleaned_description += "."
            
            if param_name: # Ensure param_name is not None
                abnormalities_list.append(Abnormality(
                    parameter_name=param_name,
                    description=cleaned_description,
                    observed_value=observed_value_str,
                    estimated_severity=severity,
                    recommendation=recommendation_text
                ))
    else:
        print("WARN: PARSE_NL_SECTIONS: OBSERVED_ABNORMALITIES section not found.")

    rec_section_match = re.search(r'GENERAL_RECOMMENDATIONS:(.*?)(?=GENERAL_SUMMARY:|OBSERVED_ABNORMALITIES:|IDENTIFIED_PARAMETERS:|$)', ai_response, re.IGNORECASE | re.DOTALL)
    if rec_section_match:
        rec_text = rec_section_match.group(1).strip()
        extracted_recs = [line.strip('-* ') for line in rec_text.split('\n') if line.strip().startswith(('-', '*')) and line.strip('-* ') and len(line.strip('-* ')) > 10]
        if extracted_recs: recommendations_list = extracted_recs
        elif rec_text and len(rec_text) > 10 : recommendations_list = [rec_text] 
    else:
        print("WARN: PARSE_NL_SECTIONS: GENERAL_RECOMMENDATIONS section not found.")

    follow_up_text = "Consult with healthcare provider for further guidance." 

    has_abnormal = any(p.status == 'abnormal' for p in parameters_list) or \
                   any(p.status == 'borderline' for p in parameters_list) or \
                   len(abnormalities_list) > 0
    
    # Check for "Attention Required" keywords in summary to influence overall_status
    attention_keywords = ['abnormal', 'elevated', 'decreased', 'concerning', 'requires attention', 'follow-up needed', 'investigation']
    summary_lower = summary_text.lower()
    needs_attention_from_summary = any(keyword in summary_lower for keyword in attention_keywords)

    if has_abnormal or needs_attention_from_summary:
        overall_status_text = 'abnormal' # Could be 'attention_needed' from React logic
    else:
        overall_status_text = 'normal'

    if not parameters_list and not abnormalities_list and summary_text.startswith("Summary not provided"):
        overall_status_text = 'nodata'

    # React code has 'overall_status' as 'normal' | 'abnormal' | 'attention_needed'
    # We will use 'normal' and 'abnormal' for now, client can adapt.
    # The client side `processAnalysisText` will use these server-side parsed fields.

    print(f"DEBUG: PARSE_NL_SECTIONS: Parsed {len(parameters_list)} params, {len(abnormalities_list)} abnorms. {len(other_details_list)} other details. Overall: {overall_status_text}")
    return StructuredAnalysis(
        overall_status=overall_status_text, summary=summary_text, parameters=parameters_list,
        abnormalities=abnormalities_list, recommendations=recommendations_list,
        follow_up=follow_up_text, other_details=other_details_list if other_details_list else None
    )


async def analyze_report_with_ai(content_input: Any, file_name: str) -> Dict:
    print(f"DEBUG: AI_ANALYZE (Simplified NL Prompt): Analyzing {file_name}. Input type: {type(content_input)}")
    try:
        if not API_KEY or "pplx-" not in API_KEY : 
             print("ERROR: AI_ANALYZE: Perplexity API key not configured or invalid.")
             raise ValueError("Perplexity API key not configured or invalid.")

        client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")
        
        system_prompt = """You are a medical AI assistant. Your primary task is to accurately transcribe and list medical parameters and identify abnormalities from the provided report content (text or image).

TASK:
1.  If the input is an image, first transcribe ALL visible text as accurately as possible, especially tables and lists of lab parameters. Present this under a heading "TRANSCRIPTION:".
2.  Under a heading "IDENTIFIED_PARAMETERS:", list each medical parameter you can identify with its value, reference range (if available), and status (if available or inferable). Format each as:
    Parameter Name: Value (Reference Range) - Status
    Example: Hemoglobin: 12.00 g/dL (13.00-17.00 g/dL) - Low
    Example: RBC Count: 5.79 mill/mm (Not specified) - Normal
    If status is not directly stated, infer it if possible (e.g., value outside reference range implies 'Abnormal', 'Low', or 'High').

3.  Under a heading "OBSERVED_ABNORMALITIES:", describe in simple, clear sentences any abnormalities found. For each, mention the parameter and the observation. If a recommendation is directly associated with an abnormality in the source, include it briefly.
    Example: Hemoglobin is low at 12.00 g/dL. Recommendation: Further investigation for anemia.
    Example: MCV is 65.00 fL, which is below the normal range.
    Example: The white blood cell differential shows low neutrophils and high lymphocytes. Suggests viral infection or other cause.

4.  Under a heading "GENERAL_SUMMARY:", provide a very brief, one or two-sentence overall summary of the findings, highlighting if results are generally normal or if there are areas of concern.

5.  Under a heading "GENERAL_RECOMMENDATIONS:", list 1-3 general recommendations based on any significant findings. These should be distinct from specific abnormality recommendations.

Do NOT attempt to create complex JSON. Focus on accurate transcription and clear, simple lists/sentences under the specified headings.
Prioritize information directly present in the report.
"""
        messages = [{"role": "system", "content": system_prompt}]
        
        if isinstance(content_input, str): 
            user_prompt_text_content = f"Please analyze this medical report text from file '{file_name}' according to the TASK instructions in the system prompt.\n\nREPORT CONTENT:\n{content_input}"
            messages.append({"role": "user", "content": user_prompt_text_content})
        elif isinstance(content_input, list): 
            messages.append({"role": "user", "content": content_input})
        else:
            raise ValueError(f"Unsupported content_input type: {type(content_input)}")

        print(f"DEBUG: AI_ANALYZE: Sending request for {file_name}...")
        response = client.chat.completions.create(
            model="sonar-pro", # Using a potentially more capable model
            messages=messages, 
            max_tokens=3500, # Increased max tokens
            temperature=0.1 
        )
        ai_full_response_text = response.choices[0].message.content
        print(f"DEBUG: AI_ANALYZE: Perplexity Full Response (first 1000 chars): {ai_full_response_text[:1000]}...")

        structured_data_obj = parse_structured_analysis(ai_full_response_text) 
        
        return {
            "summary": structured_data_obj.summary, 
            "detailed_analysis": ai_full_response_text, 
            "structured_data": structured_data_obj.dict(),
            "follow_up_recommendations": structured_data_obj.follow_up 
        }
    
    except Exception as e_ai:
        print(f"ERROR: AI_ANALYZE: General error for {file_name}: {str(e_ai)}")
        error_s_data = StructuredAnalysis(
            overall_status='error', summary=f"AI analysis failed: {str(e_ai)}", parameters=[], abnormalities=[], 
            recommendations=["Retry or consult manually."], follow_up="Consult provider; AI analysis failed."
        )
        return {"summary": f"Error during AI analysis: {str(e_ai)}", "detailed_analysis": f"AI analysis could not be completed. Error: {str(e_ai)}", "structured_data": error_s_data.dict(), "follow_up_recommendations": "Consult provider; AI analysis failed."}

# --- Report Processing Logic (Your existing process_report) ---
async def process_report(file_path: str, file_name: str, analysis_id: str):
    """Background task to process the report (extract content, then call AI)."""
    print(f"DEBUG: PROCESS_REPORT: Starting for {file_name}, ID: {analysis_id}")
    try:
        file_extension = file_name.split('.')[-1].lower() if '.' in file_name else 'txt'
        print(f"DEBUG: PROCESS_REPORT: Extracting content from {file_name}...")
        extracted_content_or_marker = extract_text_from_file(file_path, file_extension)
        ai_input_payload: Any = None 

        if extracted_content_or_marker.startswith("ERROR:"): 
            raise Exception(f"File extraction failed: {extracted_content_or_marker}")
        
        elif extracted_content_or_marker.startswith("IMAGE_FILE:"): 
            image_actual_path = extracted_content_or_marker.split(":", 1)[1]
            print(f"DEBUG: PROCESS_REPORT: Image file identified: {image_actual_path}. Encoding.")
            base64_image_uri = image_to_base64_data_uri(image_actual_path)
            if not base64_image_uri: raise Exception(f"Failed to encode image {image_actual_path} to base64.")
            user_query_for_image = (f"This is a medical report image from file '{file_name}'. Analyze its content thoroughly, extract visible text, parameters, and findings according to the system prompt.")
            ai_input_payload = [{"type": "text", "text": user_query_for_image}, {"type": "image_url", "image_url": {"url": base64_image_uri}}]
            print(f"DEBUG: PROCESS_REPORT: Image {file_name} prepared for AI vision.")
        
        else: 
            actual_text = extracted_content_or_marker
            if not actual_text or len(actual_text.strip()) < 10: 
                raise Exception("Could not extract meaningful text (too short or empty).")
            print(f"DEBUG: PROCESS_REPORT: Extracted text length: {len(actual_text)} chars.")
            ai_input_payload = actual_text 
            
        print(f"DEBUG: PROCESS_REPORT: Starting AI analysis for {file_name}...")
        analysis_dict = await analyze_report_with_ai(ai_input_payload, file_name) 
        
        structured_data_from_ai = analysis_dict.get("structured_data")
        final_structured_data_model: Optional[StructuredAnalysis] = None
        if isinstance(structured_data_from_ai, dict): 
            try: 
                final_structured_data_model = StructuredAnalysis(**structured_data_from_ai)
            except Exception as p_val_err: 
                print(f"WARN: PROCESS_REPORT: Pydantic validation failed for structured_data from AI: {p_val_err}")
        
        if final_structured_data_model is None: 
             print(f"WARN: PROCESS_REPORT: structured_data from AI was invalid or not a dict. Using default error structure.")
             final_structured_data_model = StructuredAnalysis(overall_status='error', summary='Error in AI response structure or parsing.', parameters=[], abnormalities=[], recommendations=["Review full AI response manually."], follow_up='Review AI output and consult provider.')

        result = AnalysisResult(
            id=analysis_id, file_name=file_name, upload_date=datetime.now().isoformat(),
            summary=analysis_dict.get("summary", "Summary not available."),
            detailed_analysis=analysis_dict.get("detailed_analysis", "Detailed analysis not available."),
            structured_data=final_structured_data_model,
            follow_up_recommendations=analysis_dict.get("follow_up_recommendations", final_structured_data_model.follow_up if final_structured_data_model else "Follow-up not specified.")
        )
        analysis_results[analysis_id] = result.dict() 
        results_file_path = os.path.join(RESULTS_DIR, f"{analysis_id}.json") 
        with open(results_file_path, 'w') as f: json.dump(result.dict(), f, indent=2)
        print(f"DEBUG: PROCESS_REPORT: Analysis completed for {file_name}. Results saved to {results_file_path}")
    
    except Exception as e_proc: 
        print(f"ERROR: PROCESS_REPORT: Error processing report '{file_name}' (ID: {analysis_id}): {str(e_proc)}")
        error_s_data = StructuredAnalysis(overall_status='error', summary=f"Processing failed: {str(e_proc)}", parameters=[], abnormalities=[], recommendations=["Try uploading again or check file."], follow_up="Contact support if issue persists.")
        error_result_obj = AnalysisResult(
            id=analysis_id, file_name=file_name, upload_date=datetime.now().isoformat(),
            summary=f"Error processing file: {str(e_proc)}", detailed_analysis="An error occurred during file processing.",
            structured_data=error_s_data, follow_up_recommendations="Try uploading again. Contact support if persistent."
        )
        analysis_results[analysis_id] = error_result_obj.dict() 
        try: 
            with open(os.path.join(RESULTS_DIR, f"{analysis_id}_error.json"), 'w') as f_err: json.dump(error_result_obj.dict(), f_err, indent=2)
        except Exception as ef_write: print(f"ERROR: PROCESS_REPORT: Additionally, failed to write error file: {ef_write}")

# --- CORS Configuration ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or ["*"] for permissive development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints (Your existing endpoints) ---
@router.post("/api/reports/upload", status_code=202)
async def upload_report_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    allowed_extensions = ['pdf', 'png', 'jpg', 'jpeg', 'txt', 'rtf', 'tiff', 'bmp', 'gif', 'webp']
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_extension not in allowed_extensions: raise HTTPException(status_code=400, detail=f"File type '{file_extension}' not supported. Allowed: {', '.join(allowed_extensions)}")
    
    analysis_id = str(uuid.uuid4())
    safe_original_filename = "".join(c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in file.filename)
    file_path = os.path.join(UPLOAD_DIR, f"{analysis_id}_{safe_original_filename}")
    
    try: 
        with open(file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        print(f"DEBUG: UPLOAD: File saved: {file_path}")
    except Exception as e_save: 
        print(f"ERROR: UPLOAD: Could not save file: {e_save}")
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {str(e_save)}")
    
    background_tasks.add_task(process_report, file_path=file_path, file_name=safe_original_filename, analysis_id=analysis_id)
    
    return {"id": analysis_id, "message": "File uploaded successfully. Analysis is in progress.", "filename": file.filename}

@router.get("/api/reports/{analysis_id}", response_model=AnalysisResult)
async def get_report_analysis_endpoint(analysis_id: str):
    if analysis_id in analysis_results: 
        try: return AnalysisResult(**analysis_results[analysis_id])
        except Exception as e_val: print(f"WARN: GET_REPORT: Pydantic validation error for in-memory result {analysis_id}: {e_val}")
    
    primary_path = os.path.join(RESULTS_DIR, f"{analysis_id}.json")
    error_path = os.path.join(RESULTS_DIR, f"{analysis_id}_error.json")
    target_path = None
    if os.path.exists(primary_path): target_path = primary_path
    elif os.path.exists(error_path): target_path = error_path

    if target_path: 
        with open(target_path, 'r') as f: data = json.load(f)
        analysis_results[analysis_id] = data 
        return AnalysisResult(**data) 

    for filename in os.listdir(UPLOAD_DIR): 
        if filename.startswith(analysis_id):
            # File exists in upload, but no result yet. This indicates "in progress"
            # We can make the frontend poll or wait for this status.
            # For now, keep HTTPException but with a specific message for the frontend to interpret.
            raise HTTPException(status_code=202, detail="Analysis is still in progress.") 
            
    raise HTTPException(status_code=404, detail="Analysis not found.")


@router.get("/api/reports", response_model=Dict[str, List[Dict[str, str]]])
async def list_all_reports_endpoint():
    reports_summary = []
    all_report_ids = set(analysis_results.keys()) 
    
    for res_file in os.listdir(RESULTS_DIR):
        if res_file.endswith(".json"):
            report_id_base = res_file.replace(".json", "").replace("_error", "") 
            all_report_ids.add(report_id_base)
            if report_id_base not in analysis_results: 
                try:
                    with open(os.path.join(RESULTS_DIR, res_file), 'r') as f: 
                        analysis_results[report_id_base] = json.load(f) 
                except Exception as e_load: print(f"WARN: LIST_REPORTS: Failed to load {res_file}: {e_load}")
    
    for analysis_id_key in sorted(list(all_report_ids)): 
        result_data = analysis_results.get(analysis_id_key)
        if not result_data: continue 

        is_error_status = result_data.get("structured_data", {}).get("overall_status") == "error" or \
                          result_data.get("summary", "").lower().startswith("error processing file") or \
                          result_data.get("summary", "").lower().startswith("error during ai analysis")
        
        reports_summary.append({
            "id": analysis_id_key, 
            "file_name": result_data.get("file_name", "N/A"),
            "upload_date": result_data.get("upload_date", "N/A"),
            "status": "error" if is_error_status else "completed"
        })
    return {"reports": reports_summary}

@router.delete("/api/reports/{analysis_id}", status_code=200)
async def delete_specific_report_endpoint(analysis_id: str):
    deleted_something = False
    if analysis_id in analysis_results: del analysis_results[analysis_id]; deleted_something = True 
    
    for suffix in [".json", "_error.json"]:
        res_path = os.path.join(RESULTS_DIR, f"{analysis_id}{suffix}")
        if os.path.exists(res_path):
            try: os.remove(res_path); deleted_something = True; print(f"DEBUG: DELETE: Removed result file {res_path}")
            except Exception as e_del_res: print(f"WARN: DELETE: Could not delete result file {res_path}: {e_del_res}")

    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(analysis_id):
            try:
                upload_path = os.path.join(UPLOAD_DIR, filename)
                os.remove(upload_path); deleted_something = True; print(f"DEBUG: DELETE: Removed upload file {upload_path}"); break 
            except Exception as e_del_up: print(f"WARN: DELETE: Could not delete upload file {upload_path}: {e_del_up}")

    if not deleted_something: raise HTTPException(status_code=404, detail="Report or associated files not found for deletion.")
    return {"message": f"Report {analysis_id} and associated files deleted successfully."}

# --- Serve Static Files and Frontend Routes ---
# This must come AFTER your API routes, or it might catch API paths.

# Serve analysis.html for /analysis/{id} paths
@router.get("/", response_class=FileResponse, include_in_schema=False) 
async def serve_report_analyzer_index_endpoint():
    index_path = STATIC_DIR / "index.html" # STATIC_DIR is .../report_analyzer_app/static/
    if not index_path.exists():
        raise HTTPException(status_code=404, detail=f"Report Analyzer App UI (index.html) not found at {index_path}")
    return FileResponse(index_path)

@router.get("/analysis/{analysis_id_path:path}", response_class=FileResponse, include_in_schema=False)
async def serve_report_analyzer_analysis_endpoint(analysis_id_path: str): # analysis_id_path not used for serving file
    analysis_html_path = STATIC_DIR / "analysis.html"
    if not analysis_html_path.exists():
        raise HTTPException(status_code=404, detail=f"Report Analyzer analysis UI page not found at {analysis_html_path}")
    return FileResponse(analysis_html_path)

@router.get("/health", include_in_schema=False) 
def health_check_endpoint_endpoint(): return {"status": "healthy", "timestamp": datetime.now().isoformat()}

