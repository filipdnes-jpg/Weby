// ================= AUDIO (ambience + SFX) =================
let ctx, master, buses={}, reverb, WHITE, BROWN, PINK;
let plipTimer=null, murmurTimer=null, wiperTimer=null, crowdDensity=0.5, ambDuck=null;
function gain(v){ const g=ctx.createGain(); g.gain.value=v; return g; }
function filt(type,f,q=0.7,g=0){ const n=ctx.createBiquadFilter(); n.type=type; n.frequency.value=f; n.Q.value=q; n.gain.value=g; return n; }
function makeNoise(type,sec=4){ const len=Math.floor(ctx.sampleRate*sec), b=ctx.createBuffer(1,len,ctx.sampleRate), d=b.getChannelData(0);
  let last=0, b0=0,b1=0,b2=0,b3=0,b4=0,b5=0,b6=0;
  for(let i=0;i<len;i++){ const w=Math.random()*2-1;
    if(type==='brown'){ last=(last+0.02*w)/1.02; d[i]=last*3.5; }
    else if(type==='pink'){ b0=0.99886*b0+w*0.0555179; b1=0.99332*b1+w*0.0750759; b2=0.969*b2+w*0.153852; b3=0.8665*b3+w*0.3104856; b4=0.55*b4+w*0.5329522; b5=-0.7616*b5-w*0.016898; d[i]=(b0+b1+b2+b3+b4+b5+b6+w*0.5362)*0.11; b6=w*0.115926; }
    else d[i]=w; }
  return b; }
function noiseSrc(buf){ const s=ctx.createBufferSource(); s.buffer=buf; s.loop=true; s.start(0,Math.random()*buf.duration); return s; }
function makeReverb(sec=2.4,decay=3){ const len=Math.floor(ctx.sampleRate*sec), b=ctx.createBuffer(2,len,ctx.sampleRate);
  for(let c=0;c<2;c++){ const d=b.getChannelData(c); for(let i=0;i<len;i++) d[i]=(Math.random()*2-1)*Math.pow(1-i/len,decay); }
  const cv=ctx.createConvolver(); cv.buffer=b; return cv; }

// Rain on a car roof, heard from inside: thousands of tiny impacts on a thin
// metal panel. Pre-rendered once (stereo, seamless loop) instead of filtered hiss.
function makeRoofRain(sec=8){
  const sr=ctx.sampleRate, len=Math.floor(sr*sec), b=ctx.createBuffer(2,len,sr);
  for(let ch=0;ch<2;ch++){ const d=b.getChannelData(ch);
    const drop=(t,amp,durMs,tone)=>{ const n=Math.floor(durMs*sr/1000); const w=2*Math.PI*tone/sr;
      for(let i=0;i<n;i++){ const k=(t+i)%len; const env=Math.exp(-i/(n*0.22)); const a=Math.min(1,i/(n*0.12)); d[k]+=amp*env*a*((Math.random()*2-1)*0.3+Math.sin(w*i)*0.7); } };
    const small=sec*2600, big=sec*55;
    for(let i=0;i<small;i++) drop(Math.floor(Math.random()*len), 0.01+Math.random()*0.022, 5+Math.random()*7, 380+Math.random()*700);
    for(let i=0;i<big;i++)   drop(Math.floor(Math.random()*len), 0.05+Math.random()*0.08, 14+Math.random()*18, 140+Math.random()*160);
    let peak=0; for(let i=0;i<len;i++) peak=Math.max(peak,Math.abs(d[i])); for(let i=0;i<len;i++) d[i]/=peak*1.15; }
  return b; }

