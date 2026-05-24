"""
Start Phase 3 (API) + Phase 4 (UI) locally and verify health.

Usage:
  python run_local.py          # start missing services, print links
  python run_local.py --test   # start + run integration test
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHASE3 = ROOT / "Phase3"
PHASE4 = ROOT / "Phase4"
ENRICHED_CSV = ROOT / "Phase2" / "data" / "zomato_enriched.csv"
RUNTIME_FILE = ROOT / ".stack_runtime.json"

API_HOST = "127.0.0.1"
API_PORT = int(os.getenv("API_PORT", "8001"))
UI_PORT = int(os.getenv("UI_PORT", "8080"))


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def probe_url(url: str, timeout: float = 3.0) -> bool:
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_for_api(timeout: float = 120.0) -> bool:
    url = f"http://{API_HOST}:{API_PORT}/health"
    deadline = time.time() + timeout
    print(f"Waiting for API at {url} ...", flush=True)
    while time.time() < deadline:
        if probe_url(url, timeout=5):
            return True
        time.sleep(2)
    return False


def wait_for_ui(timeout: float = 30.0) -> int | None:
    """Return port when UI responds, trying preferred and fallbacks."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for port in range(UI_PORT, UI_PORT + 15):
            url = f"http://{API_HOST}:{port}/"
            if probe_url(url, timeout=2):
                return port
        time.sleep(1)
    return None


def start_api() -> bool:
    """Start API if needed. Returns False on failure."""
    health = f"http://{API_HOST}:{API_PORT}/health"
    if probe_url(health, timeout=2):
        print(f"API already running on port {API_PORT}.", flush=True)
        return True

    if not is_port_free(API_HOST, API_PORT):
        print(f"ERROR: Port {API_PORT} is in use but API health check failed.", flush=True)
        print("       Stop the other process or set API_PORT to a free port.", flush=True)
        return False

    if not ENRICHED_CSV.exists():
        print(f"ERROR: Missing {ENRICHED_CSV}", flush=True)
        print("       Run: cd Phase2 && python -m src.ingestion", flush=True)
        return False

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    print(f"Starting Phase 3 API on port {API_PORT}...", flush=True)
    # Same shell background — avoids empty console windows on Windows
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            API_HOST,
            "--port",
            str(API_PORT),
        ],
        cwd=PHASE3,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    return wait_for_api(timeout=180)


def start_ui() -> int | None:
    """Start UI if needed. Returns UI port or None on failure."""
    existing = wait_for_ui(timeout=2)
    if existing is not None:
        print(f"UI already running on port {existing}.", flush=True)
        return existing

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["UI_PORT"] = str(UI_PORT)
    env["PHASE3_API_BASE"] = f"http://{API_HOST}:{API_PORT}"

    print(f"Starting Phase 4 UI (preferred port {UI_PORT})...", flush=True)
    subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=PHASE4,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    return wait_for_ui(timeout=25)


def write_runtime(ui_port: int) -> None:
    RUNTIME_FILE.write_text(
        json.dumps(
            {
                "api": f"http://{API_HOST}:{API_PORT}",
                "ui": f"http://{API_HOST}:{ui_port}",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def print_links(ui_port: int) -> None:
    ui = f"http://{API_HOST}:{ui_port}"
    api = f"http://{API_HOST}:{API_PORT}"
    print()
    print("=" * 50)
    print("  Zomato AI — ready to test locally")
    print("=" * 50)
    print(f"  App:        {ui}")
    print(f"  API health: {api}/health")
    print(f"  API docs:   {api}/docs")
    print("=" * 50)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Zomato AI stack locally")
    parser.add_argument("--test", action="store_true", help="Run test_local_stack.py after start")
    args = parser.parse_args()

    if not start_api():
        print("ERROR: Phase 3 API is not available.", flush=True)
        return 1

    ui_port = start_ui()
    if ui_port is None:
        print("ERROR: Phase 4 UI did not start.", flush=True)
        return 1

    write_runtime(ui_port)
    print_links(ui_port)

    if args.test:
        print("Running integration test...", flush=True)
        test_script = ROOT / "test_local_stack.py"
        if test_script.exists():
            env = os.environ.copy()
            env["STACK_API_URL"] = f"http://{API_HOST}:{API_PORT}"
            env["STACK_UI_URL"] = f"http://{API_HOST}:{ui_port}"
            return subprocess.call([sys.executable, str(test_script)], env=env)

    return 0


if __name__ == "__main__":
    sys.exit(main())
