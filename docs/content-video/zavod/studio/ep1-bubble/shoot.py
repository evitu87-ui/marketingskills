import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
lang, src = sys.argv[1], sys.argv[2]
only = set(int(x) for x in sys.argv[3].split(',')) if len(sys.argv) > 3 else None
L = 'Russian' if lang == 'ru' else 'English'
TAIL = ' Static camera on a tripod, same framing, bright meeting room in daylight. No music, no subtitles, no captions, no text on screen.'
def prompt(l):
    q = '«' + l['t'] + '»'
    pace = ' Steady, slightly brisk pace so that the whole line is spoken before the clip ends.' if l['dur'] == '8s' else ' Natural pace.'
    if l['who'] == 'host':
        return f'She speaks into the microphone looking at the camera, in {L}, with natural accurate lip movement, saying exactly this line: {q} Warm, calm, confident female voice.{pace} Small natural head movement, hands stay on the table, then she listens with a slight smile.' + TAIL
    if l['who'] == 'vit':
        return f'He speaks into the microphone looking at the camera, in {L}, with natural accurate lip movement, saying exactly this line: {q} Calm, low, confident male voice.{pace} A small restrained hand gesture near the table. He keeps his black glasses on the whole time.' + TAIL
    return f'The man on the right speaks in {L} toward the woman and the camera, with natural accurate lip movement, saying exactly this line: {q} Calm, low, confident male voice.{pace} He keeps his black glasses on. The woman on the left stays silent with her lips closed, listens and nods slightly.' + TAIL
lines = [l for l in json.load(open(src)) if not only or l['n'] in only]
def run(l):
    name = f"{lang}_{l['n']:02d}"
    r = subprocess.run(['/usr/bin/python3', 'gen_video.py', name, l['still'] + '.png', prompt(l), l['dur']], capture_output=True, text=True)
    return name + ': ' + ' | '.join(x[:110] for x in r.stdout.strip().splitlines())
with ThreadPoolExecutor(3) as ex:
    for o in ex.map(run, lines): print(o, flush=True)