function initAudio(){
  ctx=new (window.AudioContext||window.webkitAudioContext)();
  const comp=ctx.createDynamicsCompressor(); comp.threshold.value=-18; comp.knee.value=18; comp.ratio.value=2; comp.attack.value=0.02; comp.release.value=0.35;
  const warm=filt('lowshelf',160,0.7,1.5), air=filt('highshelf',8000,0.7,-2.5); master=gain(0.95); master.connect(warm); warm.connect(air); air.connect(comp); comp.connect(ctx.destination);
  buses.studio=makeReverb(0.45,4); const stG=gain(0.5); buses.studio.connect(stG); stG.connect(master);
  WHITE=makeNoise('white'); BROWN=makeNoise('brown'); PINK=makeNoise('pink');
  reverb=makeReverb(); const rvG=gain(0.55); reverb.connect(rvG); rvG.connect(master);
  const ambTone=filt('highshelf',5000,0.7,-6); const amb=gain(0.8); amb.connect(ambTone); ambTone.connect(master); ambDuck=amb;   // ambience bus – ducks under dialogue

  // ---------- CAR (inside, rain) ----------
  const car=gain(0); car.connect(amb); buses.car=car;
  // cabin: low road/body rumble of a parked car in rain
  const cab=noiseSrc(BROWN), cabF=filt('lowpass',140), cabG=gain(0.22); cab.connect(cabF); cabF.connect(cabG); cabG.connect(car);
  // roof rain: muffled by the headliner – no hiss above ~3 kHz, a little body around 300 Hz
  const rf1=filt('lowpass',1700,0.5), rf3=filt('highpass',90), roofG=gain(0.3); rf1.connect(rf3); rf3.connect(roofG); roofG.connect(car); buses.rainIn=rf1;
  const wip=gain(0); wip.connect(car); buses.wipers=wip;
  // engine idle (off until the engine starts)
  const eng=ctx.createOscillator(); eng.type='sawtooth'; eng.frequency.value=31;
  const eng2=ctx.createOscillator(); eng2.type='triangle'; eng2.frequency.value=62.3;
  const ef=filt('lowpass',105), eg=gain(0); eng.connect(ef); eng2.connect(ef); ef.connect(eg); eg.connect(car); eng.start(); eng2.start(); buses.engine=eg;

  // ---------- LECTURE HALL (flashback – dry, no rain) ----------
  const hall=gain(0); hall.connect(amb); buses.hall=hall;
  const hallWet=gain(0.9); hallWet.connect(reverb); buses.hallWet=hallWet;
  const room=noiseSrc(BROWN), roomF=filt('lowpass',180), roomG=gain(0.07); room.connect(roomF); roomF.connect(roomG); roomG.connect(hall);
  const crowd=gain(0.6); crowd.connect(hall); crowd.connect(hallWet); buses.crowd=crowd;
  const chat=gain(0); chat.connect(hall); buses.chat=chat;
  // ---------- POLICE STATION ----------
  buses.idle=gain(0); buses.idle.connect(master); buses.office=gain(0); buses.office.connect(amb); buses.evening=gain(0); buses.evening.connect(amb); buses.night=gain(0); buses.night.connect(amb);
}
let officeStarted=false, eveningStarted=false;
function ensureLoop(name,bus,flag){ if(window[flag]||!SFXBUF[name]) return; window[flag]=true; loopBuf(SFXBUF[name],bus); }
let rainStarted=false, chatStarted=false;
function loopBuf(buf,dest){ const s=ctx.createBufferSource(); s.buffer=buf; s.loop=true; s.loopStart=0.05; s.loopEnd=buf.duration-0.05; s.connect(dest); s.start(0,Math.random()*Math.max(0.1,buf.duration-1)); return s; }
function ensureRain(){ if(rainStarted) return; rainStarted=true;
  if(SFXBUF.rain){ loopBuf(SFXBUF.rain,buses.rainIn); }
  else { const r=ctx.createBufferSource(); r.buffer=makeRoofRain(); r.loop=true; const lp=filt('lowpass',1300,0.5); r.connect(lp); lp.connect(buses.rainIn); r.start(); } }
function ensureChat(){ if(chatStarted||!SFXBUF.chatter) return; chatStarted=true; loopBuf(SFXBUF.chatter,buses.chat); }
const fadeTo=(node,v,t=1.2)=>{ node.gain.cancelScheduledValues(ctx.currentTime); node.gain.setTargetAtTime(v,ctx.currentTime,t/3); };

