import os
from dotenv import load_dotenv

# Construct path to .env in the project root (my_ai_medical_assistant/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    APP_SECRET_KEY: str = os.getenv('APP_SECRET_KEY')
    PERPLEXITY_API_KEY: str = os.getenv('PERPLEXITY_API_KEY')
    PERPLEXITY_API_BASE_URL: str = "https://api.perplexity.ai/chat/completions"

    # Using exact model names as provided
    # These can also be set in .env for easier changes without code modification
    QNA_MODEL: str = os.getenv('PERPLEXITY_QNA_MODEL', "sonar-pro")
    SYMPTOM_MODEL: str = os.getenv('PERPLEXITY_SYMPTOM_MODEL', "sonar-reasoning-pro")
    PERSONAL_REPORT_MODEL: str = os.getenv('PERPLEXITY_REPORT_MODEL', "sonar-reasoning-pro")

    if not PERPLEXITY_API_KEY:
        print("CONFIG: CRITICAL - PERPLEXITY_API_KEY not found in .env or environment.")
    
    print(f"CONFIG: QNA_MODEL='{QNA_MODEL}', SYMPTOM_MODEL='{SYMPTOM_MODEL}', REPORT_MODEL='{PERSONAL_REPORT_MODEL}'")


settings = Settings()