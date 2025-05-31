import os
import httpx
import hashlib
import ast 
import json
import re
from datetime import datetime
from enum import Enum
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Corrected imports:
from .schemas import SurveyResearchRequest, ReportTypeEnum 
PROJECT_ROOT_FOR_ENV = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT_FOR_ENV / '.env'



PERPLEXITY_API_KEY : str = os.getenv('PERPLEXITY_API_KEY')
if not PERPLEXITY_API_KEY:
    # In a real app, consider raising an exception or logging more severely
    print("SURVEY_RESEARCH_SERVICES: CRITICAL ERROR - PERPLEXITY_API_KEY not found via shared config.")

API_BASE_URL = 'https://api.perplexity.ai/chat/completions'
# Use the specific model name for this app from the shared config
RESEARCH_MODEL_NAME = 'sonar-deep-research'
FOLLOW_UP_MODEL_NAME = 'sonar'


# Updated generate_report_id
def generate_report_id(params: dict) -> str:
    """Generates a unique report ID based on a dictionary of request parameters."""
    # Create a canonical string representation of the request parameters
    # Sort keys to ensure consistency, convert enum to value
    
    # Convert enums to their values for consistent hashing
    processed_params = {}
    for k, v in params.items():
        if isinstance(v, Enum):
            processed_params[k] = v.value
        else:
            processed_params[k] = v
            
    canonical_string = json.dumps(processed_params, sort_keys=True)
    return hashlib.md5(canonical_string.lower().encode()).hexdigest()[:16] # Increased length slightly for more complex params


# --- Dynamic Prompt Building ---

# Base structure, can be adapted
BASE_SECTION_STRUCTURE = {
    "introduction": "1. Introduction",
    "major_diseases": "2. Major Diseases", # Title will be adapted
    "emerging_risks": "3. Emerging Health Risks & Trends", # Title will be adapted
    "govt_schemes": "4. Government Healthcare Schemes & Initiatives", # Title will be adapted
    "healthcare_system": "5. Healthcare Infrastructure & System", # Title will be adapted
    "challenges_recommendations": "6. Key Challenges, Opportunities, and Strategic Recommendations", # Title will be adapted
    "conclusion": "7. Conclusion",
    "references": "References"
}

def _get_focus_points_comprehensive(area_name: str, time_range: Optional[str] = None) -> dict:
    time_constraint_md = f" Focus on data from {time_range} if specified and available." if time_range else ""
    # Adding hints for more charts within focus points
    return {
        "introduction": [
            f"Provide a comprehensive overview of **'{area_name}'**: its demographic profile (population, age structure - *consider a pie/bar chart for age distribution if available*, density, urbanization), and socio-economic context.{time_constraint_md}",
            f"General introduction to **'{area_name}'s** healthcare landscape.{time_constraint_md}",
            f"State the main objectives and scope of this report for **'{area_name}'**."
        ],
        "major_diseases": [
            f"**Under a subsection titled `### 2.1. Communicable Diseases in {area_name}`:**",
            f"  - Detailed analysis of prevalent communicable diseases in **'{area_name}'**. For each: incidence/prevalence rates (with trends - *line charts for 2-3 key diseases*), mortality, affected populations, control programs, challenges.{time_constraint_md}",
            f"**Under a subsection titled `### 2.2. Non-Communicable Diseases (NCDs) in {area_name}`:**",
            f"  - In-depth discussion of major NCDs in **'{area_name}'**. For each: prevalence/trends (*line/bar chart for top 2-3 NCDs*), risk factors, impact, management strategies, screening programs.{time_constraint_md}"
        ],
        "emerging_risks": [
            f"**Under a subsection titled `### 3.1. Zoonotic Diseases in {area_name}`:** (Notable emerging zoonotic diseases, potential, surveillance, preparedness).{time_constraint_md}",
            f"**Under a subsection titled `### 3.2. Antimicrobial Resistance (AMR) in {area_name}`:** (AMR situation, pathogen resistance patterns - *table/bar chart for key pathogen resistance*, drivers, action plans).{time_constraint_md}",
            f"**Under a subsection titled `### 3.3. Environmental Health Risks in {area_name}`:** (Impacts of air/water pollution, climate change on health - *chart pollution levels vs health outcomes if data found*).{time_constraint_md}",
            f"**Under a subsection titled `### 3.4. Mental Health in {area_name}`:** (Mental health landscape, prevalence - *bar chart for common disorders if data available*, services, stigma, initiatives).{time_constraint_md}",
            f"**Under a subsection titled `### 3.5. Population Health Trends in {area_name}:`** (Demographic shifts - *ageing trend line chart*, nutritional status - *pie/bar for malnutrition*, lifestyle changes. Discuss health equity).{time_constraint_md}"
        ],
        "govt_schemes": [ # These should be specific to area_name
            f"**Under a subsection titled `### 4.1. Major National/Regional Scheme 1 impacting {area_name}:`** (Detailed analysis: objectives, coverage - *bar chart for beneficiaries*, services, impact, challenges).{time_constraint_md}",
            f"**Under a subsection titled `### 4.2. Major National/Regional Scheme 2 impacting {area_name}:`** (Similar analysis, achievements - *chart for key performance indicator like IMR/MMR reduction if attributable*).{time_constraint_md}",
            f"**Under a subsection titled `### 4.3. Other Key Local Schemes & Public Health Programs in {area_name}:`** (Describe scope, impact).{time_constraint_md}"
        ],
        "healthcare_system": [
            f"**Under a subsection titled `### 5.1. Healthcare Facilities in {area_name}:`** (Availability, distribution, quality. Quantitative data: numbers, bed strength - *bar chart comparing facility types or beds per 1000*).{time_constraint_md}",
            f"**Under a subsection titled `### 5.2. Human Resources for Health (HRH) in {area_name}:`** (Availability, density, distribution. Doctor-population, nurse-population ratios - *bar chart comparing HRH density to benchmarks*).{time_constraint_md}",
            f"**Under a subsection titled `### 5.3. Health Financing & Expenditure in {area_name}:`** (Financing sources. Health expenditure as % of GDP, OOP - *pie chart for expenditure breakdown; line chart for OOP trend*).{time_constraint_md}",
            f"**Under a subsection titled `### 5.4. Access to Care & Health Equity in {area_name}:`** (Analyze access issues, disparities).{time_constraint_md}",
            f"**Under a subsection titled `### 5.5. Pharmaceutical Sector & Supply Chain in {area_name}:`** (Pharma industry, drug procurement, availability of essential medicines).{time_constraint_md}",
            f"**Under a subsection titled `### 5.6. Health Information Systems (HIS) & Digital Health in {area_name}:`** (State of HIS, use of digital health).{time_constraint_md}"
        ],
        "challenges_recommendations": [
            f"**Under a subsection titled `### 6.1. Major Health System Challenges in {area_name}:`** (Synthesize key problems).{time_constraint_md}",
            f"**Under a subsection titled `### 6.2. Opportunities for Improvement in {area_name}:`** (Identify strengths, levers).{time_constraint_md}",
            f"**Under a subsection titled `### 6.3. Strategic Recommendations for {area_name}:`** (Propose 3-5 actionable, evidence-informed recommendations).{time_constraint_md}"
        ],
        "conclusion": [
            f"Summarize main findings for **'{area_name}'**, reiterate key status, challenges, opportunities.{time_constraint_md}",
            f"Offer insightful future outlook for health in **'{area_name}'**."
        ],
        "references": [
            f"Provide a comprehensive list of all cited sources alphabetically."
        ]
    }

