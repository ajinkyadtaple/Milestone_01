import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    _PHASE3_ROOT = Path(__file__).resolve().parent.parent
    _REPO_ROOT = _PHASE3_ROOT.parent
    load_dotenv(_PHASE3_ROOT / ".env")
    load_dotenv(_REPO_ROOT / ".env")
except ImportError:
    pass

PHASE3_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PHASE3_ROOT.parent
# Ensure env vars from Streamlit Cloud secrets can override after import

# Reuse Phase 2 enriched data and Chroma index
PHASE2_ROOT = REPO_ROOT / "Phase2"
ENRICHED_DATA_PATH = PHASE2_ROOT / "data" / "zomato_enriched.csv"
CHROMA_DIR = PHASE2_ROOT / "chroma_db"
CHROMA_COLLECTION = "restaurants"

BUDGET_LOW_MAX = 400
BUDGET_MEDIUM_MAX = 1000
HYBRID_TOP_K = 15
SEMANTIC_TOP_K = 15

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBED_BATCH_SIZE = 64
MAX_INDEX_TEXT_CHARS = 512

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_BASE_URL = os.getenv("GROQ_API_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
GROQ_CHAT_COMPLETIONS_URL = f"{GROQ_API_BASE_URL}/chat/completions"

# Session memory & agent
MAX_SESSION_TURNS = int(os.getenv("MAX_SESSION_TURNS", "10"))
MAX_AGENT_STEPS = 4

# API
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8001"))
