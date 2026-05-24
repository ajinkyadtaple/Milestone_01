import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PHASE2_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PHASE2_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Enriched dataset with search_text for embeddings
ENRICHED_DATA_PATH = DATA_DIR / "zomato_enriched.csv"
# Fallback to Phase 1 cleaned data if enrichment not run yet
PHASE1_CLEANED_PATH = PHASE2_ROOT.parent / "Phase1" / "data" / "zomato_cleaned.csv"

CHROMA_DIR = PHASE2_ROOT / "chroma_db"
CHROMA_COLLECTION = "restaurants"

BUDGET_LOW_MAX = 400
BUDGET_MEDIUM_MAX = 1000

# Embedding model (local, no API key)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBED_BATCH_SIZE = 64
# Truncate indexed text so CPU embedding stays fast (full text kept in CSV)
MAX_INDEX_TEXT_CHARS = 512
# Optional cap for dev runs: set INDEX_MAX_ROWS=5000 in .env or use --max-rows
INDEX_MAX_ROWS = int(os.getenv("INDEX_MAX_ROWS", "0")) or None

# Hybrid retrieval limits (architecture: top 10-15 for LLM context)
HYBRID_TOP_K = 15
SEMANTIC_TOP_K = 15

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = "gemini-2.5-flash"