// windscreen drops: a soft "plip" with a little thud, panned in front of you
function plip(){ const t=ctx.currentTime, s=ctx.createBufferSource(); s.buffer=WHITE;
  const f=filt('lowpass',700+Math.random()*400,0.7), g=gain(0), p=ctx.createStereoPanner?ctx.createStereoPanner():null;
  s.connect(f); f.connect(g); if(p){ p.pan.value=Math.random()*1.4-0.7; g.connect(p); p.connect(buses.car); } else g.connect(buses.car);
  const a=0.012+Math.random()*0.025; g.gain.setValueAtTime(0,t); g.gain.linearRampToValueAtTime(a,t+0.008); g.gain.exponentialRampToValueAtTime(0.0001,t+0.05+Math.random()*0.05);
  s.start(t,Math.random()*3,0.12);
  const o=ctx.createOscillator(), og=gain(0); o.frequency.setValueAtTime(170+Math.random()*90,t); o.frequency.exponentialRampToValueAtTime(90,t+0.06);
  o.connect(og); og.connect(p||buses.car); og.gain.setValueAtTime(a*0.6,t); og.gain.exponentialRampToValueAtTime(0.0001,t+0.07); o.start(t); o.stop(t+0.08); }
function schedulePlips(){ clearTimeout(plipTimer); const loop=()=>{ plip(); plipTimer=setTimeout(loop,450+Math.random()*1100); }; loop(); }

// crowd murmur in the hall: real voice fragments, pitched and muffled into a room of people talking
function murmur(){ const ids=Object.keys(typeof BUF!=='undefined'?BUF:{}); if(!ids.length) return;
  const b=BUF[ids[Math.floor(Math.random()*ids.length)]]; const len=0.6+Math.random()*1.2; if(b.duration<len+0.2) return;
  const t=ctx.currentTime, s=ctx.createBufferSource(); s.buffer=b; s.playbackRate.value=0.78+Math.random()*0.4;
  const f=filt('lowpass',900+Math.random()*500,0.6), g=gain(0), p=ctx.createStereoPanner?ctx.createStereoPanner():null;
  s.connect(f); f.connect(g); if(p){ p.pan.value=Math.random()*2-1; g.connect(p); p.connect(buses.crowd); } else g.connect(buses.crowd);
  const a=0.05+Math.random()*0.05; g.gain.setValueAtTime(0,t); g.gain.linearRampToValueAtTime(a,t+0.15); g.gain.setValueAtTime(a,t+len-0.2); g.gain.linearRampToValueAtTime(0,t+len);
  s.start(t,Math.random()*(b.duration-len),len); }
function scheduleMurmur(){ clearTimeout(murmurTimer); const loop=()=>{ murmur(); murmurTimer=setTimeout(loop,(420+Math.random()*500)/(0.4+crowdDensity)); }; loop(); }

function setScene(s){
  clearTimeout(plipTimer); clearTimeout(murmurTimer);
  if(s==='car'){ ensureRain(); ensureLoop('idle',buses.idle,'_idleL'); fadeTo(buses.idle,1,0.6); fadeTo(buses.car,1,1.6); fadeTo(buses.hall,0,0.8); if(!SFXBUF.rain) schedulePlips(); }
  else if(s==='hall'){ fadeTo(buses.idle,0,0.6); fadeTo(buses.car,0,0.6); fadeTo(buses.hall,1,1.6); crowdDensity=0.35; ensureChat();
    if(SFXBUF.chatter){ fadeTo(buses.chat,0.12,1); fadeTo(buses.crowd,0,0.3); } else { fadeTo(buses.crowd,0.45,0.5); scheduleMurmur(); } }
  else if(s==='office'){ fadeTo(buses.idle,0,1); ensureLoop('office',buses.office,'_offL'); fadeTo(buses.car,0,1.2); fadeTo(buses.hall,0,0.8); fadeTo(buses.evening,0,1); fadeTo(buses.office,0.55,1.5); fadeTo(buses.engine,0,0.8); clearInterval(wiperTimer); if(buses.wipers) fadeTo(buses.wipers,0,0.5); }
  else if(s==='officeLow'){ ensureLoop('office',buses.office,'_offL'); fadeTo(buses.office,0.28,1.2); }
  else if(s==='night'){ ensureLoop('k3room',buses.night,'_nightL'); fadeTo(buses.idle,0,1); fadeTo(buses.car,0,1); fadeTo(buses.office,0,1.5); fadeTo(buses.evening,0,1.5); fadeTo(buses.night,0.55,2.5); }
  else if(s==='evening'){ ensureLoop('evening',buses.evening,'_eveL'); fadeTo(buses.office,0,2.5); fadeTo(buses.evening,0.6,2.5); }
  else { fadeTo(buses.idle,0,(s==='none'&&typeof Q!=='undefined'&&Q[ip+1]&&Q[ip+1].t==='dlg')?0.4:2.5); fadeTo(buses.car,0,2.5); fadeTo(buses.hall,0,2.5); fadeTo(buses.engine,0,2.5); fadeTo(buses.office,0,2.5); fadeTo(buses.evening,0,2.5); if(buses.night) fadeTo(buses.night,0,2.5); clearInterval(wiperTimer); }
  if(s==='car'){ fadeTo(buses.office,0,1); fadeTo(buses.evening,0,1.2); }
}
// ambience dips gently while someone speaks, like a real mix
function startDucking(levelFn){ setInterval(()=>{ if(!ctx||!ambDuck) return; const l=Math.min(1,levelFn()); const base=0.8; ambDuck.gain.setTargetAtTime(base*(1-0.2*Math.min(1,l*1.6)),ctx.currentTime,0.18); },60); }

