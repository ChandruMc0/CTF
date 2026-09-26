#!/usr/bin/env python3
"""Poll the challenge until it is running again; report status transitions."""
import time
import requests

BASE = "https://fe91f95d-5707-merged-1a287.mystery-challenges.webverselabs-pro.com"

deadline = time.time() + 420
seen = None
while time.time() < deadline:
    try:
        r = requests.get(f"{BASE}/", timeout=15,
                         headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"})
        running = "Mystery challenge not running" not in r.text
        state = f"UP ({r.status_code}, len={len(r.text)})" if running else f"DOWN ({r.status_code})"
    except Exception as e:
        state = f"ERR {type(e).__name__}: {e}"
    if state != seen:
        print(f"{time.strftime('%H:%M:%S')} -> {state}", flush=True)
        seen = state
        if state.startswith("UP"):
            print(r.text[:2000])
            break
    time.sleep(20)
print("final:", seen)
