"""Second reel ("Пузырь или зрелый рынок?", host G). Usage: python3 build2.py ru|en"""
import json, subprocess, sys
L = sys.argv[1]
CFG = {
 'ru': dict(K=1.12, HOOK=3.44, CTA=4.72, cuts=[0.0, 5.06, 8.3, 11.2, 16.0, 21.95, 26.2, 32.16]),
 'en': dict(K=1.28, HOOK=3.92, CTA=4.96, cuts=[0.0, 5.1, 10.65, 13.9, 18.9, 26.92, 32.7, 39.6]),
}[L]
K, HOOK, CTA, cuts = CFG['K'], CFG['HOOK'], CFG['CTA'], CFG['cuts']
def run(c): subprocess.run(c, check=True)
def dur(f): return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
body = [(cuts[i] / K, cuts[i + 1] / K) for i in range(7)]
BODY = cuts[-1] / K
VF = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,setsar=1'
PAD = ',tpad=stop_mode=clone:stop_duration=0.4'
SHIFT = ',split[m][t];[t]crop=1080:24:0:0,scale=1080:150[tt];[m]crop=1080:1770:0:0[mm];[tt][mm]vstack'
ENC = ['-c:v','libx264','-crf','16','-pix_fmt','yuv420p']
parts = []
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i',f'lip_hook_{L}.mp4','-t',str(HOOK),'-an','-vf',VF + PAD] + ENC + [f'{L}0.mp4']); parts.append(f'{L}0.mp4')
for i, (a, b) in enumerate(body):
    d = b - a
    src, ss, avail = f'b{i+2}.mp4', '0.35', 5.55
    if i == 5:                                      # fence scene: standing take, no steps; only its first seconds (camera pushes in later)
        src, ss, avail = 'b7b.mp4', '0.10', 2.4
    slow = max(d / avail, 1.0)                      # stretch the clip when the line is longer than the usable footage
    smooth = 'minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc,' if slow > 1.3 else ''
    vf = (f'setpts={slow:.4f}*PTS,' if slow > 1 else '') + smooth + VF + ',unsharp=5:5:0.6'
    run(['ffmpeg','-nostdin','-loglevel','error','-y','-ss',ss,'-i',src,'-t',f'{d:.3f}','-an','-vf',vf] + ENC + [f'{L}{i+1}.mp4']); parts.append(f'{L}{i+1}.mp4')
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i',f'lip_cta_{L}.mp4','-t',str(CTA),'-an','-vf',VF + PAD] + ENC + [f'{L}8.mp4']); parts.append(f'{L}8.mp4')
open(f'list_{L}.txt','w').write(''.join(f"file '{p}'\n" for p in parts))
run(['ffmpeg','-nostdin','-loglevel','error','-y','-f','concat','-safe','0','-i',f'list_{L}.txt','-c','copy',f'video_{L}.mp4'])
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i',f'hook_{L}.mp3','-i',f'body_{L}.mp3','-i',f'cta_{L}.mp3','-filter_complex',
     f'[0:a]aresample=48000,apad,atrim=0:{HOOK}[a];[1:a]aresample=48000,atempo={K},apad,atrim=0:{BODY:.3f}[b];[2:a]aresample=48000,apad,atrim=0:{CTA}[c];'
     '[a][b][c]concat=n=3:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=9,volume=1.2dB,alimiter=limit=0.89[o]','-map','[o]','-ar','48000',f'voice_{L}.wav'])
run(['ffmpeg','-nostdin','-loglevel','error','-y','-i',f'video_{L}.mp4','-i',f'voice_{L}.wav','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',f'base_{L}.mp4'])
print('base', dur(f'base_{L}.mp4'))

T0, T1 = HOOK, HOOK + BODY
def tb(x): return round(T0 + x / K, 2)
def tc(x): return round(T1 + x, 2)
def ln(t, w, at, size=None):
    d = dict(t=t, w=w, at=at)
    if size: d['size'] = size
    return d
