from alib import *
D=40.0; N=int(D*SR); XF=int(2.0*SR)
def tile(x,n):
    out=np.zeros((2,n+XF)); i=0; L=x.shape[1]
    while i<n+XF:
        seg=x.copy(); seg=fade(seg,0.5,0.5); e=min(n+XF,i+L); out[:,i:e]+=seg[:,:e-i]; i+=L-int(0.5*SR)
    return out
rain=load('raw/k3s_rain_window.mp3',ch=2); rain=norm(rain,-36)
clock=load('raw/k3s_clock.mp3',ch=2); clock=norm(clock,-43); clock=np.stack([clock[0]*1.0,clock[1]*0.7])
sn=load('raw/k3s_snore.mp3',ch=2); sn=np.stack([lp(c,900) for c in sn]); sn=norm(sn,-44); sn=np.stack([sn[0]*0.6,sn[1]])
bed=tile(rain,N)+tile(clock,N)
for at in [3.0,22.0]:
    i=int(at*SR); bed[:,i:i+sn.shape[1]]+=fade(sn,1,1)
# seamless loop: crossfade the overflow into the start
r=np.linspace(0,1,XF); bed[:,:XF]=bed[:,:XF]*r+bed[:,N:N+XF]*(1-r); bed=bed[:,:N]
print('bed LUFS',round(lufs(bed),1)); save(bed,'out/k3room.mp3','160k')
