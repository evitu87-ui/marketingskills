"""Scout ("Разведка"): turn a list of reel links into a hook table.

For every link: download the reel + metadata (yt-dlp), transcribe it (faster-whisper),
measure the edit pace (scene cuts), then write one JSON per reel and a Markdown report.

Usage:
  python3 scout.py links.txt WORKDIR            # fetch + analyse + report
  python3 scout.py links.txt WORKDIR --report   # rebuild the report only

links.txt: one reel URL per line, '#' starts a comment.
A reel already present as WORKDIR/raw/<code>.mp4 (+ .info.json) is not downloaded again.
Env: WHISPER_MODEL = model name or local folder (default "small").
"""
import json, os, re, subprocess, sys, time

LINKS, WORK = sys.argv[1], sys.argv[2]
REPORT_ONLY = '--report' in sys.argv
RAW, DATA = os.path.join(WORK, 'raw'), os.path.join(WORK, 'data')
os.makedirs(RAW, exist_ok=True)
os.makedirs(DATA, exist_ok=True)
HOOK_SEC, PAUSE = 3.5, 20          # hook window; pause between Instagram requests
_rj = os.path.join(WORK, 'reels.json')        # written by scout_apify.py: plays + direct video links
REELS = {r['code']: r for r in json.load(open(_rj, encoding='utf-8'))} if os.path.exists(_rj) else {}


def sh(cmd, timeout=600):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def codes():
    out = []
    for line in open(LINKS, encoding='utf-8'):
        line = line.split('#')[0].strip()
        m = re.search(r'/(?:reel|reels|p)/([A-Za-z0-9_-]+)', line)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def fetch(code):
    mp4, info = os.path.join(RAW, code + '.mp4'), os.path.join(RAW, code + '.info.json')
    if os.path.exists(mp4) and os.path.exists(info):
        return True
    r = REELS.get(code)
    if r and r.get('video_url'):
        sh(['curl', '-s', '-L', '-m', '180', '-o', mp4, r['video_url']])
        if os.path.exists(mp4) and os.path.getsize(mp4) > 100000:
            json.dump(dict(channel=r['account'], uploader=r.get('author'), upload_date=r['date'].replace('-', ''),
                           like_count=r['likes'], comment_count=r['comments'], view_count=r['plays'],
                           description=r['caption']), open(info, 'w', encoding='utf-8'), ensure_ascii=False)
            return True
    for attempt in range(4):
        r = sh(['yt-dlp', '-q', '--no-progress', '--write-info-json', '-f', 'mp4/best', '--merge-output-format', 'mp4',
                '-o', os.path.join(RAW, '%(id)s.%(ext)s'), f'https://www.instagram.com/reel/{code}/'])
        if os.path.exists(mp4) and os.path.exists(info):
            time.sleep(PAUSE)
            return True
        wait = 90 * (attempt + 1) if '429' in r.stderr else 15
        print(f'  {code}: попытка {attempt + 1} не удалась ({r.stderr.strip()[-90:]}), жду {wait} с', flush=True)
        time.sleep(wait)
    return False


def duration(mp4):
    r = sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4])
    return float(r.stdout.strip() or 0)


def cuts(mp4):
    """Scene changes at 4 fps, 270 px wide: fast and good enough to compare pace."""
    r = sh(['ffmpeg', '-nostdin', '-i', mp4, '-an', '-vf', "fps=4,scale=270:-2,select='gt(scene,0.30)',showinfo",
            '-f', 'null', '-'])
    return len(re.findall(r'pts_time:', r.stderr))


_model = None


def transcribe(mp4):
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(os.environ.get('WHISPER_MODEL', 'small'), device='cpu', compute_type='int8')
    import numpy as np  # decode with ffmpeg: no dependency on the PyAV version
    pcm = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', mp4, '-vn', '-ac', '1', '-ar', '16000', '-f', 's16le', '-'],
                         capture_output=True).stdout
    audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    segs, info = _model.transcribe(audio, word_timestamps=True, vad_filter=True)
    words = [(w.word.strip(), round(w.start, 2), round(w.end, 2)) for s in segs for w in (s.words or [])]
    return info.language, words


