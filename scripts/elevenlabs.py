#!/usr/bin/env python3
"""ElevenLabs audio for /video-edit: sound effects and background music. Standard library only.

Usage (PY = the skill's Python, see SKILL.md):
  PY elevenlabs.py credits                                   credits left this month
  PY elevenlabs.py sfx-pack                                  the 6 template SFX (whoosh-short, pop, ...) -> template
  PY elevenlabs.py sfx "<prompt>" --seconds 0.6 --out <project>/assets/sfx/<name>.mp3
  PY elevenlabs.py music "<prompt>" --seconds 26 --out <project>/assets/music/bgm.mp3
  Add --dry-run to any command: prints the estimate and the credit check, spends nothing.

Every result is cached in the audio library (config.json "audioLibrary", default <skill>/library): the same request
twice is free the second time. Before every paid call it logs the estimated credit cost and the credits left, and
stops (exit 3) when the call would leave fewer than "minCreditsLeft" (config.json, default 500). The log is also
written to <library>/credits.log.

API key: ELEVENLABS_API_KEY from the environment, else from the .env file named in config.json "envFile", else
<skill>/.env. The key is never printed.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

API = 'https://api.elevenlabs.io'
# credits, from https://elevenlabs.io/pricing (checked 2026-10-19). config.json "elevenlabsRates" overrides them.
RATES = {'sfx_per_generation': 200, 'music_per_minute': 900}
DEFAULT_MIN_LEFT = 500

# the six sounds the template's build.py uses, same names and lengths as the old Pixabay pack
SFX_PACK = {
    'whoosh-short': ('short fast airy whoosh transition, clean, no music', 0.6),
    'pop': ('soft bubbly UI pop, short and clean, no reverb', 0.5),
    'sparkle': ('gentle magical sparkle shimmer chime, light and airy', 1.8),
    'click': ('crisp phone screen tap click, dry, close', 0.5),
    'click-soft': ('soft muted UI click, gentle tap, dry', 0.5),
    'impact-bass-1': ('deep cinematic bass impact hit with short tail', 1.5),
}
TEMPLATE_SFX = os.path.join(skillenv.SKILL_DIR, 'assets', 'template', 'assets', 'sfx')


class Stop(SystemExit):
    pass


# ------------------------------------------------------------------ config, key, library
def config():
    try:
        with open(os.path.join(skillenv.SKILL_DIR, 'config.json'), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def read_env_file(path):
    vals = {}
    try:
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip().lstrip('﻿')   # Notepad may save a byte-order mark
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    vals[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return vals


def env_files(cfg):
    files = []
    if cfg.get('envFile'):
        files.append(skillenv.path_arg(cfg['envFile']))
    files.append(os.path.join(skillenv.SKILL_DIR, '.env'))
    return files


def api_key(cfg):
    key = os.environ.get('ELEVENLABS_API_KEY', '').strip()
    for f in env_files(cfg):
        if key:
            break
        key = read_env_file(f).get('ELEVENLABS_API_KEY', '').strip()
    if not key or key.lower().startswith(('paste', 'your')):
        raise Stop('ElevenLabs key missing. Open this file and paste your key after ELEVENLABS_API_KEY= then save:\n  '
                   + env_files(cfg)[0])
    return key


def library(cfg):
    lib = skillenv.path_arg(cfg.get('audioLibrary') or os.path.join(skillenv.SKILL_DIR, 'library'))
    for sub in ('sfx', 'music'):
        os.makedirs(os.path.join(lib, sub), exist_ok=True)
    return lib


def log(cfg, line):
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'ELEVENLABS {line}', flush=True)
    try:
        with open(os.path.join(library(cfg), 'credits.log'), 'a', encoding='utf-8') as f:
            f.write(f'{stamp}  {line}\n')
    except OSError:
        pass


def index_path(lib):
    return os.path.join(lib, 'index.json')


def remember(lib, entry):
    try:
        with open(index_path(lib), encoding='utf-8') as f:
            idx = json.load(f)
    except (OSError, ValueError):
        idx = []
    idx.append(entry)
    with open(index_path(lib), 'w', encoding='utf-8') as f:
        json.dump(idx, f, indent=1)


def cache_key(*parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode('utf-8')).hexdigest()[:16]


# ------------------------------------------------------------------ HTTP
def request(key, method, path, body=None, headers=None, timeout=300):
    req = urllib.request.Request(API + path, data=body, method=method,
                                 headers={'xi-api-key': key, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', 'replace')[:400]
        if e.code == 401 and 'missing_permissions' in detail:
            try:
                why = json.loads(detail)['detail']['message']
            except (ValueError, KeyError, TypeError):
                why = detail
            raise Stop(f'ElevenLabs key needs more permissions: {why}\n  Fix it at https://elevenlabs.io/app/settings/api-keys '
                       '(edit the key: User = Read, Sound Effects = Access, Music = Access).')
        if e.code == 401:
            raise Stop('ElevenLabs said the key is wrong (401). Check the key in your .env file.')
        raise Stop(f'ElevenLabs error {e.code}: {detail}')
    except urllib.error.URLError as e:
        raise Stop(f'Could not reach ElevenLabs ({e.reason}). Check the internet connection.')


def credits_left(key):
    sub = json.loads(request(key, 'GET', '/v1/user/subscription', timeout=30))
    used, limit = int(sub.get('character_count', 0)), int(sub.get('character_limit', 0))
    return limit - used, limit, sub.get('tier', '?')


SPENT = [0]   # credits this run already spent: ElevenLabs reports the balance with a delay, so subtract them


def guard(cfg, key, what, estimate, dry):
    """Log the estimate and stop when the call would take the account below minCreditsLeft."""
    floor = int(cfg.get('minCreditsLeft', DEFAULT_MIN_LEFT))
    left, limit, tier = credits_left(key)
    left -= SPENT[0]
    log(cfg, f'{what}: estimated cost {estimate} credits | {left} of {limit} left ({tier} plan) | stop below {floor}')
    if left - estimate < floor:
        log(cfg, f'{what}: STOPPED, not enough credits ({left} left, needs {estimate} + {floor} reserve)')
        raise Stop(3)
    if dry:
        log(cfg, f'{what}: dry run, nothing spent')
        raise Stop(0)
    if not what.startswith('sfx-pack'):   # the pack's check covers the calls that follow; they count themselves
        SPENT[0] += estimate


def rates(cfg):
    return {**RATES, **(cfg.get('elevenlabsRates') or {})}


def copy_out(src, out):
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)) or '.', exist_ok=True)
        shutil.copyfile(src, out)
        print(f'OUT {skillenv.shell_path(os.path.abspath(out))}')


# ------------------------------------------------------------------ sound effects
def sfx(cfg, prompt, seconds, out, dry, name=None):
    lib = library(cfg)
    params = {'text': prompt, 'duration_seconds': seconds, 'prompt_influence': 0.5}
    k = cache_key('sfx', params)
    path = os.path.join(lib, 'sfx', f'{skillenv.safe_name(name or "sfx")}-{k}.mp3')
    if os.path.isfile(path):
        log(cfg, f'sfx "{prompt}": cached, 0 credits ({os.path.basename(path)})')
    else:
        key = api_key(cfg)
        guard(cfg, key, f'sfx "{prompt}" ({seconds}s)', rates(cfg)['sfx_per_generation'], dry)
        data = request(key, 'POST', '/v1/sound-generation?output_format=mp3_44100_128',
                       json.dumps(params).encode('utf-8'), {'Content-Type': 'application/json'})
        with open(path, 'wb') as f:
            f.write(data)
        remember(lib, {'type': 'sfx', 'file': os.path.basename(path), 'name': name, **params,
                       'credits_est': rates(cfg)['sfx_per_generation'], 'date': datetime.date.today().isoformat()})
        log(cfg, f'sfx "{prompt}": saved {os.path.basename(path)}')
    copy_out(path, out)
    return path


def sfx_pack(cfg, dry, cached_only=False):
    """The template's six sounds. Cached ones are copied for free first; --cached-only never calls ElevenLabs."""
    lib = library(cfg)
    todo = []
    for n, (p, s) in SFX_PACK.items():
        k = cache_key('sfx', {'text': p, 'duration_seconds': s, 'prompt_influence': 0.5})
        cached = os.path.join(lib, 'sfx', f'{n}-{k}.mp3')
        if os.path.isfile(cached):
            os.makedirs(TEMPLATE_SFX, exist_ok=True)
            shutil.copyfile(cached, os.path.join(TEMPLATE_SFX, n + '.mp3'))
        else:
            todo.append(n)
    if not todo or cached_only:
        print(f'SFX-PACK {6 - len(todo)} cached, {len(todo)} missing')
        return
    key = api_key(cfg)
    guard(cfg, key, f'sfx-pack ({len(todo)} sounds)', len(todo) * rates(cfg)['sfx_per_generation'], dry)
    for n in todo:
        p, s = SFX_PACK[n]
        sfx(cfg, p, s, os.path.join(TEMPLATE_SFX, n + '.mp3'), dry, name=n)


