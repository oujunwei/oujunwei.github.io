import urllib.request
import ssl
import re
import html

url = 'https://scholar.google.com/citations?hl=zh-CN&user=if0PW_cAAAAJ'
headers = {'User-Agent': 'Mozilla/5.0'}
ctx = ssl.create_default_context()
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
    data = r.read().decode('utf-8', errors='ignore')
matches = re.findall(r'<a[^>]+class="gsc_a_at"[^>]*>(.*?)</a>', data)
for i, t in enumerate(matches[:20], 1):
    print(f'{i}. {html.unescape(t)}')
