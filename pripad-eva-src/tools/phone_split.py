import numpy as np, sys, json
from alib import *
from scipy.fft import dct
from scipy.ndimage import uniform_filter1d
d=np.load('spk.npz'); mu,sd,w,th=d['mu'],d['sd'],d['w'],d['th']
src=sys.argv[1]; outname=sys.argv[2]; regs_in=json.loads(sys.argv[3]) if len(sys.argv)>3 else None
x=load(src); fr=int(.025*SR); hop=int(.01*SR)
if regs_in is None:
    idx=np.arange(0,len(x)-fr+1,hop); F=np.stack([x[i:i+fr]*np.hanning(fr) for i in idx])
    P=np.abs(np.fft.rfft(F,2048))**2
    fmax=SR/2; m=np.linspace(0,2595*np.log10(1+fmax/700),42); hz=700*(10**(m/2595)-1); b=np.floor(hz/fmax*1024).astype(int)
    fb=np.zeros((40,1025))
    for k in range(1,41):
        for j in range(b[k-1],b[k]): fb[k-1,j]=(j-b[k-1])/max(1,b[k]-b[k-1])
        for j in range(b[k],b[k+1]): fb[k-1,j]=(b[k+1]-j)/max(1,b[k+1]-b[k])
    C=dct(np.log(P@fb.T+1e-10),norm='ortho')[:,1:20]; en=10*np.log10((F**2).mean(1)+1e-12)
    s=((C-mu)/sd)@w-th; voiced=en>en.max()-35
    sm=uniform_filter1d(np.where(voiced,np.sign(s),0.0),80); n=len(sm)
    runs=[];i=0
    while i<n:
        if voiced[i]:
            j=i
            while j<n:
                if not voiced[j]:
                    k=j
                    while k<n and not voiced[k]: k+=1
                    if k-j>=6 or k==n: break
                    j=k
                else: j+=1
            runs.append([i,j,float(np.mean(sm[i:j]))]); i=j
        else: i+=1
    lab=['E' if r[2]>0 else 'N' for r in runs]
    for k,r in enumerate(runs):
        if r[1]-r[0]<35 and 0<k<len(runs)-1 and lab[k-1]==lab[k+1]: lab[k]=lab[k-1]
    R=[]
    for r,l in zip(runs,lab):
        if R and R[-1][2]==l: R[-1][1]=r[1]
        else: R.append([r[0],r[1],l])
    for k in range(1,len(R)):
        m_=(R[k-1][1]+R[k][0])//2; R[k-1][1]=m_; R[k][0]=m_
    R[0][0]=0; R[-1][1]=len(x)//hop+1
    regs=[(a/100,b/100) for a,b,l in R if l=='E']
    for a,b_,l in R: print(f'{a/100:6.2f}-{b_/100:6.2f} {"Eva" if l=="E" else "Nikol"}')
else: regs=regs_in
json.dump(regs,open(outname+'.regs.json','w'))
mask=np.zeros(len(x))
for a,b_ in regs: mask[int(a*SR):min(len(x),int(b_*SR))]=1
mask=uniform_filter1d(mask,int(0.02*SR))
y=hp(hp(x,320,4),300,2); y=lp(lp(y,3400,4),3600,2); y=peq(y,1800,3.5,0.9); y=comp(y,-26,4); y=np.tanh(y*2.2)/2.2
if (mask<0.5).sum()>SR and (mask>0.5).sum()>SR:
    for _ in range(3): y=y*10**((lufs(x[mask<0.5])-0.8-lufs(y[mask>0.5]))/20)
out=x*(1-mask)+y*mask; out=out*min(1,0.89/np.abs(out).max()); st=fade(np.stack([out,out]),0.005,0.05)
save(st,outname+'.mp3','192k'); save(st,outname+'.wav')
