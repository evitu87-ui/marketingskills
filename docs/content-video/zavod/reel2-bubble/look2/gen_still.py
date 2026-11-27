"""Scene still, host G, fashion look 2. Usage: gen_still.py name "scene prompt" """
import base64, json, subprocess, sys
name, shot = sys.argv[1], sys.argv[2]
H = '/home/user/marketingskills/docs/content-video/assets/hosts/'
refs = [H + 'host_G_face.jpg', 'look_three.jpg', 'look_full.jpg']
ID = ("Use the woman in the reference photos as the subject and keep her identity and styling exactly: same face, same eyes, "
      "same skin tone and age, same long light blonde hair in soft glossy waves, same sand-beige double-breasted blazer dress "
      "with a thin belt, bare legs, same nude pointed-toe stiletto high heels, delicate gold necklace. She moves and stands "
      "like a fashion model: graceful, feminine, shoulders back, long elegant lines, relaxed hands. Photorealistic fashion "
      "editorial photograph, not an illustration, shot on a full-frame camera with a 24mm lens from a low camera angle, "
      "shallow depth of field, cinematic natural light, natural skin texture. Vertical 9:16 frame. Composition rule: a wide shot "
      "where she appears smaller: her whole figure from head to heels fits inside the lower 60 percent of the frame, the top "
      "of her head is at 40 percent of the frame height, and the whole upper 40 percent of the frame is calm uncluttered "
      "background with nothing important in it. No readable text, no letters, no logos, no watermark anywhere in the image. ")
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
