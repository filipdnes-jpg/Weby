import json, os, re, numpy as np
from alib import *

S = {o['id']: o for o in json.load(open('script.json')) if o.get('id')}
WHO = {'eva': 'eva', 'nikol': 'nikol', 'nikol_think': 'nikolT', 'babka': 'babka'}
IR_ROOM = room_ir(0.38, seed=3, bright=4500)
IR_FAR = room_ir(0.55, seed=5, bright=3800)
os.makedirs('out', exist_ok=True)

def clean(t): return re.sub(r'\s+', ' ', re.sub(r'\[[^\]]*\]', '', t)).strip()

def voice(idx):
    x = load(f'lines/{idx}.wav'); who = S[idx]['who']
    if who == 'eva':
        y = hp(hp(x, 320, 4), 300, 2); y = lp(lp(y, 3400, 4), 3600, 2); y = peq(y, 1800, 3.5, 0.9)
        y = comp(y, -26, 4, makeup=0); y = np.tanh(y * 2.2) / 2.2
        y = norm(y, -21.0); st = np.stack([y, y]) * 0.98; L = len(y)
    elif who == 'nikol':
        y = hp(x, 80); y = peq(y, 260, -1.5, 1); y = comp(y, -22, 2.5); y = norm(y, -18.0)
        st = verb(y, IR_ROOM, 0.10); L = len(y)
    elif who == 'nikol_think':
        y = hp(x, 90); y = shelf(y, 200, 1.5, 'low'); y = shelf(y, 7000, -2, 'high'); y = comp(y, -24, 2.5); y = norm(y, -19.0)
        st = verb(y, IR_ROOM, 0.035); L = len(y)
    else:  # babka – a few steps away, at the bedroom door
        y = hp(x, 120); y = lp(y, 6500); y = comp(y, -22, 2.5); y = norm(y, -21.5)
        st = verb(y, IR_FAR, 0.24); st = st * np.array([[0.82], [1.0]]); L = len(y)
    return st, L / SR

def sfx(name, trim=None, target=None, gain_db=0, lpf=None, hpf=None, fo=0.05):
    x = load(f'raw/k3s_{name}.mp3', ch=2)
    if trim: x = x[:, int(trim[0] * SR):int(trim[1] * SR) if trim[1] else None]
    if hpf: x = np.stack([hp(c, hpf) for c in x])
    if lpf: x = np.stack([lp(c, lpf) for c in x])
    if target is not None: x = norm(x, target)
    return fade(x * 10 ** (gain_db / 20), 0.01, fo)

def phone_filter(y):
    y = hp(hp(y, 320, 4), 300); y = lp(lp(y, 3400, 4), 3600); return y

def tone_pattern(on, off, n, f=425, lvl=-26):
    seg = []
    for i in range(n):
        t = np.arange(int(on * SR)) / SR; s = np.sin(2 * np.pi * f * t); s = fade(s, 0.008, 0.008)
        seg += [s, np.zeros(int(off * SR))]
    y = phone_filter(np.concatenate(seg)); y = norm(y, lvl)
    return np.stack([y * 0.9, y])  # in Nikol's right ear (phone)

def click(lvl=-34):
    rng = np.random.default_rng(7); n = int(0.012 * SR); y = rng.standard_normal(n) * np.exp(-np.arange(n) / (0.002 * SR))
    y = np.concatenate([y, np.zeros(int(0.05 * SR))]); y = phone_filter(y); y = norm(y, lvl); return np.stack([y, y])

