import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from src.config import CLEANED_DATA_PATH, TEMPLATES_DIR
from src.ingestion import run_ingestion
from src.filter import filter_restaurants
from src.llm_client import get_recommendations, RecommendationResponse

# Global variable to store loaded DataFrame in memory
db_df = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_df
    print("Initializing application dependencies...")
    # Trigger ingestion if cleaned dataset doesn't exist
    if not CLEANED_DATA_PATH.exists():
        print(f"{CLEANED_DATA_PATH} not found. Triggering dataset ingestion...")
        run_ingestion()
    
    # Load dataset into memory
    print(f"Loading cleaned dataset from {CLEANED_DATA_PATH}...")
    db_df = pd.read_csv(CLEANED_DATA_PATH)
    print(f"Dataset loaded. Number of records: {len(db_df)}")
    yield
    print("Application shutdown complete.")

app = FastAPI(
    title="Zomato AI Recommendation Portal",
    lifespan=lifespan
)

# Input request schema
class RecommendRequest(BaseModel):
    location: str = ""
    cuisine: str = ""
    budget_tier: str = ""
    min_rating: float = 0.0
    description: str = ""

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    """Serves the dashboard front-end single-page application."""
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendRequest):
    """Processes user parameters, filters dataset candidates, and uses Gemini to recommend."""
    global db_df
    if db_df is None:
        raise HTTPException(status_code=500, detail="Database is not initialized.")

    try:
        # 1. Filter candidates using relational criteria
        candidates = filter_restaurants(
            df=db_df,
            location=request.location,
            cuisine=request.cuisine,
            budget_tier=request.budget_tier,
            min_rating=request.min_rating,
            limit=15  # Extract top 15 candidate matches for reasoning context
        )

        # 2. Query LLM to rank and provide context-specific recommendations
        # If candidates df is empty, get_recommendations handles it gracefully
        recommendations = get_recommendations(
            candidates_df=candidates,
            user_description=request.description
        )
        return recommendations

    except Exception as e:
        print(f"Error serving recommendation request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
