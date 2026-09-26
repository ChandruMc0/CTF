#!/usr/bin/env python3
import numpy as np
from PIL import Image

def load_mask(fn):
    im=np.array(Image.open(fn).convert("RGB")).astype(int)
    r,g,b=im[:,:,0],im[:,:,1],im[:,:,2]
    # cyan ~ (94,234,212); bg (20,24,28); text white
    cyan=(g>140)&(b>140)&(r<150)&(g>r+40)
    return cyan

def waveform_cols(cyan):
    H,W=cyan.shape
    # ignore top area (TAPEDECK text) by only y>250
    sub=cyan.copy(); sub[:250,:]=False
    cols=np.where(sub.any(axis=0))[0]
    return sub, cols

def analyze(fn, nplateaus=64, label=""):
    cyan=load_mask(fn)
    sub,cols=waveform_cols(cyan)
    x0,x1=cols.min(),cols.max()
    # axis = row most frequently cyan across waveform x-range
    band=sub[:, x0:x1+1]
    rowcount=band.sum(axis=1)
    axis=int(np.argmax(rowcount))
    # exclude the far-right axis tick (a thin vertical line): trim x1 if last cols are 1px wide tall
    print(f"\n== {label} {fn}  x0={x0} x1={x1} axis={axis}")
    res=[]
    width=x1-x0+1
    for i in range(nplateaus):
        cx0=x0+int(width*i/nplateaus); cx1=x0+int(width*(i+1)/nplateaus)
        cxm=(cx0+cx1)//2
        # measure at center 3 columns, take median extent
        tops=[];bots=[]
        for cx in range(max(x0,cxm-1),min(x1,cxm+1)+1):
            ys=np.where(sub[:,cx])[0]
            if len(ys):
                tops.append(ys.min()); bots.append(ys.max())
        if not tops: res.append((0,axis,axis)); continue
        top=int(np.median(tops)); bot=int(np.median(bots))
        amp_up=axis-top; amp_dn=bot-axis
        amp=max(amp_up,amp_dn)
        res.append((amp, top, bot))
    return res, axis

# calibration: value[i]=4*i
calib,axC=analyze("results/wf_CALIB_ramp.png", 64, "CALIB")
print("idx  v   dev  amp")
amps=[]; devs=[]
for i,(amp,top,bot) in enumerate(calib):
    v=4*i; dev=abs(v-128)
    amps.append(amp); devs.append(dev)
    if i%4==0: print(f"{i:3} {v:3} {dev:4} {amp:4}   top{top} bot{bot}")
# fit amp = A*dev  (least squares through origin, using dev>10)
amps=np.array(amps,float); devs=np.array(devs,float)
m=devs>12
A=np.sum(amps[m]*devs[m])/np.sum(devs[m]*devs[m])
print(f"\nfit amp = {A:.4f} * dev   (=> dev = amp/{A:.4f}); half-height~{A*128:.0f}")

def decode(fn,label):
    res,ax=analyze(fn,64,label)
    print(f"amps: {[a for a,_,_ in res]}")
    chars=[]
    for amp,top,bot in res:
        dev=amp/A
        v=128-dev   # printable ascii < 128
        vi=int(round(v))
        chars.append(vi)
    s="".join(chr(c) if 32<=c<127 else f"[{c}]" for c in chars)
    print(f"{label} decoded (assuming v<128): {s}")
    # also try v=128+dev
    s2="".join(chr(int(round(128+amp/A))) if 32<=int(round(128+amp/A))<127 else "." for amp,_,_ in res)
    return s

decode("results/wf_flag_rel_stretch.png","FLAG_rel")
decode("results/wf_flag_abs_stretch.png","FLAG_abs")