def vibrate_pulses(total):
    x = load('raw/k3s_vibrate.mp3', ch=2)[:, :int(6.5 * SR)]; x = np.concatenate([x, x, x], 1)[:, :int(total * SR)]
    g = np.zeros(x.shape[1]); p = int(0.42 * SR); per = int(1.0 * SR)
    for s in range(0, len(g), per):
        if (s // per) % 3 == 2: continue  # ring cadence: buzz, buzz, pause
        e = min(len(g), s + p); g[s:e] = 1
    g = np.convolve(g, np.ones(int(0.012 * SR)) / int(0.012 * SR), 'same')
    return norm(x * g, -31)

class TL:
    def __init__(self): self.buf = np.zeros((2, SR * 200)); self.t = 0.0; self.subs = []; self.end = 0.0; self.last = None
    def put(self, st, at, gain=1.0):
        i = int(at * SR); n = st.shape[1]
        if i + n > self.buf.shape[1]: self.buf = np.pad(self.buf, ((0, 0), (0, i + n)))
        self.buf[:, i:i + n] += st * gain; self.end = max(self.end, at + n / SR)
    def line(self, idx, gap=None, at=None):
        st, d = voice(idx); who = S[idx]['who']
        if gap is None:
            gap = 0.5 if self.last == who else (0.45 if who == 'eva' else 0.38)
            if who == 'nikol_think': gap = 0.6
            if self.last is None: gap = 0
        at = self.t + gap if at is None else at
        self.put(st, at); self.subs.append({'who': WHO[who], 'text': clean(S[idx]['text']), 'at': round(at, 2)})
        self.t = at + d; self.last = who
        return at
    def fx(self, st, at=None, rel=0.0, advance=False, gain=1.0):
        at = self.t + rel if at is None else at
        self.put(st, at, gain)
        if advance: self.t = at + st.shape[1] / SR
        return at
    def wait(self, s): self.t += s
    def render(self, name, tail=0.6, fo=0.4):
        n = int((max(self.t, self.end) + tail) * SR) if tail is not None else int(self.end * SR)
        y = self.buf[:, :n]; y = fade(y, 0.0, fo)
        y = y * 10 ** (-1.5 / 20)
        a = np.abs(y).max(0); g = np.minimum(1, 0.89 / (a + 1e-9))
        w = int(0.004 * SR); g = -np.convolve(-g, np.ones(1), 'same')
        from scipy.ndimage import minimum_filter1d, uniform_filter1d
        g = uniform_filter1d(minimum_filter1d(g, 2 * w), 2 * w); y = y * g
        save(y, f'out/{name}.mp3', '192k'); save(y, f'out/{name}.wav')
        json.dump(self.subs, open(f'out/{name}.json', 'w'), ensure_ascii=False)
        print(name, round(y.shape[1] / SR, 1), 's', 'LUFS', round(lufs(y), 1), 'peak', round(20 * np.log10(np.abs(y).max()), 1))

# ---------------- ÚVOD ----------------
T = TL(); T.t = 1.6
vib = vibrate_pulses(14.0); v0 = T.fx(vib)
T.line('k3_uvod_01', at=v0 + 1.1)
T.line('k3_uvod_02', gap=0.35)
pick = max(T.t + 0.25, v0 + 4.0)
# vibration ends where she picks up
cut = int((pick - v0) * SR); vib2 = vib.copy(); vib2[:, cut:] = 0; vib2[:, max(0, cut - 600):cut] *= np.linspace(1, 0, min(600, cut))
T.buf[:, int(v0 * SR):int(v0 * SR) + vib.shape[1]] -= vib; T.put(vib2, v0)
T.fx(sfx('duvet', (0.8, 3.9), -30), at=pick - 0.2)
T.fx(click(-36), at=pick + 1.6); T.t = pick + 1.9
for i in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
    T.line(f'k3_uvod_{i:02d}')
T.wait(2.0)
T.line('k3_uvod_15', gap=0)
for i in [16, 17, 18, 19]: T.line(f'k3_uvod_{i:02d}')
clk = sfx('clock', (0, 6), -27); clk = clk * np.linspace(0.15, 1, clk.shape[1])
T.fx(clk, rel=0.2); T.wait(0.2 + 5.6)
T.render('k3_uvod', tail=0.1, fo=1.2)

# ---------------- A1 ----------------
T = TL(); T.t = 0.3
for i in [1, 2, 3]: T.line(f'k3_a1_{i:02d}')
T.render('k3_a1')

# ---------------- A2 ----------------
T = TL(); T.t = 0.3
T.line('k3_a2_01'); T.wait(2.0); T.line('k3_a2_02', gap=0)
T.fx(tone_pattern(0.33, 0.33, 3, lvl=-27), rel=0.5, advance=True)
T.line('k3_a2_03', gap=0.3)
T.fx(tone_pattern(1.0, 2.2, 2, lvl=-28), rel=0.5, advance=True)
T.fx(sfx('sms', None, -27), rel=0.3, advance=True)
T.line('k3_a2_04', gap=0.5)
T.line('k3_a2_05', gap=0.4)
T.fx(tone_pattern(1.0, 1.6, 1, lvl=-28), rel=0.4, advance=True)
T.fx(click(-36), rel=0.1, advance=True); T.wait(0.9)
T.line('k3_a2_06', gap=0); T.line('k3_a2_07')
T.render('k3_a2')

# ---------------- A3 ----------------
T = TL(); T.t = 0.3
T.line('k3_a3_01'); T.line('k3_a3_02')
T.fx(sfx('tap_rec', None, -36), rel=0.3, advance=True)
T.line('k3_a3_03', gap=0.4); T.line('k3_a3_04')
T.render('k3_a3')

# ---------------- OBÁLKA ----------------
T = TL(); T.t = 0.5
for i in [1, 2, 3, 4, 5, 6]: T.line(f'k3_obalka_{i:02d}')
T.wait(1.0); T.line('k3_obalka_07', gap=0)
T.render('k3_obalka')

# ---------------- B1 / B2 / B3 ----------------
T = TL(); T.t = 0.3
T.line('k3_b1_01'); T.fx(sfx('zip_bag', None, -30), rel=0.3, advance=True); T.line('k3_b1_02', gap=0.3)
T.render('k3_b1')

T = TL(); T.t = 0.3
T.line('k3_b2_01'); T.fx(sfx('tear_env', None, -30), rel=0.3, advance=True)
for i in [2, 3, 4, 5]: T.line(f'k3_b2_{i:02d}')
T.fx(sfx('dressing', (1.0, 2.6), -34, fo=0.3), rel=0.2, advance=True)
T.render('k3_b2')

T = TL(); T.t = 0.3
T.line('k3_b3_01'); T.fx(sfx('parquet', (0.0, 8.0), -32, fo=0.4), rel=0.3); T.wait(2.6)
T.line('k3_b3_02', gap=0); T.wait(1.2); T.line('k3_b3_03')
T.t = max(T.t, T.end - 0.5)
T.render('k3_b3')

# ---------------- ODCHOD ----------------
T = TL(); T.t = 0.3
T.line('k3_odchod_01'); T.line('k3_odchod_02'); T.line('k3_odchod_03')
T.fx(sfx('dressing', None, -31, fo=0.3), rel=0.4, advance=True)
d = sfx('door_slippers', (0.0, 7.0), -31, lpf=7000, fo=0.6); T.fx(d, rel=0.2); T.wait(3.2)
T.line('k3_odchod_04', gap=0); T.line('k3_odchod_05')
T.render('k3_odchod')

# ---------------- SLUŽBA / PRAVDA ----------------
T = TL(); T.t = 0.3
for i in [1, 2, 3, 4]: T.line(f'k3_sluzba_{i:02d}')
T.render('k3_sluzba')

T = TL(); T.t = 0.3
for i in [1, 2, 3]: T.line(f'k3_pravda_{i:02d}')
T.wait(2.0); T.line('k3_pravda_04', gap=0); T.line('k3_pravda_05')
T.render('k3_pravda')

# ---------------- ZÁVER ----------------
T = TL(); T.t = 0.2
ex = sfx('exit_stairs', (0.0, 13.0), -24, fo=1.0); T.fx(ex); T.t = 11.0
car = sfx('car_start', (0.0, 11.4), -24, fo=2.5); c0 = T.fx(car)
T.t = c0 + 4.2
T.line('k3_zaver_01', gap=0); T.line('k3_zaver_02'); T.line('k3_zaver_03'); T.line('k3_zaver_04')
T.t = max(T.t + 1.0, T.end)
T.render('k3_zaver', tail=0.0, fo=2.5)

# choice prompts (engine applies the thought colour itself)
for q in ['k3_uvod_q', 'k3_obalka_q', 'k3_odchod_q']:
    x = load(f'lines/{q}.wav'); y = norm(comp(hp(x, 90), -24, 2.5), -19.0); save(fade(y, .005, .05), f'out/{q}.mp3', '192k')
