import numpy as np, json, re, math, sys
from diar import frames
from scipy.ndimage import binary_closing, binary_opening
def segs(p):
    d=frames(p); db=d['db']; floor=np.percentile(db,20)
    v=(db>floor+14)&(d['vo']>0.45)&(d['flat']>0.004)
    v=binary_closing(v,np.ones(15)); v=binary_opening(v,np.ones(6))
    out=[];i=0;n=len(v)
    while i<n:
        if v[i]:
            j=i
            while j<n and v[j]: j+=1
            if j-i>=10:
                sl=slice(i,j); lo=np.median(d['lo'][sl]); hi=np.median(d['hi'][sl])
                lab='E' if (lo<-18 and hi<-26) else ('N' if lo>-15 and hi>-30 else '?')
                out.append((i/100,j/100,lab))
            i=j
        else: i+=1
    return out
def fit(segs_, lines, rate=13.5):
    S=segs_; N=len(lines); M=len(S); INF=1e18
    cat=['E' if l['who']=='eva' else 'N' for l in lines]
    exp=[len(re.sub(r'\[[^\]]*\]','',l['text']).strip())/rate+0.35 for l in lines]
    # dp[i][j]: best cost assigning first i lines using segments up to j (exclusive); segments can be skipped
    dp=np.full((N+1,M+1),INF); bk={}; dp[0,0]=0
    for j in range(1,M+1): dp[0,j]=dp[0,j-1]+1.5; bk[(0,j)]=('skip',)
    for i in range(1,N+1):
        for j in range(1,M+1):
            best=dp[i,j-1]+1.5; arg=('skip',)
            for k in range(j-1,max(-1,j-14),-1):  # group S[k:j]
                if dp[i-1,k]>=INF: continue
                grp=S[k:j]; dur=grp[-1][1]-grp[0][0]
                mis=sum(1 for g in grp if g[2]!='?' and g[2]!=cat[i-1])
                # internal long gaps are suspicious
                gp=sum(max(0,grp[t+1][0]-grp[t][1]-1.2) for t in range(len(grp)-1))
                c=dp[i-1,k]+4*math.log(max(dur,0.2)/exp[i-1])**2+6*mis+1.5*gp
                if c<best: best=c; arg=('grp',k)
            dp[i,j]=best; bk[(i,j)]=arg
    i,j=N,M; groups=[None]*N
    while i>0 or j>0:
        a=bk[(i,j)]
        if a[0]=='skip': j-=1
        else: k=a[1]; groups[i-1]=(k,j); i-=1; j=k
    res=[]
    for l,(k,j) in zip(lines,groups):
        res.append(dict(l,at=round(S[k][0],2),end=round(S[j-1][1],2),spk=[[S[t][0],S[t][1]] for t in range(k,j)]))
    return res
