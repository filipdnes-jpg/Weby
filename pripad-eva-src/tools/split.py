import json,subprocess,numpy as np,re,os
SR=44100
def load(p):
    a=subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout
    return np.frombuffer(a,np.float32).copy()
def save(x,p):
    subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(SR),'-ac','1','-i','-','-c:a','pcm_s24le',p],input=x.astype(np.float32).tobytes())
B=json.load(open('batches.json')); S={o['id']:o for o in json.load(open('script.json')) if 'id' in o}
os.makedirs('lines',exist_ok=True); rep={}
for b in B:
    x=load(f"raw/k3v_{b['name']}.mp3"); hop=int(.01*SR)
    fr=np.sqrt(np.convolve(x**2,np.ones(hop*3)/(hop*3),'same')[::hop]+1e-12); db=20*np.log10(fr)
    sil=db<-50
    runs=[];i=0
    while i<len(sil):
        if sil[i]:
            j=i
            while j<len(sil) and sil[j]: j+=1
            if i>0 and j<len(sil): runs.append((j-i,i,j))
            i=j
        else: i+=1
    n=len(b['ids']); cuts=sorted(runs,reverse=True)[:n-1]
    cuts=sorted(cuts,key=lambda r:r[1])
    bounds=[0]+[ (r[1]+r[2])//2 for r in cuts]+[len(sil)]
    for k,idx in enumerate(b['ids']):
        s,e=bounds[k],bounds[k+1]
        seg=np.where(~sil[s:e])[0]
        a=max(0,(s+seg[0])*hop-int(.08*SR)); z=min(len(x),(s+seg[-1])*hop+int(.25*SR))
        y=x[a:z].copy(); f=int(.01*SR); y[:f]*=np.linspace(0,1,f); y[-f*3:]*=np.linspace(1,0,f*3)
        save(y,f'lines/{idx}.wav')
        txt=re.sub(r'\[[^\]]*\]','',S[idx]['text']).strip()
        rep[idx]=(round(len(y)/SR,2),len(txt))
    print(b['name'],'minsil_used',[round(r[0]*.01,2) for r in cuts][:3],'next',[round(r[0]*.01,2) for r in sorted(runs,reverse=True)[n-1:n+1]])
for k,(d,c) in rep.items(): print(k,d,c,round(c/d,1))
