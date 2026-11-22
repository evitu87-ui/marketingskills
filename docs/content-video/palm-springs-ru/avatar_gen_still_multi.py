"""Avatar still from several reference photos. Usage: gen_still2.py name "scene prompt" ref1.jpg [ref2.jpg ...]"""
import base64, json, subprocess, sys
name, prompt, refs = sys.argv[1], sys.argv[2], sys.argv[3:]
ID = ("The reference photos all show the same man. Use him as the subject and keep his identity exactly: same shaved bald head, "
      "same face shape, same dark eyebrows and eyes, same short dark stubble, same age and build. "
      "Photorealistic photograph, not an illustration. Vertical 9:16 frame, full-frame camera, 35mm lens at f/1.8, "
      "natural skin texture, no text, no watermark. ")
body = {"key": open('key.txt').read().strip(), "model": "gemini-3-pro-image", "aspect": "9:16", "size": "2K",
        "prompt": ID + prompt,
        "images": [{"mime": "image/jpeg", "b64": base64.b64encode(open(r, 'rb').read()).decode()} for r in refs]}
json.dump(body, open(f'req_{name}.json', 'w'))
r = subprocess.run(['curl', '-sS', '-m', '300', '-X', 'POST', '-H', 'Content-Type: application/json', '--data-binary',
                    f'@req_{name}.json', '-o', f'resp_{name}.json', '-w', '%{http_code}',
                    'https://service.aida-oceana.com/webhook/avatar-image'], capture_output=True, text=True)
print(name, 'HTTP', r.stdout, r.stderr[:200])
try:
    d = json.load(open(f'resp_{name}.json'))
    if isinstance(d, list): d = d[0]
    for p in d['candidates'][0]['content']['parts']:
        if 'inlineData' in p:
            open(f'{name}.jpg', 'wb').write(base64.b64decode(p['inlineData']['data'])); print('saved', f'{name}.jpg')
        elif 'text' in p:
            print('text:', p['text'][:200])
except Exception as e:
    print('ERR', e, open(f'resp_{name}.json').read()[:600])
