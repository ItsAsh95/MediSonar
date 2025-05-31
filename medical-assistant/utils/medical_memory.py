# medical-assistant/utils/medical_memory.py
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Literal, Optional, get_args

# Conversation Modes for this main application - "report" is REMOVED
ConversationMode = Literal["qna", "symptoms"]

DATA_DIR_RELATIVE_TO_PROJECT_ROOT = os.path.join('medical-assistant', 'data')
CONVERSATIONS_FILE = os.path.join(DATA_DIR_RELATIVE_TO_PROJECT_ROOT, 'conversations_by_mode.json')
MEDICAL_SUMMARY_FILE = os.path.join(DATA_DIR_RELATIVE_TO_PROJECT_ROOT, 'medical_summary.json')

SINGLE_USER_ID = "default_persistent_user"

class MedicalMemory:
    def __init__(self):
        self.user_id = SINGLE_USER_ID
        if not os.path.exists(DATA_DIR_RELATIVE_TO_PROJECT_ROOT):
            os.makedirs(DATA_DIR_RELATIVE_TO_PROJECT_ROOT, exist_ok=True)
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        # Default structure now only includes qna and symptoms
        default_conversations_structure = {
            self.user_id: {
                "qna": [],
                "symptoms": []
            }
        }
        if not os.path.exists(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, 'w') as f:
                json.dump(default_conversations_structure, f, indent=4)
        else: 
            try:
                with open(CONVERSATIONS_FILE, 'r+') as f:
                    data = json.load(f)
                    if self.user_id not in data: 
                        data[self.user_id] = default_conversations_structure[self.user_id]
                    for mode_key in get_args(ConversationMode): # Use Literal values
                        if mode_key not in data[self.user_id]: 
                            data[self.user_id][mode_key] = []
                    if "report" in data.get(self.user_id, {}): # Clean up old "report" key if present
                        del data[self.user_id]["report"]
                    f.seek(0); json.dump(data, f, indent=4); f.truncate()
            except json.JSONDecodeError:
                with open(CONVERSATIONS_FILE, 'w') as f: 
                    json.dump(default_conversations_structure, f, indent=4)

        # Medical summary no longer stores report-specific analysis summaries from this app
        default_medical_summary = {
            self.user_id: {
                "symptoms_log": [], 
                # "analyzed_reports_info": [], # This key is fully removed
                "key_diagnoses_mentioned": [], # From symptom analysis
                "allergies": [], 
                "medications_log": []
            }
        }
        if not os.path.exists(MEDICAL_SUMMARY_FILE):
            with open(MEDICAL_SUMMARY_FILE, 'w') as f:
                json.dump(default_medical_summary, f, indent=4)
        else: 
            try:
                with open(MEDICAL_SUMMARY_FILE, 'r+') as f:
                    data = json.load(f)
                    if self.user_id not in data: 
                        data[self.user_id] = default_medical_summary[self.user_id]
                    for key_summary in default_medical_summary[self.user_id]:
                        if key_summary not in data[self.user_id]: 
                            data[self.user_id][key_summary] = default_medical_summary[self.user_id][key_summary]
                    if "analyzed_reports_info" in data.get(self.user_id, {}): # Clean up old report info key
                        del data[self.user_id]["analyzed_reports_info"]
                    f.seek(0); json.dump(data, f, indent=4); f.truncate()
            except json.JSONDecodeError:
                 with open(MEDICAL_SUMMARY_FILE, 'w') as f: 
                    json.dump(default_medical_summary, f, indent=4)

    def _load_conversations(self) -> Dict[str, Any]:
        try:
            with open(CONVERSATIONS_FILE, 'r') as f: 
                data = json.load(f)
                # Ensure basic structure for current user and valid modes
                if self.user_id not in data: data[self.user_id] = {}
                for mode_key in get_args(ConversationMode):
                    if mode_key not in data[self.user_id]: data[self.user_id][mode_key] = []
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {self.user_id: {"qna": [], "symptoms": []}}

    def _save_conversations(self, data: Dict[str, Any]):
        with open(CONVERSATIONS_FILE, 'w') as f: json.dump(data, f, indent=4)

    def _load_medical_summary(self) -> Dict[str, Any]:
        try:
            with open(MEDICAL_SUMMARY_FILE, 'r') as f: 
                data = json.load(f)
                # Ensure basic structure
                if self.user_id not in data: data[self.user_id] = {}
                for key_summary in ["symptoms_log", "key_diagnoses_mentioned", "allergies", "medications_log"]:
                    if key_summary not in data[self.user_id]: data[self.user_id][key_summary] = []
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {self.user_id: {"symptoms_log": [], "key_diagnoses_mentioned": [], "allergies": [], "medications_log": []}}

    def _save_medical_summary(self, data: Dict[str, Any]):
        with open(MEDICAL_SUMMARY_FILE, 'w') as f: json.dump(data, f, indent=4)

    def add_to_conversation_history(self, mode: ConversationMode, user_message: Optional[str], ai_response: str, file_name: Optional[str] = None, interaction_id: Optional[str]=None):
        if mode not in get_args(ConversationMode): # Runtime check just in case
            print(f"Warning: Attempted to add history for invalid mode '{mode}'. Skipping.")
            return

        all_convos = self._load_conversations()
        if self.user_id not in all_convos: all_convos[self.user_id] = {"qna": [], "symptoms": []}
        if mode not in all_convos[self.user_id]: all_convos[self.user_id][mode] = []
            
        user_mode_history = all_convos[self.user_id][mode]
        
        interaction = {
            "id": interaction_id or datetime.utcnow().isoformat() + "Z",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_message": user_message,
            "ai_response": ai_response, # Storing the main answer string for simplicity
        }
        if file_name: interaction["file_processed"] = file_name
        user_mode_history.append(interaction)
        
        all_convos[self.user_id][mode] = user_mode_history[-50:]
        self._save_conversations(all_convos)

    def get_conversation_history(self, mode: ConversationMode) -> List[Dict[str, Any]]:
        if mode not in get_args(ConversationMode): return [] # Return empty for invalid modes
        all_convos = self._load_conversations()
        return all_convos.get(self.user_id, {}).get(mode, [])

    def get_all_conversations_summary(self) -> Dict[str, List[Dict[str,Any]]]:
        all_convos = self._load_conversations()
        user_convos = all_convos.get(self.user_id, {})
        return {
            "qna": user_convos.get("qna", []),
            "symptoms": user_convos.get("symptoms", [])
            # "report" key is no longer included
        }

    def update_medical_summary(self, medical_info_dict: Dict[str, Any]):
        # This function is now only called by "symptoms" mode analysis
        summary_data = self._load_medical_summary()
        user_summary = summary_data.get(self.user_id, {})
        
        if not user_summary: 
            user_summary = {"symptoms_log": [], "key_diagnoses_mentioned": [], "allergies": [], "medications_log": []}

        if "current_symptoms_list" in medical_info_dict:
            log_entry = {"date": datetime.utcnow().isoformat() + "Z", "symptoms": medical_info_dict["current_symptoms_list"]}
            if "potential_conditions_discussed_list" in medical_info_dict:
                log_entry["notes"] = f"Potential relation to: {', '.join(medical_info_dict['potential_conditions_discussed_list'])}"
            user_summary.setdefault("symptoms_log", []).append(log_entry)
            user_summary["symptoms_log"] = user_summary["symptoms_log"][-20:]

        if "new_diagnoses_mentioned_list" in medical_info_dict:
            current_diagnoses = user_summary.setdefault("key_diagnoses_mentioned", [])
            for diag in medical_info_dict["new_diagnoses_mentioned_list"]:
                if diag not in current_diagnoses: current_diagnoses.append(diag)
        
        # No longer handles "reports_analyzed_info_item"
        
        summary_data[self.user_id] = user_summary
        self._save_medical_summary(summary_data)

    def get_medical_summary(self) -> Dict[str, Any]:
        summary_data = self._load_medical_summary()
        return summary_data.get(self.user_id, {})

    def clear_all_user_data(self):
        self._save_conversations({self.user_id: {"qna": [], "symptoms": []}})
        self._save_medical_summary({
            self.user_id: {"symptoms_log": [], "key_diagnoses_mentioned": [], "allergies": [], "medications_log": []}
        })
        print(f"All main app data cleared for user: {self.user_id} (QnA and Symptoms only)")

    def get_context_for_ai(self, mode: ConversationMode) -> str:
        if mode not in get_args(ConversationMode): return "Invalid mode for context."

        mode_specific_conv_history = self.get_conversation_history(mode)[-3:]
        medical_summary = self.get_medical_summary()
        
        context_parts = []
        
        if mode == "qna":
            if mode_specific_conv_history:
                context_parts.append("Recent Q&A Snippets (User -> AI):")
                for entry in mode_specific_conv_history:
                    user_msg_snippet = (entry.get('user_message') or f"File: {entry.get('file_processed','N/A')}")[:100]
                    ai_msg_snippet = (entry.get('ai_response') or "")[:100]
                    context_parts.append(f"- User: {user_msg_snippet}... -> AI: {ai_msg_snippet}...")
        
        elif mode == "symptoms":
            if mode_specific_conv_history:
                context_parts.append(f"Recent '{mode}' Interaction Snippets (User -> AI):")
                for entry in mode_specific_conv_history:
                    user_msg_snippet = (entry.get('user_message') or f"File: {entry.get('file_processed','N/A')}")[:100]
                    ai_msg_snippet = (entry.get('ai_response') or "")[:100]
                    context_parts.append(f"- User: {user_msg_snippet}... -> AI: {ai_msg_snippet}...")

            if medical_summary:
                context_parts.append("\nRelevant Medical Summary (from QnA/Symptom interactions):")
                if medical_summary.get("symptoms_log"):
                    s_logs = [f"{s['date'][:10]}: {', '.join(s['symptoms'])}" for s in medical_summary['symptoms_log'][-3:]]
                    if s_logs: context_parts.append(f"- Recent Symptom Logs: {'; '.join(s_logs)}")
                if medical_summary.get("key_diagnoses_mentioned"):
                    context_parts.append(f"- Key Diagnoses Mentioned: {', '.join(medical_summary['key_diagnoses_mentioned'][-3:])}")
                if medical_summary.get("allergies"):
                    context_parts.append(f"- Known Allergies: {', '.join(medical_summary['allergies'])}")
                # No "analyzed_reports_info" in context from this app's memory
        
        if not context_parts:
            return "No significant context available for this mode."
            
        return "\n".join(context_parts)