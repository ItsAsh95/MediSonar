from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime

# Assuming this script is in my_ai_medical_assistant/medical-assistant/utils/
# and main.py is in my_ai_medical_assistant/medical-assistant/
# The data directory will be created at my_ai_medical_assistant/medical-assistant/data/
# If running uvicorn from my_ai_medical_assistant/ then path needs to be relative to that
# CWD is 'my_ai_medical_assistant' when running 'uvicorn medical-assistant.main:app --reload'
DATA_DIR_RELATIVE_TO_PROJECT_ROOT = os.path.join('medical-assistant', 'data')

CONVERSATION_HISTORY_FILE = os.path.join(DATA_DIR_RELATIVE_TO_PROJECT_ROOT, 'conversation_history.json')
MEDICAL_HISTORY_FILE = os.path.join(DATA_DIR_RELATIVE_TO_PROJECT_ROOT, 'medical_history.json')

# SINGLE USER ID for this persistent setup
SINGLE_USER_ID = "default_persistent_user"

class MedicalMemory:
    def __init__(self):
        self.user_id = SINGLE_USER_ID
        # Ensure data directory exists relative to project root
        if not os.path.exists(DATA_DIR_RELATIVE_TO_PROJECT_ROOT):
            os.makedirs(DATA_DIR_RELATIVE_TO_PROJECT_ROOT, exist_ok=True)
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        if not os.path.exists(CONVERSATION_HISTORY_FILE):
            with open(CONVERSATION_HISTORY_FILE, 'w') as f:
                json.dump({self.user_id: []}, f, indent=4)
        else: # Ensure user_id key exists if file exists but is empty or malformed
            try:
                with open(CONVERSATION_HISTORY_FILE, 'r+') as f:
                    data = json.load(f)
                    if self.user_id not in data:
                        data[self.user_id] = []
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()
            except json.JSONDecodeError:
                 with open(CONVERSATION_HISTORY_FILE, 'w') as f:
                    json.dump({self.user_id: []}, f, indent=4)


        default_med_history_structure = {
            "symptoms_history": [], "reports_analyzed_info": [], "diagnoses_suggested": [],
            "medications_mentioned": [], "surgeries_operations": [], "allergies": []
        }
        if not os.path.exists(MEDICAL_HISTORY_FILE):
            with open(MEDICAL_HISTORY_FILE, 'w') as f:
                json.dump({self.user_id: default_med_history_structure.copy()}, f, indent=4)
        else: # Ensure user_id key exists and has basic structure
            try:
                with open(MEDICAL_HISTORY_FILE, 'r+') as f:
                    data = json.load(f)
                    if self.user_id not in data or not isinstance(data.get(self.user_id), dict):
                        data[self.user_id] = default_med_history_structure.copy()
                    else: # Ensure all keys are present
                        for key, val_list in default_med_history_structure.items():
                            if key not in data[self.user_id]:
                                data[self.user_id][key] = val_list
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()
            except json.JSONDecodeError:
                with open(MEDICAL_HISTORY_FILE, 'w') as f:
                    json.dump({self.user_id: default_med_history_structure.copy()}, f, indent=4)


    def _load_data(self, filepath: str) -> dict:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Ensure the single user's data structure exists
                if self.user_id not in data:
                    if filepath == CONVERSATION_HISTORY_FILE:
                        data[self.user_id] = []
                    elif filepath == MEDICAL_HISTORY_FILE:
                        data[self.user_id] = {
                            "symptoms_history": [], "reports_analyzed_info": [], "diagnoses_suggested": [],
                            "medications_mentioned": [], "surgeries_operations": [], "allergies": []
                        }
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            # This should ideally be caught by _ensure_files_exist, but as a safety net:
            if filepath == CONVERSATION_HISTORY_FILE:
                return {self.user_id: []}
            elif filepath == MEDICAL_HISTORY_FILE:
                return {self.user_id: {
                    "symptoms_history": [], "reports_analyzed_info": [], "diagnoses_suggested": [],
                    "medications_mentioned": [], "surgeries_operations": [], "allergies": []
                }}
        return {}


    def _save_data(self, filepath: str, data: dict):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def add_to_conversation_history(self, user_message: Optional[str], ai_response: str, mode: str, file_name: Optional[str] = None):
        all_history = self._load_data(CONVERSATION_HISTORY_FILE)
        user_conv_history = all_history.get(self.user_id, [])
        
        interaction = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mode": mode,
            "user_message": user_message,
            "ai_response": ai_response,
        }
        if file_name:
            interaction["file_processed"] = file_name

        user_conv_history.append(interaction)
        all_history[self.user_id] = user_conv_history[-100:] # Keep last 100 interactions
        self._save_data(CONVERSATION_HISTORY_FILE, all_history)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        all_history = self._load_data(CONVERSATION_HISTORY_FILE)
        return all_history.get(self.user_id, [])
    
    def update_medical_history(self, medical_info_dict: Dict[str, Any]):
        all_med_history = self._load_data(MEDICAL_HISTORY_FILE)
        user_med_history = all_med_history.get(self.user_id, {})
        
        # Ensure base structure if somehow missing (should not happen with _ensure_files_exist)
        if not user_med_history:
            user_med_history = {
                "symptoms_history": [], "reports_analyzed_info": [], "diagnoses_suggested": [],
                "medications_mentioned": [], "surgeries_operations": [], "allergies": []
            }

        for key, value in medical_info_dict.items():
            if key in user_med_history and isinstance(user_med_history[key], list):
                current_list = user_med_history[key]
                if isinstance(value, list): # If value is a list, extend with unique items
                    current_list.extend(item for item in value if item not in current_list)
                else: # If value is a single item, append if unique
                    if value not in current_list:
                        current_list.append(value)
            else: # If key not present or not a list, set/overwrite
                user_med_history[key] = value
        
        all_med_history[self.user_id] = user_med_history
        self._save_data(MEDICAL_HISTORY_FILE, all_med_history)

    def get_medical_history(self) -> Dict[str, Any]:
        all_med_history = self._load_data(MEDICAL_HISTORY_FILE)
        return all_med_history.get(self.user_id, {})

    def clear_all_history(self):
        # Clears for the single_user_id and recreates the base structure
        default_med_history = {
            "symptoms_history": [], "reports_analyzed_info": [], "diagnoses_suggested": [],
            "medications_mentioned": [], "surgeries_operations": [], "allergies": []
        }
        self._save_data(CONVERSATION_HISTORY_FILE, {self.user_id: []})
        self._save_data(MEDICAL_HISTORY_FILE, {self.user_id: default_med_history})
        print(f"History cleared for user: {self.user_id}")

    def get_relevant_history_for_query(self) -> str:
        med_history = self.get_medical_history()
        conv_history = self.get_conversation_history()
        
        context_parts = []
        
        recent_conv = conv_history[-5:] # Last 5 interactions
        if recent_conv:
            context_parts.append("Recent Conversation Snippets (User -> AI):")
            for entry in recent_conv:
                user_msg_snippet = (entry.get('user_message') or f"File: {entry.get('file_processed','N/A')}")[:150]
                ai_msg_snippet = (entry.get('ai_response') or "")[:150]
                context_parts.append(f"- User: {user_msg_snippet}... -> AI: {ai_msg_snippet}...")
        
        if med_history:
            context_parts.append("\nKey Medical Summary:")
            if med_history.get("symptoms_history"):
                context_parts.append(f"- Past Symptoms: {', '.join(med_history['symptoms_history'][-5:])}")
            if med_history.get("diagnoses_suggested"):
                context_parts.append(f"- Past Diagnoses Suggested: {', '.join(med_history['diagnoses_suggested'][-3:])}")
            if med_history.get("allergies"):
                context_parts.append(f"- Known Allergies: {', '.join(med_history['allergies'])}")
            if med_history.get("reports_analyzed_info"): # This should store brief info like report name and key findings
                report_names = [info.get('name', 'Unknown Report') for info in med_history['reports_analyzed_info'][-3:]]
                if report_names:
                    context_parts.append(f"- Recently Analyzed Reports: {', '.join(report_names)}")
        
        if not context_parts:
            return "No significant history available."
            
        return "\n".join(context_parts)