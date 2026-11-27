"""Assemble the pilot: lipsync hook + 7 walking shots under the voice-over + lipsync CTA, then titles."""
import json, subprocess
K = 1.1                                    # body voice speed-up
HOOK, CTA = 3.52, 4.96
def run(c): subprocess.run(c, check=True)
def dur(f): return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
cuts = [0.0, 4.2, 7.9, 12.4, 17.25, 20.8, 25.5, 31.2]          # beat borders in the raw body take
body = [(cuts[i] / K, cuts[i + 1] / K) for i in range(7)]
BODY = cuts[-1] / K
VF = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,setsar=1'
SHIFT = ',split[m][t];[t]crop=1080:24:0:0,scale=1080:170[tt];[m]crop=1080:1750:0:0[mm];[tt][mm]vstack'   # push the close shot down
parts = []
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','lip_hook.mp4','-t',str(HOOK),'-an','-vf',VF + ',tpad=stop_mode=clone:stop_duration=0.3','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','p0.mp4']); parts.append('p0.mp4')
for i, (a, b) in enumerate(body):
    d = b - a
    run(['ffmpeg','-nostdin','-loglevel','error','-y','-ss','0.35','-i',f'b{i+2}.mp4','-t',f'{d:.3f}','-an','-vf',VF + ',unsharp=5:5:0.6' ,'-c:v','libx264','-crf','16','-pix_fmt','yuv420p',f'p{i+1}.mp4']); parts.append(f'p{i+1}.mp4')
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','lip_cta.mp4','-t',str(CTA),'-an','-vf',VF + ',tpad=stop_mode=clone:stop_duration=0.3','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','p8.mp4']); parts.append('p8.mp4')
open('list.txt','w').write(''.join(f"file '{p}'\n" for p in parts))
run(['ffmpeg','-nostdin','-loglevel','error','-y','-f','concat','-safe','0','-i','list.txt','-c','copy','video.mp4'])
# voice: hook + sped-up body + cta, padded to the exact slot lengths, then loudness
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','hook.mp3','-i','body.mp3','-i','cta.mp3','-filter_complex',
     f'[0:a]aresample=48000,apad,atrim=0:{HOOK}[a];[1:a]aresample=48000,atempo={K},apad,atrim=0:{BODY:.3f}[b];[2:a]aresample=48000,apad,atrim=0:{CTA}[c];'
     '[a][b][c]concat=n=3:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=9,volume=1.6dB,alimiter=limit=0.89[o]','-map','[o]','-ar','48000','voice.wav'])
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i','video.mp4','-i','voice.wav','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','base.mp4'])
print('base', dur('base.mp4'), 'video', dur('video.mp4'), 'voice', dur('voice.wav'))

T0, T1 = HOOK, HOOK + BODY
def tb(x): return round(T0 + x / K, 2)
def tc(x): return round(T1 + x, 2)
Y = 140
ev = [dict(start=0.02, end=3.40, y=170, tilt=0.05, roll=1.2, lines=[
        dict(t='Застройщик', w='heavy', size=150, at=0.02), dict(t='достроит?', w='heavy', at=0.68),
        dict(t='вот как мы это проверяем', w='mid', size=84, at=1.6)])]
vd, subs = [], []
beats = [
 (0.0, 3.30, [('Деньги покупателей','mid',0.0), ('на эскроу-счёт','heavy',1.52), ('проекта?','mid',2.4)], ('НАДЁЖНО','ok',3.36), 4.2),
 (4.42, 7.0, [('Просят перевести','mid',4.42), ('напрямую','heavy',5.2), ('на счёт компании?','mid',5.74)], ('РИСК','risk',7.06), 7.9),
 (8.14, 11.58, [('Проект зарегистрирован','mid',8.14), ('в DLD,','heavy',9.12), ('есть номер в реестре?','mid',10.08)], ('НАДЁЖНО','ok',11.64), 12.4),
 (12.62, 16.4, [('Сданные проекты','heavy',12.62), ('и фактические сроки сдачи','mid',13.62), ('можно проверить?','heavy',15.2)], ('НАДЁЖНО','ok',16.46), 17.25),
 (17.44, 20.0, [('Только рендеры,','heavy',17.44), ('ни одного сданного дома?','mid',18.2)], ('РИСК','risk',20.08), 20.8),
 (20.98, 24.74, [('Прогресс стройки','mid',20.98), ('виден в отчётах','heavy',21.8), ('и совпадает с графиком','mid',22.74), ('платежей?','heavy',23.86)], ('НАДЁЖНО','ok',24.8), 25.5),
 (25.7, 28.66, [('Обещают, что цена','mid',25.7), ('точно вырастет','heavy',26.74), ('к сдаче?','mid',27.68)], ('РИСК','risk',28.72), 31.2),
]
for i, (s, e, lines, (vt, kind, vat), bend) in enumerate(beats):
    ev.append(dict(start=tb(s), end=tb(e), y=Y, tilt=0.05 if i % 2 else -0.05, roll=1.2 if i % 2 else -1.0,
                   lines=[dict(t=t, w=w, at=tb(a), **({'size': 124} if w == 'heavy' and len(t) > 12 else {})) for t, w, a in lines]))
    vd.append(dict(t=vt, kind=kind, at=tb(vat), end=tb(bend) - 0.04, y=220))
ev.append(dict(start=tb(29.12), end=tb(31.0), y=420, tilt=0.12, roll=-4.0, lines=[dict(t='такого никто не знает', w='mid', size=74, at=tb(29.12))]))
vd[-1]['y'] = 200
ev.append(dict(start=tc(0.0), end=tc(3.95), y=170, tilt=0.05, roll=1.0, lines=[
    dict(t='Напишите', w='mid', at=tc(0.0)), dict(t='ЭСКРОУ', w='heavy', size=200, at=tc(0.58)),
    dict(t='пришлём чек-лист проверки', w='mid', size=80, at=tc(1.6))]))
ev.append(dict(start=tc(4.1), end=tc(CTA) + 0.2, y=230, tilt=-0.04, roll=-1.0, lines=[
    dict(t='Подробности', w='heavy', size=150, at=tc(4.1)), dict(t='у нас', w='mid', at=tc(4.45))]))
spec = dict(fps=30, shade=0.6, events=ev, verdicts=vd, subs=subs, flashes=[T0, round(T1, 2)])
json.dump(spec, open('spec.json', 'w'), ensure_ascii=False, indent=1)
print('spec ok', len(ev), 'events')
