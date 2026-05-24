"""Test Phase 3 backend + Phase 4 frontend on localhost."""
import json
import sys
import urllib.request

API = "http://127.0.0.1:8001"
UI = "http://127.0.0.1:8080"


def get(url: str) -> dict:
    return json.loads(urllib.request.urlopen(url, timeout=30).read())


def post(url: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


def main() -> int:
    print("=== Local stack test ===\n")
    errors = 0

    try:
        h = get(f"{API}/health")
        print(f"[OK] Backend /health: {h['status']} | records={h['records']} | chroma={h['vector_index_count']}")
    except Exception as e:
        print(f"[FAIL] Backend /health: {e}")
        errors += 1

    try:
        html = urllib.request.urlopen(f"{UI}/", timeout=10).read().decode()
        ok = "Zomato" in html and "PHASE 4" in html
        print(f"[OK] Frontend / : page loaded ({'PASS' if ok else 'WARN: missing markers'})")
        if not ok:
            errors += 1
    except Exception as e:
        print(f"[FAIL] Frontend / : {e}")
        errors += 1

    for path in ("/css/styles.css", "/js/app.js", "/js/config.js"):
        try:
            r = urllib.request.urlopen(f"{UI}{path}", timeout=10)
            print(f"[OK] Frontend {path} -> HTTP {r.status}")
        except Exception as e:
            print(f"[FAIL] Frontend {path}: {e}")
            errors += 1

    print("\nCalling POST /recommend (Bellandur, max_cost=2000, rating>=4)...")
    try:
        body = {
            "location": "Bellandur",
            "min_rating": 4.0,
            "max_cost": 2000,
            "description": "good ambience, family friendly",
        }
        r = post(f"{API}/recommend", body)
        recs = r.get("recommendations", [])
        print(f"[OK] Recommend: session={r['session_id'][:12]}... tools={r.get('tools_used')} count={len(recs)}")
        for i, rec in enumerate(recs[:5], 1):
            expl = rec.get("explanation", "")
            if len(expl) > 90:
                expl = expl[:90] + "..."
            print(f"  {i}. {rec['name']} | {rec['rating']}* | Rs.{rec['cost']} @ {rec['location']}")
            print(f"     {expl}")
        if not recs:
            print("[WARN] No recommendations returned")
    except Exception as e:
        print(f"[FAIL] POST /recommend: {e}")
        errors += 1

    print()
    if errors:
        print(f"FAILED ({errors} check(s))")
        return 1
    print("PASS — Open http://127.0.0.1:8080 in your browser")
    print("      API docs: http://127.0.0.1:8001/docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
