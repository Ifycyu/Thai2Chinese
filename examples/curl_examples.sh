#!/bin/bash
# ThaiWord API Curl Examples
# Note: For encrypted headers, use the Python helper instead

BASE_URL="http://localhost:8082/api/v1"

echo "=== 1. Dictionary Lookup ==="
curl -s "${BASE_URL}/dict/ตลาด" | python -m json.tool

echo -e "\n=== 2. Split Sentence ==="
curl -s -X POST "${BASE_URL}/split?sentence=ไปเที่ยวตลาด" | python -m json.tool

echo -e "\n=== 3. Tone Analysis ==="
curl -s "${BASE_URL}/tone/สวัสดี" | python -m json.tool

echo -e "\n=== 4. Analyze (without encryption) ==="
curl -s -X POST "${BASE_URL}/analyze?sentence=สวัสดี" \
  -H "X-Dict-API: https://xcxapi.seak.online/wxapi//t1/t2cv2?tp=1&userid=xxx&useridkey=xxx" \
  | python -m json.tool

echo -e "\n=== 5. Translate (without encryption) ==="
curl -s -X POST "${BASE_URL}/translate?sentence=สวัสดีครับ" \
  -H "X-Translate-Endpoint: https://token-plan-sgp.xiaomimimo.com/anthropic/v1/messages" \
  -H "X-Translate-Token: tp-so9m2glxxxxxx" \
  -H "X-Translate-Model: mimo-v2.5-pro" \
  | python -m json.tool
