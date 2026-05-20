# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pythainlp.transliterate import romanize, transliterate

words = ["สวัสดี", "ครับ", "ขอบคุณ", "กินข้าว", "ประเทศไทย"]

print("=== pythainlp 发音示例 ===\n")

for word in words:
    print(f"泰文: {word}")
    print(f"  罗马字: {romanize(word)}")
    try:
        ipa = transliterate(word, engine='thaig2p')
        print(f"  IPA: {ipa}")
    except Exception as e:
        print(f"  IPA: (错误: {e})")
    print()
