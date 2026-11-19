import json,re
from alib import *
from scipy.ndimage import minimum_filter1d, uniform_filter1d
A='/home/claude/site/a/'
def L(n): return load(A+n+'.mp3',ch=2)
def lvl(x): return x*10**((-18.5-lufs(x))/20)
def lim(x):
    a=np.abs(x).max(0); g=np.minimum(1,0.89/(a+1e-9)); w=int(.004*SR); return x*uniform_filter1d(minimum_filter1d(g,2*w),2*w)
def act_end(x,th=-38):
    m=x.mean(0); hop=int(.01*SR); r=20*np.log10(np.sqrt(np.convolve(m**2,np.ones(hop*3)/(hop*3),'same')[::hop])+1e-9)
    return np.where(r>th)[0][-1]/100
def join(a,b,gap,foley=None):
    """b starts `gap` s after a's last activity (negative = overlap). a's tail fades under b."""
    ea=act_end(a); tb=ea+gap; n=int((tb)*SR)+b.shape[1]
    out=np.zeros((2,max(n,a.shape[1])))
    fa=a.copy(); i0=int((ea+0.05)*SR); f=int(0.5*SR)
    if i0<fa.shape[1]:
        k=min(f,fa.shape[1]-i0); fa[:,i0:i0+k]*=np.linspace(1,0,k); fa[:,i0+k:]=0
    out[:,:fa.shape[1]]+=fa
    bb=fade(b,0.08,0.0); j=int(tb*SR); out[:,j:j+bb.shape[1]]+=bb
    if foley is not None:
        x,at=foley; j=int((ea+at)*SR); m=min(x.shape[1],out.shape[1]-j); out[:,j:j+m]+=x[:,:m]
    return out, tb
def sfx(name,a,b,target,fi=0.15,fo=0.5):
    x=load(f'raw/{name}.mp3',ch=2)[:,int(a*SR):int(b*SR)]; return fade(norm(x,target),fi,fo)
D_subs=json.load(open('/tmp/dlg_subs.json'))
res={}
# A-branches -> s3_2 (Nikol is already getting out of bed when she asks for the keys)
s32=L('s3_2')
for k in ['1','2','3']:
    a=L('s3_a'+k); duv=sfx('k3s_duvet',0.6,3.6,-37)
    y,tb=join(a,s32,0.35,(duv,-0.1)); y=lim(lvl(y)); save(y,A+f's3_a{k}x.mp3','192k')
    res[f's3_a{k}x']=D_subs['s3_a'+k]+[dict(d,at=round(d['at']+tb,2)) for d in D_subs['s3_2']]
    print('a'+k, round(y.shape[1]/SR,1), 'join at', round(tb,2))
# B-branches -> s3_3 (Eva interrupts while Nikol is still busy with the envelope)
s33=load('user/s3_32.wav',ch=2); s33=lvl(s33)
fol={'1':sfx('k3s_zip_bag',0.0,4.0,-34),'2':sfx('k3s_tear_env',1.2,3.0,-35),'3':sfx('k3s_parquet',4.5,8.0,-35)}
s33subs=[{'who':'eva','text':'Nika? Ešte si tam?','at':0.2},{'who':'nikol','text':'Som. Obliekam sa. Ostaň na telefóne. Nepoložíš mi to, jasné?','at':2.9},
 {'who':'eva','text':'Nepoložím. Budem tu.','at':7.4},{'who':'babka','text':'Nikolka? Čo sa deje? Kam ideš v takom čase?','at':24.9},{'who':'nikolT','text':'Babka. Samozrejme.','at':27.5}]
for k in ['1','2','3']:
    b=L('s3_2_'+k); y,tb=join(b,s33,-0.15,(fol[k],-0.7)); y=lim(lvl(y)); save(y,A+f's3_2_{k}x.mp3','192k')
    res[f's3_2_{k}x']=D_subs['s3_2_'+k]+[dict(d,at=round(d['at']+tb,2)) for d in s33subs]
    print('b'+k, round(y.shape[1]/SR,1), 'join at', round(tb,2))
json.dump(res,open('/tmp/new_subs.json','w'),ensure_ascii=False)