function burst(dest,{f=1000,type='bandpass',q=1,a=0.3,dur=0.1,attack=0.005,pan=0,delay=0}){
  const t=ctx.currentTime+delay, s=ctx.createBufferSource(); s.buffer=WHITE; const fl=filt(type,f,q); const g=gain(0);
  let out=g; if(ctx.createStereoPanner){ const p=ctx.createStereoPanner(); p.pan.value=pan; g.connect(p); out=p; }
  s.connect(fl); fl.connect(g); out.connect(dest||master);
  g.gain.setValueAtTime(0,t); g.gain.linearRampToValueAtTime(a,t+attack); g.gain.exponentialRampToValueAtTime(0.0001,t+attack+dur); s.start(t,Math.random()*3,attack+dur+0.05); }
function tone(f,{a=0.2,dur=0.15,type='sine',delay=0,dest,pan=0,decay=true}={}){
  const t=ctx.currentTime+delay, o=ctx.createOscillator(); o.type=type; o.frequency.value=f; const g=gain(0);
  let out=g; if(ctx.createStereoPanner){ const p=ctx.createStereoPanner(); p.pan.value=pan; g.connect(p); out=p; }
  o.connect(g); out.connect(dest||master); g.gain.setValueAtTime(0,t); g.gain.linearRampToValueAtTime(a,t+0.005);
  if(decay) g.gain.exponentialRampToValueAtTime(0.0001,t+dur); else { g.gain.setValueAtTime(a,t+dur-0.01); g.gain.linearRampToValueAtTime(0,t+dur); }
  o.start(t); o.stop(t+dur+0.05); }
function wiper(){ const t=ctx.currentTime; [0,0.95].forEach((d,i)=>{
  // rubber blade dragging over wet glass, then the soft thunk at the end of the stroke
  const s=ctx.createBufferSource(); s.buffer=PINK; const f=filt('bandpass',520,0.9), f2=filt('peaking',1500,2,5), g=gain(0);
  let out=g; if(ctx.createStereoPanner){ const p=ctx.createStereoPanner(); p.pan.setValueAtTime(i?0.5:-0.5,t+d); p.pan.linearRampToValueAtTime(i?-0.5:0.5,t+d+0.75); g.connect(p); out=p; }
  s.connect(f); f.connect(f2); f2.connect(g); out.connect(buses.car); g.gain.setValueAtTime(0,t+d); g.gain.linearRampToValueAtTime(0.05,t+d+0.18); g.gain.linearRampToValueAtTime(0.0,t+d+0.8); s.start(t+d,Math.random()*2,0.9);
  burst(buses.car,{f:160,type:'lowpass',a:0.12,dur:0.08,delay:d+0.8,pan:i?-0.5:0.5}); }); }
