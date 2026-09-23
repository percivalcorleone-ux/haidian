import json, base64, os, sys
src, clips, out, credit = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
man = json.load(open(os.path.join(clips, 'manifest.json')))
data = {}
for s, beats in enumerate(man['durations']):
    for b, _ in enumerate(beats):
        k = f's{s+1:02d}-b{b}'; data[k] = base64.b64encode(open(os.path.join(clips, k + '.mp3'), 'rb').read()).decode()
blob = json.dumps({'credit': credit, 'durations': man['durations'], 'clips': data}, ensure_ascii=False, separators=(',', ':'))
html = open(src, encoding='utf-8').read()
marker = '<script>\n"use strict";'
assert html.count(marker) == 1
html = html.replace(marker, '<script type="application/json" id="voice-data">' + blob + '</script>\n' + marker)
open(out, 'w', encoding='utf-8').write(html); print(out, round(os.path.getsize(out) / 1e6, 2), 'MB')
