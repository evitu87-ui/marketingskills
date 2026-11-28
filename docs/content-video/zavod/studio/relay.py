"""Put a local file on the private n8n relay for 10 minutes. Usage: relay.py file [file ...]  -> prints one URL per file"""
import base64, json, mimetypes, os, secrets, subprocess, sys
KEY = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key.txt')).read().strip()
BASE = 'https://service.aida-oceana.com/webhook/'
for path in sys.argv[1:]:
    name = os.path.basename(path); tok = secrets.token_hex(16)
    body = {'key': KEY, 'token': tok, 'name': name, 'mime': mimetypes.guess_type(name)[0] or 'application/octet-stream',
            'b64': base64.b64encode(open(path, 'rb').read()).decode()}
    json.dump(body, open('_relay_req.json', 'w'))
    r = subprocess.run(['curl', '-sS', '-m', '120', '-X', 'POST', '-H', 'Content-Type: application/json', '--data-binary', '@_relay_req.json',
                        BASE + 'zavod-relay-put'], capture_output=True, text=True)
    os.remove('_relay_req.json')
    print(name, r.stdout[:120], BASE + 'zavod-relay-get?t=' + tok + '&f=' + name)
