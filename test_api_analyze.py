import urllib.request, json

req = urllib.request.Request('http://127.0.0.1:8082/api/analyze',
    data=json.dumps({'sentence': 'ไปเที่ยว'}).encode(),
    headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read())
    with open('analyze_result.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("OK")
except Exception as e:
    print(f"Error: {e}")