def sentences(words):
    out, cur = [], []
    for w, a, b in words:
        cur.append((w, a, b))
        if re.search(r'[.!?…]$', w):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [(' '.join(x[0] for x in s), s[0][1], s[-1][2]) for s in out]


def analyse(code):
    out = os.path.join(DATA, code + '.json')
    if os.path.exists(out):
        return json.load(open(out, encoding='utf-8'))
    mp4 = os.path.join(RAW, code + '.mp4')
    meta = json.load(open(os.path.join(RAW, code + '.info.json'), encoding='utf-8'))
    dur = duration(mp4)
    lang, words = transcribe(mp4)
    sents = sentences(words)
    hook = []
    for text, a, b in sents:            # whole sentences that start inside the hook window
        if a <= HOOK_SEC or not hook:
            hook.append(text)
        else:
            break
    n_cuts = cuts(mp4)
    d = dict(
        code=code, url=f'https://www.instagram.com/reel/{code}/',
        account=meta.get('channel') or meta.get('uploader_id'), author=meta.get('uploader'),
        date=(meta.get('upload_date') or '')[:8], likes=meta.get('like_count'), comments=meta.get('comment_count'),
        views=meta.get('view_count'), caption=(meta.get('description') or '').strip(),
        duration=round(dur, 1), language=lang, words=len(words),
        words_per_sec=round(len(words) / dur, 2) if dur else None,
        speech_start=words[0][1] if words else None,
        cuts=n_cuts, cuts_per_min=round(n_cuts / dur * 60, 1) if dur else None,
        hook=' '.join(hook), cta=sents[-1][0] if sents else '',
        transcript=' '.join(s[0] for s in sents),
    )
    json.dump(d, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return d


def report(rows):
    def n(v):
        return '—' if v is None else str(v)

    for d in rows:                      # fresh numbers from the scraper, when we have them
        r = REELS.get(d['code']) or {}
        d['views'], d['x_median'] = r.get('plays', d.get('views')), r.get('x_median')
    if any(d['x_median'] for d in rows):
        rows = sorted(rows, key=lambda d: -(d['x_median'] or 0))
        order = 'просмотры ролика к медиане своего аккаунта'
    else:
        rows = sorted(rows, key=lambda d: -((d.get('comments') or 0) * 5 + (d.get('likes') or 0)))
        order = 'лайки + 5 × комментарии'
    L = ['# Разведка: таблица рилсов', '', f'Роликов: {len(rows)}. Сортировка: {order}.', '',
         '| Аккаунт | Дата | × медианы | Просмотры | Лайки | Комм. | Длина, с | Склеек/мин | Слов/с | Язык | Хук (первые 3,5 с) | Концовка |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for d in rows:
        date = d['date'] and f"{d['date'][6:8]}.{d['date'][4:6]}.{d['date'][:4]}"
        L.append(f"| [{d['account']}]({d['url']}) | {date} | {n(d['x_median'])} | {n(d['views'])} | {n(d['likes'])} | {n(d['comments'])} | {n(d['duration'])} | "
                 f"{n(d['cuts_per_min'])} | {n(d['words_per_sec'])} | {d['language']} | {d['hook'].replace('|', '/')} | "
                 f"{d['cta'].replace('|', '/')} |")
    open(os.path.join(WORK, 'report.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(f'report: {os.path.join(WORK, "report.md")} ({len(rows)} роликов)')


rows = []
for c in codes():
    if not REPORT_ONLY and not fetch(c):
        print(f'ПРОПУСК {c}: не скачался')
        continue
    if not os.path.exists(os.path.join(RAW, c + '.mp4')) and not os.path.exists(os.path.join(DATA, c + '.json')):
        continue
    d = analyse(c)
    rows.append(d)
    print(f"{c}: {d['account']}, {d['duration']} с, склеек/мин {d['cuts_per_min']}, хук: {d['hook'][:70]}", flush=True)
report(rows)
