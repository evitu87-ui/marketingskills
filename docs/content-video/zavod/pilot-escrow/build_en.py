"""Assemble the pilot: lipsync hook + 7 walking shots under the voice-over + lipsync CTA, then titles."""
import json, subprocess
K = 1.1                                    # body voice speed-up
HOOK, CTA = 3.12, 4.24
def run(c): subprocess.run(c, check=True)
def dur(f): return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
cuts = [0.0, 3.75, 7.5, 12.3, 16.8, 20.85, 25.4, 30.88]          # beat borders in the raw body take
body = [(cuts[i] / K, cuts[i + 1] / K) for i in range(7)]
BODY = cuts[-1] / K
VF = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,setsar=1'
SHIFT = ',split[m][t];[t]crop=1080:24:0:0,scale=1080:170[tt];[m]crop=1080:1750:0:0[mm];[tt][mm]vstack'   # push the close shot down
parts = []
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','lip_hook_en.mp4','-t',str(HOOK),'-an','-vf',VF + ',tpad=stop_mode=clone:stop_duration=0.3','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','e0.mp4']); parts.append('e0.mp4')
for i, (a, b) in enumerate(body):
    d = b - a
    run(['ffmpeg','-nostdin','-loglevel','error','-y','-ss','0.35','-i',f'b{i+2}.mp4','-t',f'{d:.3f}','-an','-vf',VF + ',unsharp=5:5:0.6' + (SHIFT if i == 6 else ''),'-c:v','libx264','-crf','16','-pix_fmt','yuv420p',f'e{i+1}.mp4']); parts.append(f'e{i+1}.mp4')
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','lip_cta_en.mp4','-t',str(CTA),'-an','-vf',VF + ',tpad=stop_mode=clone:stop_duration=0.3','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','e8.mp4']); parts.append('e8.mp4')
open('list_en.txt','w').write(''.join(f"file '{p}'\n" for p in parts))
run(['ffmpeg','-nostdin','-loglevel','error','-y','-f','concat','-safe','0','-i','list_en.txt','-c','copy','video_en.mp4'])
# voice: hook + sped-up body + cta, padded to the exact slot lengths, then loudness
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','hook_en.mp3','-i','body_en.mp3','-i','cta_en.mp3','-filter_complex',
     f'[0:a]aresample=48000,apad,atrim=0:{HOOK}[a];[1:a]aresample=48000,atempo={K},apad,atrim=0:{BODY:.3f}[b];[2:a]aresample=48000,apad,atrim=0:{CTA}[c];'
     '[a][b][c]concat=n=3:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=9,volume=1.6dB,alimiter=limit=0.89[o]','-map','[o]','-ar','48000','voice_en.wav'])
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','video_en.mp4','-i','voice_en.wav','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','base_en.mp4'])
print('base', dur('base_en.mp4'), 'video', dur('video_en.mp4'), 'voice', dur('voice_en.wav'))

T0, T1 = HOOK, HOOK + BODY
def tb(x): return round(T0 + x / K, 2)
def tc(x): return round(T1 + x, 2)
Y = 215
ev = [dict(start=0.02, end=3.02, y=300, tilt=0.05, roll=1.2, lines=[
        dict(t='Will the developer', w='light', at=0.02), dict(t='finish?', w='heavy', size=200, at=0.74),
        dict(t="here's how we check", w='light', size=84, at=1.84)])]
vd, subs = [], []
beats = [
 (0.0, 3.08, [('Buyer payments go','light',0.0), ("into the project's",'light',0.96), ('escrow account?','heavy',1.82)], ('SAFE','ok',3.14), 3.75),
 (4.04, 6.76, [('Asked to pay','light',4.04), ('straight','heavy',4.62), ("into the company's account?",'light',5.04)], ('RISK','risk',6.82), 7.5),
 (7.84, 11.56, [('Project registered','light',7.84), ('with DLD,','heavy',8.74), ('with a registry number?','light',9.76)], ('SAFE','ok',11.62), 12.3),
 (12.66, 16.04, [('Delivered projects','heavy',12.66), ('and real handover dates','light',13.38), ('you can verify?','heavy',14.8)], ('SAFE','ok',16.1), 16.8),
 (17.08, 20.08, [('Only renders,','heavy',17.08), ('not a single finished building?','light',18.12)], ('RISK','risk',20.14), 20.85),
 (21.12, 24.68, [('Construction progress','light',21.12), ('is reported','heavy',21.98), ('and matches the','light',22.7), ('payment plan?','heavy',23.66)], ('SAFE','ok',24.74), 25.4),
 (25.74, 28.28, [('Told the price will','light',25.74), ('definitely rise','heavy',26.54), ('by handover?','light',27.44)], ('RISK','risk',28.34), 30.88),
]
for i, (s, e, lines, (vt, kind, vat), bend) in enumerate(beats):
    ev.append(dict(start=tb(s), end=tb(e), y=Y, tilt=0.05 if i % 2 else -0.05, roll=1.2 if i % 2 else -1.0,
                   lines=[dict(t=t, w=w, at=tb(a), **({'size': 124} if w == 'heavy' and len(t) > 12 else {})) for t, w, a in lines]))
    vd.append(dict(t=vt, kind=kind, at=tb(vat), end=tb(bend) - 0.04, y=300))
ev.append(dict(start=tb(29.5), end=tb(30.75), y=505, tilt=0.12, roll=-4.0, lines=[dict(t='nobody knows that', w='light', size=74, at=tb(29.5))]))
vd[-1]['y'] = 250
ev.append(dict(start=tc(0.0), end=tc(3.1), y=190, tilt=0.05, roll=1.0, lines=[
    dict(t='Comment', w='light', at=tc(0.0)), dict(t='ESCROW', w='heavy', size=200, at=tc(0.28)),
    dict(t='for our pre-booking checklist', w='light', size=74, at=tc(1.1))]))
ev.append(dict(start=tc(3.26), end=tc(CTA) + 0.2, y=230, tilt=-0.04, roll=-1.0, lines=[
    dict(t='Your call', w='heavy', size=170, at=tc(3.26)), dict(t='details in DM', w='light', at=tc(3.6))]))
spec = dict(fps=30, shade=0.45, events=ev, verdicts=vd, subs=subs, flashes=[T0, round(T1, 2)])
json.dump(spec, open('spec_en.json', 'w'), ensure_ascii=False, indent=1)
print('spec ok', len(ev), 'events')
