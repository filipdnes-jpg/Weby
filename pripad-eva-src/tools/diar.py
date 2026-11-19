import numpy as np
from alib import *
from scipy.ndimage import uniform_filter1d, binary_closing, binary_opening
from scipy.signal import butter, sosfilt
SR16=16000
def frames(p):
    x=load(p,ch=2).mean(0)
    # downsample to 16k for analysis
    x16=x[::3]; fr=640; hop=160  # 40ms / 10ms
    n=(len(x16)-fr)//hop
    idx=np.arange(n)*hop
    F=np.stack([x16[i:i+fr] for i in idx])*np.hanning(fr)
    P=np.abs(np.fft.rfft(F,1024))**2+1e-14; f=np.fft.rfftfreq(1024,1/SR16)
    mid=P[:,(f>300)&(f<3200)].sum(1); hi=P[:,(f>4000)&(f<7800)].sum(1); lo=P[:,(f>80)&(f<250)].sum(1)
    # voicing via autocorrelation of band-passed frame
    sos=butter(4,[70,1000],'bandpass',fs=SR16,output='sos')
    xb=sosfilt(sos,x16); Fb=np.stack([xb[i:i+fr] for i in idx])
    Fb=Fb-Fb.mean(1,keepdims=True)
    S=np.fft.rfft(Fb,2048); ac=np.fft.irfft(np.abs(S)**2)[:, :fr]; ac=ac/(ac[:,:1]+1e-12)
    lagmin,lagmax=int(SR16/450),int(SR16/70)
    vo=ac[:,lagmin:lagmax].max(1)
    band=P[:,(f>300)&(f<3200)]; flat=np.exp(np.log(band).mean(1))/band.mean(1)
    db=10*np.log10(mid)
    return dict(db=db,hi=10*np.log10(hi/mid),lo=10*np.log10(lo/mid),vo=vo,flat=flat,dur=len(x)/SR)
def segments(p, vo_th=0.45, lev=14, mingap=22, minseg=12):
    d=frames(p); db=d['db']; floor=np.percentile(db,20)
    v=(db>floor+lev)&(d['vo']>vo_th)&(d['flat']>0.004)
    v=binary_closing(v,np.ones(15)); v=binary_opening(v,np.ones(6))
    segs=[];i=0;n=len(v)
    while i<n:
        if v[i]:
            j=i
            while j<n:
                if not v[j]:
                    k=j
                    while k<n and not v[k]: k+=1
                    if k-j>=mingap or k==n: break
                    j=k
                else: j+=1
            if j-i>=minseg:
                seg=slice(i,j); phone=np.median(d['hi'][seg][v[seg]]) < -30 and np.median(d['lo'][seg][v[seg]])< -12
                segs.append([i/100,j/100,'E' if phone else 'N', float(np.median(d['hi'][seg][v[seg]])), float(np.median(d['lo'][seg][v[seg]]))])
            i=j
        else: i+=1
    return segs,d
if __name__=='__main__':
    import sys
    s,d=segments(sys.argv[1])
    for a in s: print(f'{a[0]:6.2f}-{a[1]:6.2f} {a[2]} hi{a[3]:6.1f} lo{a[4]:6.1f}')
