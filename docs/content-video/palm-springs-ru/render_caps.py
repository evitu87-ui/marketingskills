"""Render the cover panel and per-line Russian caption PNGs (1080x1920, transparent)."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
X0, Y0, X1, Y1 = 90, 1368, 990, 1562  # covers presenter plate (x232-848, y1390-1558)
FONT = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
OUT = sys.argv[1]
script = json.load(open(sys.argv[2]))
os.makedirs(OUT, exist_ok=True)

# Base panel: deep navy glass, soft shadow, hairline border.
panel = Image.new('RGBA', (W, H), (0, 0, 0, 0))
sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((X0 + 6, Y0 + 10, X1 + 6, Y1 + 12), radius=40, fill=(0, 0, 0, 110))
sh = sh.filter(ImageFilter.GaussianBlur(14))
panel.alpha_composite(sh)
d = ImageDraw.Draw(panel)
d.rounded_rectangle((X0, Y0, X1, Y1), radius=40, fill=(11, 18, 40, 255), outline=(255, 255, 255, 34), width=2)
# thin accent line (Nakheel-ish blue, neutral, no branding)
d.rounded_rectangle((X0 + 40, Y0 + 14, X0 + 120, Y0 + 18), radius=2, fill=(86, 140, 255, 200))
panel.save(os.path.join(OUT, 'panel.png'))

for line in script:
    rows = line['sub']
    size = 40 if len(rows) <= 2 else 36
    f = ImageFont.truetype(FONT, size)
    # shrink if any row is too wide
    while max(f.getlength(r) for r in rows) > (X1 - X0 - 70) and size > 28:
        size -= 2
        f = ImageFont.truetype(FONT, size)
    lh = int(size * 1.28)
    total = lh * len(rows)
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cy = (Y0 + Y1) / 2 + 4
    y = cy - total / 2
    for r in rows:
        w = f.getlength(r)
        dr.text(((W - w) / 2, y), r, font=f, fill=(255, 255, 255, 255))
        y += lh
    img.save(os.path.join(OUT, f"{line['id']}.png"))
print('ok', len(script))
