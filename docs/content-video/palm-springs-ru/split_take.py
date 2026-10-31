"""Split one continuous voice take into the script's lines, then level each line.
Usage: python3 split_take.py take.wav outdir [target_lufs]
Cuts are chosen among detected pauses by DP: in order, close to positions predicted
from cumulative text length, preferring longer pauses.
"""
import json, re, subprocess, sys

take, outdir = sys.argv[1], sys.argv[2]
TARGET = float(sys.argv[3]) if len(sys.argv) > 3 else -18.0
S = json.load(open('ps_script.json'))
n = len(S)


def ff(args):
    return subprocess.run(['ffmpeg', '-hide_banner', *args], capture_output=True, text=True).stderr


log = ff(['-i', take, '-af', 'silencedetect=noise=-38dB:d=0.28', '-f', 'null', '-'])
starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
total = float(re.findall(r'time=(\d+):(\d+):([\d.]+)', log)[-1][2]) + 60 * int(re.findall(r'time=(\d+):(\d+):([\d.]+)', log)[-1][1])
sil = [(s, e) for s, e in zip(starts, ends)]
lead = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
tail = sil[-1][0] if sil and sil[-1][1] > total - 0.05 else total
inner = [(s, e) for s, e in sil if s > lead + 0.1 and e < tail - 0.1]
print(f'take {total:.2f}s, speech {lead:.2f}-{tail:.2f}, pauses {len(inner)}')

w = [len(l['tts']) for l in S]
cum, acc = [], 0
for x in w[:-1]:
    acc += x
    cum.append(acc / sum(w))
exp = [lead + c * (tail - lead) for c in cum]  # expected boundary times
K, N = n - 1, len(inner)
assert N >= K, f'only {N} pauses for {K} boundaries'
INF = 1e18
cost = [[INF] * N for _ in range(K)]
back = [[-1] * N for _ in range(K)]


def c(k, j):
    s, e = inner[j]
    mid = (s + e) / 2
    return ((mid - exp[k]) / 1.5) ** 2 - 4.0 * min(e - s, 1.2)


for j in range(N):
    cost[0][j] = c(0, j)
for k in range(1, K):
    best, bi = INF, -1
    for j in range(N):
        if j - 1 >= 0 and cost[k - 1][j - 1] < best:
            best, bi = cost[k - 1][j - 1], j - 1
        if bi >= 0:
            cost[k][j] = best + c(k, j)
            back[k][j] = bi
j = min(range(N), key=lambda x: cost[K - 1][x])
pick = []
for k in range(K - 1, -1, -1):
    pick.append(j)
    j = back[k][j]
pick = pick[::-1]
cuts = [lead] + [(inner[p][0] + inner[p][1]) / 2 for p in pick] + [tail]

for i, l in enumerate(S):
    a, b = max(cuts[i] - 0.04, 0), cuts[i + 1] + 0.04
    tmp = f'{outdir}/{l["id"]}_raw.wav'
    ff(['-y', '-loglevel', 'error', '-ss', f'{a:.3f}', '-to', f'{b:.3f}', '-i', take, '-ar', '48000', tmp])
    m = re.findall(r'I:\s+(-?[\d.]+) LUFS', ff(['-i', tmp, '-af', 'ebur128=framelog=quiet', '-f', 'null', '-']))
    lu = float(m[-1]) if m else TARGET
    g = max(min(TARGET - lu, 6.0), -6.0)
    ff(['-y', '-loglevel', 'error', '-i', tmp, '-af', f'volume={g:.2f}dB', f'{outdir}/{l["id"]}.wav'])
    exp_t = exp[i - 1] if i else lead
    print(f'{l["id"]} {a:6.2f}-{b:6.2f} ({b - a:4.2f}s) lufs {lu:6.1f} gain {g:+.1f}  exp_start {exp_t:6.2f}')
