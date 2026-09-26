#!/usr/bin/env python3
"""Recon: register an issuer account and dump raw HTML of key pages."""
import re, sys, html
import requests

BASE = "https://fe91f95d-5707-merged-1a287.mystery-challenges.webverselabs-pro.com"

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"

def dump(name, r, maxlen=8000, show_headers=False):
    print(f"\n{'='*70}\n### {name}: {r.status_code} {r.url}")
    if show_headers:
        for k, v in r.headers.items():
            print(f"  H {k}: {v}")
    body = r.text
    print(body[:maxlen])
    if len(body) > maxlen:
        print(f"... [truncated, total {len(body)} bytes]")

r = s.get(f"{BASE}/", timeout=20)
print("SERVER HEADERS:")
for k, v in r.headers.items():
    print(f"  {k}: {v}")
print(f"\nCookies after GET /: {s.cookies.get_dict()}")

r = s.get(f"{BASE}/register", timeout=20)
dump("GET /register", r, 12000)

# find the form action and inputs
inputs = re.findall(r'<input[^>]*>', r.text)
print("\nINPUT TAGS ON /register:")
for i in inputs:
    print("  ", i)
m = re.search(r'<form[^>]*>', r.text)
print("\nFORM TAG:", m.group(0) if m else None)

# try to register
data = {}
for i in inputs:
    name = re.search(r'name="([^"]+)"', i)
    typ = re.search(r'type="([^"]+)"', i)
    val = re.search(r'value="([^"]*)"', i)
    if not name:
        continue
    n = name.group(1)
    t = typ.group(1) if typ else "text"
    if t == "hidden":
        data[n] = html.unescape(val.group(1)) if val else ""
    elif t == "email" or "email" in n:
        data[n] = "recon.bot+certmarq@example.org"
    elif t == "password" or "password" in n:
        data[n] = "Certmarq!Recon2026"
    else:
        # org name or anything else
        data[n] = "Recon Academy"
print("\nREGISTER POST DATA:", data)

action = f"{BASE}/register"
if m:
    act = re.search(r'action="([^"]*)"', m.group(0))
    if act:
        action = requests.compat.urljoin(f"{BASE}/register", act.group(1))
r = s.post(action, data=data, allow_redirects=True, timeout=20)
dump("POST register (followed)", r, 12000)
print(f"\nCookies now: {s.cookies.get_dict()}")

# probe common authenticated pages
for path in ["/dashboard", "/designer", "/templates", "/design", "/certificates",
             "/roster", "/learners", "/settings", "/logout", "/preview"]:
    try:
        rr = s.get(f"{BASE}{path}", allow_redirects=False, timeout=20)
        loc = rr.headers.get("Location", "")
        print(f"GET {path}: {rr.status_code} {('-> '+loc) if loc else ''} len={len(rr.text)}")
    except Exception as e:
        print(f"GET {path}: ERR {e}")
