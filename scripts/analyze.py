#!/usr/bin/env python3
import re,base64,json,numpy as np
from PIL import Image

raw=open('results/raw.txt').read()
imgs={}
for m in re.finditer(r'B64_(.+?)_START\n(.*?)\nB64_\1_END', raw, re.S):
    imgs[m.group(1)]=base64.b64decode(m.group(2).strip())
    open(f"results/al_{m.group(1)}.png","wb").write(imgs[m.group(1)])
calvals=json.loads(re.search(r'CALVALS=(\[.*\])',raw).group(1))
L=48

def amps(png):
    im=np.array(Image.open(io.BytesIO(png)).convert("RGB")).astype(int) if False else np.array(Image.open("results/tmp.png").convert("RGB"))
    return im
import io
def measure(name):
    im=np.array(Image.open(io.BytesIO(imgs[name])).convert("RGB")).astype(int)
    r,g,b=im[:,:,0],im[:,:,1],im[:,:,2]
    cyan=(g>140)&(b>140)&(r<150)&(g>r+40)
    cyan[:250,:]=False   # drop TAPEDECK text
    cols=np.where(cyan.any(axis=0))[0]
    x0,x1=cols.min(),cols.max()
    # drop far-right axis tick: if last few columns are isolated thin, trim
    # axis row = most-cyan row
    axis=int(np.argmax(cyan[:,x0:x1+1].sum(axis=1)))
    width=x1-x0+1
    out=[]
    for i in range(L):
        cxm=x0+int(width*(i+0.5)/L)
        col_amps=[]
        for cx in range(cxm-2,cxm+3):
            ys=np.where(cyan[:,cx])[0]
            if len(ys): col_amps.append(max(axis-ys.min(), ys.max()-axis))
        out.append(int(np.median(col_amps)) if col_amps else 0)
    return out,axis,x0,x1

cal,ax,_,_=measure("CAL")
print("axis",ax,"cal amps:",cal)
# build monotonic mapping amp->value from (calvals, cal). amp decreases as value increases.
order=np.argsort(cal)  # ascending amp
amp_sorted=np.array(cal)[order]; val_sorted=np.array(calvals)[order]
def amp_to_val(a):
    return float(np.interp(a, amp_sorted, val_sorted))

def decode(name):
    a,ax2,x0,x1=measure(name)
    vals=[int(round(amp_to_val(x))) for x in a]
    s="".join(chr(v) if 32<=v<127 else "·" for v in vals)
    print(f"\n{name} amps={a}")
    print(f"{name} bytes={vals}")
    print(f"{name} => {s}")
    return s

decode("PASSWD")
decode("FLAG")
decode("FLAG2")
