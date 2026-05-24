"""
Phase 4 static UI server. Serves the frontend; all API calls go to Phase 3.
"""
import json
import os
import socket
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

PUBLIC_DIR = Path(__file__).resolve().parent / "public"
UI_HOST = os.getenv("UI_HOST", "127.0.0.1")
DEFAULT_UI_PORT = int(os.getenv("UI_PORT", "8080"))
API_BASE = os.getenv("PHASE3_API_BASE", "http://127.0.0.1:8001").rstrip("/")

app = FastAPI(title="Zomato AI — Phase 4 UI", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def pick_ui_port(host: str, preferred: int) -> int:
    if is_port_free(host, preferred):
        return preferred
    for port in range(preferred + 1, preferred + 20):
        if is_port_free(host, port):
            print(f"Port {preferred} in use — using {port} instead.", flush=True)
            return port
    raise RuntimeError(f"No free port found near {preferred}")


@app.get("/runtime-config.json")
async def runtime_config():
    return JSONResponse(
        {
            "apiBase": API_BASE,
            "uiBase": f"http://{UI_HOST}:{UI_PORT}",
        }
    )


@app.get("/")
async def index():
    return FileResponse(PUBLIC_DIR / "index.html")


app.mount("/css", StaticFiles(directory=PUBLIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=PUBLIC_DIR / "js"), name="js")

UI_PORT = DEFAULT_UI_PORT


if __name__ == "__main__":
    UI_PORT = pick_ui_port(UI_HOST, DEFAULT_UI_PORT)
    runtime_path = Path(__file__).resolve().parent.parent / ".stack_runtime.json"
    runtime_path.write_text(
        json.dumps(
            {
                "api": API_BASE,
                "ui": f"http://{UI_HOST}:{UI_PORT}",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Phase 4 UI:  http://{UI_HOST}:{UI_PORT}", flush=True)
    print(f"Phase 3 API: {API_BASE}", flush=True)
    print("Ensure Phase 3 is running: cd Phase3 && python -m uvicorn src.main:app --port 8001", flush=True)
    uvicorn.run(app, host=UI_HOST, port=UI_PORT)
