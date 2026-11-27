"""Kinetic titles in the reference style (Sidorova, "Опус"), composited straight onto a video.

What the reference does and this module repeats:
  - the block sits in the upper third, above the presenter's head (shots must leave ~40 % headroom);
  - big bold-italic key lines and thin upright secondary lines, stacked almost without leading;
  - silver sheen (white in the middle, grey to the edges), soft shadow, slight 3D tilt, slow push-in;
  - letters arrive one by one, slightly out of order, out of a blur; the block leaves in a horizontal smear.
Extras: a big "verdict" word thrown into depth, a small italic subtitle at the bottom, white flashes on cuts.

Usage: python3 titles.py base.mp4 spec.json out.mp4

spec.json:
{"fps": 30,
 "events":   [{"start": 0.1, "end": 3.4, "y": 350, "tilt": 0.05, "roll": 1.5,
               "lines": [{"t": "Застройщик", "w": "heavy", "size": 150, "at": 0.1},
                         {"t": "достроит?", "w": "heavy", "at": 0.9},
                         {"t": "вот как мы проверяем", "w": "light", "at": 1.9}]}],
 "verdicts": [{"t": "НАДЁЖНО", "at": 6.2, "end": 7.3, "kind": "ok"}],          # kind: ok | risk | plain
 "subs":     [{"t": "Напишите «эскроу»", "start": 30.0, "end": 33.0}],
 "flashes":  [3.5, 7.4],
 "shade": 0.45}                                       # optional: darken the top of the frame under the titles
"at" = when a line starts to appear, seconds from the start of the video. "size" is optional.
"""
import json, math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

BASE, SPEC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920
FD = '/usr/share/fonts/opentype/inter/'
FACE = {'heavy': FD + 'InterDisplay-BoldItalic.otf', 'light': FD + 'InterDisplay-Light.otf',
        'mid': FD + 'InterDisplay-Medium.otf',      # secondary line for bright backgrounds, where Light gets lost
        'sub': FD + 'InterDisplay-LightItalic.otf'}
SIZE = {'heavy': 176, 'light': 98, 'mid': 90, 'sub': 46}
GAP = 14                  # px between the cap boxes of neighbouring lines
MAXW = 0.80 * W           # a line wider than this is scaled down; phones crop the sides of a 9:16 video
PER_LETTER, L_FADE, L_JIT = 0.028, 0.11, 0.035   # letter cadence, letter fade-in, order jitter (s)
OUT_T = 0.22              # exit smear (s)
PAD = 60
TINT = {'plain': (255, 255, 255), 'ok': (186, 255, 205), 'risk': (255, 150, 140)}
spec = json.load(open(SPEC, encoding='utf-8'))
FPS = spec.get('fps', 30)
random.seed(7)
_fonts = {}


def font(kind, size):
    if (kind, size) not in _fonts:
        _fonts[(kind, size)] = ImageFont.truetype(FACE[kind], size)
    return _fonts[(kind, size)]


def fit(kind, text, size):
    while font(kind, size).getlength(text) > MAXW and size > 40:
        size -= 4
    return size


def letters(kind, size, text):
    """[(x offset, sharp alpha sprite, blurred sprite, very blurred sprite)] for every visible glyph."""
    f, out = font(kind, size), []
    asc, desc = f.getmetrics()
    for i, ch in enumerate(text):
        if ch == ' ':
            continue
        x = f.getlength(text[:i])
        im = Image.new('L', (int(f.getlength(ch)) + PAD * 2, asc + desc + PAD * 2), 0)
        ImageDraw.Draw(im).text((PAD, PAD), ch, font=f, fill=255)
        out.append((x, im, im.filter(ImageFilter.GaussianBlur(size * 0.035)),
                    im.filter(ImageFilter.GaussianBlur(size * 0.09))))
    return out