def _get_focus_points_disease(area_name: str, disease_name: str, time_range: Optional[str] = None) -> tuple[dict, dict]:
    time_constraint_md = f" Focus on data from {time_range} if specified and available, specifically for {disease_name} in {area_name}." if time_range else f" specifically for {disease_name} in {area_name}."
    
    disease_section_guide = {
        "introduction_disease": f"1. Introduction to {disease_name}",
        "epidemiology": f"2. Epidemiology of {disease_name} in {area_name}",
        "risk_factors": f"3. Risk Factors for {disease_name} in {area_name}",
        "prevention_control": f"4. Prevention and Control Strategies for {disease_name} in {area_name}",
        "diagnosis_treatment": f"5. Diagnosis and Treatment of {disease_name} in {area_name}",
        "impact_disease": f"6. Impact of {disease_name} on {area_name} (Health, Social, Economic)",
        "govt_initiatives_disease": f"7. Government & NGO Initiatives for {disease_name} in {area_name}",
        "research_future": f"8. Current Research & Future Outlook for {disease_name} in {area_name}",
        "conclusion_disease": f"9. Conclusion on {disease_name} in {area_name}",
        "references": "References"
    }
    disease_focus_points = {
        "introduction_disease": [
            f"Briefly introduce **{disease_name}** globally and its significance.{time_constraint_md}",
            f"State the report's objective: to provide an in-depth analysis of **{disease_name}** in **'{area_name}'**."
        ],
        "epidemiology": [
            f"Detailed analysis of prevalence, incidence, and trends of **{disease_name}** in **'{area_name}'**. (*Line/bar chart for trends if data available*).{time_constraint_md}",
            f"Mortality and morbidity rates associated with **{disease_name}** in **'{area_name}'**.",
            f"Demographic breakdown of affected populations (age, gender, socio-economic groups) by **{disease_name}** in **'{area_name}'**. (*Consider a chart if distinct patterns exist*)."
        ],
        "risk_factors": [
            f"Identify and discuss major modifiable and non-modifiable risk factors for **{disease_name}** specific to **'{area_name}'**.{time_constraint_md}",
            f"Analyze local environmental, behavioral, and genetic predispositions if applicable for **{disease_name}**."
        ],
        "prevention_control": [
            f"Outline primary, secondary, and tertiary prevention strategies for **{disease_name}** implemented or relevant in **'{area_name}'**.{time_constraint_md}",
            f"Discuss public health campaigns, screening programs, and control measures for **{disease_name}** in **'{area_name}'**. (*Chart screening uptake if data exists*)."
        ],
        "diagnosis_treatment": [
            f"Describe diagnostic methods available and utilized for **{disease_name}** in **'{area_name}'**.{time_constraint_md}",
            f"Overview of standard treatment protocols, access to treatment, and challenges in managing **{disease_name}** in **'{area_name}'**.",
            f"Availability and accessibility of medications and therapies for **{disease_name}**."
        ],
        "impact_disease": [
            f"Assess the health burden (DALYs, QALYs if data available) of **{disease_name}** in **'{area_name}'**.{time_constraint_md}",
            f"Discuss the socio-economic impact of **{disease_name}** on individuals, families, and the healthcare system in **'{area_name}'**."
        ],
        "govt_initiatives_disease": [
            f"Detail specific government schemes, policies, and NGO efforts addressing **{disease_name}** in **'{area_name}'**.{time_constraint_md}",
            f"Evaluate the effectiveness and reach of these initiatives for **{disease_name}**. (*Chart funding or beneficiary numbers if available*)."
        ],
        "research_future": [
            f"Summarize ongoing research related to **{disease_name}** relevant to **'{area_name}'**.{time_constraint_md}",
            f"Discuss future challenges and opportunities in tackling **{disease_name}** in **'{area_name}'**."
        ],
         "conclusion_disease": [
            f"Summarize key findings regarding **{disease_name}** in **'{area_name}'**.{time_constraint_md}",
            f"Reiterate significant challenges and potential interventions for **{disease_name}**."
        ],
        "references": [
            f"Provide a comprehensive list of all cited sources alphabetically."
        ]
    }
    return disease_section_guide, disease_focus_points


