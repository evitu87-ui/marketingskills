"""Airy titles that sit BEHIND the people in the frame.

Typography follows the reference brand book Vitaly supplied (28.11.2026): IBM Plex Sans,
light headlines, extra-light large numbers, tracked caps labels, thin rules, lots of air.
A person matte (u2net_human_seg, ONNX) is computed per frame and the text layer is multiplied
by (1 - matte), so hosts always stay in front of the graphics.

Usage:  python3 titles_air.py base.mp4 spec.json out.mp4            # video
        python3 titles_air.py base.mp4 spec.json out.png 3.2        # one frame at 3.2 s

Spec: {"fps":30, "events":[{"start":0.1,"end":5.6,"x":84,"y":210,"tone":"auto|pearl|ink",
        "items":[{"type":"label","t":"РЫНОК В ЦИФРАХ","at":0.1},
                 {"type":"number","t":"−21 %","at":0.4},
                 {"type":"rule","at":0.9},
                 {"type":"head","t":"сделок за год","at":1.0},
                 {"type":"sub","t":"DLD · 25.11.2026","at":1.3}]}]}
Item sizes can be overridden with "size". Head text wraps at "maxw" (default 0.80 of width).
Model path: env U2NET or ./u2net_human_seg.onnx next to this file (not kept in the repo).
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
W, H = 1080, 1920
FACE = {'number': 'IBMPlexSans-ExtraLight.ttf', 'head': 'IBMPlexSans-Light.ttf',
        'sub': 'IBMPlexSans-Regular.ttf', 'label': 'IBMPlexSans-Medium.ttf'}
SIZE = {'number': 236, 'head': 76, 'sub': 36, 'label': 30}
GAP = {'number': 4, 'head': 10, 'sub': 14, 'label': 18, 'rule': 26}
TRACK = {'label': 0.24, 'number': -0.01, 'head': 0.0, 'sub': 0.01}
PEARL, INK, STEEL = (244, 241, 236), (27, 31, 34), (139, 147, 153)
FADE, DRIFT, OUT = 0.50, 16, 0.35

def font(kind, size):
    return ImageFont.truetype(os.path.join(FONTS, FACE[kind]), size)

def text_w(f, s, track):
    return sum(f.getlength(c) + track * f.size for c in s) - track * f.size

def wrap(f, s, maxw, track):
    out, cur = [], ''
    for word in s.split(' '):
        t = (cur + ' ' + word).strip()
        if cur and text_w(f, t, track) > maxw:
            out.append(cur); cur = word
        else:
            cur = t
    return out + [cur] if cur else out

def sprite(kind, s, size, color, maxw):
    """RGBA sprite of one item (text with a very soft halo for legibility)."""
    track = TRACK[kind]
    f = font(kind, size)
    if kind == 'number':
        while text_w(f, s, track) > maxw and size > 90:
            size -= 6; f = font(kind, size)
    lines = wrap(f, s, maxw, track) if kind in ('head', 'sub') else [s.upper() if kind == 'label' else s]
    asc, desc = f.getmetrics()
    lh = int(size * (1.14 if kind == 'head' else 1.0)) if kind != 'number' else int(size * 0.92)
    pad = 60
    w = int(max(text_w(f, l, track) for l in lines)) + pad * 2
    h = lh * len(lines) + pad * 2 + desc
    mask = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(mask)
    for i, l in enumerate(lines):
        x = pad
        y = pad + i * lh - (int(asc * 0.16) if kind == 'number' else 0)
        for c in l:
            d.text((x, y), c, font=f, fill=255)
            x += f.getlength(c) + track * size
    halo_c = (0, 0, 0) if color == PEARL else (255, 255, 255)
    halo = mask.filter(ImageFilter.GaussianBlur(max(6, size // 9))).point(lambda v: int(v * (0.42 if color == PEARL else 0.5)))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.paste(Image.new('RGBA', (w, h), halo_c + (255,)), (0, 0), halo)
    out.paste(Image.new('RGBA', (w, h), color + (255,)), (0, 0), mask)
    return out, pad, lh * len(lines)

def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3

class Matte:
    def __init__(self):
        import onnxruntime as ort
        path = os.environ.get('U2NET') or os.path.join(HERE, 'u2net_human_seg.onnx')
        so = ort.SessionOptions(); so.intra_op_num_threads = int(os.environ.get('THREADS', '4'))
        self.s = ort.InferenceSession(path, so, providers=['CPUExecutionProvider'])
        self.n = self.s.get_inputs()[0].name
        self.prev = None
    def __call__(self, rgb):
        import cv2
        im = cv2.resize(rgb, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        im = (im - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
        o = self.s.run(None, {self.n: im.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
        o = (o - o.min()) / (o.max() - o.min() + 1e-8)
        m = cv2.resize(o, (W, H), interpolation=cv2.INTER_CUBIC)
        m = np.clip((m - 0.35) / 0.4, 0, 1)                      # firm up the core
        m = cv2.dilate(m, np.ones((5, 5), np.uint8))              # text stops just before the hair edge
        m = cv2.GaussianBlur(m, (0, 0), 2.2)
        if self.prev is not None:
            m = 0.65 * m + 0.35 * self.prev                       # calm the edge between frames
        self.prev = m
        return m

def build(spec, probe):
    """Pre-render sprites; probe(t) returns an RGB frame for automatic tone."""
    evs = []
    for ev in spec['events']:
        x0, y = ev.get('x', 84), ev.get('y', 210)
        maxw = int(ev.get('maxw', 0.80) * W)
        tone = ev.get('tone', 'auto')
        if tone == 'auto':
            fr = probe((ev['start'] + ev['end']) / 2)
            box = fr[y:min(y + 420, H), x0:min(x0 + maxw, W)].astype(np.float32)
            lum = (0.2126 * box[..., 0] + 0.7152 * box[..., 1] + 0.0722 * box[..., 2]).mean()
            tone = 'ink' if lum > 150 else 'pearl'
        color = INK if tone == 'ink' else PEARL
        items = []
        for it in ev['items']:
            k = it['type']
            if k == 'rule':
                y += GAP['rule']
                items.append({'k': k, 'x': x0, 'y': y, 'w': it.get('w', 360), 'at': it['at'], 'c': STEEL if tone == 'ink' else PEARL})
                y += 2 + GAP['rule']
                continue
            sp, pad, hh = sprite(k, it['t'], it.get('size', SIZE[k]), color, maxw)
            items.append({'k': k, 'sp': sp, 'x': x0 - pad, 'y': y - pad, 'at': it['at']})
            y += hh + GAP[k]
        evs.append({'start': ev['start'], 'end': ev['end'], 'items': items})
    return evs

def layer(evs, t):
    L = None
    for ev in evs:
        if not (ev['start'] - 0.05 <= t <= ev['end'] + OUT):
            continue
        fade_out = 1 - ease((t - ev['end']) / OUT) if t > ev['end'] else 1.0
        for it in ev['items']:
            p = ease((t - it['at']) / FADE)
            if p <= 0:
                continue
            if L is None:
                L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            a = p * fade_out
            if it['k'] == 'rule':
                d = ImageDraw.Draw(L)
                d.rectangle([it['x'], it['y'], it['x'] + int(it['w'] * p), it['y'] + 2], fill=it['c'] + (int(200 * fade_out),))
                continue
            sp = it['sp']
            if a < 0.999:
                sp = sp.copy(); sp.putalpha(sp.getchannel('A').point(lambda v: int(v * a)))
            L.alpha_composite(sp, (it['x'], int(it['y'] + DRIFT * (1 - p))))
    return L

def compose(rgb, L, matte):
    if L is None:
        return rgb
    la = np.asarray(L, dtype=np.float32)
    a = la[..., 3:4] / 255.0 * (1.0 - matte(rgb)[..., None])
    return (rgb * (1 - a) + la[..., :3] * a).astype(np.uint8)

def main():
    base, spec_p, out = sys.argv[1:4]
    spec = json.load(open(spec_p, encoding='utf-8'))
    fps = spec.get('fps', 30)
    def probe(t):
        raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{t:.3f}', '-i', base, '-frames:v', '1',
                              '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(H, W, 3)
    evs = build(spec, probe)
    matte = Matte()
    if out.lower().endswith('.png'):
        t = float(sys.argv[4])
        Image.fromarray(compose(probe(t), layer(evs, t), matte)).save(out)
        return
    dec = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-i', base, '-vf', f'scale={W}:{H},fps={fps}',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', str(fps), '-i', '-', '-i', base, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-crf', '16',
                            '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-shortest', out], stdin=subprocess.PIPE)
    n = 0
    while True:
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3:
            break
        rgb = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        enc.stdin.write(compose(rgb, layer(evs, n / fps), matte).tobytes())
        n += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print('built', out, n, 'frames')

if __name__ == '__main__':
    main()
