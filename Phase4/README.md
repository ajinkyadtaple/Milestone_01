# Phase 4: Premium Web UI

Zomato-inspired frontend that talks **only** to the Phase 3 API (`http://127.0.0.1:8001` by default).

## Features

- Filter bar: location, cuisine, budget tier ($ / $$ / $$$), max cost (₹), min rating
- Soft-preference search text → hybrid + Groq recommendations
- Shimmer skeleton loaders and step-by-step progress
- Restaurant cards with rating, tags, and AI explanation panel
- Floating **follow-up chat** (uses `session_id` from Phase 3)
- API health indicator in the header

## Run the full stack

**Terminal 1 — Backend (required):**

```powershell
cd d:\Milestone_01\Phase3
python -m src.main
```

**Terminal 2 — Frontend:**

```powershell
cd d:\Milestone_01\Phase4
pip install -r requirements.txt
python server.py
```

Open **http://127.0.0.1:8080**

## Configuration

| Setting | How |
|---------|-----|
| Phase 3 URL | Default `http://127.0.0.1:8001` in `public/js/config.js` |
| Override | `http://127.0.0.1:8080?api=http://localhost:8001` |
| Persist override | Saved to `localStorage` key `zomato_api_base` |

Groq and dataset setup: see `Phase3/README.md` and `Phase2/README.md`.

## Project layout

```
Phase4/
├── server.py           # Static file server (port 8080)
├── public/
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── config.js   # API base URL
│       └── app.js      # Phase 3 client
└── requirements.txt
```

## API mapping

| UI | `POST /recommend` field |
|----|-------------------------|
| Location | `location` |
| Cuisine | `cuisine` |
| Budget tier buttons | `budget_tier` |
| Max cost (₹) | `max_cost` |
| Min rating | `min_rating` |
| Soft preferences | `description` |
| Chat follow-up | `session_id` + `description` |
