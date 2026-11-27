"""Studio still. Usage: gen.py name "prompt" ref1 [ref2 ...]"""
import base64, json, subprocess, sys
name, prompt, refs = sys.argv[1], sys.argv[2], sys.argv[3:]
body = {"key": open('key.txt').read().strip(), "model": "gemini-3-pro-image", "aspect": "9:16", "size": "2K", "prompt": prompt,
        "images": [{"mime": "image/jpeg", "b64": base64.b64encode(open(r, 'rb').read()).decode()} for r in refs]}
json.dump(body, open(f'req_{name}.json', 'w'))
r = subprocess.run(['curl', '-sS', '-m', '300', '-X', 'POST', '-H', 'Content-Type: application/json', '--data-binary',
                    f'@req_{name}.json', '-o', f'resp_{name}.json', '-w', '%{http_code}',
                    'https://service.aida-oceana.com/webhook/avatar-image'], capture_output=True, text=True)
try:
    d = json.load(open(f'resp_{name}.json'))
    if isinstance(d, list): d = d[0]
    for p in d['candidates'][0]['content']['parts']:
        if 'inlineData' in p:
            open(f'{name}.png', 'wb').write(base64.b64decode(p['inlineData']['data'])); print('saved', name)
except Exception as e:
    print('ERR', name, r.stdout, e, open(f'resp_{name}.json').read()[:300])