const SFX={
  rustle(){ for(let i=0;i<12;i++) burst(master,{f:1800+Math.random()*2200,q:0.7,a:0.035+Math.random()*0.05,dur:0.05+Math.random()*0.08,delay:i*0.07+Math.random()*0.05,pan:0.3}); },
  keypad(){ const dt=[[697,1209],[770,1336],[852,1477],[697,1336]];
    dt.forEach((k,i)=>{ tone(k[0],{a:0.035,dur:0.11,delay:i*0.28,decay:false,pan:0.25}); tone(k[1],{a:0.035,dur:0.11,delay:i*0.28,decay:false,pan:0.25}); burst(master,{f:3500,q:2,a:0.03,dur:0.01,delay:i*0.28,pan:0.25}); }); },
  whoosh(){ const t=ctx.currentTime, s=ctx.createBufferSource(); s.buffer=PINK; const f=filt('bandpass',200,1.1); const g=gain(0);
    s.connect(f); f.connect(g); g.connect(master); f.frequency.setValueAtTime(150,t); f.frequency.exponentialRampToValueAtTime(2400,t+0.9); f.frequency.exponentialRampToValueAtTime(120,t+1.8);
    g.gain.setValueAtTime(0,t); g.gain.linearRampToValueAtTime(0.22,t+0.8); g.gain.linearRampToValueAtTime(0,t+1.8); s.start(t,0,2);
    tone(110,{a:0.05,dur:1.8}); tone(164.8,{a:0.035,dur:1.8,delay:0.1}); },
  crowdUp(){ crowdDensity=1; if(SFXBUF.chatter) fadeTo(buses.chat,0.55,1.6); else fadeTo(buses.crowd,0.8,1.2); },
  laugh(){ if(!SFXBUF.laugh) return; const s=ctx.createBufferSource(); s.buffer=SFXBUF.laugh; const g=gain(0.75); s.connect(g); g.connect(buses.hall); g.connect(buses.hallWet); s.start(); },
  steps(){ for(let i=0;i<6;i++){ burst(buses.hall,{f:170,type:'lowpass',a:0.28,dur:0.07,delay:i*0.48,pan:(i%2?0.2:-0.2)}); burst(buses.hallWet,{f:2200,q:2,a:0.03,dur:0.02,delay:i*0.48+0.01}); } },
  cups(){ for(let i=0;i<3;i++){ const d=Math.random()*1.2; tone(2600+Math.random()*1600,{a:0.03,dur:0.3,delay:d,dest:buses.hall,pan:Math.random()-.5}); tone(5000+Math.random()*800,{a:0.012,dur:0.18,delay:d,dest:buses.hallWet}); } },
  bumpSynth(){ burst(master,{f:240,type:'lowpass',a:0.5,dur:0.16,pan:0.4}); const t=ctx.currentTime,o=ctx.createOscillator(),g=gain(0); o.frequency.setValueAtTime(110,t); o.frequency.exponentialRampToValueAtTime(45,t+0.2); o.connect(g); g.connect(master); g.gain.setValueAtTime(0.35,t); g.gain.exponentialRampToValueAtTime(0.001,t+0.25); o.start(t); o.stop(t+0.3);
    burst(master,{f:2600,q:0.7,a:0.07,dur:0.22,delay:0.05,pan:0.4}); },
  radio(){ tone(1250,{a:0.05,dur:0.09,decay:false}); burst(master,{f:1800,q:0.8,a:0.1,dur:0.3,delay:0.1,attack:0.01}); },
  radioEnd(){ burst(master,{f:1800,q:0.8,a:0.11,dur:0.22,attack:0.01}); tone(900,{a:0.045,dur:0.08,delay:0.26,decay:false}); },
  engineStart(){ const t=ctx.currentTime;
    if(SFXBUF.engine){ const s=ctx.createBufferSource(); s.buffer=SFXBUF.engine; const g=gain(0.8); s.connect(g); g.connect(buses.car); s.start();
      const d=SFXBUF.engine.duration; g.gain.setValueAtTime(0.8,t+Math.max(0.5,d-1.2)); g.gain.linearRampToValueAtTime(0,t+d);
      buses.engine.gain.setValueAtTime(0,t+Math.max(0.5,d-1.4)); buses.engine.gain.linearRampToValueAtTime(0.08,t+d);
      if(SFXBUF.wipers){ setTimeout(()=>{ loopBuf(SFXBUF.wipers,buses.wipers); fadeTo(buses.wipers,0.35,1.5); },1600); }
      else { clearInterval(wiperTimer); setTimeout(()=>{ wiper(); wiperTimer=setInterval(wiper,2700); },1800); }
      return; }
    for(let i=0;i<7;i++) burst(buses.car,{f:200,type:'lowpass',a:0.32,dur:0.09,delay:i*0.12});
    buses.engine.gain.setValueAtTime(0,t+0.85); buses.engine.gain.linearRampToValueAtTime(0.26,t+1.0); buses.engine.gain.setTargetAtTime(0.11,t+1.2,0.4);
    clearInterval(wiperTimer); setTimeout(()=>{ wiper(); wiperTimer=setInterval(wiper,2700); },1800); },
  indicator(){ for(let i=0;i<10;i++){ burst(buses.car,{f:3200,q:3,a:0.07,dur:0.015,delay:i*0.38,pan:-0.5}); burst(buses.car,{f:1700,q:3,a:0.05,dur:0.015,delay:i*0.38+0.19,pan:-0.5}); } },
  // collision: play the recording, then let it die away right after the impact so no footsteps run under the dialogue
  bump(){ if(!SFXBUF.bump) return SFX.bumpSynth(); const t=ctx.currentTime, s=ctx.createBufferSource(); s.buffer=SFXBUF.bump; const g=gain(0.9); s.connect(g); g.connect(buses.hall); g.connect(buses.hallWet); s.start(t);
    /* short take: impact ~1.25 s, cup + coffee follow; let it finish naturally under the dialogue (ducked) */ },
  // decision moment: a cue, a tense bed under the question, a satisfying hit on commit
  choiceIn(){ if(SFXBUF.cue){ const s=ctx.createBufferSource(); s.buffer=SFXBUF.cue; const g=gain(0.7); s.connect(g); g.connect(master); s.start(); }
    else { const t=ctx.currentTime, o=ctx.createOscillator(), g=gain(0); o.frequency.setValueAtTime(70,t); o.frequency.exponentialRampToValueAtTime(42,t+0.35); o.connect(g); g.connect(master); g.gain.setValueAtTime(0.5,t); g.gain.exponentialRampToValueAtTime(0.001,t+0.5); o.start(t); o.stop(t+0.6);
      tone(880,{a:0.03,dur:1.2,delay:0.15}); tone(1318,{a:0.02,dur:1.4,delay:0.25}); }
    if(ambDuck) ambDuck.gain.setTargetAtTime(0.35,ctx.currentTime,0.4); },
  tensionOn(){ if(!buses.tension){ buses.tension=gain(0); buses.tension.connect(master);
      if(SFXBUF.tension) loopBuf(SFXBUF.tension,buses.tension);
      else { const o1=ctx.createOscillator(), o2=ctx.createOscillator(), f=filt('lowpass',420,1), lfo=ctx.createOscillator(), lg=gain(0.25);
        o1.type='sawtooth'; o2.type='sawtooth'; o1.frequency.value=55; o2.frequency.value=55.4; lfo.frequency.value=1.1; lfo.connect(lg);
        const v=gain(0.12); lg.connect(v.gain); o1.connect(f); o2.connect(f); f.connect(v); v.connect(buses.tension); o1.start(); o2.start(); lfo.start(); } }
    fadeTo(buses.tension,0.5,1.8); },
  tensionOff(){ if(buses.tension) fadeTo(buses.tension,0,0.6); },
  choicePick(){ if(SFXBUF.pick){ const s=ctx.createBufferSource(); s.buffer=SFXBUF.pick; const g=gain(0.75); s.connect(g); g.connect(master); s.start(); }
    else { burst(master,{f:900,q:0.6,a:0.18,dur:0.35,attack:0.12}); const t=ctx.currentTime,o=ctx.createOscillator(),g=gain(0); o.frequency.setValueAtTime(90,t+0.12); o.frequency.exponentialRampToValueAtTime(40,t+0.5); o.connect(g); g.connect(master); g.gain.setValueAtTime(0,t); g.gain.linearRampToValueAtTime(0.45,t+0.13); g.gain.exponentialRampToValueAtTime(0.001,t+0.6); o.start(t); o.stop(t+0.7); }
    if(ambDuck) ambDuck.gain.setTargetAtTime(0.8,ctx.currentTime+0.4,0.6); },
  phoneTap(){ burst(master,{f:1800,q:1.2,a:0.12,dur:0.04,pan:0.15}); burst(master,{f:300,type:'lowpass',a:0.18,dur:0.06,pan:0.15}); },
  pings(){ [0,0.45,0.8,1.1].forEach((d,i)=>{ tone(1568,{a:0.03,dur:0.18,delay:d,pan:0.2}); tone(2093,{a:0.02,dur:0.22,delay:d+0.07,pan:0.2}); }); },
  chime(){ tone(660,{a:0.05,dur:0.6}); tone(990,{a:0.035,dur:0.8,delay:0.12}); }
};
