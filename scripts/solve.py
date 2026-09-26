#!/usr/bin/env python3
import re, urllib.request, urllib.error

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"

def req(path, cookie=None, headers=None, data=None, method=None):
    r = urllib.request.Request(BASE + path, data=data, method=method)
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

for p in ["/", "/studio", "/features"]:
    st, h, body = req(p)
    print("\n################ RAW", p, "status", st, "################")
    print("Set-Cookie:", h.get("Set-Cookie",""))
    print(body)

print("\n################ referenced assets ################")
st, h, body = req("/studio")
assets = set(re.findall(r'(?:src|href|action|data-\w+)\s*=\s*["\']([^"\']+)["\']', body))
for a in sorted(assets):
    print(" ", a)

# fetch js/css assets that look local
for a in sorted(assets):
    if a.startswith("/") and re.search(r"\.(js|css|json)$", a):
        st, h, b = req(a)
        print(f"\n===== {a} ({st}, {len(b)}b) =====")
        print(b[:4000])

print("\n################ endpoint probe ################")
for p in ["/api", "/api/studio", "/upload", "/api/upload", "/render", "/api/render",
          "/audiogram", "/api/audiogram", "/download", "/exports", "/export",
          "/studio/upload", "/studio/render", "/studio/export", "/workspace",
          "/.git/HEAD", "/package.json", "/server.js", "/app.js", "/source", "/robots.txt",
          "/public/", "/public/img/", "/uploads/", "/tmp/"]:
    st, h, b = req(p)
    is404 = st == 404 or "could not find that page" in b.lower() or "Cannot GET" in b
    print(f"{'   ' if is404 else '***'} {st:>4} {p:24} ct={h.get('Content-Type','')[:24]:24} {re.sub(chr(92)+'s+',' ',b)[:100]}")

print("\nDONE")
