"""
Simple API usage examples
"""
from encrypt_helper import make_request
import json

BASE_URL = "http://localhost:8082/api/v1"
SECRET = "your-secret-key"  # Same as set in browser settings

# 1. Query dictionary
print("1. Query dictionary")
result = make_request(
    url=f"{BASE_URL}/dict/ตลาด",
    secret=SECRET,
    dict_api="https://xcxapi.seak.online/wxapi//t1/t2cv2?tp=1&userid=xxx&useridkey=xxx"
)
print(f"   ตลาด = {result.get('chinese', '')[:30]}...")

# 2. Analyze sentence
print("\n2. Analyze sentence")
result = make_request(
    url=f"{BASE_URL}/analyze?sentence=ไปเที่ยวตลาด",
    secret=SECRET,
    dict_api="https://xcxapi.seak.online/wxapi//t1/t2cv2?tp=1&userid=xxx&useridkey=xxx"
)
for word in result.get('words', []):
    print(f"   {word['word']}: {word.get('chinese', '')[:20]}...")

# 3. Split sentence
print("\n3. Split sentence")
result = make_request(
    url=f"{BASE_URL}/split?sentence=สวัสดีครับ ผมชื่อสมชาย",
    secret=""
)
print(f"   Words: {result.get('words', [])}")

# 4. Tone analysis
print("\n4. Tone analysis")
result = make_request(
    url=f"{BASE_URL}/tone/สวัสดี",
    secret=""
)
for syl in result.get('syllables', []):
    tone = syl.get('tone', {})
    print(f"   {syl['syllable']}: {tone.get('tone_cn', '')} (第{tone.get('tone_number', '')}调)")

# 5. Translate
print("\n5. Translate")
result = make_request(
    url=f"{BASE_URL}/translate?sentence=สวัสดีครับ",
    secret=SECRET,
    translate_endpoint="https://token-plan-sgp.xiaomimimo.com/anthropic/v1/messages",
    translate_token="tp-so9m2glxxxxxx",
    translate_model="mimo-v2.5-pro"
)
print(f"   {result.get('original', '')} → {result.get('translated', '')}")
