"""Quick local test for Phase 3 API + Phase 4 UI."""
import json
import os
import sys
import urllib.request

API_BASE = os.getenv("STACK_API_URL", "http://127.0.0.1:8001").rstrip("/")
UI_BASE = os.getenv("STACK_UI_URL", "http://127.0.0.1:8080").rstrip("/")


def get(url: str, timeout: int = 30) -> dict:
    return json.loads(urllib.request.urlopen(url, timeout=timeout).read())


def post(url: str, body: dict, timeout: int = 120) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def main() -> int:
    print("=== Local stack test ===\n")
    print(f"UI:  {UI_BASE}")
    print(f"API: {API_BASE}\n")

    try:
        html = urllib.request.urlopen(f"{UI_BASE}/", timeout=10).read().decode()
        ok_ui = "Zomato" in html or "Phase" in html
        print(f"UI : {'OK' if ok_ui else 'FAIL'}")
        if not ok_ui:
            return 1
    except Exception as e:
        print(f"UI : FAIL - {e}")
        return 1

    try:
        health = get(f"{API_BASE}/health")
        print(f"API health: OK (records={health.get('records')})")
    except Exception as e:
        print(f"API health: FAIL - {e}")
        return 1

    try:
        result = post(
            f"{API_BASE}/recommend",
            {
                "location": "Bellandur",
                "min_rating": 4.0,
                "max_cost": 2000,
                "description": "good ambience for dinner",
            },
        )
        recs = result.get("recommendations", [])
        print(f"POST /recommend: OK — {len(recs)} recommendations")
        for i, rec in enumerate(recs[:3], 1):
            print(f"  {i}. {rec.get('name')} ({rec.get('rating')})")
    except Exception as e:
        print(f"POST /recommend: FAIL - {e}")
        return 1

    print("\n=== All tests passed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
