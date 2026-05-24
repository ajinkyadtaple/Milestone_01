# Run Zomato AI locally

## One command (recommended)

```powershell
cd d:\Milestone_01
pip install -r Phase3\requirements.txt
pip install -r Phase4\requirements.txt
python run_local.py
```

With automated test:

```powershell
python run_local.py --test
```

## Links (after start)

| Service | URL |
|---------|-----|
| **Web app** | http://127.0.0.1:8080 |
| **API health** | http://127.0.0.1:8001/health |
| **API docs** | http://127.0.0.1:8001/docs |

If port 8080 is busy, the UI may use **8081** — check the terminal output or `.stack_runtime.json`.

## Manual start (two terminals)

**Terminal 1 — API**

```powershell
cd d:\Milestone_01\Phase3
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001
```

Wait for: `Ready: ... restaurants`

**Terminal 2 — UI**

```powershell
cd d:\Milestone_01\Phase4
python server.py
```

## Requirements

1. **Phase 2 data**: `Phase2\data\zomato_enriched.csv` (run `cd Phase2 && python -m src.ingestion` if missing)
2. **Groq API key**: copy `Phase3\.env.example` → `Phase3\.env` and set `GROQ_API_KEY`

## Streamlit UI (alternative)

```powershell
pip install -r requirements-streamlit.txt
streamlit run streamlit_app.py
```

Opens at http://localhost:8501 (uses Phase 3 agent in-process; set `GROQ_API_KEY` in `Phase3\.env`).

## UI design (Next.js via Google Stitch)

Prompts for generating mockups and screens: [Docs/google-stitch-ui-prompt.md](Docs/google-stitch-ui-prompt.md)

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ERR_CONNECTION_REFUSED` on 8080 | Run `python run_local.py` or `cd Phase4 && python server.py` |
| API offline in UI header | Start Phase 3 on port 8001 |
| Port already in use | Phase 4 auto-picks 8081+; or stop old `python server.py` windows |
| Chroma warning | Optional: `cd Phase2 && python -m src.main --build-index` |
