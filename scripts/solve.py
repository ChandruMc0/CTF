#!/usr/bin/env python3
import io, json, struct, math, re, urllib.request, urllib.error, http.cookiejar

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent","Mozilla/5.0 studio")]

def do(path, data=None, headers=None, method=None):
    r = urllib.request.Request(BASE + path, data=data, method=method)
    for k, v in (headers or {}).items(): r.add_header(k, v)
    try:
        resp = op.open(r, timeout=60); return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()

def is404(st,b):
    return st==404 or "could not find that page" in b.decode('utf-8','replace').lower() or "Cannot GET" in b.decode('utf-8','replace') or "Cannot POST" in b.decode('utf-8','replace')

do("/studio")
print("########## PAGES ##########")
for p in ["/about","/pricing"]:
    st,h,b=do(p)
    t=re.sub(r"<[^>]+>"," ",b.decode('utf-8','replace'))
    t=re.sub(r"\s+"," ",t)
    print(f"\n== {p} {st} ==\n{t[:900]}")

print("\n########## ROUTE FUZZ (GET & POST) ##########")
routes = ["/splice","/api/splice","/studio/splice","/combine","/api/combine","/merge","/api/merge",
    "/join","/api/join","/concat","/api/concat","/clips","/api/clips","/api/workspace","/workspace",
    "/api/clip","/clip","/studio/clips","/studio/clip","/api/upload","/api/render","/render",
    "/api/preview","/preview","/api/export","/export","/api/jobs","/jobs","/api/media","/media",
    "/api/session","/api/studio","/api/audiograms","/audiograms","/api/posters","/posters"]
for p in routes:
    stg,hg,bg=do(p)
    stp,hp,bp=do(p, data=b"{}", headers={"Content-Type":"application/json"}, method="POST")
    g = "404" if is404(stg,bg) else str(stg)
    pp = "404" if is404(stp,bp) else str(stp)
    if g!="404" or pp!="404":
        print(f"*** {p:22} GET={g:>4} POST={pp:>4}  POSTbody={re.sub(chr(92)+'s+',' ',bp.decode('utf-8','replace'))[:160]}")
    else:
        print(f"    {p:22} GET={g:>4} POST={pp:>4}")

print("\n########## render with multi-clip / playlist style params ##########")
def make_wav():
    n=8000; fr=b"".join(struct.pack("<h",int(3000*math.sin(2*math.pi*220*i/n))) for i in range(n))
    return b"RIFF"+struct.pack("<I",36+len(fr))+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,8000,16000,2,16)+b"data"+struct.pack("<I",len(fr))+fr
b="----x"; body=io.BytesIO()
body.write((f"--{b}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"c.wav\"\r\nContent-Type: audio/wav\r\n\r\n").encode()); body.write(make_wav()); body.write(b"\r\n--"+b.encode()+b"--\r\n")
do("/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={b}"},method="POST")
for kw in [
    {"slug":"p","theme":"midnight","clips":["a","b"]},
    {"slug":"p","theme":"midnight","tracks":["a","b"]},
    {"slug":"p","theme":"midnight","segments":[{"start":0,"end":5}]},
    {"slug":"p","theme":"midnight","splice":[{"start":0,"end":5}]},
    {"slug":"p","theme":"midnight","start":0,"end":9999},
    {"slug":"p","theme":"midnight","trim":{"start":0,"end":5}},
    {"slug":"p","theme":"midnight","duration":9999},
]:
    st,h,bb=do("/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    print(f"\n>> {json.dumps(kw)[:70]} -> {st} {bb.decode('utf-8','replace')[:200]}")

print("\nDONE")
