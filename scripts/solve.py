#!/usr/bin/env python3
import urllib.request, urllib.error, http.cookiejar, re, concurrent.futures
BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
def do(path, method="GET", data=None, ct=None):
    cj=http.cookiejar.CookieJar()
    op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders=[("User-Agent","Mozilla/5.0")]
    r=urllib.request.Request(BASE+path, data=data, method=method)
    if ct: r.add_header("Content-Type",ct)
    try:
        resp=op.open(r,timeout=25); return resp.status, resp.read()
    except urllib.error.HTTPError as e: return e.code, e.read()
    except Exception as e: return -1, str(e).encode()

APP404 = "could not find that page"
def check(p):
    st,b=do(p)
    body=b.decode('utf-8','replace')
    if st in (0,-1): return None
    is404 = APP404 in body.lower()
    if not is404 and st not in (400,):
        return (p, st, len(b), re.sub(r"\s+"," ",body)[:90])
    if st not in (404,) and not is404:
        return (p, st, len(b), re.sub(r"\s+"," ",body)[:90])
    return None

words = """admin administrator login signin sign-in signup register logout account accounts user users
profile me settings config configuration api v1 api/v1 internal debug dev test status health healthz
metrics ping version info about-us dashboard console panel manage management studio/render studio/export
studio/download studio/list studio/workspace studio/session studio/status render export download list
media clips clip posters poster audiograms audiogram feed feeds rss podcast podcasts show shows episode
episodes upload uploads files file download downloads job jobs queue task tasks worker workers analytics
stats billing plans subscribe secret secrets flag flags key keys token tokens .git .git/config .gitignore
.env .env.local env config.json app.json manifest.json package.json package-lock.json yarn.lock server
index main routes lib src public/js public/app.js robots sitemap sitemap.xml humans.txt security.txt
.well-known/security.txt api/render api/upload api/status api/health api/me api/user api/session api/config
api/flag api/clips api/render/status api/export api/jobs api/media api/workspace api/studio backup backups
db database dump sql data storage tmp temp cache logs log""".split()

print("Brute results (non-404):")
found=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
    for r in ex.map(check, ["/"+w for w in words]):
        if r: found.append(r); print(f"  {r[0]:34} {r[1]} len={r[2]} {r[3]!r}")
print("total hits:", len(found))

print("\nMethods on /api/render and /studio/upload:")
for m in ["GET","PUT","DELETE","PATCH","OPTIONS","HEAD"]:
    st,b=do("/api/render", method=m, data=(b"{}" if m in("PUT","PATCH") else None), ct="application/json")
    print(f"  render {m:7} -> {st} {b[:80]!r}")
    st,b=do("/studio/upload", method=m)
    print(f"  upload {m:7} -> {st} {b[:60]!r}")
print("\nDONE")
