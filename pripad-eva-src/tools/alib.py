import numpy as np, subprocess
from scipy.signal import butter, sosfilt, lfilter, fftconvolve
SR = 48000

def load(p, sr=SR, ch=1):
    a = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', str(ch), '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(a, np.float32).copy()
    return x.reshape(-1, ch).T if ch > 1 else x

def save(x, p, br=None):
    x = np.atleast_2d(x)
    if x.shape[0] > x.shape[1]: x = x.T
    ch = x.shape[0]
    args = ['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', str(ch), '-i', '-']
    args += (['-c:a', 'libmp3lame', '-b:a', br] if br else ['-c:a', 'pcm_s24le'])
    subprocess.run(args + [p], input=np.ascontiguousarray(x.T).astype(np.float32).tobytes(), check=True)

def kw(x):
    # BS.1770 K-weighting @48k
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]; a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]; a2 = [1.0, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, x))

def lufs(x):
    x = np.atleast_2d(x)
    if x.shape[0] > x.shape[1]: x = x.T
    y = np.stack([kw(c) for c in x])
    blk = int(0.4 * SR); hop = int(0.1 * SR)
    if y.shape[1] < blk: blk = hop = y.shape[1]
    ms = np.array([np.sum(np.mean(y[:, i:i + blk] ** 2, axis=1)) for i in range(0, y.shape[1] - blk + 1, hop)])
    L = -0.691 + 10 * np.log10(ms + 1e-12)
    g = ms[L > -70]
    if not len(g): return -70
    rel = -0.691 + 10 * np.log10(np.mean(g)) - 10
    g2 = ms[(L > -70) & (L > rel)]
    return -0.691 + 10 * np.log10(np.mean(g2) + 1e-12)

def norm(x, target):
    return x * 10 ** ((target - lufs(x)) / 20)

def hp(x, f, o=2): return sosfilt(butter(o, f, 'highpass', fs=SR, output='sos'), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'lowpass', fs=SR, output='sos'), x)

def peq(x, f, gdb, q=1.0):
    A = 10 ** (gdb / 40); w = 2 * np.pi * f / SR; al = np.sin(w) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w), 1 - al * A]; a = [1 + al / A, -2 * np.cos(w), 1 - al / A]
    return lfilter(np.array(b) / a[0], np.array(a) / a[0], x)

def shelf(x, f, gdb, kind='low'):
    A = 10 ** (gdb / 40); w = 2 * np.pi * f / SR; al = np.sin(w) / 2 * np.sqrt(2); c = np.cos(w); s = 2 * np.sqrt(A) * al
    if kind == 'low':
        b = [A * ((A + 1) - (A - 1) * c + s), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - s)]
        a = [(A + 1) + (A - 1) * c + s, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - s]
    else:
        b = [A * ((A + 1) + (A - 1) * c + s), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - s)]
        a = [(A + 1) - (A - 1) * c + s, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - s]
    return lfilter(np.array(b) / a[0], np.array(a) / a[0], x)

def comp(x, thr=-20, ratio=3, att=0.005, rel=0.12, makeup=0):
    env = np.abs(x); out = np.empty_like(x); e = 0.0
    aa = np.exp(-1 / (att * SR)); ar = np.exp(-1 / (rel * SR))
    # vectorised-ish envelope via loop on decimated signal
    d = 32; ed = np.zeros(len(x) // d + 1)
    for i, v in enumerate(env[::d]):
        c = aa ** d if v > e else ar ** d
        e = c * e + (1 - c) * v; ed[i] = e
    eu = np.repeat(ed, d)[:len(x)]
    db = 20 * np.log10(eu + 1e-9)
    gr = np.minimum(0, (thr - db) * (1 - 1 / ratio))
    return x * 10 ** ((gr + makeup) / 20)

def room_ir(t60=0.45, pre=0.008, seed=1, bright=5000):
    rng = np.random.default_rng(seed); n = int(t60 * SR)
    ir = rng.standard_normal((2, n)) * np.exp(-6.9 * np.arange(n) / n)
    ir = np.stack([lp(c, bright) for c in ir])
    # early reflections
    for k, (dt, g) in enumerate([(0.011, .5), (0.017, .35), (0.023, .3), (0.031, .22)]):
        i = int(dt * SR); ir[k % 2, i] += g
    ir = np.concatenate([np.zeros((2, int(pre * SR))), ir], 1)
    return ir / np.sqrt(np.sum(ir ** 2) / 2)

def verb(x, ir, wet):
    n = len(x) + ir.shape[1]
    y = np.stack([np.pad(fftconvolve(x, c), (0, 1))[:n] for c in ir])
    dry = np.pad(x, (0, ir.shape[1]))
    return np.stack([dry, dry]) + wet * y

def fade(x, fi=0.01, fo=0.02):
    x = x.copy(); a = int(fi * SR); b = int(fo * SR)
    if a: x[..., :a] *= np.linspace(0, 1, a)
    if b: x[..., -b:] *= np.linspace(1, 0, b)
    return x

def pan(x, p):  # p -1..1, constant power
    t = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(t), x * np.sin(t)])
