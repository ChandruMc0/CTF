#!/usr/bin/env python3
import io, json, struct, math, urllib.request, urllib.error, http.cookiejar

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

def upload():
    b="----wbnd"; body=io.BytesIO()
    body.write(f"--{b}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"clip.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode()); body.write(make_wav()); body.write(b"\r\n")
    body.write(f"--{b}--\r\n".encode())
    return do("/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={b}"},method="POST")

def render(**kw):
    st,h,b=do("/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    try: return st, json.loads(b)
    except: return st, b.decode('utf-8','replace')

do("/studio"); upload()

# slugs designed to break the drawtext/filtergraph so ffmpeg echoes the graph
probes = ["ok_baseline", "a:b", "a'b", 'a"b', "a\\b", "a]b", "a[b", "a,b", "a;b",
          "a=b", "a%b", "a{b", "a}b", "a:x=10", "'", "]", "[in]"]
for s in probes:
    st,j=render(slug=s, theme="midnight")
    err = j.get("errors") if isinstance(j,dict) else j
    ok = j.get("ok") if isinstance(j,dict) else None
    print(f"\n################ slug={s!r} ok={ok} ################")
    if err:
        # print the parts that matter: filter/parse errors, and the command echo
        print(err[:4000])
    else:
        print("(no errors; outputs:", j.get("outputs"), ")")

print("\nDONE")
