import base64, json, subprocess, sys
name, prompt = sys.argv[1], sys.argv[2]
ID = ("Use the man in the reference photo as the subject and keep his identity exactly: same bald head, same face shape, "
      "same dark rectangular glasses, same short grey stubble, same age. Photorealistic photograph, not an illustration. "
      "Vertical 9:16 frame, shot on a full-frame camera with a 35mm lens at f/1.8, natural skin texture, no text, no watermark. ")
body = {"key": open('key.txt').read().strip(), "model": "gemini-3-pro-image", "aspect": "9:16", "size": "2K",
        "prompt": ID + prompt,
        "images": [{"mime": "image/jpeg", "b64": base64.b64encode(open('ref.jpg', 'rb').read()).decode()}]}
json.dump(body, open(f'req_{name}.json', 'w'))
r = subprocess.run(['curl', '-sS', '-m', '300', '-X', 'POST', '-H', 'Content-Type: application/json', '--data-binary',
                    f'@req_{name}.json', '-o', f'resp_{name}.json', '-w', '%{http_code}',
                    'https://service.aida-oceana.com/webhook/avatar-image'], capture_output=True, text=True)
print(name, 'HTTP', r.stdout, r.stderr[:200])
try:
    d = json.load(open(f'resp_{name}.json'))
    if isinstance(d, list): d = d[0]
    parts = d['candidates'][0]['content']['parts']
    for p in parts:
        if 'inlineData' in p:
            ext = 'png' if 'png' in p['inlineData'].get('mimeType', '') else 'jpg'
            open(f'{name}.{ext}', 'wb').write(base64.b64decode(p['inlineData']['data']))
            print('saved', f'{name}.{ext}', d.get('usageMetadata', {}).get('totalTokenCount'))
        elif 'text' in p:
            print('text:', p['text'][:200])
except Exception as e:
    print('ERR', e, open(f'resp_{name}.json').read()[:600])