def prepare(ev):
    """Lay the block out once: every line centred, cap boxes stacked GAP apart."""
    y, lines = PAD, []
    for ln in ev['lines']:
        kind = ln.get('w', 'heavy')
        size = fit(kind, ln['t'], ln.get('size', SIZE[kind]))
        f = font(kind, size)
        cap = f.getbbox('Н')                       # (x0, top, x1, bottom) of a capital
        width = f.getlength(ln['t'])
        glyphs = letters(kind, size, ln['t'])
        n = len(glyphs)
        order = sorted(range(n), key=lambda i: i + random.uniform(-2.2, 2.2))     # mostly left to right
        times = [0.0] * n
        for rank, i in enumerate(order):
            times[i] = ln['at'] + rank * PER_LETTER + random.uniform(0, L_JIT)
        lines.append(dict(glyphs=glyphs, times=times, x=(W - width) / 2, y=y - cap[1], size=size))
        y += (cap[3] - cap[1]) + GAP
    ev['_lines'], ev['_h'] = lines, int(y + PAD + 40)
    xs = np.linspace(0, 1, W)                      # silver sheen: bright centre, grey edges
    sheen = 0.80 + 0.20 * np.exp(-((xs - 0.54) / 0.28) ** 2)
    col = np.clip(np.outer(np.ones(ev['_h']), sheen) * 255, 0, 255).astype(np.uint8)
    ev['_rgb'] = Image.merge('RGB', [Image.fromarray(col)] * 3)


def persp(im, tilt, roll, scale):
    """Rotate the block a little around the vertical axis (right side closer), roll it, push in."""
    w, h = im.size
    cx, cy = w / 2, h / 2
    a = math.radians(roll)
    dst = []
    for sx, sy in ((0, 0), (w, 0), (w, h), (0, h)):
        k = scale * (1 + tilt * ((sx - cx) / cx))                 # right edge grows, left shrinks
        dx, dy = (sx - cx) * scale, (sy - cy) * k
        dst.append((cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)))
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (X, Y), (x, y) in zip(dst, src):                          # PIL wants output -> input
        A += [[X, Y, 1, 0, 0, 0, -x * X, -x * Y], [0, 0, 0, X, Y, 1, -y * X, -y * Y]]
        B += [x, y]
    co = np.linalg.solve(np.array(A, float), np.array(B, float))
    return im.transform((w, h), Image.PERSPECTIVE, tuple(co), Image.BICUBIC)


def smear(im, amount):
    """Cheap horizontal motion blur: squeeze and stretch back."""
    if amount <= 1.02:
        return im
    w, h = im.size
    return im.resize((max(int(w / amount), 2), h), Image.BOX).resize((w, h), Image.BILINEAR)


def with_shadow(layer):
    a = layer.getchannel('A')
    far = ImageChops.offset(a.filter(ImageFilter.GaussianBlur(16)), 8, 12).point(lambda v: int(v * 0.55))
    near = ImageChops.offset(a.filter(ImageFilter.GaussianBlur(4)), 3, 4).point(lambda v: int(v * 0.60))
    out = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    out.putalpha(ImageChops.lighter(far, near))
    out.alpha_composite(layer)
    return out


def draw_event(fr, ev, t):
    if not (ev['start'] <= t <= ev['end'] + OUT_T):
        return
    alpha = Image.new('L', (W, ev['_h']), 0)
    for ln in ev['_lines']:
        for (gx, sharp, soft, softer), lt in zip(ln['glyphs'], ln['times']):
            if t < lt:
                continue
            k = min((t - lt) / L_FADE, 1)
            e = 1 - (1 - k) ** 3
            spr = sharp if k >= 1 else (soft if k > 0.5 else softer)
            if e < 0.999:
                spr = spr.point(lambda v, e=e: int(v * e))
            alpha.paste(255, (int(ln['x'] + gx - PAD - 26 * (1 - e)), int(ln['y'] - PAD)), spr)
    k_out = min(max((t - ev['end']) / OUT_T, 0), 1)
    if k_out > 0:
        alpha = smear(alpha, 1 + 30 * k_out)
        alpha = ImageChops.offset(alpha, -int(150 * k_out), 0).point(lambda v: int(v * (1 - k_out) ** 1.5))
    layer = ev['_rgb'].copy()
    layer.putalpha(alpha)
    life = (t - ev['start']) / max(ev['end'] - ev['start'], 0.1)
    layer = persp(layer, ev.get('tilt', 0.05), ev.get('roll', 1.2), 1 + 0.035 * min(life, 1.2))
    fr.alpha_composite(with_shadow(layer), (0, int(ev.get('y', 350) - PAD)))