Y = 140
if L == 'ru':
    hook = [('Пузырь','heavy',0.0,170), ('или зрелый рынок?','mid',0.52,88), ('разберём по цифрам','mid',2.1,70)]
    beats = [
     (0.0, 4.95, [('Сделок за год','mid',0.0,None), ('−21%','heavy',1.0,220), ('но больше, чем в 2023-м','mid',2.66,72)]),
     (5.2, 8.2, [('Это не обвал,','light',5.2,None), ('спокойный рынок','heavy',6.34,124), ('после рекордов','light',7.26,None)]),
     (8.52, 11.1, [('Ипотека лишь','light',8.52,None), ('в каждой десятой','heavy',9.42,124), ('сделке','light',10.5,None)]),
     (11.5, 15.9, [('С 2020 года в Дубае','light',11.5,84), ('+1,4 млн','heavy',13.9,200), ('жителей','light',15.34,None)]),
     (16.2, 21.85, [('Медиана за фут','light',16.2,None), ('1 730 AED','heavy',17.32,170), ('осенью −1–2% в месяц','light',19.4,76)]),
     (22.2, 26.1, [('В 2027-м по плану сдают','light',22.2,76), ('122 000','heavy',24.18,178), ('юнитов','light',25.54,None)]),
     (26.22, 30.2, [('Больше всего:','light',26.22,80), ('Dubai South','heavy',27.12,100), ('Wadi Al Safa','heavy',28.36,100), ('JVC','heavy',29.4,100)]),
     (30.38, 32.05, [('Считать надо','light',30.38,None), ('по районам','heavy',31.06,170)]),
    ]
    cta1 = (0.0, 3.6, [('Напишите','light',0.0,None), ('РАЙОНЫ','heavy',0.58,200), ('пришлём разбор по районам','light',1.72,76)])
    cta2 = (3.76, [('Решать вам','heavy',3.76,150), ('подробности у нас','light',4.1,80)])
    src = 'Данные DLD через DXBinteract, 25.11.2026'
else:
    hook = [('Bubble','heavy',0.0,190), ('or a maturing market?','mid',0.32,84), ("let's check the numbers",'mid',2.54,70)]
    beats = [
     (0.0, 5.0, [('Sales, year on year','mid',0.0,None), ('−21%','heavy',1.22,220), ('still more than all of 2023','mid',2.92,70)]),
     (5.58, 10.55, [('Not a crash.','light',6.56,None), ('A market cooling','heavy',8.0,124), ('after record years','light',9.04,None)]),
     (10.98, 13.8, [('Only about','light',10.98,None), ('one deal in ten','heavy',11.46,124), ('uses a mortgage','light',12.58,None)]),
     (14.28, 18.8, [('Since 2020, Dubai added','light',14.28,80), ('+1.4M','heavy',16.44,200), ('residents','light',18.02,None)]),
     (19.28, 26.8, [('Median price per sq ft','light',19.28,84), ('AED 1,730','heavy',20.4,170), ('this autumn: −1–2% a month','light',24.16,72)]),
     (26.92, 32.6, [('Scheduled for handover in 2027','light',26.92,72), ('122,000','heavy',27.64,178), ('units','light',29.52,None)]),
     (33.02, 37.1, [('Most of it lands in','light',33.02,80), ('Dubai South','heavy',34.08,100), ('Wadi Al Safa','heavy',35.18,100), ('JVC','heavy',36.2,100)]),
     (37.26, 39.45, [('Assess risk','light',37.26,None), ('area by area','heavy',37.96,150)]),
    ]
    cta1 = (0.0, 3.9, [('Comment','light',0.0,None), ('AREAS','heavy',0.32,200), ('for our handover breakdown','light',0.86,76)])
    cta2 = (4.18, [('Your call','heavy',4.18,170), ('details in DM','light',4.5,None)])
    src = 'Data: DLD via DXBinteract, 25 Nov 2026'
ev = [dict(start=0.02, end=HOOK - 0.1, y=150, tilt=0.05, roll=1.2, lines=[ln(t, w, a if a else 0.02, s) for t, w, a, s in hook])]
for i, (s, e, lines) in enumerate(beats):
    ev.append(dict(start=tb(s), end=tb(e), y=Y, tilt=0.05 if i % 2 else -0.05, roll=1.2 if i % 2 else -1.0,
                   lines=[ln(t, w, tb(a), sz) for t, w, a, sz in lines]))
ev.append(dict(start=tc(cta1[0]), end=tc(cta1[1]), y=150, tilt=0.05, roll=1.0, lines=[ln(t, w, tc(a), s) for t, w, a, s in cta1[2]]))
ev.append(dict(start=tc(cta2[0]), end=tc(CTA) + 0.2, y=190, tilt=-0.04, roll=-1.0, lines=[ln(t, w, tc(a), s) for t, w, a, s in cta2[1]]))
subs = []   # sources go into the post caption; on-screen line was unreadable on light pavement
spec = dict(fps=30, shade=0.6, events=ev, verdicts=[], subs=subs, flashes=[T0, round(T1, 2)])
json.dump(spec, open(f'spec_{L}.json', 'w'), ensure_ascii=False, indent=1)
print('spec ok', len(ev), 'events')
