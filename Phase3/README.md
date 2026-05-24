# Phase 3: REST API & Agentic Memory

Production-style FastAPI backend with **in-memory session memory** and a **ReAct agent** that picks search tools (structured filter, hybrid vector search, follow-up refinement, or filter relaxation).

Depends on Phase 2 data (`Phase2/data/zomato_enriched.csv`) and Chroma index (`Phase2/chroma_db/`).

## Setup

```powershell
cd d:\Milestone_01\Phase3
pip install -r requirements.txt
```

Ensure Phase 2 ingestion and index are done (see `Phase2/README.md`).

Copy the example env file and set your Groq API key:

```powershell
copy .env.example .env
```

Edit `.env` — see `.env.example` for all supported variables.

## Run server

```powershell
cd d:\Milestone_01\Phase3
python -m src.main
```

Default: `http://127.0.0.1:8001` — interactive docs at `/docs`.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Dataset load status, vector index size, active sessions |
| `POST` | `/recommend` | Agent-driven recommendations (supports `session_id`) |
| `DELETE` | `/session/{session_id}` | Clear conversation memory |

### `POST /recommend` example

```json
{
  "location": "Banashankari",
  "cuisine": "Italian",
  "budget_tier": "medium",
  "min_rating": 4.0,
  "description": "quiet rooftop place with good views"
}
```

Response includes `session_id` — send it on follow-ups:

```json
{
  "session_id": "abc-123-...",
  "description": "show me the first one but with outdoor seating"
}
```

### Health check

```powershell
curl http://127.0.0.1:8001/health
```

## Agent tools

1. **structured_search** — pandas hard filters only  
2. **hybrid_search** — filters + Chroma semantic ranking  
3. **refine_previous** — follow-up on a prior recommendation (e.g. “the first one…”)  
4. **relax_filters** — loosen constraints when zero results  
5. **format_recommendations** — LLM ranking and explanations  

The planner and recommendation formatter use **Groq** (`POST https://api.groq.com/openai/v1/chat/completions`) when `GROQ_API_KEY` is set; otherwise rule-based routing and mock explanations apply.

## Project layout

```
Phase3/
├── src/
│   ├── main.py           # FastAPI app
│   ├── agent.py          # ReAct orchestrator
│   ├── session_memory.py # In-memory sessions
│   ├── tools.py          # Search tools
│   ├── hybrid.py         # Phase 2 hybrid retrieval
│   └── ...
└── requirements.txt
```

See `Docs/architecture.md` for Phase 4 (Web UI).
