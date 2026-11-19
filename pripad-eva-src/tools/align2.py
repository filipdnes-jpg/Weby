import numpy as np, re
from alib import *
from align import speech_frames
def gaps(v,minf=15):
    out=[];n=len(v);i=0
    while i<n:
        if not v[i]:
            j=i
            while j<n and not v[j]: j+=1
            if 0<i and j<n and j-i>=minf: out.append((i/100,j/100))
            i=j
        else: i+=1
    return out
def align_prop(x,texts,pause_after=None):
    v=speech_frames(x); on=np.where(v)[0]; s0,e0=on[0]/100,on[-1]/100
    G=gaps(v); ch=np.array([max(4,len(re.sub(r'\[[^\]]*\]','',t).strip())) for t in texts],float)
    # speaking time = span minus long silences (>1s) which are true pauses
    long=sum(b-a for a,b in G if b-a>1.0)
    speak=(e0-s0)-long; starts=[s0]; t=s0; cum=0
    for k in range(len(texts)-1):
        cum+=ch[k]; target=s0+speak*cum/ch.sum()
        # add the long pauses that fall before target
        tt=target+sum(b-a for a,b in G if b-a>1.0 and a<target)
        cands=[(abs((a+b)/2-tt)-0.4*(b-a),a,b) for a,b in G if a>starts[-1]+0.4]
        best=min(cands) if cands else None
        if best and abs((best[1]+best[2])/2-tt)<1.5: starts.append(best[2])
        else: starts.append(tt)
    return starts
