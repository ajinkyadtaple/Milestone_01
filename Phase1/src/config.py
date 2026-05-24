import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Root directory of Phase1
PHASE1_ROOT = Path(__file__).resolve().parent.parent

# Data directory and cleaned CSV file path
DATA_DIR = PHASE1_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_DATA_PATH = DATA_DIR / "zomato_cleaned.csv"

# Templates directory
TEMPLATES_DIR = PHASE1_ROOT / "src" / "templates"

# Budget thresholds (cost for two people)
BUDGET_LOW_MAX = 400
BUDGET_MEDIUM_MAX = 1000

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = "gemini-2.5-flash"