# ------------------------------------------------------------------ music
def ffmpeg():
    return skillenv.tool('ffmpeg')


def music(cfg, prompt, seconds, out, dry, fade=1.5):
    lib = library(cfg)
    ms = max(3000, min(600000, int(round(seconds * 1000))))
    params = {'prompt': prompt, 'music_length_ms': ms, 'force_instrumental': True}
    k = cache_key('music', params)
    path = os.path.join(lib, 'music', f'bgm-{k}.mp3')
    if os.path.isfile(path):
        log(cfg, f'music "{prompt}": cached, 0 credits ({os.path.basename(path)})')
    else:
        key = api_key(cfg)
        est = math.ceil(ms / 60000 * rates(cfg)['music_per_minute'])
        guard(cfg, key, f'music "{prompt}" ({ms / 1000:.1f}s)', est, dry)
        data = request(key, 'POST', '/v1/music', json.dumps(params).encode('utf-8'),
                       {'Content-Type': 'application/json'}, timeout=600)
        with open(path, 'wb') as f:
            f.write(data)
        remember(lib, {'type': 'music', 'file': os.path.basename(path), **params, 'credits_est': est,
                       'date': datetime.date.today().isoformat()})
        log(cfg, f'music "{prompt}": saved {os.path.basename(path)}')
    if out:   # the project copy gets a short fade in and out; the library keeps the raw track
        os.makedirs(os.path.dirname(os.path.abspath(out)) or '.', exist_ok=True)
        r = subprocess.run([ffmpeg(), '-y', '-v', 'error', '-i', path, '-af',
                            f'afade=t=in:d=0.3,afade=t=out:st={max(0, seconds - fade):.3f}:d={fade}',
                            '-t', f'{seconds:.3f}', '-c:a', 'libmp3lame', '-b:a', '192k', out], **skillenv.TEXT)
        if r.returncode:
            raise Stop('ffmpeg could not fade the music:\n' + r.stderr[-800:])
        print(f'OUT {skillenv.shell_path(os.path.abspath(out))}')
    return path


