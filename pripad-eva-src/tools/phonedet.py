import numpy as np, sys
from alib import *
from scipy.ndimage import uniform_filter1d
def timeline(p):
    x=load(p,ch=2).mean(0); fr=int(.03*SR); hop=int(.01*SR)
    idx=np.arange(0,len(x)-fr,hop); F=np.stack([x[i:i+fr]*np.hanning(fr) for i in idx])
    P=np.abs(np.fft.rfft(F))**2+1e-14; f=np.fft.rfftfreq(fr,1/SR)
    mid=P[:,(f>300)&(f<3200)].sum(1); hi=P[:,(f>4200)&(f<9000)].sum(1)
    db=10*np.log10(mid); v=db>np.percentile(db,25)+15
    ratio=10*np.log10(hi/mid)
    return v, ratio
if __name__=='__main__':
    v,r=timeline(sys.argv[1]); sm=uniform_filter1d(np.where(v,r,np.nan if False else 0),1)
    line=''
    for i in range(0,len(v),10):
        seg=slice(i,i+10); vv=v[seg]
        line+= '.' if vv.mean()<0.3 else ('E' if np.median(r[seg][vv])<-32 else 'n')
    for k in range(0,len(line),100): print(f'{k*0.1:5.1f}',line[k:k+100])
