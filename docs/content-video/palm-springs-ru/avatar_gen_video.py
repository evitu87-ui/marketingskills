"""Animate a still with Gemini Omni via the n8n webhook. Usage: gen_video.py name still.jpg "prompt" [duration]"""
import base64, io, json, subprocess, sys
from PIL import Image
name, still, prompt = sys.argv[1], sys.argv[2], sys.argv[3]
dur = sys.argv[4] if len(sys.argv) > 4 else '8s'
im = Image.open(still).convert('RGB'); im.thumbnail((1080, 1920))
buf = io.BytesIO(); im.save(buf, 'JPEG', quality=90)
body = {"key": open('key.txt').read().strip(), "aspect": "9:16", "duration": dur, "resolution": "720p",
        "images": [{"mime": "image/jpeg", "b64": base64.b64encode(buf.getvalue()).decode()}], "prompt": prompt}
json.dump(body, open(f'vreq_{name}.json', 'w'))
r = subprocess.run(['curl', '-sS', '-m', '900', '-X', 'POST', '-H', 'Content-Type: application/json', '--data-binary',
                    f'@vreq_{name}.json', '-o', f'vresp_{name}.json', '-w', '%{http_code} %{time_total}s',
                    'https://service.aida-oceana.com/webhook/avatar-video'], capture_output=True, text=True)
print(name, 'HTTP', r.stdout, r.stderr[:200])
try:
    d = json.load(open(f'vresp_{name}.json'))
    if isinstance(d, list): d = d[0]
    got = False
    for s in d.get('steps', []):
        for c in s.get('content', []) or []:
            if c.get('type') == 'video' and c.get('data'):
                open(f'{name}.mp4', 'wb').write(base64.b64decode(c['data'])); got = True
                print('saved', f'{name}.mp4', 'status', d.get('status'), 'usage', d.get('usage'))
            elif c.get('type') == 'video':
                print('video by uri:', c.get('uri'))
    if not got:
        print('NO VIDEO', json.dumps(d, ensure_ascii=False)[:900])
except Exception as e:
    print('ERR', e, open(f'vresp_{name}.json').read()[:700])
