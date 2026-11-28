"""Assemble the studio episode: python3 build_ep.py ru"""
import json, subprocess, sys
lang = sys.argv[1]
S = '/tmp/claude-0/-home-user-marketingskills/367d5ad3-be96-5896-9cf1-da760ede2d29/scratchpad'
R = '/home/user/marketingskills/docs/content-video/zavod'
VF = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,setsar=1,unsharp=5:5:0.5'
titles = json.load(open(f'titles_{lang}.json', encoding='utf-8'))
clips, t0, events = [], 0.0, []
for c in titles:
    n = c['n']; name = f'{lang}_{n:02d}'
    w = json.load(open(name + '.words.json'))
    a = max(0.0, w[0][1] - 0.30) if w[0][1] > 0.5 else 0.0
    b = min(float(c['dur']), w[-1][2] + 0.42)
    d = round(b - a, 3)
    out = f'c_{name}.mp4'
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{a:.3f}', '-i', name + '.mp4', '-ss', f'{a:.3f}', '-i', f'v_{name}.mp3',
                    '-t', f'{d:.3f}', '-map', '0:v', '-map', '1:a', '-vf', VF, '-af', f'aresample=48000,afade=t=in:d=0.03,afade=t=out:st={d-0.06:.3f}:d=0.06',
                    '-ac', '2', '-c:v', 'libx264', '-crf', '15', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', out], check=True)
    clips.append(out)
    def at(key):                       # time of a word (by prefix) on the episode timeline
        if isinstance(key, (int, float)): return round(t0 + key - a, 2)
        for x in w:
            if x[0].lower().strip('.,?!—-').startswith(key.lower()): return round(t0 + x[1] - a, 2)
        raise SystemExit(f'word {key} not found in {name}: {[x[0] for x in w]}')
    for ev in c['events']:
        s = at(ev['from']) if 'from' in ev else t0 + 0.12
        e = at(ev['to']) - 0.12 if 'to' in ev else t0 + d - 0.30
        items = [dict(it, at=max(s, at(it['at'])) if 'at' in it else s) for it in ev['items']]
        events.append({'start': round(s, 2), 'end': round(e, 2), 'x': ev.get('x', 110), 'maxw': ev.get('maxw', 0.78), 'y': ev.get('y', 'auto'), 'items': items})
    t0 += d
open(f'cat_{lang}.txt', 'w').write(''.join(f"file '{c}'\n" for c in clips))
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'cat_{lang}.txt', '-c', 'copy', f'cat_{lang}.mp4'], check=True)
m = subprocess.run(['ffmpeg', '-nostdin', '-i', f'cat_{lang}.mp4', '-af', 'volumedetect', '-vn', '-f', 'null', '-'], capture_output=True, text=True).stderr
mean = float(m.split('mean_volume:')[1].split('dB')[0])
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', f'cat_{lang}.mp4', '-c:v', 'copy', '-af', f'volume={-19.0 - mean:.1f}dB,alimiter=limit=0.84',
                '-c:a', 'aac', '-b:a', '192k', f'base_{lang}.mp4'], check=True)
json.dump({'fps': 30, 'events': events}, open(f'spec_{lang}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('base', round(t0, 2), 's, mean', mean, 'dB, events', len(events))
