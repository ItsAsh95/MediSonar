import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))


class Settings:
    APP_SECRET_KEY: str = os.getenv('APP_SECRET_KEY', "default-secret-key-app")
    PERPLEXITY_API_KEY: str = os.getenv('PERPLEXITY_API_KEY')
    PERPLEXITY_API_BASE_URL: str = "https://api.perplexity.ai/chat/completions"

    # Define model names you'll use (examples, adjust as per your Perplexity access)
    DEFAULT_CHAT_MODEL: str = "sonar-medium-chat" # Or "mistral-7b-instruct", "mixtral-8x7b-instruct"
    SYMPTOM_ANALYSIS_MODEL: str = "sonar-medium-chat"
    REPORT_ANALYSIS_MODEL: str = "sonar-medium-online" # For access to web if analyzing general report info

    if not PERPLEXITY_API_KEY:
        print("CRITICAL WARNING: PERPLEXITY_API_KEY not found. AI features will not work.")

settings = Settings()