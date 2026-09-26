#!/usr/bin/env python3
import io, json, struct, math, urllib.request, urllib.error, http.cookiejar

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"

def newsess():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0 studio")]
    return op

def do(op, path, data=None, headers=None, method=None):
    r = urllib.request.Request(BASE + path, data=data, method=method)
    for k, v in (headers or {}).items(): r.add_header(k, v)
    try:
        resp = op.open(r, timeout=90); return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()

def make_wav(seconds=1, rate=8000):
    n=seconds*rate
    fr=b"".join(struct.pack("<h",int(3000*math.sin(2*math.pi*220*i/rate))) for i in range(n))
    return b"RIFF"+struct.pack("<I",36+len(fr))+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,rate,rate*2,2,16)+b"data"+struct.pack("<I",len(fr))+fr

def upload(op, fn):
    b="----wbnd"; body=io.BytesIO()
    body.write((f"--{b}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\n"
                f"Content-Type: audio/wav\r\n\r\n").encode()); body.write(make_wav()); body.write(b"\r\n")
    body.write(f"--{b}--\r\n".encode())
    return do(op,"/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={b}"},method="POST")

def render(op, **kw):
    st,h,b=do(op,"/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    try: return st, json.loads(b)
    except: return st, b.decode('utf-8','replace')

# Test whether the ORIGINAL UPLOAD FILENAME flows into the ffmpeg filtergraph (drawtext).
fns = ["probe.wav", "pr:obe.wav", "pr'obe.wav", "pr\\obe.wav", "a=b.wav",
       "cap[tion].wav", "x,y.wav", "he:llo:wav", "name%{n}.wav"]
for fn in fns:
    op = newsess()
    do(op,"/studio")
    st,h,b = upload(op, fn)
    # what does upload echo as the stored clip name?
    body = b.decode('utf-8','replace')
    import re
    chip = re.search(r'clip-chip.*?<span class="mono">([^<]*)</span>', body, re.S)
    st2,j = render(op, slug="poster", theme="midnight")
    ok = j.get("ok") if isinstance(j,dict) else None
    err = (j.get("errors") if isinstance(j,dict) else j) or ""
    print(f"\n################ filename={fn!r} chip={chip.group(1) if chip else None!r} render_ok={ok}")
    if err:
        # show only the meaningful filter/parse portion
        low = err.find("Stream mapping")
        seg = err[max(0,err.find("Input #0")):]
        print(seg[:2500])

print("\nDONE")
