"""Generate one narration clip per lesson beat.
usage: python3 make_voice.py edge|elevenlabs [out_dir]
edge:       free Microsoft neural voice via edge-tts (voice: zh-CN-XiaoxiaoNeural)
elevenlabs: needs ELEVENLABS_API_KEY; optional ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL
Writes <out>/sSS-bB.mp3 and <out>/manifest.json (durations in seconds)."""
import json, os, sys, subprocess, concurrent.futures as cf, urllib.request
from mutagen.mp3 import MP3
prov = sys.argv[1] if len(sys.argv) > 1 else 'edge'
out = sys.argv[2] if len(sys.argv) > 2 else 'clips'
os.makedirs(out, exist_ok=True)
lines = json.load(open(os.path.join(os.path.dirname(__file__) or '.', 'narration.json'), encoding='utf-8'))
jobs = [(s, b, t) for s, beats in enumerate(lines) for b, t in enumerate(beats)]
def edge(path, text):
    env = dict(os.environ, SSL_CERT_FILE=os.environ.get('SSL_CERT_FILE', '/root/.ccr/ca-bundle.crt'))
    cmd = ['edge-tts', '--voice', 'zh-CN-XiaoxiaoNeural', '--rate=-4%', '--text', text, '--write-media', path]
    if os.environ.get('HTTPS_PROXY'): cmd[1:1] = ['--proxy', os.environ['HTTPS_PROXY']]
    subprocess.run(cmd, check=True, env=env, capture_output=True, timeout=120)
def eleven(path, text):
    vid = os.environ.get('ELEVENLABS_VOICE_ID', 'XrExE9yKIg1WjnnlVkGX')
    body = json.dumps({'text': text, 'model_id': os.environ.get('ELEVENLABS_MODEL', 'eleven_multilingual_v2'),
                       'voice_settings': {'stability': .5, 'similarity_boost': .75}}).encode()
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_64', data=body,
                                 headers={'xi-api-key': os.environ['ELEVENLABS_API_KEY'], 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, 'wb') as f: f.write(r.read())
gen = edge if prov == 'edge' else eleven
def run(job):
    s, b, t = job; p = os.path.join(out, f's{s+1:02d}-b{b}.mp3')
    for attempt in range(3):
        try: gen(p, t); return s, b, MP3(p).info.length
        except Exception as e: err = e
    raise RuntimeError(f'{p}: {err}')
with cf.ThreadPoolExecutor(4) as ex: res = list(ex.map(run, jobs))
man = [[0.0] * len(bs) for bs in lines]
for s, b, d in res: man[s][b] = round(d, 3)
json.dump({'provider': prov, 'durations': man}, open(os.path.join(out, 'manifest.json'), 'w'), ensure_ascii=False)
print('clips', len(res), 'total s', round(sum(d for _, _, d in res), 1))