def prepare_verdict(v):
    size = fit('heavy', v['t'], v.get('size', 250))
    f = font('heavy', size)
    b = f.getbbox(v['t'])
    im = Image.new('L', (W, b[3] + PAD * 3), 0)
    ImageDraw.Draw(im).text(((W - f.getlength(v['t'])) / 2, PAD), v['t'], font=f, fill=255)
    r, g, bl = TINT[v.get('kind', 'plain')]
    xs = np.linspace(0, 1, W)
    sheen = 0.82 + 0.18 * np.exp(-((xs - 0.5) / 0.30) ** 2)
    rows = np.ones(im.size[1])
    rgb = Image.merge('RGB', [Image.fromarray(np.clip(np.outer(rows, sheen) * c, 0, 255).astype(np.uint8))
                              for c in (r, g, bl)])
    v['_rgb'], v['_a'] = rgb, im


def draw_verdict(fr, v, t):
    IN_T, OUT_V = 0.20, 0.30
    if not (v['at'] <= t <= v['end'] + OUT_V):
        return
    k = min((t - v['at']) / IN_T, 1)
    e = 1 - (1 - k) ** 3
    k_out = min(max((t - v['end']) / OUT_V, 0), 1)
    a = v['_a']
    if k < 1:
        a = a.filter(ImageFilter.GaussianBlur(22 * (1 - e)))
    a = a.point(lambda x: int(x * e * (1 - k_out) ** 1.3))
    layer = v['_rgb'].copy()
    layer.putalpha(a)
    scale = (1.45 - 0.45 * e) * (1 - 0.42 * k_out)                 # lands from the camera, leaves into depth
    layer = persp(layer, v.get('tilt', 0.16), v.get('roll', -4.0), scale)
    fr.alpha_composite(with_shadow(layer), (0, int(v.get('y', 430) - PAD - 60 * k_out)))


def draw_sub(fr, s, t):
    if not (s['start'] <= t <= s['end']):
        return
    f = font('sub', s.get('size', SIZE['sub']))
    a = min((t - s['start']) / 0.25, (s['end'] - t) / 0.25, 1)
    im = Image.new('RGBA', (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = (W - f.getlength(s['t'])) / 2
    d.text((x + 2, 42), s['t'], font=f, fill=(0, 0, 0, 150))
    im = im.filter(ImageFilter.GaussianBlur(4))
    ImageDraw.Draw(im).text((x, 40), s['t'], font=f, fill=(255, 255, 255, 235))
    if a < 1:
        im.putalpha(im.getchannel('A').point(lambda v: int(v * max(a, 0))))
    fr.alpha_composite(im, (0, int(s.get('y', 1540))))


for ev in spec.get('events', []):
    prepare(ev)
for v in spec.get('verdicts', []):
    prepare_verdict(v)


_g = np.clip(1 - np.arange(H) / (0.52 * H), 0, 1) ** 1.3 * 255 * spec.get('shade', 0.0)   # darker "sky" under the titles
SHADE = Image.new('RGBA', (W, H), (0, 8, 20, 0))
SHADE.putalpha(Image.fromarray(np.repeat(_g[:, None], W, 1).astype(np.uint8)))


def frame(t):
    fr = SHADE.copy()
    for fl in spec.get('flashes', []):                             # white flash across a cut
        d = t - fl
        if -0.07 <= d <= 0.20:
            k = 1 - abs(d) / (0.07 if d < 0 else 0.20)
            fr.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(215 * k))))
    for ev in spec.get('events', []):
        draw_event(fr, ev, t)
    for v in spec.get('verdicts', []):
        draw_verdict(fr, v, t)
    for s in spec.get('subs', []):
        draw_sub(fr, s, t)
    return fr


if OUT.lower().endswith('.png'):                                   # one frame for a look: out.png, time in argv[4]
    t = float(sys.argv[4])
    subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-ss', str(t), '-i', BASE, '-frames:v', '1',
                    '-vf', f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}', OUT + '.base.png'])
    bg = Image.open(OUT + '.base.png').convert('RGBA')
    bg.alpha_composite(frame(t))
    bg.convert('RGB').save(OUT)
    sys.exit()

dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', BASE],
                           capture_output=True, text=True).stdout.strip())
n = int(dur * FPS)
cmd = ['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-i', BASE,
       '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
       '-filter_complex', f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}[b];[b][1:v]overlay=0:0:shortest=1[v]',
       '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
       '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for i in range(n):
    p.stdin.write(frame(i / FPS).tobytes())
p.stdin.close()
p.wait()
print('built', OUT, f'{n} frames')
