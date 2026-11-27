"""New fashion look for a host: studio reference shots. Usage: gen_look.py name "shot" """
import base64, json, subprocess, sys
name, shot = sys.argv[1], sys.argv[2]
H = '/home/user/marketingskills/docs/content-video/assets/hosts/'
refs = [H + 'host_E_face.jpg']
LOOK = ("Use the woman in the reference photo as the subject and keep her identity exactly: same face, same eyes, same skin "
        "tone and age, same dark brown hair, now worn loose: long, sleek, glossy and straight with a middle parting. New "
        "outfit, high-fashion and elegant: an ivory-white double-breasted tailored blazer dress with gold buttons, "
        "mid-thigh length, softly fitted at the waist, bare legs, ivory pointed-toe stiletto high heels, small gold hoop "
        "earrings and a thin gold bracelet. Slim graceful silhouette, confident model posture, shoulders back. "
        "Photorealistic fashion editorial photograph, not an illustration. Vertical 9:16 frame, soft even studio light, "
        "plain light-grey seamless background, natural skin texture, no text, no watermark. ")
body = {"key": open('key.txt').read().strip(), "model": "gemini-3-pro-image", "aspect": "9:16", "size": "2K",
        "prompt": LOOK + shot,
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