async def get_perplexity_response(prompt_content: str, model_name: str, system_prompt_content: str = None, max_tokens: int = 8192, temperature: float = 0.3) -> str:
    # ... (get_perplexity_response function remains largely the same as provided in the problem description)
    # ... (ensure the latest version of this function, especially the <think> tag stripping, is used)
    if not PERPLEXITY_API_KEY:
        return "Error: API Key is not configured on the server."

    if system_prompt_content is None:
        system_prompt_content = (
            "You are an AI report writing machine. Your SOLE function is to produce the report text EXACTLY as requested by the user's prompt structure. "
            "DO NOT include ANY conversational phrases, introductory remarks, summaries of your understanding, self-corrections, or ANY text whatsoever that is not part of the direct report content. "
            "If you have any internal planning, thoughts, or meta-commentary about the generation process, you MUST enclose this information in <think>Your thought here</think> tags. These tags and their content will be programmatically removed and MUST NOT appear in the final report body. "
            "Your final output, after these <think> tags are notionally removed, MUST begin *EXACTLY* with the specified report title (e.g., 'Comprehensive Report on Healthcare in...')."
        )
    
    messages = [{"role": "system", "content": system_prompt_content}, {"role": "user", "content": prompt_content}]
    payload = {"model": model_name, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json", "Accept": "application/json"}
    timeout_duration = 900.0 # 15 minutes

    try:
        async with httpx.AsyncClient(timeout=timeout_duration) as client:
            print(f"Sending prompt to Perplexity (model: {model_name}, prompt length: {len(prompt_content)} chars). Expecting a long response.")
            response = await client.post(API_BASE_URL, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()

        if response_data.get("choices") and response_data["choices"][0].get("message"):
            raw_content = response_data["choices"][0]["message"]["content"]
            print(f"Raw response received from {model_name} (length: {len(raw_content)} chars).")

            content_without_thoughts = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL | re.IGNORECASE).strip()
            print(f"Content after stripping <think> tags (length: {len(content_without_thoughts)} chars).")
            
            # Determine expected report start based on prompt (this needs to be passed or inferred)
            # For now, we'll use a generic part of the title. This could be improved by passing the exact expected title.
            # A simple heuristic: find the first "##" which should be the main title.
            first_h2_match = re.search(r"##\s*.+", content_without_thoughts)
            cleaned_content = content_without_thoughts
            if first_h2_match:
                actual_start_index = first_h2_match.start()
                if actual_start_index > 0:
                    print(f"WARNING: Untagged preamble detected before the first H2 title. Stripping {actual_start_index} characters.")
                    cleaned_content = content_without_thoughts[actual_start_index:]
                else: # actual_start_index == 0
                    print("Report starts correctly with an H2 heading after <think> tag removal.")
            else:
                # Fallback to "Comprehensive Report on" or similar if H2 not found at start.
                # This part is tricky because the title itself is dynamic.
                # The instruction is to start EXACTLY with the title. If it doesn't, it's an AI deviation.
                # We rely on the AI following "MUST begin *EXACTLY* with the specified report title".
                # The current logic checks for "Comprehensive Report on Healthcare in". This will fail for new titles.
                # The BEST approach is if the AI *always* starts with "## Title". Then stripping up to the first "##" is robust.
                # For now, the existing logic in the problem description for title finding is okay, but less robust for dynamic titles.
                # The key is the system prompt enforcing the AI starts correctly.
                # Let's assume the current system prompt + <think> tag stripping is the primary cleaning mechanism.
                # The prompt itself will specify the exact starting title.
                print(f"Report content after <think> stripping (length: {len(cleaned_content)} chars). Further title-specific stripping might be needed if AI deviates.")


            return cleaned_content.strip()
        else:
            error_msg = response_data.get("error", {}).get("message", "Unknown API response format.")
            print(f"API Error (model: {model_name}): {error_msg} Full response: {json.dumps(response_data, indent=2)}")
            return f"Error: AI API returned an error: {error_msg}"
    except httpx.HTTPStatusError as http_err:
        error_content = "Unknown error"
        try:
            error_details = http_err.response.json()
            error_content = error_details.get("error", {}).get("message", http_err.response.text)
        except json.JSONDecodeError: error_content = http_err.response.text
        print(f"HTTP error (model: {model_name}): {http_err} - Details: {error_content}")
        return f"Error: AI API request failed (HTTP {http_err.response.status_code}). Details: {error_content}"
    except httpx.TimeoutException:
        print(f"API request timed out for model {model_name} after {timeout_duration}s.")
        return "Error: The AI API request timed out. This can happen with very long report requests. Please try a more focused area or try again later."
    except httpx.RequestError as req_err:
        print(f"Request error (model: {model_name}): {req_err}")
        return f"Error: AI API request failed due to a network issue: {str(req_err)}"
    except Exception as e:
        print(f"Generic error in get_perplexity_response (model: {model_name}): {e.__class__.__name__} - {e}")
        import traceback; traceback.print_exc()
        return f"Error: An unexpected error occurred: {str(e)}"

def _build_report_prompt(params: SurveyResearchRequest) -> str:
    current_date_str = datetime.now().strftime("%B %Y")
    area1 = params.area1
    area2 = params.area2
    disease = params.disease_focus
    time_range = params.time_range
    report_type = params.report_type

    title = ""
    section_guide = {}
    focus_points_map = {}
    comparison_instructions = ""
    time_constraint_global = f" All data and analysis should, where possible and specified, focus on the time range: **{time_range}**." if time_range else ""
    disease_focus_global = f" The primary focus of this report is **{disease}**." if disease else ""


    if report_type == ReportTypeEnum.COMPREHENSIVE_SINGLE_AREA:
        title = f"Comprehensive Report on Healthcare in {area1}: Diseases, Emerging Risks, and Government Schemes"
        if time_range: title += f" (Focus: {time_range})"
        section_guide = BASE_SECTION_STRUCTURE # Adjust titles slightly
        # Update section titles to include area_name for clarity in the prompt
        adapted_section_guide = {k: v.replace("in {area_name}", f"in {area1}").replace("{area_name}", area1) if "{area_name}" in v else v for k,v in BASE_SECTION_STRUCTURE.items()}
        section_guide = {k: f"{v} for {area1}" if k not in ["introduction", "conclusion", "references"] else v for k, v in adapted_section_guide.items()}
        section_guide["introduction"] = f"1. Introduction to Healthcare in {area1}"

        focus_points_map = _get_focus_points_comprehensive(area1, time_range)

    elif report_type == ReportTypeEnum.DISEASE_FOCUS:
        title = f"In-Depth Analysis of {disease} in {area1}"
        if area2: # Disease focus comparison
            title = f"Comparative Analysis of {disease} in {area1} vs. {area2}"
            comparison_instructions = (
                f" This report MUST compare and contrast the situation of **{disease}** between **{area1}** and **{area2}** for relevant sections.\n"
                f"Structure sections to first discuss **{area1}**, then **{area2}**, followed by a comparative summary for that section, or integrate comparisons directly."
            )
        if time_range: title += f" (Focus: {time_range})"
        
        # For disease focus, we use a different structure
        # If comparing, the focus points need to ask for data from both areas.
        # This simplified version of disease focus points needs expansion for comparison.
        # For now, let's assume _get_focus_points_disease primarily targets area1, and AI needs to adapt for area2 if title suggests comparison.
        # A more robust solution would have _get_focus_points_disease_comparison.
        temp_section_guide, temp_focus_points = _get_focus_points_disease(area1, disease, time_range)
        section_guide = temp_section_guide
        focus_points_map = temp_focus_points
        if area2: # Add note for comparison to focus points
            for section, points in focus_points_map.items():
                focus_points_map[section] = [p + f" If comparing with '{area2}', provide similar details for '{area2}' and highlight differences." for p in points]


    elif report_type == ReportTypeEnum.COMPARE_AREAS:
        title = f"Comparative Healthcare Analysis: {area1} vs. {area2}"
        if disease: title += f" (with a focus on {disease})" # Allow disease focus in comparison
        if time_range: title += f" (Focus: {time_range})"
        
        comparison_instructions = (
            f"This report MUST comprehensively compare and contrast the healthcare landscapes of **{area1}** and **{area2}**.\n"
            f"For each major section, discuss **{area1}** first, then **{area2}**, and conclude with a **comparative summary or analysis** highlighting key differences, similarities, and relative performance.\n"
            f"Charts should ideally be comparative (e.g., side-by-side bars, grouped data)."
        )
        if disease:
             comparison_instructions += f"\nPay special attention to comparing aspects related to **{disease}** within each relevant section."


        # Use comprehensive structure but adapt for comparison
        section_guide = {k: v.replace("in {area_name}", "").replace("{area_name}", "").strip() for k,v in BASE_SECTION_STRUCTURE.items()}
        
        # Get base focus points for area1 and area2 and then instruct AI to compare
        fp1 = _get_focus_points_comprehensive(area1, time_range)
        fp2 = _get_focus_points_comprehensive(area2, time_range)
        
        focus_points_map = {}
        for key in section_guide.keys():
            if key == "references": 
                focus_points_map[key] = ["Provide a combined, alphabetized list of all sources cited for both areas."]
                continue
            if key == "conclusion":
                focus_points_map[key] = [
                    f"Summarize the main comparative findings between {area1} and {area2}.",
                    f"Offer an insightful outlook considering the comparison."
                ]
                continue


            focus_points_map[key] = []
            if key in fp1:
                focus_points_map[key].append(f"**For {area1}:**")
                for point in fp1[key]: focus_points_map[key].append(f"  - {point.replace(f'in {area1}', '').replace(f'for {area1}', '').replace(f'{area1}', 'this area')}") # Generalize points
            if key in fp2:
                focus_points_map[key].append(f"**For {area2}:**")
                for point in fp2[key]: focus_points_map[key].append(f"  - {point.replace(f'in {area2}', '').replace(f'for {area2}', '').replace(f'{area2}', 'this area')}")
            focus_points_map[key].append(f"**Comparative Analysis ({key.replace('_', ' ').title()}):**")
            focus_points_map[key].append(f"  - Provide a detailed comparison of {area1} and {area2} for this section, highlighting similarities, differences, strengths, and weaknesses. Use comparative data and charts where possible.")
            if disease and key in ["major_diseases", "emerging_risks", "govt_schemes"]: # Emphasize disease in relevant sections
                focus_points_map[key].append(f"  - Specifically compare how **{disease}** is addressed or manifests in {area1} vs {area2} within this section.")


    prompt_start = f"""**CRITICAL INSTRUCTION: YOUR ENTIRE RESPONSE MUST BE ONLY THE REPORT CONTENT. START *EXACTLY* WITH THE FOLLOWING TITLE AND DATE, THEN THE "Contents" HEADING. DO NOT ADD ANY OTHER TEXT BEFORE THIS.**
**If you have any internal planning, thoughts, or self-correction steps during generation, you MUST enclose them in <think>...</think> tags. These tags and their content will be programmatically removed and MUST NOT appear in the final report body.**

## {title}
{current_date_str}

## Contents
*(You will generate the list of sections here based on the H2 and H3 headings used in the report. DO NOT include page numbers. Ensure each main section from the guide below has an entry.)*

---
"""
    prompt_body_instructions = f"""
**MAIN REPORT BODY INSTRUCTIONS:**
{comparison_instructions}
{disease_focus_global}
{time_constraint_global}

The report MUST be AT LEAST **5000-7000 WORDS** (or as extensively detailed as possible for the given scope).
Use ONLY certified and official sources of data. AIM TO INCLUDE SEVERAL RELEVANT CHARTS THROUGHOUT THE REPORT AS GUIDED.
**Remember to use <think>...</think> for any internal thought processes or meta-commentary that are not part of the report itself. These will be stripped out.**

**Overall Markdown Formatting:**
- Main sections MUST use H2 Markdown headings (e.g., `## 1. Introduction`).
- Subsections within main sections MUST use H3 Markdown headings (e.g., `### 1.1. Overview`).
- **FOR EACH SUBSECTION, provide THOROUGH and IN-DEPTH analysis, discussion, and detailed information. Do not be brief. Elaborate extensively, drawing on multiple data points and explaining their significance.**

**Detailed Content Guide for Each Section:**
"""

    for section_key, section_title_template in section_guide.items():
        actual_section_title = section_title_template # Already formatted by logic above
        prompt_body_instructions += f"\n## {actual_section_title}\n"
        if section_key in focus_points_map:
            for point in focus_points_map[section_key]:
                if point.strip().startswith("**Under a subsection titled"):
                    h3_match = re.search(r"`(### .*?)`", point)
                    if h3_match:
                        h3_title = h3_match.group(1)
                        prompt_body_instructions += f"{h3_title}\n"
                        instruction_for_h3 = point.split("`:**", 1)[-1].strip()
                        prompt_body_instructions += f"- {instruction_for_h3}\n"
                    else: # Fallback if regex fails
                        prompt_body_instructions += f"- {point}\n"
                elif point.strip().startswith("**For ") or point.strip().startswith("**Comparative Analysis"): # For comparative structure
                     prompt_body_instructions += f"{point}\n"
                else:
                    prompt_body_instructions += f"- {point}\n"
        else:
            prompt_body_instructions += f"- (Provide comprehensive information for this section: {actual_section_title})\n"

    chart_area_ref = area1
    if report_type == ReportTypeEnum.COMPARE_AREAS and area2:
        chart_area_ref = f"{area1} and {area2}"
    elif report_type == ReportTypeEnum.DISEASE_FOCUS and disease:
        chart_area_ref = f"{disease} in {area1}"


    prompt_end_rules = f"""
**General Content Style:**
- Provide EXTREMELY IN-DEPTH analysis, not just lists. Explain data significance. Aim for a total report length of AT LEAST 5000-7000 WORDS.
- Integrate statistics smoothly and extensively.
- Use bullet points (`* item`) for lists where appropriate, but main content should be detailed prose.

**Tables:**
- Include data in Markdown tables where relevant. Caption *above* table: "Table X: Description for {chart_area_ref}."

**Charts and Graphs (Data Provision - INCLUDE PLENTY OF RELEVANT CHARTS):**
- Actively look for opportunities to include charts to visualize data, trends, and comparisons. The more relevant charts, the better.
- For EACH chart, provide data ON ITS OWN LINE, immediately after the paragraph discussing it:
    `CHART_DATA: TYPE=[bar|line|pie|doughnut|horizontalBar] TITLE="Chart Title for {chart_area_ref}" LABELS=["L1","L2"] DATA=[V1,V2] SOURCE="(Source, Year)"`
    *(For multi-series charts like comparative bar charts, you might represent as multiple DATA_SERIES_X or structure the DATA array itself if the type supports it, e.g. for grouped bar, each item in DATA could be an array of values for that label. However, the schema expects `datasets: List[ChartDataset]`, so if the AI can provide multiple datasets per CHART_DATA directive, that would be ideal. For simplicity, it can also provide separate CHART_DATA directives for each series if that's easier for it, and we can group them in post-processing if necessary, or it can specify multiple datasets in one directive with `DATASET_1_LABEL="Label1" DATASET_1_DATA=[v1,v2] DATASET_2_LABEL="Label2" DATASET_2_DATA=[v3,v4]`. The current parsing only directly supports one dataset per CHART_DATA line. For now, stick to the simple one-dataset-per-CHART_DATA directive or let the AI decide how to format complex chart data for multiple series within the single DATA field, e.g. `DATA=[[10,20],[15,25]]` for two series and two labels, which would need more complex parsing on our end. **Let's stick to the existing simple CHART_DATA format and encourage multiple CHART_DATA entries if needed for comparisons.**)*
- Chart data arrays (LABELS, DATA) should be concise (3-10 points typically).

**Citations:**
- ALL data/claims MUST be attributed in-text: `(Author/Organization, Year)`.

**Final Section - References:**
- The last H2 section of the report MUST be `## References`.
- List all cited sources alphabetically with full details.

**ABSOLUTELY NO TEXT, THOUGHTS, PLANNING, OR PREFATORY REMARKS BEFORE THE MAIN REPORT TITLE. YOUR RESPONSE IS ONLY THE REPORT CONTENT AS SPECIFIED. All internal thoughts or meta-commentary MUST be in <think>...</think> tags.**
"""
    full_prompt = prompt_start + prompt_body_instructions + prompt_end_rules
    # print("---- GENERATED PROMPT ----")
    # print(full_prompt[:2000] + "\n...\n" + full_prompt[-1000:])
    # print("---- END PROMPT ----")
    return full_prompt


async def conduct_deep_research(research_params: SurveyResearchRequest):
    request_desc = f"type={research_params.report_type.value}, area1={research_params.area1}"
    if research_params.area2: request_desc += f", area2={research_params.area2}"
    if research_params.disease_focus: request_desc += f", disease={research_params.disease_focus}"
    if research_params.time_range: request_desc += f", time_range={research_params.time_range}"
    
    print(f"Starting HEALTH ANALYSIS for: {request_desc} using {RESEARCH_MODEL_NAME}")
    
    # Generate a unique ID based on all relevant parameters of the request
    # The model_dump should exclude Nones by default if not set otherwise.
    # exclude_defaults=True ensures that if report_type is the default, it's still included if it affects the prompt.
    # However, generate_report_id in app.py already handles this. We need to ensure consistency.
    # The report_id passed to the ReportResponse model should be the one generated based on the request.
    
    # Construct a user-friendly "area_name" for the report response based on the request
    report_title_display_name = research_params.area1
    if research_params.report_type == ReportTypeEnum.COMPARE_AREAS and research_params.area2:
        report_title_display_name = f"{research_params.area1} vs. {research_params.area2}"
    elif research_params.report_type == ReportTypeEnum.DISEASE_FOCUS and research_params.disease_focus:
        report_title_display_name = f"{research_params.disease_focus} in {research_params.area1}"
        if research_params.area2: # Disease comparison
             report_title_display_name = f"{research_params.disease_focus} in {research_params.area1} vs. {research_params.area2}"

    if research_params.time_range:
        report_title_display_name += f" (Time Focus: {research_params.time_range})"


    # The report_id should be generated once, ideally before this function or right at the start.
    # Let's assume app.py generates it and if caching is missed, we re-generate it here for the response object.
    # For the response object, it must match the one used for caching.
    # So, it's better if app.py generates it and passes it, or we ensure this matches.
    # For simplicity, we'll use the passed research_params to construct it.
    current_report_id = generate_report_id(research_params.model_dump(exclude_none=True, exclude_defaults=False))


    report_data = {
        "report_id": current_report_id,
        "area_name": report_title_display_name, # This is for display in UI
        "full_report_markdown": "",
        "charts": [],
        "full_text_for_follow_up": ""
    }

    mega_prompt = _build_report_prompt(research_params)

    estimated_tokens = len(mega_prompt) / 3.7 
    print(f"Structured Prompt Estimated length: ~{len(mega_prompt)} chars, ~{estimated_tokens:.0f} tokens.")

    full_report_markdown_content = await get_perplexity_response(
        prompt_content=mega_prompt,
        model_name=RESEARCH_MODEL_NAME,
        max_tokens=8192, 
        temperature=0.3 
    )

    report_data["full_report_markdown"] = full_report_markdown_content
    report_data["full_text_for_follow_up"] = full_report_markdown_content

    if full_report_markdown_content.startswith("Error:"):
        print(f"Report generation failed for {request_desc}. API Error: {full_report_markdown_content}")
        # report_data structure is already initialized, so just return it.
        return report_data 
    
    # Chart parsing logic
    # Pattern needs to be robust, title can now contain "vs." etc.
    chart_pattern_str = r'CHART_DATA:\s*TYPE=(?P<type>\w+)\s*TITLE="(?P<title>[^"]+)"\s*LABELS=(?P<labels>\[[^\]]*\])\s*DATA=(?P<data>\[[^\]]*\])(?:\s*SOURCE="(?P<source>[^"]+)")?'
    chart_matches = re.finditer(chart_pattern_str, full_report_markdown_content)
    temp_charts_list = []

    for match_idx_chart, chart_match_item in enumerate(chart_matches):
        try:
            chart_dict = chart_match_item.groupdict()
            chart_type = chart_dict['type'].lower()
            # Allow more characters in title, including those relevant for comparisons like 'vs.'
            chart_title = re.sub(r'[^\w\s\-\(\)%.,:&vs]', '', chart_dict['title']).strip() # Added .,:&vs
            labels_str = chart_dict['labels']
            data_str = chart_dict['data']
            chart_source = chart_dict.get('source')

            try: labels = json.loads(labels_str)
            except json.JSONDecodeError: labels = ast.literal_eval(labels_str)
            
            # Handle potentially nested data for multi-series charts if AI provides it that way
            # For now, assuming simple list of numbers or list of lists for data.
            # The schema expects `datasets: List[ChartDataset]` where each dataset has `data: List[Union[int, float]]`.
            # The simplest AI output is one CHART_DATA per dataset.
            # If AI outputs `DATA=[[10,20],[15,25]]` and `LABELS=["A","B"]`, this means 2 series.
            # Our current parsing logic is for a single series per CHART_DATA directive.
            # This part needs to be more robust if the AI is to generate multi-series data in one DATA field.
            # For now, we'll process as if DATA is a single list of numbers.
            
            try: raw_data_points_or_series = json.loads(data_str)
            except json.JSONDecodeError: raw_data_points_or_series = ast.literal_eval(data_str)

            # Check if it's a multi-series chart (list of lists)
            is_multi_series = isinstance(raw_data_points_or_series, list) and \
                              all(isinstance(sublist, list) for sublist in raw_data_points_or_series) and \
                              len(raw_data_points_or_series) > 0

            datasets_for_chart = []

            if is_multi_series:
                # This is a crude way to handle it. AI might not provide labels for each series.
                # TODO: The CHART_DATA format needs to be extended for multi-series (e.g. DATASET_1_LABEL, DATASET_1_DATA etc.)
                # For now, assume generic labels for series if AI provides list of lists for DATA.
                print(f"Chart '{chart_title}' detected as multi-series from DATA structure. This is experimental parsing.")
                num_series = len(raw_data_points_or_series)
                # Ensure all series have same length as labels
                if not all(len(series_data) == len(labels) for series_data in raw_data_points_or_series):
                    print(f"Multi-series chart data length mismatch for '{chart_title}'. Skipping.")
                    continue

                for i, series_data_raw in enumerate(raw_data_points_or_series):
                    numeric_data_points, valid = _parse_chart_data_points(series_data_raw, chart_title)
                    if valid and numeric_data_points:
                         datasets_for_chart.append({"label": f"Series {i+1} for {chart_title}", "data": numeric_data_points})
                    else:
                        print(f"Failed to parse series {i+1} for multi-series chart '{chart_title}'. Skipping entire chart.")
                        datasets_for_chart = [] # Invalidate chart
                        break 
            else: # Single series
                raw_data_points = raw_data_points_or_series
                if not (isinstance(labels, list) and isinstance(raw_data_points, list) and len(labels) == len(raw_data_points) and len(labels) > 0):
                    print(f"Chart data format/length mismatch for '{chart_title}' (Match {match_idx_chart}). Labels: {len(labels)}, Data: {len(raw_data_points)}. Skipping.")
                    continue
                
                numeric_data_points, valid = _parse_chart_data_points(raw_data_points, chart_title)
                if valid and numeric_data_points:
                    chart_dataset_label = chart_title 
                    if chart_source: chart_dataset_label += f" (Source: {chart_source})" # Add source to dataset label for single series
                    datasets_for_chart.append({"label": chart_dataset_label, "data": numeric_data_points})
            
            if datasets_for_chart: # If any valid datasets were processed
                if len(labels) > 15: # Increased limit slightly
                    print(f"Warning: Chart '{chart_title}' has {len(labels)} labels, truncating to 15 for display.")
                    labels = labels[:15]
                    # Datasets must also be truncated
                    for ds in datasets_for_chart:
                        ds["data"] = ds["data"][:15]


                temp_charts_list.append({
                    "type": chart_type, "title": chart_title, "labels": [str(l) for l in labels],
                    "datasets": datasets_for_chart,
                    "source": chart_source
                })
                print(f"Successfully parsed chart: '{chart_title}' with {len(datasets_for_chart)} dataset(s) for {request_desc}")

        except Exception as e_chart_parse:
            print(f"Error parsing CHART_DATA (Match {match_idx_chart}): {e_chart_parse}. Raw: {chart_match_item.group(0)}")
    
    report_data["charts"] = temp_charts_list
    print(f"Total charts parsed and ready for rendering: {len(report_data['charts'])}")
    
    print(f"Finished HEALTH ANALYSIS for: {request_desc}.")
    return report_data

def _parse_chart_data_points(raw_points_list: list, chart_title_for_log: str) -> tuple[list, bool]:
    """Helper to parse a list of raw data points into numeric, returns (data_list, is_valid)"""
    numeric_data = []
    valid_chart = True
    for point_idx, point in enumerate(raw_points_list):
        try:
            val_str = str(point).strip().replace('%', '')
            # Try to remove any non-numeric characters except decimal, minus, and 'e' for scientific notation
            cleaned_val_str = re.sub(r'[^\d\.\-eE]', '', val_str) if isinstance(val_str, str) else str(point)
            
            if cleaned_val_str: # If something remains after cleaning
                numeric_data.append(float(cleaned_val_str))
            elif isinstance(point, (int, float)): # If it was already a number
                numeric_data.append(float(point))
            else: # If cleaning resulted in empty string and it wasn't a number
                raise ValueError(f"Non-convertible point after cleaning: '{point}' -> '{cleaned_val_str}'")
        except (ValueError, TypeError) as e_conv:
            print(f"Could not convert chart data point '{point}' (index {point_idx}) for '{chart_title_for_log}'. Error: {e_conv}. Skipping chart or series.")
            valid_chart = False
            numeric_data = [] # Clear data if any point is bad
            break
    if not numeric_data and valid_chart and raw_points_list: # Had points, but all failed conversion or were empty after clean
        print(f"Chart '{chart_title_for_log}' had no valid numeric data after parsing. Raw: {raw_points_list}")
        valid_chart = False
        
    return numeric_data, valid_chart


async def answer_follow_up_question(question: str, report_context: str) -> str:
    # ... (answer_follow_up_question function remains the same as provided in problem description)
    system_prompt_content = (
        "You are a helpful AI assistant. The user is asking a follow-up question about a detailed health report they just reviewed. "
        "Base your answer ONLY on the information contained within the provided report context. "
        "If the answer isn't in the report, clearly state that the information is not available in the provided document. "
        "Do not use external knowledge."
    )
    
    user_prompt_content = (
        f"Here is the health report content:\n"
        f"--- BEGIN REPORT CONTEXT ---\n{report_context}\n--- END REPORT CONTEXT ---\n\n"
        f"My question is: {question}\n\n"
        f"Based on the report, what is the answer? If it's not mentioned, please say so."
    )
    
    print(f"Answering follow-up with {FOLLOW_UP_MODEL_NAME}: '{question[:100]}...'")
    
    return await get_perplexity_response(
        prompt_content=user_prompt_content,
        model_name=FOLLOW_UP_MODEL_NAME,
        system_prompt_content=system_prompt_content, 
        max_tokens=1024,
        temperature=0.3
    )