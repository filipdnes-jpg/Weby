import numpy as np, re, math, json, sys
from alib import *
def speech_frames(x):
    hop=int(.01*SR); fr=int(.03*SR)
    idx=np.arange(0,len(x)-fr,hop); F=np.stack([x[i:i+fr]*np.hanning(fr) for i in idx])
    P=np.abs(np.fft.rfft(F))**2+1e-12
    db=10*np.log10(P.mean(1)); band=P[:,int(300/SR*fr):int(3500/SR*fr)]
    flat=np.exp(np.log(band).mean(1))/band.mean(1)
    peakf=np.argmax(band,1)
    floor=np.percentile(db,15)
    v=(db>floor+14)&(flat>0.02)
    # close tiny holes
    from scipy.ndimage import binary_closing, binary_opening
    v=binary_opening(binary_closing(v,np.ones(12)),np.ones(6))
    return v
def align(x, texts, mingap=25):
    v=speech_frames(x); n=len(v)
    runs=[];i=0
    while i<n:
        if not v[i]:
            j=i
            while j<n and not v[j]: j+=1
            if i>0 and j<n and j-i>=mingap: runs.append(((j-i)*.01,i,j))
            i=j
        else: i+=1
    on=np.where(v)[0]; s0,e0=on[0],on[-1]
    exp=[len(re.sub(r'\[[^\]]*\]','',t).strip())/12+0.6 for t in texts]
    cand=[(0,s0,s0)]+runs+[(0,e0,e0)]; C=len(cand); N=len(texts); INF=1e9
    dp=[[INF]*(N+1) for _ in range(C)]; bk=[[0]*(N+1) for _ in range(C)]; dp[0][0]=0
    for j in range(1,C):
        for k in range(1,N+1):
            if (k==N)!=(j==C-1): continue
            for i in range(j):
                if dp[i][k-1]>=INF: continue
                d=(cand[j][1]-cand[i][2])*.01
                if d<=0.25: continue
                c=dp[i][k-1]+3*math.log(d/exp[k-1])**2-(2.5*cand[j][0] if j<C-1 else 0)
                if c<dp[j][k]: dp[j][k]=c; bk[j][k]=i
    j=C-1;k=N;ch=[]
    while k>0: ch.append(j); j=bk[j][k]; k-=1
    ch=ch[::-1]; starts=[cand[0][2]]+[cand[c][2] for c in ch[:-1]]; ends=[cand[c][1] for c in ch]
    return [(s*.01,e*.01) for s,e in zip(starts,ends)]
