import urllib.request
import urllib.parse
import json

q = """[out:json][timeout:15];
(
  way["waterway"="river"](36.33,127.33,36.46,127.49);
  relation["waterway"="river"](36.33,127.33,36.46,127.49);
  way["natural"="water"](36.33,127.33,36.46,127.49);
);
out geom;
"""
url = 'https://overpass-api.de/api/interpreter'
data = urllib.parse.urlencode({'data': q}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'User-Agent': 'CitiesSim/1.0'})
try:
    with urllib.request.urlopen(req, timeout=12) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print('Overpass elements found:', len(res.get('elements', [])))
        for el in res.get('elements', [])[:5]:
            print(el.get('tags', {}).get('name'), el.get('type'), len(el.get('geometry', [])))
except Exception as e:
    print('Overpass error:', e)
