#!/usr/bin/env python3
import io, json, re, urllib.request, urllib.error, http.cookiejar, struct, math

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
def sess():
    cj=http.cookiejar.CookieJar()
    o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    o.addheaders=[("User-Agent","Mozilla/5.0")]; return o
def do(o, path, data=None, headers=None, method=None):
    r=urllib.request.Request(BASE+path, data=data, method=method)
    for k,v in (headers or {}).items(): r.add_header(k,v)
    try:
        resp=o.open(r,timeout=60); return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e: return e.code, dict(e.headers), e.read()
    except Exception as e: return -1,{},str(e).encode()
def wav():
    n=8000; fr=b"".join(struct.pack("<h",int(4000*math.sin(2*math.pi*300*i/8000))) for i in range(n))
    return b"RIFF"+struct.pack("<I",36+len(fr))+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,8000,16000,2,16)+b"data"+struct.pack("<I",len(fr))+fr
def upload(o, fn, content=None, ct="audio/wav"):
    bd="----x"; body=io.BytesIO()
    body.write((f"--{bd}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\nContent-Type: {ct}\r\n\r\n").encode())
    body.write(content or wav()); body.write(f"\r\n--{bd}--\r\n".encode())
    return do(o,"/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={bd}"},method="POST")

def show(tag, st, h, b):
    body=b.decode('utf-8','replace')
    print(f"\n===== {tag} -> {st} ct={h.get('Content-Type','')[:30]} len={len(b)} =====")
    print(body[:1800])

o=sess(); do(o,"/studio")

# 1. null byte in filename -> 500 stack?
st,h,b=upload(o,"x.wav\x00.png"); show("upload null-byte filename", st,h,b)

# 2. render with non-JSON / malformed body
st,h,b=do(o,"/api/render",data=b"{bad json", headers={"Content-Type":"application/json"}, method="POST"); show("render malformed json", st,h,b)

# 3. render with slug as wrong types
for payload in ['{"slug":{"a":1},"theme":"midnight"}','{"slug":["x"],"theme":"midnight"}',
                '{"slug":123,"theme":"midnight"}','{"theme":"midnight"}','{"slug":null,"theme":null}']:
    st,h,b=do(o,"/api/render",data=payload.encode(),headers={"Content-Type":"application/json"},method="POST")
    show(f"render {payload}", st,h,b)

# 4. very long slug (buffer/pathmax) 
st,h,b=do(o,"/api/render",data=json.dumps({"slug":"A"*5000,"theme":"midnight"}).encode(),headers={"Content-Type":"application/json"},method="POST"); show("render 5000-char slug", st,h,b)

# 5. render before any upload (fresh session)
o2=sess(); st,h,b=do(o2,"/api/render",data=json.dumps({"slug":"p","theme":"midnight"}).encode(),headers={"Content-Type":"application/json"},method="POST"); show("render no-upload", st,h,b)

# 6. upload with array field / wrong field name
bd="----x"; body=io.BytesIO()
body.write((f"--{bd}\r\nContent-Disposition: form-data; name=\"wrongfield\"; filename=\"x.wav\"\r\nContent-Type: audio/wav\r\n\r\n").encode())
body.write(wav()); body.write(f"\r\n--{bd}--\r\n".encode())
st,h,b=do(o,"/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={bd}"},method="POST"); show("upload wrong field name", st,h,b)

# 7. GET the /studio/upload (method mismatch) and a random 404 to see error page style
st,h,b=do(o,"/studio/upload"); show("GET /studio/upload", st,h,b)
st,h,b=do(o,"/nonexistent-xyz"); show("404 page", st,h,b)
print("\nDONE")
