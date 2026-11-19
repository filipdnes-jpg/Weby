import json,subprocess,numpy as np,re,os,math
SR=44100
def load(p):
    a=subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout
    return np.frombuffer(a,np.float32).copy()
def save(x,p):
    subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','1','-i','-','-c:a','pcm_s24le',p],input=x.astype(np.float32).tobytes())
B=json.load(open('batches.json')); S={o['id']:o for o in json.load(open('script.json')) if 'id' in o}
for b in B:
    x=load(f"raw/k3v_{b['name']}.mp3"); hop=int(.01*SR)
    fr=np.sqrt(np.convolve(x**2,np.ones(hop*3)/(hop*3),'same')[::hop]+1e-12); db=20*np.log10(fr); sil=db<-50
    runs=[];i=0
    while i<len(sil):
        if sil[i]:
            j=i
            while j<len(sil) and sil[j]: j+=1
            if i>0 and j<len(sil) and (j-i)>=20: runs.append(((j-i)*.01,(i+j)//2))
            i=j
        else: i+=1
    ids=b['ids']; n=len(ids)
    exp=[len(re.sub(r'\[[^\]]*\]','',S[k]['text']).strip())/11.5+0.5 for k in ids]
    cand=[(0,0)]+[(r[0],r[1]) for r in runs]+[(0,len(sil))]
    C=len(cand); INF=1e9
    # dp[j][k]: best cost with k-th boundary at cand j
    dp=[[INF]*(n+1) for _ in range(C)]; bk=[[None]*(n+1) for _ in range(C)]
    dp[0][0]=0
    for j in range(1,C):
        for k in range(1,n+1):
            if k==n and j!=C-1: continue
            if j==C-1 and k!=n: continue
            for i in range(j):
                if dp[i][k-1]>=INF: continue
                d=(cand[j][1]-cand[i][1])*.01
                if d<=0.2: continue
                c=dp[i][k-1]+4*math.log(d/exp[k-1])**2-(3*cand[j][0] if j<C-1 else 0)
                if c<dp[j][k]: dp[j][k]=c; bk[j][k]=i
    j=C-1;k=n;bd=[]
    while k>0: bd.append(cand[j][1]); j=bk[j][k]; k-=1
    bd=[0]+bd[::-1]
    out=[]
    for k,idx in enumerate(ids):
        s,e=bd[k],bd[k+1]; seg=np.where(~sil[s:e])[0]
        a=max(0,(s+seg[0])*hop-int(.08*SR)); z=min(len(x),(s+seg[-1])*hop+int(.25*SR))
        y=x[a:z].copy(); f=int(.01*SR); y[:f]*=np.linspace(0,1,f); y[-f*3:]*=np.linspace(1,0,f*3)
        save(y,f'lines/{idx}.wav'); out.append(f"{idx}:{len(y)/SR:.1f}/{exp[k]:.1f}")
    print(b['name'],' '.join(out))
