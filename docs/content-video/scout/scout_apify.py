"""Scout, step 1: collect recent reels of the accounts in accounts.txt through the Apify
Instagram Reel Scraper and rank them by how far each reel beats its own account.

Usage:
  python3 scout_apify.py accounts.txt WORKDIR [--limit 30] [--newer "3 months"] [--top 20]

Writes to WORKDIR:
  reels.json   all reels (merged with earlier runs by shortcode, newest numbers win)
  accounts.md  per-account medians + the ranked outlier table
  links.txt    the --top outliers, input for scout.py (hooks, pace, transcript)

Auth: the Apify token is injected by the environment proxy for api.apify.com.
Outside this environment set APIFY_TOKEN. Cost on the Free plan: $0.0026 per reel.
"""
import json, os, statistics, sys, urllib.request

ACC, WORK = sys.argv[1], sys.argv[2]


def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


LIMIT, NEWER, TOP = int(opt('--limit', 30)), opt('--newer', ''), int(opt('--top', 20))
os.makedirs(WORK, exist_ok=True)
accounts = [l.split('#')[0].strip().lstrip('@') for l in open(ACC, encoding='utf-8')]
accounts = [a for a in accounts if a]

body = {'username': accounts, 'resultsLimit': LIMIT, 'skipTrialReels': True}
if NEWER:
    body['onlyPostsNewerThan'] = NEWER
cap = round(len(accounts) * LIMIT * 0.0026 + 0.05, 2)          # hard spend ceiling for this run
url = f'https://api.apify.com/v2/acts/apify~instagram-reel-scraper/run-sync-get-dataset-items?timeout=280&maxTotalChargeUsd={cap}'
head = {'Content-Type': 'application/json'}
if os.environ.get('APIFY_TOKEN'):
    head['Authorization'] = 'Bearer ' + os.environ['APIFY_TOKEN']
req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=head, method='POST')
items = json.loads(urllib.request.urlopen(req, timeout=300).read())
if not isinstance(items, list):
    raise SystemExit('Apify error: ' + json.dumps(items, ensure_ascii=False)[:500])
print(f'получено рилсов: {len(items)} (потолок расхода ${cap})')

path = os.path.join(WORK, 'reels.json')
old = {r['code']: r for r in json.load(open(path, encoding='utf-8'))} if os.path.exists(path) else {}
for x in items:
    if not x.get('shortCode'):
        continue
    src = (x.get('inputUrl') or '').rstrip('/').split('/')[-1].lower()
    old[x['shortCode']] = dict(
        code=x['shortCode'], url=f"https://www.instagram.com/reel/{x['shortCode']}/",
        account=src or x.get('ownerUsername'),            # the account we asked for (collabs keep their source)
        owner=x.get('ownerUsername'), author=x.get('ownerFullName'),
        date=(x.get('timestamp') or '')[:10], plays=x.get('videoPlayCount'), likes=x.get('likesCount'),
        comments=x.get('commentsCount'), duration=round(x.get('videoDuration') or 0, 1), pinned=bool(x.get('isPinned')),
        caption=(x.get('caption') or '').strip(), video_url=x.get('videoUrl'),
        music=(x.get('musicInfo') or {}).get('song_name'),
    )
reels = list(old.values())

by = {}
for r in reels:
    by.setdefault(r['account'], []).append(r)
med = {a: statistics.median([r['plays'] or 0 for r in rs]) for a, rs in by.items()}
for r in reels:
    m = med[r['account']]
    r['x_median'] = round((r['plays'] or 0) / m, 1) if m else None
json.dump(reels, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

rank = sorted([r for r in reels if r['x_median']], key=lambda r: -r['x_median'])
L = ['# Разведка: аккаунты и выбросы', '', '## Аккаунты', '',
     '| Аккаунт | Рилсов | Медиана просмотров | Лучший | Средняя длина, с |', '|---|---|---|---|---|']
for a, rs in sorted(by.items(), key=lambda kv: -med[kv[0]]):
    L.append(f"| {a} | {len(rs)} | {int(med[a])} | {max(r['plays'] or 0 for r in rs)} | "
             f"{round(statistics.mean(r['duration'] for r in rs))} |")
L += ['', f'## Выбросы: просмотры ролика к медиане своего аккаунта (топ {TOP})', '',
      '| × медианы | Аккаунт | Дата | Просмотры | Лайки | Комм. | Длина, с | Начало подписи |', '|---|---|---|---|---|---|---|---|']
for r in rank[:TOP]:
    cap_ = r['caption'].replace('\n', ' ').replace('|', '/')[:90]
    L.append(f"| {r['x_median']} | [{r['account']}]({r['url']}) | {r['date']} | {r['plays']} | {r['likes']} | {r['comments']} | "
             f"{r['duration']} | {cap_} |")
open(os.path.join(WORK, 'accounts.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
open(os.path.join(WORK, 'links.txt'), 'w', encoding='utf-8').write(
    '\n'.join(f"{r['url']}  # {r['account']} x{r['x_median']}" for r in rank[:TOP]) + '\n')
print(f"аккаунтов: {len(by)}, всего рилсов в базе: {len(reels)}; отчёт: {os.path.join(WORK, 'accounts.md')}")
