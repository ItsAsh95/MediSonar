# medical-assistant/utils/medical_memory.py
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Literal, Optional, Annotated

# Conversation Modes
ConversationMode = Literal["qna", "symptoms", "report"]

DATA_DIR_RELATIVE_TO_PROJECT_ROOT = os.path.join('medical-assistant', 'data')
CONVERSATIONS_FILE = os.path.join(DATA_DIR_RELATIVE_TO_PROJECT_ROOT, 'conversations_by_mode.json')
MEDICAL_SUMMARY_FILE = os.path.join(DATA_DIR_RELATIVE_TO_PROJECT_ROOT, 'medical_summary.json') # Consolidated summary

SINGLE_USER_ID = "default_persistent_user" # For this single-user setup

class MedicalMemory:
    def __init__(self):
        self.user_id = SINGLE_USER_ID
        if not os.path.exists(DATA_DIR_RELATIVE_TO_PROJECT_ROOT):
            os.makedirs(DATA_DIR_RELATIVE_TO_PROJECT_ROOT, exist_ok=True)
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        default_conversations_structure = {
            self.user_id: {
                "qna": [],
                "symptoms": [],
                "report": []
            }
        }
        if not os.path.exists(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, 'w') as f:
                json.dump(default_conversations_structure, f, indent=4)
        else: # Ensure structure integrity
            try:
                with open(CONVERSATIONS_FILE, 'r+') as f:
                    data = json.load(f)
                    if self.user_id not in data: data[self.user_id] = default_conversations_structure[self.user_id]
                    for mode in ["qna", "symptoms", "report"]:
                        if mode not in data[self.user_id]: data[self.user_id][mode] = []
                    f.seek(0); json.dump(data, f, indent=4); f.truncate()
            except json.JSONDecodeError:
                with open(CONVERSATIONS_FILE, 'w') as f: json.dump(default_conversations_structure, f, indent=4)

        default_medical_summary = {
            self.user_id: {
                "symptoms_log": [], "analyzed_reports_info": [], "key_diagnoses_mentioned": [],
                "allergies": [], "medications_log": [] # More granular now
            }
        }
        if not os.path.exists(MEDICAL_SUMMARY_FILE):
            with open(MEDICAL_SUMMARY_FILE, 'w') as f:
                json.dump(default_medical_summary, f, indent=4)
        else: # Ensure structure
            try:
                with open(MEDICAL_SUMMARY_FILE, 'r+') as f:
                    data = json.load(f)
                    if self.user_id not in data: data[self.user_id] = default_medical_summary[self.user_id]
                    for key in default_medical_summary[self.user_id]:
                        if key not in data[self.user_id]: data[self.user_id][key] = []
                    f.seek(0); json.dump(data, f, indent=4); f.truncate()
            except json.JSONDecodeError:
                 with open(MEDICAL_SUMMARY_FILE, 'w') as f: json.dump(default_medical_summary, f, indent=4)


    def _load_conversations(self) -> Dict[str, Any]:
        try:
            with open(CONVERSATIONS_FILE, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {self.user_id: {"qna": [], "symptoms": [], "report": []}}

    def _save_conversations(self, data: Dict[str, Any]):
        with open(CONVERSATIONS_FILE, 'w') as f: json.dump(data, f, indent=4)

    def _load_medical_summary(self) -> Dict[str, Any]:
        try:
            with open(MEDICAL_SUMMARY_FILE, 'r') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {self.user_id: {"symptoms_log": [], "analyzed_reports_info": [], "key_diagnoses_mentioned": []}}

    def _save_medical_summary(self, data: Dict[str, Any]):
        with open(MEDICAL_SUMMARY_FILE, 'w') as f: json.dump(data, f, indent=4)


    def add_to_conversation_history(self, mode: ConversationMode, user_message: Optional[str], ai_response: str, file_name: Optional[str] = None, interaction_id: Optional[str]=None):
        all_convos = self._load_conversations()
        user_mode_history = all_convos.get(self.user_id, {}).get(mode, [])
        
        interaction = {
            "id": interaction_id or datetime.utcnow().isoformat() + "Z", # Add ID for editing later
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_message": user_message,
            "ai_response": ai_response,
        }
        if file_name: interaction["file_processed"] = file_name
        user_mode_history.append(interaction)
        
        if self.user_id not in all_convos: all_convos[self.user_id] = {}
        all_convos[self.user_id][mode] = user_mode_history[-50:] # Keep last 50 per mode
        self._save_conversations(all_convos)

    def get_conversation_history(self, mode: ConversationMode) -> List[Dict[str, Any]]:
        all_convos = self._load_conversations()
        return all_convos.get(self.user_id, {}).get(mode, [])

    def get_all_conversations_summary(self) -> Dict[str, List[Dict[str,Any]]]: # For master history view
        all_convos = self._load_conversations()
        return all_convos.get(self.user_id, {"qna":[], "symptoms":[], "report":[]})


    def update_medical_summary(self, medical_info_dict: Dict[str, Any]):
        # This medical_info_dict comes from AI analysis (symptoms/report modes)
        # It should contain keys like 'current_symptoms_list', 'potential_conditions_discussed_list', 'report_name', 'key_findings_list' etc.
        summary_data = self._load_medical_summary()
        user_summary = summary_data.get(self.user_id, {})

        if "current_symptoms_list" in medical_info_dict:
            log_entry = {"date": datetime.utcnow().isoformat() + "Z", "symptoms": medical_info_dict["current_symptoms_list"]}
            if "potential_conditions_discussed_list" in medical_info_dict:
                log_entry["notes"] = f"Potential relation to: {', '.join(medical_info_dict['potential_conditions_discussed_list'])}"
            user_summary.setdefault("symptoms_log", []).append(log_entry)
            user_summary["symptoms_log"] = user_summary["symptoms_log"][-20:] # Keep recent

        if "reports_analyzed_info_item" in medical_info_dict: # Expecting a single report item
            user_summary.setdefault("analyzed_reports_info", []).append(medical_info_dict["reports_analyzed_info_item"])
            user_summary["analyzed_reports_info"] = user_summary["analyzed_reports_info"][-10:]

        if "new_diagnoses_mentioned_list" in medical_info_dict:
            current_diagnoses = user_summary.setdefault("key_diagnoses_mentioned", [])
            for diag in medical_info_dict["new_diagnoses_mentioned_list"]:
                if diag not in current_diagnoses: current_diagnoses.append(diag)
        
        summary_data[self.user_id] = user_summary
        self._save_medical_summary(summary_data)

    def get_medical_summary(self) -> Dict[str, Any]:
        summary_data = self._load_medical_summary()
        return summary_data.get(self.user_id, {})

    def clear_all_user_data(self):
        # Clears everything for the single_user_id
        self._save_conversations({self.user_id: {"qna": [], "symptoms": [], "report": []}})
        self._save_medical_summary({
            self.user_id: {"symptoms_log": [], "analyzed_reports_info": [], "key_diagnoses_mentioned": [], "allergies": [], "medications_log": []}
        })
        print(f"All data cleared for user: {self.user_id}")

    def get_context_for_ai(self, mode: ConversationMode) -> str:
        # This is now mode-specific context!
        # QnA mode might not use history, or use a very short snippet of its own QnA history.
        # Symptoms/Report modes use their own history AND the medical summary.
        
        mode_specific_conv_history = self.get_conversation_history(mode)[-3:] # Last 3 from current mode
        medical_summary = self.get_medical_summary()
        
        context_parts = []
        
        if mode == "qna":
            if mode_specific_conv_history:
                context_parts.append("Recent Q&A Snippets (User -> AI):")
                for entry in mode_specific_conv_history:
                    user_msg_snippet = (entry.get('user_message') or f"File: {entry.get('file_processed','N/A')}")[:100]
                    ai_msg_snippet = (entry.get('ai_response') or "")[:100]
                    context_parts.append(f"- User: {user_msg_snippet}... -> AI: {ai_msg_snippet}...")
            # No medical summary for general Q&A to avoid influencing it with unrelated past personal issues.
        
        elif mode in ["symptoms", "report"]:
            if mode_specific_conv_history:
                context_parts.append(f"Recent '{mode}' Interaction Snippets (User -> AI):")
                for entry in mode_specific_conv_history:
                    user_msg_snippet = (entry.get('user_message') or f"File: {entry.get('file_processed','N/A')}")[:100]
                    ai_msg_snippet = (entry.get('ai_response') or "")[:100]
                    context_parts.append(f"- User: {user_msg_snippet}... -> AI: {ai_msg_snippet}...")

            if medical_summary:
                context_parts.append("\nRelevant Medical Summary:")
                if medical_summary.get("symptoms_log"):
                    s_logs = [f"{s['date'][:10]}: {', '.join(s['symptoms'])}" for s in medical_summary['symptoms_log'][-3:]]
                    if s_logs: context_parts.append(f"- Recent Symptom Logs: {'; '.join(s_logs)}")
                if medical_summary.get("key_diagnoses_mentioned"):
                    context_parts.append(f"- Key Diagnoses Mentioned: {', '.join(medical_summary['key_diagnoses_mentioned'][-3:])}")
                if medical_summary.get("allergies"):
                    context_parts.append(f"- Known Allergies: {', '.join(medical_summary['allergies'])}")
                if medical_summary.get("analyzed_reports_info"):
                    r_names = [r.get('name', 'Report') for r in medical_summary['analyzed_reports_info'][-2:]]
                    if r_names: context_parts.append(f"- Recently Analyzed Reports: {', '.join(r_names)}")
        
        if not context_parts:
            return "No significant context available for this mode."
            
        return "\n".join(context_parts)

    # TODO: Add methods for editing/deleting specific interactions if that feature is pursued.
    # def edit_user_message(self, mode: ConversationMode, interaction_id: str, new_message: str): ...
    # def regenerate_ai_response(self, mode: ConversationMode, interaction_id: str): ...