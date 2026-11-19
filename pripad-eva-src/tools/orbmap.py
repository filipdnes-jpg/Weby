import numpy as np, json, re
from alib import *
from diar import frames, SR16
from scipy.fft import dct
from scipy.ndimage import binary_closing, binary_opening
d0=np.load('spk.npz'); MU,SD,W,TH=d0['mu'],d0['sd'],d0['w'],d0['th']
def mfcc_score(x48,a,b):
    x=x48[int(a*SR):int(b*SR)]; fr=int(.025*SR); hop=int(.01*SR)
    if len(x)<fr*3: return 0.0
    idx=np.arange(0,len(x)-fr+1,hop); F=np.stack([x[i:i+fr]*np.hanning(fr) for i in idx])
    P=np.abs(np.fft.rfft(F,2048))**2
    fmax=SR/2; m=np.linspace(0,2595*np.log10(1+fmax/700),42); hz=700*(10**(m/2595)-1); bb=np.floor(hz/fmax*1024).astype(int)
    fb=np.zeros((40,1025))
    for k in range(1,41):
        for j in range(bb[k-1],bb[k]): fb[k-1,j]=(j-bb[k-1])/max(1,bb[k]-bb[k-1])
        for j in range(bb[k],bb[k+1]): fb[k-1,j]=(bb[k+1]-j)/max(1,bb[k+1]-bb[k])
    C=dct(np.log(P@fb.T+1e-10),norm='ortho')[:,1:20]; e=(F**2).sum(1); C=C[e>np.percentile(e,40)]
    return float(np.mean(((C-MU)/SD)@W-TH > 0))
def segments(path):
    d=frames(path); db=d['db']; floor=np.percentile(db,20)
    v=(db>floor+14)&(d['vo']>0.45)&(d['flat']>0.004)
    v=binary_closing(v,np.ones(25)); v=binary_opening(v,np.ones(8))
    # f0 per frame is not stored; approximate from autocorr would need lag; use 'lo' & 'hi' bands
    out=[];i=0;n=len(v)
    while i<n:
        if v[i]:
            j=i
            while j<n and v[j]: j+=1
            if j-i>=12:
                sl=slice(i,j); out.append(dict(a=i/100,b=j/100,lo=float(np.median(d['lo'][sl])),hi=float(np.median(d['hi'][sl]))))
            i=j
        else: i+=1
    return out
def f0(x48,a,b):
    x=x48[int(a*SR):int(b*SR)][::3]
    if len(x)<1600: return 0
    fr=640; vals=[]
    for i in range(0,len(x)-fr,320):
        f=x[i:i+fr]-x[i:i+fr].mean(); ac=np.correlate(f,f,'full')[fr-1:]; ac/=ac[0]+1e-12
        lo,hi=int(16000/400),int(16000/70); k=np.argmax(ac[lo:hi])+lo
        if ac[k]>0.5: vals.append(16000/k)
    return float(np.median(vals)) if vals else 0
def band_limited(s): return s['lo']<-18 and s['hi']<-26
