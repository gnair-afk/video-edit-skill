#!/usr/bin/env python3
"""Beat grid of the reel's music, and cuts snapped onto it (the "beat" look: every cut lands on a beat).

Usage (PY = the skill's Python; needs numpy, which the venv has):
  PY beatgrid.py <project> [--music assets/music/bgm.mp3] [--bpm 110] [--max-shift 0.15] [--snap] [--check]

  (no flag)  detect tempo + beats, write <project>/beats.json, print the grid
  --snap     move each segment's in/out in edl.json, only inside real pauses of the source audio (never into a
             word), so every cut and the reel's end land on a beat, or a half beat when no full beat fits. It also
             tries every start offset of the music (one beat's worth) and keeps the one that lands the most cuts.
             Backs up edl.json to work/edl.pre-beat.json first. Run BEFORE assemble.py.
  --check    after assemble.py: read segments.json (exact frames) and report how far each cut is from the grid.

beats.json (timeline seconds, music already offset): {"bpm", "period", "musicStart" (play bgm.mp3 from this second:
data-media-start in build.py), "beats", "strong" (louder than median: use them for the big moments), "half"}.
build.py reads it to place image swaps, card changes, punch zooms and word slams on the beat.

Why audio and not words: Whisper word ends run straight into the next word (no gaps), so they cannot show a
pause. The source clip's own loudness can: a cut may slide while the audio around it stays quiet.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

SR, HOP, N, FPS = 22050, 256, 1024, 30


def pcm(path, sr=SR):
    raw = subprocess.run([skillenv.tool('ffmpeg'), '-v', 'error', '-i', path, '-vn', '-ac', '1', '-ar', str(sr),
                          '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def onset_env(x):
    fr = np.lib.stride_tricks.sliding_window_view(x, N)[::HOP] * np.hanning(N)
    spec = np.log1p(100 * np.abs(np.fft.rfft(fr, axis=1)))
    low = spec[:, : int(200 / (SR / N))]                      # kick / bass band weighs double
    e = np.maximum(np.diff(spec, axis=0), 0).sum(1) + 2 * np.maximum(np.diff(low, axis=0), 0).sum(1)
    e = np.maximum(e - np.convolve(e, np.ones(16) / 16, 'same'), 0)
    return e / (e.max() + 1e-9)


def comb(env, period, step=0.25):
    """Best mean onset strength of a rigid beat comb with this period (env frames), and its phase."""
    best = (0.0, 0.0)
    for ph in np.arange(0, period, step):
        idx = np.round(np.arange(ph, len(env) - 1, period)).astype(int)
        best = max(best, (float(env[idx].mean()), ph))
    return best


def grid(path, bpm_hint=None):
    """Tempo from a rigid comb scan. Music models do not always play the bpm asked for (asked 110, got 122), so the
    hint only widens/narrows the search (+-20%); it never forces the tempo."""
    x = pcm(path)
    env, dur, rate = onset_env(x), len(x) / SR, SR / HOP
    lo, hi = (bpm_hint / 1.2, bpm_hint * 1.2) if bpm_hint else (80, 160)
    coarse = max(np.arange(lo, hi, 0.25), key=lambda q: comb(env, 60 * rate / q, 1.0)[0])
    bpm = max(np.arange(coarse - .3, coarse + .3, .02), key=lambda q: comb(env, 60 * rate / q, 1.0)[0])
    period = 60 / bpm
    phase = comb(env, period * rate)[1] / rate
    beats, t, w = [], phase, int(0.03 * rate)                  # follow slight drift: re-centre on onsets +-30 ms
    while t < dur - 0.05:
        i = int(round(t * rate))
        seg = env[max(i - w, 0): i + w + 1]
        if len(seg) and seg.max() > 0.15:
            t = (max(i - w, 0) + int(np.argmax(seg))) / rate
        beats.append(round(t, 4))
        t += period
    strength = [float(env[min(int(round(q * rate)), len(env) - 1)]) for q in beats]
    return {'bpm': round(60 / period, 2), 'period': round(period, 4), 'beats': beats, 'strength': strength,
            'music_seconds': round(dur, 3)}


def shifted(g, start):
    """Grid in timeline seconds when bgm.mp3 plays from `start`."""
    med = float(np.median(g['strength']))
    keep = [(b - start, s) for b, s in zip(g['beats'], g['strength']) if b - start >= 0]
    beats = [round(b, 4) for b, _ in keep]
    return {'bpm': g['bpm'], 'period': g['period'], 'musicStart': round(start, 3), 'beats': beats,
            'strong': [s > med for _, s in keep], 'half': [round((p + q) / 2, 4) for p, q in zip(beats, beats[1:])],
            'music_seconds': g['music_seconds']}


class Quiet:
    """Loudness of a source clip, 10 ms steps: where a cut may slide without clipping speech."""

    def __init__(self, path):
        x = pcm(path, 16000)
        n = len(x) // 160
        r = np.sqrt((x[: n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-6
        db = 20 * np.log10(r)
        self.db, self.limit = db, np.percentile(db, 90) - 22     # 22 dB under loud speech = pause / breath

    def span(self, t, guard=0.03):
        """(earliest, latest) a cut at t may move to while staying in quiet audio."""
        i = int(t * 100)
        if i >= len(self.db) or self.db[min(i, len(self.db) - 1)] > self.limit:
            return t - 1 / FPS, t + 1 / FPS                    # cut sits in sound: allow one frame only
        a = b = i
        while a > 0 and self.db[a - 1] <= self.limit:
            a -= 1
        while b < len(self.db) - 1 and self.db[b + 1] <= self.limit:
            b += 1
        return min(a / 100 + guard, t), max(b / 100 - guard, t)


def plan(edl, quiet, g, max_shift):
    full, half = np.array(g['beats']), np.array(g['half'])
    t, out, hits = 0.0, [], 0
    for s in edl:
        q = quiet[s['clip']]
        o_lo, o_hi = q.span(s['out'])
        i_lo, i_hi = q.span(s['in'])
        grow = min(o_hi - s['out'], max_shift) + min(s['in'] - i_lo, max_shift)
        shrink = min(s['out'] - o_lo, max_shift) + min(i_hi - s['in'], max_shift)
        end = t + s['out'] - s['in']
        # pace first: trimming is cheap, growing costs (it slows the reel and adds up); a half beat costs a little
        fit = [(p, kind) for pts, kind in ((full, 'beat'), (half, 'half')) for p in pts
               if -shrink - 1e-6 <= p - end <= grow + 1e-6 and p - t > 0.4]
        best = min(fit, key=lambda f: abs(f[0] - end) + 0.8 * max(f[0] - end, 0) + (0.04 if f[1] == 'half' else 0),
                   default=None)
        n = dict(s)
        if best:
            target = round(best[0] * FPS) / FPS
            delta = target - end
            tail = max(min(delta, min(o_hi - s['out'], max_shift)), -min(s['out'] - o_lo, max_shift))
            head = delta - tail
            n['out'], n['in'] = round(s['out'] + tail, 3), round(max(s['in'] - head, 0.0), 3)
            n['beatSnap'] = f"{best[1]} {delta:+.3f}s"
            hits += 2 if best[1] == 'beat' else 1
            end = target
        else:
            n['beatSnap'] = 'end (music fades)' if s is edl[-1] else 'OFF'
        n['_cut'] = end
        out.append(n)
        t = end
    return out, hits


def snap(proj, raw, max_shift):
    path = os.path.join(proj, 'edl.json')
    with open(path, encoding='utf-8') as fh:
        edl = json.load(fh)
    with open(os.path.join(proj, 'sources.json'), encoding='utf-8') as fh:
        src = json.load(fh)
    quiet = {c: Quiet(src[c]) for c in {s['clip'] for s in edl}}
    best = None
    for start in np.arange(0, raw['period'], 0.01):          # every music offset within one beat
        g = shifted(raw, float(start))
        res, hits = plan(edl, quiet, g, max_shift)
        if best is None or hits > best[1]:
            best = (res, hits, g)
    res, _, g = best
    os.makedirs(os.path.join(proj, 'work'), exist_ok=True)
    shutil.copy(path, os.path.join(proj, 'work', 'edl.pre-beat.json'))
    for s in res:
        print(f"{s['id']:10s} cut at {s.pop('_cut'):7.3f}s  {s['beatSnap']:>14s}  in {s['in']:.3f} out {s['out']:.3f}")
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    off = sum(1 for s in res[:-1] if s['beatSnap'] == 'OFF')
    print(f"music starts at {g['musicStart']}s of bgm.mp3 (build.py: data-media-start). "
          f"{len(res) - 1 - off}/{len(res) - 1} cuts on the grid. edl.json updated, backup work/edl.pre-beat.json.")
    if off:
        print('OFF cuts: no pause to slide into. Land a graphic hit (punch zoom, image swap) on the nearest beat '
              'instead, or pick a take with a pause there.')
    return g


def check(proj, g):
    with open(os.path.join(proj, 'segments.json'), encoding='utf-8') as fh:
        seg = json.load(fh)
    pts = np.array(sorted(g['beats'] + g['half']))
    bad = 0
    for s in seg[:-1]:                                        # the reel's end is free (music fades)
        c = (s['frame'] + s['frames']) / FPS
        p = pts[np.argmin(abs(pts - c))]
        err = (c - p) * FPS
        bad += abs(err) > 1.5
        print(f"{s['id']:10s} cut {c:7.3f}s  nearest grid {p:7.3f}s  {err:+.1f} frames" + ('   <<' if abs(err) > 1.5 else ''))
    print('all cuts within 1 frame of the grid' if not bad else f'{bad} cut(s) more than 1 frame off')


def main():
    skillenv.utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument('project')
    ap.add_argument('--music', default='assets/music/bgm.mp3')
    ap.add_argument('--bpm', type=float, help='tempo asked for in the music prompt (narrows the search)')
    ap.add_argument('--max-shift', type=float, default=0.15, help='most each end of a segment may move, seconds')
    ap.add_argument('--snap', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    proj = skillenv.path_arg(a.project)
    music = a.music if os.path.isabs(a.music) else os.path.join(proj, a.music)
    out = os.path.join(proj, 'beats.json')
    if a.bpm is None and not a.snap and os.path.isfile(out):  # --check reuses the tempo found by --snap
        with open(out, encoding='utf-8') as fh:
            a.bpm = json.load(fh)['bpm']
    raw = grid(music, a.bpm)
    if a.snap:
        g = snap(proj, raw, a.max_shift)
    elif os.path.isfile(out):                                 # keep the offset chosen by --snap
        with open(out, encoding='utf-8') as fh:
            g = shifted(raw, json.load(fh).get('musicStart', 0))
    else:
        g = shifted(raw, 0)
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(g, fh, indent=1)
    print(f"{g['bpm']} bpm, beat {g['period']}s, {len(g['beats'])} beats, music from {g['musicStart']}s -> beats.json")
    if a.check:
        check(proj, g)


if __name__ == '__main__':
    main()
