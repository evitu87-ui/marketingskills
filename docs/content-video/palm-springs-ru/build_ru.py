"""Assemble Palm Springs RU: place TTS lines on the original timing, overlay cover panel + captions."""
import json, re, subprocess, sys

S = json.load(open('ps_script.json'))
VID = 'reel/reel.mp4'
DUR = 114.546
CUT = 107.5   # author's DM mock-up + Phoenix logo start right after this
FINAL = 111.0
GAP = 0.10
MAX_TEMPO = 1.15
OUT = sys.argv[1] if len(sys.argv) > 1 else 'out/palm_springs_ru.mp4'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:])
        raise SystemExit(1)
    return r


def dur(path):
    out = run(['ffmpeg', '-hide_banner', '-i', path, '-f', 'null', '-']).stderr
    t = re.findall(r'time=(\d+):(\d+):([\d.]+)', out)[-1]
    return int(t[0]) * 3600 + int(t[1]) * 60 + float(t[2])


trim = ('silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,'
        'areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse')
plan = []
prev_end = 0.0
for i, l in enumerate(S):
    src = f"tts/{l['id']}.wav"
    tr = f"tts/{l['id']}_trim.wav"
    run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-af', trim, tr])
    d = dur(tr)
    start = max(l['start'], prev_end + GAP)
    nxt = S[i + 1]['start'] if i + 1 < len(S) else FINAL - 0.6
    room = nxt - GAP - start
    tempo = 1.0
    if d > room:
        tempo = min(d / room, MAX_TEMPO)
    d2 = d / tempo
    end = start + d2
    plan.append(dict(id=l['id'], start=round(start, 3), end=round(end, 3), tempo=round(tempo, 3),
                     drift=round(start - l['start'], 2), src=tr))
    prev_end = end

for p in plan:
    print(f"{p['id']} {p['start']:7.2f}-{p['end']:7.2f} tempo {p['tempo']:.3f} drift {p['drift']:+.2f}")
json.dump(plan, open('ru_plan.json', 'w'), indent=1)

# --- audio: delay each line, mix, loudness-normalise
inputs, fl = [], []
for k, p in enumerate(plan):
    inputs += ['-i', p['src']]
    chain = f"[{k}:a]aresample=48000"
    if p['tempo'] > 1.0:
        chain += f",atempo={p['tempo']}"
    ms = int(p['start'] * 1000)
    chain += f",adelay={ms}|{ms}[a{k}]"
    fl.append(chain)
mix = ''.join(f'[a{k}]' for k in range(len(plan)))
fl.append(f"{mix}amix=inputs={len(plan)}:normalize=0:dropout_transition=0,apad,atrim=0:{FINAL},afade=t=out:st={FINAL-0.7}:d=0.7,"
          "loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo[out]")
run(['ffmpeg', '-loglevel', 'error', '-y', *inputs, '-filter_complex', ';'.join(fl), '-map', '[out]',
     '-ar', '48000', 'out/ru_voice.wav'])

# --- video: panel always on, caption per line
vin = ['-i', VID, '-loop', '1', '-i', 'caps/panel.png']
vf = [f'[0:v]trim=0:{CUT},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={FINAL-CUT}[base]', '[base][1:v]overlay=0:0:shortest=1[v0]']
for k, p in enumerate(plan):
    vin += ['-loop', '1', '-i', f"caps/{p['id']}.png"]
    on = max(p['start'] - 0.05, 0)
    off = p['end'] + 0.25
    if k + 1 < len(plan):
        off = min(off, plan[k + 1]['start'] - 0.06)
    vf.append(f"[v{k}][{k + 2}:v]overlay=0:0:shortest=1:enable='between(t,{on:.3f},{off:.3f})'[v{k + 1}]")
vf.append(f"[v{len(plan)}]fade=t=out:st={FINAL-0.7}:d=0.7[vend]")
last = 'vend'
vin += ['-i', 'out/ru_voice.wav']
run(['ffmpeg', '-loglevel', 'error', '-y', *vin, '-filter_complex', ';'.join(vf),
     '-map', f'[{last}]', '-map', f'{len(plan) + 2}:a', '-t', str(FINAL),
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
     '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT])
print('built', OUT)
