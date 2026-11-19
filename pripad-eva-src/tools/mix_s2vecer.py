from alib import *
V0=1.6
x=load('user/s2_vecer_new.mp3'); N=len(x)
IR=room_ir(0.5,seed=21,bright=4200)
# split Nikol's last line (walking away) for distance treatment
a,b=int(19.5*SR),int(20.95*SR)
near=x.copy(); near[a:b]=0
far=np.zeros_like(x); far[a:b]=x[a:b]*np.linspace(1,0.7,b-a)
far=lp(far,5500)
v=verb(norm(near,-20.0)*1.0,IR,0.09)
ratio=10**((-20.0-lufs(x))/20)
vf=verb(far*ratio*0.85,IR,0.28)
voice=v+vf
L=int((V0+N/SR+4.0)*SR); mixb=np.zeros((2,L))
def put(st,t,g=1.0):
    i=int(t*SR); n=min(st.shape[1],L-i); mixb[:,i:i+n]+=st[:,:n]*g
put(voice,V0)
bed=load('/home/claude/site/s/evening.mp3',ch=2); bed=np.tile(bed,(1,3))[:,:L]; bed=norm(bed,-39); bed=fade(bed,1.0,2.5); put(bed,0)
typ=load('raw/s2s_typing.mp3',ch=2); typ=np.stack([lp(c,7000) for c in typ]); typ=norm(typ,-37)
typ=np.tile(typ,(1,2))[:,:L]; typ=np.stack([typ[0]*0.75,typ[1]*1.0])  # Eva sits to the right
env=np.ones(L); 
for s0,s1 in [(V0+11.6,V0+19.5),(V0+21.0,V0+23.0)]:
    i,j=int(s0*SR),int(s1*SR); env[i:j]=0.55
from scipy.ndimage import uniform_filter1d
env=uniform_filter1d(env,int(0.3*SR)); put(fade(typ*env,1.5,2.5),0)
st=load('raw/s2s_standup.mp3',ch=2); st=norm(st,-34); st=np.stack([st[0],st[1]*0.8]); put(fade(st,0.05,0.4),0.3)
wo=load('raw/s2s_walkout.mp3',ch=2); wo=norm(wo,-33); wo=np.stack([wo[0],wo[1]*0.7]); put(fade(wo,0.05,0.3),V0+19.3)
y=mixb*10**(0/20); y=fade(y,0.0,2.0)
from scipy.ndimage import minimum_filter1d
y=y*10**((-18.5-lufs(y))/20)
a_=np.abs(y).max(0); g=np.minimum(1,0.89/(a_+1e-9)); w=int(.004*SR); g=uniform_filter1d(minimum_filter1d(g,2*w),2*w); y=y*g
save(y,'out/s2_vecer_scena.mp3','192k'); save(y,'out/s2_vecer_scena.wav')
print(round(L/SR,1),'s',round(lufs(y),1))
