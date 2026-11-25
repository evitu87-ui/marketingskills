"""Kinetic titles in the reference style: words pop in one by one with a motion smear,
key words in heavy italic, the rest in a thin weight. Composites straight onto a video.

Usage: python3 titles.py base.mp4 spec.json out.mp4

spec.json:
{"fps": 30, "events": [
  {"start": 0.2, "end": 3.4, "y": 300,
   "lines": [[{"t": "Можно", "w": "heavy", "at": 0.25}, {"t": "ли найти", "w": "light", "at": 0.6}],
             [{"t": "в Дубае", "w": "heavy", "at": 1.0}]]}
]}
"at" is the time a word appears (seconds from the start of the video). "w": heavy | light.
"""
import json, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE, SPEC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920
FONTS = {'heavy': ('/usr/share/fonts/opentype/inter/Inter-ExtraBoldItalic.otf', 104),
         'light': ('/usr/share/fonts/opentype/inter/Inter-Light.otf', 64)}
IN, OUT_T, SMEAR, LEAD = 0.20, 0.16, 70, 1.02      # pop-in s, exit s, smear px, line spacing
spec = json.load(open(SPEC, encoding='utf-8'))
FPS = spec.get('fps', 30)
font = {k: ImageFont.truetype(p, s) for k, (p, s) in FONTS.items()}


def layout(ev):
    """Place every word of an event; returns [(word, x, y)] with lines centred."""
    out, y = [], ev.get('y', 300)
    for line in ev['lines']:
        sizes = [font[w['w']].getbbox(w['t']) for w in line]
        widths = [b[2] - b[0] for b in sizes]
        gap = 22
        total = sum(widths) + gap * (len(line) - 1)
        asc = max(font[w['w']].getmetrics()[0] for w in line)
        x = (W - total) // 2
        for w, wd in zip(line, widths):
            f = font[w['w']]
            out.append((w, x, y + asc - f.getmetrics()[0]))
            x += wd + gap
        y += int(max(f.size for f in (font[w['w']] for w in line)) * LEAD)
    return out


for ev in spec['events']:
    ev['_words'] = layout(ev)


def word_sprite(w):
    f = font[w['w']]
    b = f.getbbox(w['t'])
    pad = 30
    im = Image.new('RGBA', (b[2] - b[0] + pad * 2, b[3] + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - b[0], pad), w['t'], font=f, fill=(0, 0, 0, 150))
    im = im.filter(ImageFilter.GaussianBlur(7))                       # soft shadow
    ImageDraw.Draw(im).text((pad - b[0], pad - 3), w['t'], font=f, fill=(255, 255, 255, 255))
    return im, pad


SPR = {}
for ev in spec['events']:
    for w, x, y in ev['_words']:
        SPR[id(w)] = word_sprite(w)


def fade(im, a):
    if a >= 0.999:
        return im
    al = im.getchannel('A').point(lambda v: int(v * a))
    im = im.copy(); im.putalpha(al)
    return im


def frame(t):
    fr = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for ev in spec['events']:
        if not (ev['start'] <= t <= ev['end'] + OUT_T):
            continue
        k_out = min(max((t - ev['end']) / OUT_T, 0), 1)             # 0..1 while leaving
        for w, x, y in ev['_words']:
            if t < w['at']:
                continue
            k = min((t - w['at']) / IN, 1)                             # 0..1 while arriving
            ease = 1 - (1 - k) ** 3
            spr, pad = SPR[id(w)]
            dx = -SMEAR * (1 - ease) + SMEAR * 1.4 * k_out
            a = ease * (1 - k_out)
            steps = 1 if (k >= 1 and k_out == 0) else 7                # smear = several faint copies
            for s in range(steps):
                off = dx - (SMEAR * 0.5 * (1 - ease) + SMEAR * 0.6 * k_out) * s / steps
                layer = fade(spr, a / steps if steps > 1 else a)
                fr.alpha_composite(layer, (int(x - pad + off), int(y - pad)))
    return fr


dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', BASE],
                           capture_output=True, text=True).stdout.strip())
n = int(dur * FPS)
cmd = ['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-i', BASE,
       '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
       '-filter_complex', f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}[b];[b][1:v]overlay=0:0:shortest=1[v]',
       '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
       '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
empty = Image.new('RGBA', (W, H), (0, 0, 0, 0)).tobytes()
for i in range(n):
    t = i / FPS
    active = any(ev['start'] <= t <= ev['end'] + OUT_T for ev in spec['events'])
    p.stdin.write(frame(t).tobytes() if active else empty)
p.stdin.close()
p.wait()
print('built', OUT, f'{n} frames')
