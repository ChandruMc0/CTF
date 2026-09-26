#!/usr/bin/env python3
import io, json, re, base64, urllib.request, urllib.error, http.cookiejar

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent","Mozilla/5.0")]

def do(path, data=None, headers=None, method=None):
    r = urllib.request.Request(BASE + path, data=data, method=method)
    for k, v in (headers or {}).items(): r.add_header(k, v)
    try:
        resp = op.open(r, timeout=40); return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()

def showcookies():
    for c in cj:
        print(f"  cookie {c.name}={c.value[:120]}")
        if c.value.count('.')==2:
            for part in c.value.split('.')[:2]:
                try:
                    pad=part+'='*(-len(part)%4)
                    print("     jwt part:", base64.urlsafe_b64decode(pad).decode('utf-8','replace'))
                except Exception as e: print("     (decode fail)",e)

print("===== landing =====")
st,h,b=do("/")
print("status",st)
for k in ["Set-Cookie","Server","X-Powered-By","Content-Security-Policy"]:
    if k in h: print(f"  {k}: {h[k]}")

print("\n===== try signup + login to capture session cookie =====")
import random
u=f"user{random.randint(1000,9999)}"
for path,payload in [("/signup",{"email":f"{u}@x.com","password":"Passw0rd!","name":u}),
                     ("/login",{"email":f"{u}@x.com","password":"Passw0rd!"})]:
    for ct,data in [("json",json.dumps(payload).encode()),
                    ("form",urllib.parse.urlencode(payload).encode() if False else None)]:
        pass
    st,h,b=do(path, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"}, method="POST")
    print(f"{path} json -> {st}  setcookie={h.get('Set-Cookie','-')[:150]}")
import urllib.parse
# also form-encoded
st,h,b=do("/login", data=urllib.parse.urlencode({"email":f"{u}@x.com","password":"Passw0rd!"}).encode(),
          headers={"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
print(f"/login form -> {st} setcookie={h.get('Set-Cookie','-')[:150]}")
print("cookies now:"); showcookies()

print("\n===== dump ALL inline scripts on /studio =====")
st,h,b=do("/studio")
html=b.decode('utf-8','replace')
print("studio status",st,"len",len(html))
for m in re.finditer(r"<script[^>]*>(.*?)</script>", html, re.S):
    s=m.group(1).strip()
    if s: print("---- inline script ----\n"+s[:3000])
for m in re.finditer(r'<script[^>]*src="([^"]+)"', html):
    print("ext script src:", m.group(1))

print("\n===== endpoint probe =====")
for p in ["/admin","/account","/api/me","/api/user","/api/account","/dashboard","/settings",
          "/feed","/feed.xml","/rss","/rss.xml","/api/feeds","/robots.txt","/sitemap.xml",
          "/.env","/package.json","/server.js","/app.js","/api/flag","/flag","/api/config",
          "/api/render.js","/static/studio.js","/js/studio.js","/assets/studio.js","/main.js"]:
    st,h,b=do(p)
    body=b.decode('utf-8','replace')
    is404 = st==404 or "could not find that page" in body.lower()
    if not is404:
        print(f"  {p:22} {st} ct={h.get('Content-Type','')[:30]} len={len(b)} snip={re.sub(chr(92)+'s+',' ',body)[:120]!r}")
print("\nDONE")
