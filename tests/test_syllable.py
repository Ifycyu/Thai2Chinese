"""Syllable segmentation regression tests.

Run: python -m pytest tests/test_syllable.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "venv", "Lib", "site-packages"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.services.analysis import analyze_word_syllables

# (word, expected_syllables, expected_count)
# Expected syllables are joined with '+'
SYLLABLE_TESTS = [
    # === 隐含元音 (implicit vowel สะ) ===
    ("สวัสดี",     "สะ+วัส+ดี",       3),  # ส has implicit vowel
    ("สนาม",       "สะ+นาม",          2),  # ส has implicit vowel
    ("สนุก",       "สะ+นุก",          2),  # ส has implicit vowel
    ("สว่าง",      "สะ+ว่าง",         2),  # ส has implicit vowel, tone mark breaks cluster
    ("ขนม",        "ขะ+นม",           2),  # ข has implicit vowel
    ("ถนน",        "ถะ+นน",           2),  # ถ has implicit vowel
    ("ขมอง",       "ขะ+มอง",          2),  # ข has implicit vowel

    # === 辅音簇 (consonant clusters, should NOT split) ===
    ("ประกอบ",     "ประ+กอบ",         2),  # ปร cluster intact
    ("ตำรวจ",      "ตำ+รวจ",          2),  # ตร cluster intact
    ("กรุงเทพ",    "กรุง+เทพ",        2),  # กว cluster intact
    ("ครับ",        "ครับ",             1),  # คร cluster intact, ั is cluster vowel
    ("ไป",          "ไป",               1),  # no split needed

    # === 单音节词 ===
    ("สด",          "สด",               1),
    ("แฟน",         "แฟน",              1),
    ("เด็ก",        "เด็ก",             1),
    ("เรียน",       "เรียน",            1),
    ("กิน",         "กิน",              1),
    ("มาก",         "มาก",              1),
    ("สวย",         "สวย",              1),
    ("ดี",          "ดี",               1),
    ("ข้าว",        "ข้าว",             1),
    ("ผม",          "ผม",               1),
    ("รัก",         "รัก",              1),
    ("คุณ",         "คุณ",              1),

    # === 多音节词 ===
    ("หนังสือ",     "หนัง+สือ",         2),
    ("มหาวิทยาลัย",  "มหา+วิท+ยา+ลัย",  4),
    ("โรงเรียน",    "โรง+เรียน",        2),
    ("ภาษาไทย",     "ภา+ษา+ไทย",        3),

    # === อ silent prefix ===
    ("อร่อย",       "อะ+ร่อย",          2),  # อ pronounced as อะ
    ("อยู่",        "อยู่",             1),  # อ is silent

    # === 辅音簇 ตร ===
    ("ตรง",         "ตรง",              1),  # ตร cluster intact

    # === 辅音簇 จร ===
    ("จริง",        "จริง",             1),  # จร cluster intact

    # === 辅音簇 ขว ===
    ("ขวา",         "ขวา",              1),  # ขว cluster intact

    # === อ as vowel after consonant ===
    ("คอน",         "คอน",              1),  # อ is vowel -อ, not consonant

    # === ห นำ with tone mark ===
    ("เห็น",        "เห็น",             1),  # ห นำ, tone mark doesn't break
    ("หน่อย",       "หน่อย",            1),  # ห นำ, tone mark doesn't break

    # === อ นำ ===
    ("อีก",         "อีก",              1),  # อ นำ

    # === multi-syllable ===
    ("กังวล",       "กัง+วล",           2),

    # === single syllable ===
    ("ตก",          "ตก",               1),
    ("สาย",         "สาย",              1),

    # === ห นำ ===
    ("ห้องน้ำ",     "ห้อง+น้ำ",         2),  # ห นำ, two syllables
    ("เหรอ",        "เหรอ",             1),  # ห นำ, อ as vowel

    # === 复合词 ===
    ("สวัสดีครับ",  "สะ+วัส+ดี+ครับ",  4),  # multi-word
]


@pytest.mark.parametrize("word, expected_syls, expected_count",
                         SYLLABLE_TESTS,
                         ids=[t[0] for t in SYLLABLE_TESTS])
def test_syllable_segmentation(word, expected_syls, expected_count):
    syllables = analyze_word_syllables(word)
    actual_syls = "+".join(s.text for s in syllables)
    assert len(syllables) == expected_count, \
        f"{word}: expected {expected_count} syllables ({expected_syls}), got {len(syllables)} ({actual_syls})"
    assert actual_syls == expected_syls, \
        f"{word}: expected [{expected_syls}], got [{actual_syls}]"
