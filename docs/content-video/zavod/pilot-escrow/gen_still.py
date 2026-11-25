"""Scene still with a host identity pack. Usage: gen_still.py name "scene prompt" """
import base64, json, subprocess, sys
name, shot = sys.argv[1], sys.argv[2]
H = '/home/user/marketingskills/docs/content-video/assets/hosts/'
refs = [H + 'host_E_face.jpg', H + 'host_E_three.jpg', H + 'host_E_full.jpg']
ID = ("Use the woman in the reference photos as the subject and keep her identity exactly: same face, same eyes, same dark "
      "brown hair in a sleek low ponytail, same skin tone and age, same white tailored suit. Photorealistic photograph, "
      "not an illustration, shot on a full-frame camera with a 35mm lens, shallow depth of field, cinematic natural light, "
      "natural skin texture. Vertical 9:16 frame. Composition rule: low camera angle, wide 24mm lens; her head is at about 45 percent of "
      "the frame height and the whole upper 40 percent of the frame is calm uncluttered background with nothing important in it. No readable text, no letters, no logos, no watermark anywhere in the image. ")
body = {"key": open('key.txt').read().strip(), "model": "gemini-3-pro-image", "aspect": "9:16", "size": "2K",
        "prompt": ID + shot,
        "images": [{"mime": "image/jpeg", "b64": base64.b64encode(open(p, 'rb').read()).decode()} for p in refs]}
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
