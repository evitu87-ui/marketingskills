import numpy as np, soundfile as sf, subprocess, re
T=-18.0
cuts={ # id: (chunk, start, end)  end=None -> split search
 'L01':('C1',0.318,2.918),'L02':('C1',3.638,6.378),'L03':('C1',6.938,'S1'),'L04':('C1','S1',10.857),
 'L05':('C1',11.378,15.898),'L06':('C1',16.438,18.178),'L07':('C1',18.718,23.378),
 'L08':('C2',0.337,3.638),'L09':('C2',4.438,8.677),'L10':('C2',9.437,'S2'),'L11':('C2','S2',17.938),
 'L12':('C2',18.817,23.298),'L13':('C2',23.698,27.758),'L14':('C2',28.278,28.958),
 'L15':('C3',0.378,5.798),'L16':('C3',6.278,9.058),'L17':('C3',9.638,12.258),'L18':('C3',12.777,16.338),
 'L19':('C3',16.858,21.678),'L20':('C3',22.078,24.958),'L21':('C3',25.458,30.098),
 'L22':('C4',0.306,2.006),'L23':('C4',2.746,9.766),'L24':('C4',10.325,15.866),'L25':('C4',16.826,20.006),
 'L26':('C4',20.706,22.266),'L27':('C4',22.866,27.266),'L28':('C4',27.766,30.086)}
aud={c:sf.read(f'tts2/{c}.wav',dtype='float32') for c in ['C1','C2','C3','C4']}
def quietest(c,a,b):
    x,sr=aud[c]; seg=x[int(a*sr):int(b*sr)]; hop=int(0.01*sr); win=int(0.04*sr)
    e=[np.sqrt(np.mean(seg[i:i+win]**2)) for i in range(0,len(seg)-win,hop)]
    i=int(np.argmin(e)); return a+(i*hop+win/2)/sr, 20*np.log10(e[i]+1e-9)
s1,d1=quietest('C1',7.8,8.9)   # after "Вот что известно"
s2,d2=quietest('C2',12.9,13.95) # after "рабочих мест"
print(f'split1 {s1:.2f}s ({d1:.0f} dBFS), split2 {s2:.2f}s ({d2:.0f} dBFS)')
S={'S1':s1,'S2':s2}
for lid,(c,a,b) in cuts.items():
    a=S.get(a,a); b=S.get(b,b)
    x,sr=aud[c]
    a0=max(0,a-0.06 if isinstance(cuts[lid][1],float) else a); b0=min(len(x)/sr,b+0.12 if isinstance(cuts[lid][2],float) else b)
    seg=x[int(a0*sr):int(b0*sr)].copy()
    f=int(0.01*sr); seg[:f]*=np.linspace(0,1,f); seg[-f:]*=np.linspace(1,0,f)
    sf.write(f'tts2/{lid}_raw.wav',seg,sr)
    out=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-i',f'tts2/{lid}_raw.wav','-af','ebur128=framelog=quiet','-f','null','-'],capture_output=True,text=True).stderr
    lu=float(re.findall(r'I:\s+(-?[\d.]+) LUFS',out)[-1]); g=max(min(T-lu,6),-6)
    subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-i',f'tts2/{lid}_raw.wav','-af',f'volume={g:.2f}dB',f'tts/{lid}.wav'])
    print(lid,c,f'{a0:.2f}-{b0:.2f}',f'lufs {lu:.1f} -> gain {g:+.1f}')
