import os
from dotenv import load_dotenv


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

if os.path.exists(dotenv_path):
    print(f"CONFIG: Loading .env from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"CONFIG: WARNING - .env file not found at {dotenv_path}. Relying on environment variables.")

class Settings:
    APP_SECRET_KEY: str = os.getenv('APP_SECRET_KEY')
    

    PERPLEXITY_API_KEY: str = os.getenv('PERPLEXITY_API_KEY')
    PERPLEXITY_API_BASE_URL: str = "https://api.perplexity.ai/chat/completions"

    
    QNA_MODEL: str = os.getenv('PERPLEXITY_QNA_MODEL', "sonar-pro")
    SYMPTOM_MODEL: str = os.getenv('PERPLEXITY_SYMPTOM_MODEL', "sonar-reasoning-pro")
  
    SURVEY_APP_MODEL_NAME_CONFIG: str = os.getenv('SURVEY_APP_MODEL_NAME', "sonar-deep-research")
    ADVISORY_APP_MODEL_NAME_CONFIG: str = os.getenv('ADVISORY_APP_MODEL_NAME', "sonar-pro")
    REPORT_APP_MODEL_NAME_CONFIG: str = os.getenv('REPORT_APP_MODEL_NAME', "sonar-pro") 

  

    if not PERPLEXITY_API_KEY:
        print("CONFIG: CRITICAL - PERPLEXITY_API_KEY not found. Some AI features will fail.")
   

settings = Settings()