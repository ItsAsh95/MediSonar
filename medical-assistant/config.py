import os
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    APP_SECRET_KEY: str = os.getenv('APP_SECRET_KEY')
    PERPLEXITY_API_KEY: str = os.getenv('PERPLEXITY_API_KEY')
    PERPLEXITY_API_BASE_URL: str = "https://api.perplexity.ai/chat/completions"

    # Define model names you'll use (examples, adjust as per your Perplexity access)
    DEFAULT_CHAT_MODEL: str = "sonar" # Or "mistral-7b-instruct", "mixtral-8x7b-instruct"
    SYMPTOM_ANALYSIS_MODEL: str = "sonar-pro"
    REPORT_ANALYSIS_MODEL: str = "sonar-pro" # For access to web if analyzing general report info

    if not PERPLEXITY_API_KEY:
        print("CRITICAL WARNING: PERPLEXITY_API_KEY not found. AI features will not work.")

settings = Settings()