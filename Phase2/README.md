# Phase 2: Hybrid Retrieval & Vector Database

Semantic search (ChromaDB + local embeddings) combined with strict pandas filters from Phase 1. Natural-language queries (e.g. *"quiet rooftop with good views"*) are ranked within hard-filtered candidates before the LLM step.

## Prerequisites

```powershell
cd d:\Milestone_01\Phase2
pip install -r requirements.txt
```

Optional: copy `.env` from project root with `GEMINI_API_KEY` for LLM explanations (mock responses work without it).

## Quick start

### 1. Build enriched dataset (first time)

Downloads from Hugging Face and adds `search_text` + review snippets:

```powershell
python -m src.ingestion
```

Output: `data/zomato_enriched.csv`

### 2. Build vector index

**Full dataset (~51k rows)** — expect **1–2 hours on CPU**. Progress prints every batch if output is unbuffered:

```powershell
$env:PYTHONUNBUFFERED="1"
python -m src.main --build-index
```

**Faster test run** (subset only):

```powershell
python -m src.main --build-index --max-rows 5000
```

**Rebuild from scratch** (drops existing Chroma collection):

```powershell
python -m src.main --build-index --rebuild-index
```

Index is stored under `chroma_db/`. If a run stops midway, run `--build-index` again — it **resumes** and skips rows already indexed.

### 3. Search

**Interactive CLI:**

```powershell
python -m src.main
```

**One-shot (filters + soft query):**

```powershell
python -m src.main --location Banashankari --cuisine Italian --budget medium --min-rating 4.0 --query "quiet rooftop with good views"
```

**Hybrid results only (no LLM):**

```powershell
python -m src.main --location BTM --query "family friendly" --no-llm
```

## Project layout

```
Phase2/
├── data/zomato_enriched.csv   # enriched CSV with search_text
├── chroma_db/                 # persisted vector index
├── src/
│   ├── ingestion.py           # HF download + review snippets
│   ├── embeddings.py          # sentence-transformers (all-MiniLM-L6-v2)
│   ├── vector_store.py        # ChromaDB index + semantic ranking
│   ├── hybrid.py              # pandas filters → semantic top-k
│   ├── filter.py              # hard filters (location, cuisine, budget, rating)
│   ├── llm_client.py          # Gemini ranking + explanations
│   └── main.py                # CLI entry point
└── requirements.txt
```

## Troubleshooting

| Issue | What to do |
|-------|------------|
| Build looks frozen | Set `$env:PYTHONUNBUFFERED="1"` and wait; first batch can take ~1 min after model load. |
| Interrupted index | Run `python -m src.main --build-index` again to resume. |
| Too slow on CPU | Use `--max-rows 5000` for dev, or let full build run overnight. |
| No LLM output | Set `GEMINI_API_KEY` in `.env`; otherwise mock explanations are used. |

## Flow (architecture)

```
User filters → pandas (strict) → Chroma semantic rank (top 15) → LLM (top 5 + explanations)
```

See `Docs/architecture.md` for the full roadmap (Phase 3: FastAPI, Phase 4: Web UI).
