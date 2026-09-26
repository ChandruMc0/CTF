#!/usr/bin/env python3
import io, json, zlib, struct, urllib.request, urllib.error, http.cookiejar

BASE="https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
def sess():
    cj=http.cookiejar.CookieJar()
    o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)); o.addheaders=[("User-Agent","Mozilla/5.0")]; return o
def do(o,path,data=None,headers=None,method=None):
    r=urllib.request.Request(BASE+path,data=data,method=method)
    for k,v in (headers or {}).items(): r.add_header(k,v)
    try:
        resp=o.open(r,timeout=90); return resp.status,dict(resp.getheaders()),resp.read()
    except urllib.error.HTTPError as e: return e.code,dict(e.headers),e.read()
    except Exception as e: return -1,{},str(e).encode()
def upload(o,fn,content,ct):
    bd="----x"; body=io.BytesIO()
    body.write((f"--{bd}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\nContent-Type: {ct}\r\n\r\n").encode())
    body.write(content); body.write(f"\r\n--{bd}--\r\n".encode())
    return do(o,"/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={bd}"},method="POST")
def render(o,**kw):
    st,h,b=do(o,"/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    try: return json.loads(b)
    except: return b.decode('utf-8','replace')

def png(w=16,h=16,color=(200,60,60)):
    raw=b""
    for y in range(h):
        raw+=b"\x00"+bytes(color*w)
    def chunk(t,d): return struct.pack(">I",len(d))+t+d+struct.pack(">I",zlib.crc32(t+d)&0xffffffff)
    ihdr=struct.pack(">IIBBBBB",w,h,8,2,0,0,0)
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(raw,9))+chunk(b"IEND",b"")

# 1. upload an image (no audio stream) -> showwavespic mapping fails -> ffmpeg echoes filtergraph
o=sess(); do(o,"/studio")
st,h,b=upload(o,"clip.png",png(),"image/png")
print("upload png status",st)
j=render(o,slug="p",theme="midnight")
err=(j.get("errors") if isinstance(j,dict) else str(j)) or ""
print("ok=",j.get("ok") if isinstance(j,dict) else None)
print("=====FULL STDERR (image input)=====")
print(err)
print("\n\n")

# 2. also try jpg extension
o=sess(); do(o,"/studio")
upload(o,"clip.jpg",png(),"image/jpeg")
j=render(o,slug="p",theme="midnight")
err=(j.get("errors") if isinstance(j,dict) else str(j)) or ""
print("=====STDERR (jpg-ext png)===== ok=",j.get('ok') if isinstance(j,dict) else None)
print(err[-1500:])
print("DONE")
