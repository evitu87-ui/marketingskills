"""Voice-led build: the presenter's own recording sets the pace, the video follows.
Each group = slice of the source video + a continuous slice of the recording.
If the voice is longer than the video slice, the slice is slowed (max MAX_SLOW) and then
its last frame is held. Captions switch per line inside a group.
Usage: python3 build_vit.py out.mp4   (PLAN_ONLY=1 to print the plan only)
"""
import json, os, subprocess, sys

D = json.load(open('vit_script.json'))
VID, REC = 'reel/reel.mp4', 'vit/clean.wav'
LEAD, TAIL, MAX_SLOW, END_HOLD = 0.12, 0.35, 1.5, 1.4
OUT = sys.argv[1] if len(sys.argv) > 1 else 'out/palm_springs_ru_vitaly.mp4'
V = D['voice']


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:])
        raise SystemExit(1)


plan, t = [], 0.0
for gi, g in enumerate(D['groups']):
    va, vb = g['video']
    vdur = vb - va
    ra, rb = V[g['lines'][0]][0], V[g['lines'][-1]][1]
    lead = g.get('lead', LEAD)
    last = gi == len(D['groups']) - 1
    need = lead + (rb - ra) + (END_HOLD if last else TAIL)
    T = max(vdur, need)
    slow = 1.0
    if vdur > 0 and T > vdur:
        slow = min(T / vdur, MAX_SLOW)
    hold = T - vdur * slow
    caps = [(lid, t + lead + (V[lid][0] - ra), t + lead + (V[lid][1] - ra)) for lid in g['lines']]
    plan.append(dict(i=gi, video=(va, vb), slow=round(slow, 3), hold=round(hold, 3), out=(round(t, 3), round(t + T, 3)),
                     rec=(ra, rb), voice_at=round(t + lead, 3), caps=caps))
    t += T
TOTAL = t
for p in plan:
    print(f"G{p['i']:02d} {'+'.join(c[0] for c in p['caps']):14s} video {p['video'][0]:6.2f}-{p['video'][1]:6.2f} "
          f"slow x{p['slow']:.2f} hold {p['hold']:4.2f}s  out {p['out'][0]:6.2f}-{p['out'][1]:6.2f}")
print(f'TOTAL {TOTAL:.2f}s')
json.dump(plan, open('vit_plan.json', 'w'), indent=1)
if os.environ.get('PLAN_ONLY'):
    raise SystemExit(0)

# --- audio: cut each group's slice of the cleaned recording, delay to its output time
ain, af = [], []
for k, p in enumerate(plan):
    ra, rb = p['rec']
    ain += ['-i', REC]
    ms = int(p['voice_at'] * 1000)
    af.append(f"[{k}:a]atrim={max(ra - 0.05, 0):.3f}:{rb + 0.15:.3f},asetpts=PTS-STARTPTS,"
              f"afade=t=in:d=0.02,areverse,afade=t=in:d=0.04,areverse,adelay={ms}|{ms}[a{k}]")
mix = ''.join(f'[a{k}]' for k in range(len(plan)))
af.append(f"{mix}amix=inputs={len(plan)}:normalize=0,apad,atrim=0:{TOTAL:.3f},"
          f"afade=t=out:st={TOTAL - 0.8:.3f}:d=0.8,loudnorm=I=-16:TP=-1.5:LRA=9,aformat=channel_layouts=stereo[aout]")
run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', *ain, '-filter_complex', ';'.join(af), '-map', '[aout]',
     '-ar', '48000', 'out/vit_voice.wav'])

# --- video pass 1: each group rendered on its own (avoids buffering the whole source in RAM)
os.makedirs('vseg', exist_ok=True)
lst = []
for k, p in enumerate(plan):
    va, vb = p['video']
    T = p['out'][1] - p['out'][0]
    seg = f'vseg/g{k:02d}.mp4'
    if vb - va < 0.02:
        run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-ss', f'{va - 0.05:.3f}', '-i', VID, '-frames:v', '1',
             'vseg/freeze.png'])
        run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-loop', '1', '-framerate', '60', '-i', 'vseg/freeze.png',
             '-t', f'{T:.3f}', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', seg])
    else:
        vfx = f"setpts=(PTS-STARTPTS)*{p['slow']},fps=60"
        if p['hold'] > 0.01:
            vfx += f",tpad=stop_mode=clone:stop_duration={p['hold']:.3f}"
        vfx += f",trim=duration={T:.3f}"
        run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-ss', f'{va:.3f}', '-to', f'{vb:.3f}', '-i', VID,
             '-an', '-vf', vfx, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', seg])
    lst.append(f"file '{os.path.basename(seg)}'")
open('vseg/list.txt', 'w').write('\n'.join(lst) + '\n')
run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'vseg/list.txt', '-c', 'copy',
     'vseg/base.mp4'])
print('base ready')
vf = []
vin = ['-i', 'vseg/base.mp4', '-loop', '1', '-i', 'caps_vit/panel.png']
vf.append('[0:v][1:v]overlay=0:0:shortest=1[c0]')
caps = [c for p in plan for c in p['caps']]
for k, (lid, a, b) in enumerate(caps):
    vin += ['-loop', '1', '-i', f'caps_vit/{lid}.png']
    on = max(a - 0.08, 0)
    off = b + 0.3
    if k + 1 < len(caps):
        off = min(off, caps[k + 1][1] - 0.1)
    vf.append(f"[c{k}][{k + 2}:v]overlay=0:0:shortest=1:enable='between(t,{on:.3f},{off:.3f})'[c{k + 1}]")
vf.append(f"[c{len(caps)}]fade=t=out:st={TOTAL - 0.8:.3f}:d=0.8[vout]")
vin += ['-i', 'out/vit_voice.wav']
run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', *vin, '-filter_complex', ';'.join(vf),
     '-map', '[vout]', '-map', f'{len(caps) + 2}:a', '-t', f'{TOTAL:.3f}',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
     '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT])
print('built', OUT)