# ------------------------------------------------------------------ main
def main():
    skillenv.utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('credits')
    sub.add_parser('sfx-pack').add_argument('--cached-only', action='store_true')
    p = sub.add_parser('sfx'); p.add_argument('prompt'); p.add_argument('--seconds', type=float, default=1.0)
    p.add_argument('--out'); p.add_argument('--name')
    p = sub.add_parser('music'); p.add_argument('prompt'); p.add_argument('--seconds', type=float, required=True)
    p.add_argument('--out')
    for sp in sub.choices.values():
        sp.add_argument('--dry-run', action='store_true', dest='dry_sub')
    a = ap.parse_args()
    dry = a.dry_run or getattr(a, 'dry_sub', False)
    cfg = config()
    try:
        if a.cmd == 'credits':
            left, limit, tier = credits_left(api_key(cfg))
            log(cfg, f'{left} of {limit} credits left ({tier} plan)')
        elif a.cmd == 'sfx-pack':
            sfx_pack(cfg, dry, a.cached_only)
        elif a.cmd == 'sfx':
            if not 0.5 <= a.seconds <= 30:
                raise Stop('--seconds must be between 0.5 and 30')
            sfx(cfg, a.prompt, a.seconds, a.out, dry, a.name)
        elif a.cmd == 'music':
            music(cfg, a.prompt, a.seconds, a.out, dry)
    except Stop as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            return 2
        return e.code or 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
