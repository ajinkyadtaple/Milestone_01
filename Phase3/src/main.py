"""
Phase 3: FastAPI server with session memory and ReAct agent orchestration.
"""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from contextlib import asynccontextmanager
from typing import Any, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import API_HOST, API_PORT, ENRICHED_DATA_PATH, MAX_SESSION_TURNS

# Heavy modules (agent, chroma, groq) load in lifespan — keeps uvicorn startup fast
db_df: pd.DataFrame | None = None
vector_store: Any = None
session_memory: Any = None
agent: Any = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_df, vector_store, session_memory, agent

    from src.agent import RecommendationAgent
    from src.session_memory import SessionMemory
    from src.vector_store import NullVectorStore, RestaurantVectorStore

    if not ENRICHED_DATA_PATH.exists():
        raise RuntimeError(
            f"Enriched dataset not found at {ENRICHED_DATA_PATH}. "
            "Run Phase 2 ingestion first: cd Phase2 && python -m src.ingestion"
        )

    print(f"Loading dataset from {ENRICHED_DATA_PATH}...", flush=True)
    db_df = pd.read_csv(ENRICHED_DATA_PATH)
    if "restaurant_id" not in db_df.columns:
        db_df["restaurant_id"] = db_df.index.astype(str)

    print("Connecting to vector index (Chroma)...", flush=True)
    vector_store = NullVectorStore()
    indexed = 0
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(RestaurantVectorStore)
            vs = future.result(timeout=20)
        indexed = vs.count()
        vector_store = vs
        print(f"Chroma connected ({indexed} vectors).", flush=True)
    except FuturesTimeout:
        print("Warning: Chroma init timed out. Structured search only.", flush=True)
    except Exception as e:
        print(f"Warning: Chroma unavailable ({e}). Structured search only.", flush=True)

    session_memory = SessionMemory(max_turns=MAX_SESSION_TURNS)
    agent = RecommendationAgent(db_df, vector_store, session_memory)

    print(f"Ready: {len(db_df)} restaurants, Chroma index={indexed}", flush=True)
    if indexed == 0:
        print("Warning: Chroma index empty. Run Phase 2: python -m src.main --build-index")

    yield
    print("Phase 3 API shutdown.", flush=True)


app = FastAPI(
    title="Zomato AI API — Phase 3",
    description="REST API with session memory and ReAct agent for restaurant recommendations",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendRequest(BaseModel):
    session_id: Optional[str] = Field(default=None)
    location: str = ""
    cuisine: str = ""
    budget_tier: str = ""
    min_rating: float = 0.0
    max_cost: Optional[int] = Field(default=None)
    description: str = ""


class RecommendationItem(BaseModel):
    name: str
    rating: float
    cost: int
    cuisines: str
    location: str
    explanation: str


class RecommendResponse(BaseModel):
    session_id: str
    recommendations: List[RecommendationItem]
    message: str = ""
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    tools_used: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    dataset_loaded: bool
    records: int
    vector_index_count: int
    active_sessions: int


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        dataset_loaded=db_df is not None,
        records=len(db_df) if db_df is not None else 0,
        vector_index_count=vector_store.count() if vector_store else 0,
        active_sessions=session_memory.count() if session_memory else 0,
    )


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    if agent is None or db_df is None:
        raise HTTPException(status_code=503, detail="Service is still starting. Retry in a few seconds.")

    try:
        result = agent.run(
            session_id=request.session_id,
            message=request.description,
            location=request.location,
            cuisine=request.cuisine,
            budget_tier=request.budget_tier,
            min_rating=request.min_rating,
            max_cost=request.max_cost,
            description=request.description,
        )
        return RecommendResponse(
            session_id=result.session_id,
            recommendations=[
                RecommendationItem(**r.model_dump()) for r in result.recommendations
            ],
            message=result.message,
            filters_applied=result.filters_applied,
            tools_used=result.tools_used,
        )
    except Exception as e:
        print(f"Recommend error: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    if session_memory is None:
        raise HTTPException(status_code=503, detail="Service not initialized.")
    if not session_memory.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"status": "deleted", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn

    print(f"Starting API on http://{API_HOST}:{API_PORT}", flush=True)
    uvicorn.run("src.main:app", host=API_HOST, port=API_PORT, reload=False)
