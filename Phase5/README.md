# Phase 5: Streamlit Cloud deployment

Hosted Streamlit UI that runs the **Phase 3 agent in-process** — no separate FastAPI server. Designed for free deployment on [Streamlit Community Cloud](https://share.streamlit.io).

## Features

- Light Zomato-themed UI (aligned with `Screens/zomato-ai-home/`)
- Sidebar filters: location, cuisine, budget tier, max cost (₹), min rating, contextual preferences
- In-process hybrid search + Groq-ranked recommendations
- Multi-turn follow-up chat with session memory
- Header: Beta badge, API status, session ID, new session
- Metrics: restaurant count, vector index size, active session

## Run locally

**From Phase 5 folder:**

```powershell
cd d:\Milestone_01\Phase5
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**From repo root (Streamlit Cloud entrypoint):**

```powershell
cd d:\Milestone_01
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Open **http://localhost:8501**

## Deploy to Streamlit Cloud (free)

1. Push repo to GitHub.
2. [share.streamlit.io](https://share.streamlit.io) → **Create app** → select repo.
3. **Main file path:** `streamlit_app.py` (repo root).
4. **Secrets** (Settings → Secrets), from `.streamlit/secrets.toml.example`:

```toml
GROQ_API_KEY = "your_key"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

5. Deploy → `https://<app-name>.streamlit.app`

## Requirements

| Item | Location |
|------|----------|
| Enriched CSV | `Phase2/data/zomato_enriched.csv` |
| Groq API key | `Phase3/.env` locally or Streamlit **Secrets** |
| Chroma index | Optional — structured search fallback if missing |

## Project layout

```
Phase5/
├── streamlit_app.py      # Main Streamlit app
├── requirements.txt
├── .env.example
└── src/
    ├── config.py         # Env, filters, Phase 3 path
    ├── stack.py          # @st.cache_resource agent loader
    └── ui.py             # Theme + components
```

Repo root `streamlit_app.py` delegates here for Streamlit Cloud compatibility.

## vs Phase 4

| | Phase 4 | Phase 5 |
|---|---------|---------|
| Backend | Separate FastAPI :8001 | Agent in-process |
| UI | Custom HTML/JS | Streamlit |
| Hosting | Vercel / local | Streamlit Cloud |

See [Docs/architecture.md](../Docs/architecture.md) for full Phase 5 architecture.
