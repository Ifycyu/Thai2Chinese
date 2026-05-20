# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("           PyThaiNLP 完整功能示例")
print("=" * 60)

# 1. 分词 (Word Segmentation)
print("\n【1】分词 (Word Segmentation)")
print("-" * 40)
from pythainlp.tokenize import word_tokenize

text = "สวัสดีครับ ผมชื่อโอ๊ต ยินดีที่ได้รู้จัก"
print(f"原文: {text}")
tokens = word_tokenize(text, engine="newmm")
print(f"分词结果: {tokens}")

# 2. 句子分割 (Sentence Segmentation)
print("\n【2】句子分割 (Sentence Segmentation)")
print("-" * 40)
from pythainlp.tokenize import sent_tokenize

text = "สวัสดีครับ ผมชื่อโอ๊ต ยินดีที่ได้รู้จัก วันนี้อากาศดีมาก"
sentences = sent_tokenize(text)
print(f"原文: {text}")
print(f"句子: {sentences}")

# 3. 罗马字转写 (Romanization)
print("\n【3】罗马字转写 (Romanization)")
print("-" * 40)
from pythainlp.transliterate import romanize

words = ["สวัสดี", "ครับ", "ขอบคุณ", "กรุงเทพ"]
for word in words:
    print(f"  {word} -> {romanize(word)}")

# 4. IPA 音标 (Phonetic Transcription)
print("\n【4】IPA 音标 (Phonetic Transcription)")
print("-" * 40)
from pythainlp.transliterate import transliterate

words = ["สวัสดี", "ครับ", "ขอบคุณ"]
for word in words:
    ipa = transliterate(word, engine="thaig2p")
    print(f"  {word} -> {ipa}")

# 5. 词性标注 (Part-of-Speech Tagging)
print("\n【5】词性标注 (Part-of-Speech Tagging)")
print("-" * 40)
from pythainlp.tag import pos_tag

text = "ผมชอบกินข้าว"
tokens = word_tokenize(text)
tags = pos_tag(tokens)
print(f"原文: {text}")
print(f"分词: {tokens}")
print(f"词性: {tags}")

# 6. 命名实体识别 (Named Entity Recognition)
print("\n【6】命名实体识别 (Named Entity Recognition)")
print("-" * 40)
from pythainlp.tag import NER

ner = NER("thainer")
text = "นายโอ๊ตไปกรุงเทพเมื่อวาน"
result = ner.tag(text)
print(f"原文: {text}")
print(f"实体: {result}")

# 7. 拼写检查 (Spell Checking)
print("\n【7】拼写检查 (Spell Checking)")
print("-" * 40)
from pythainlp.spell import correct

words = ["ส่วัสดี", "ครัีบ", "ขอบคุุณ"]
for word in words:
    corrected = correct(word)
    print(f"  {word} -> {corrected}")

# 8. 停用词 (Stopwords)
print("\n【8】停用词 (Stopwords)")
print("-" * 40)
from pythainlp.corpus import thai_stopwords

stopwords = thai_stopwords()
print(f"泰语停用词数量: {len(stopwords)}")
print(f"示例: {list(stopwords)[:10]}")

# 9. 数字转泰文 (Number to Thai Text)
print("\n【9】数字转泰文 (Number to Thai Text)")
print("-" * 40)
from pythainlp.util import bahttext, num_to_thaiword

numbers = [123, 4567, 100000]
for num in numbers:
    thai_text = num_to_thaiword(num)
    baht = bahttext(num)
    print(f"  {num} -> {thai_text}")
    print(f"         -> {baht}")

# 10. 泰文转数字 (Thai Text to Number)
print("\n【10】泰文转数字 (Thai Text to Number)")
print("-" * 40)
from pythainlp.util import thaiword_to_num

texts = ["หนึ่ง", "สิบ", "ร้อย", "พัน"]
for text in texts:
    num = thaiword_to_num(text)
    print(f"  {text} -> {num}")

# 11. 文本规范化 (Text Normalization)
print("\n【11】文本规范化 (Text Normalization)")
print("-" * 40)
from pythainlp.util import normalize

text = "สวัสดี   ครับ"  # 多余空格
normalized = normalize(text)
print(f"原文: '{text}'")
print(f"规范化: '{normalized}'")

# 12. 泰文字符检测 (Thai Character Detection)
print("\n【12】泰文字符检测 (Thai Character Detection)")
print("-" * 40)
from pythainlp.util import isthaichar, isthai

chars = ["ก", "a", "1", "สวัสดี"]
for char in chars:
    is_thai_char = isthaichar(char) if len(char) == 1 else "N/A"
    is_thai = isthai(char)
    print(f"  '{char}' -> isthaichar: {is_thai_char}, isthai: {is_thai}")

# 13. 泰文排序 (Thai Sorting)
print("\n【13】泰文排序 (Thai Sorting)")
print("-" * 40)
try:
    from pythainlp.util import thai_sort

    words = ["กล้วย", "กิน", "กา", "กาง"]
    sorted_words = thai_sort(words)
    print(f"原文: {words}")
    print(f"排序: {sorted_words}")
except ImportError:
    print("  (thai_sort 函数在当前版本中不可用)")

# 14. 音节分割 (Syllable Segmentation)
print("\n【14】音节分割 (Syllable Segmentation)")
print("-" * 40)
from pythainlp.tokenize import syllable_tokenize

text = "สวัสดีครับ"
syllables = syllable_tokenize(text)
print(f"原文: {text}")
print(f"音节: {syllables}")

# 15. 关键词提取 (Keyword Extraction)
print("\n【15】关键词提取 (Keyword Extraction)")
print("-" * 40)
from pythainlp.summarize import summarize

text = """กรุงเทพมหานครเป็นเมืองหลวงและเมืองที่มีประชากรมากที่สุดของประเทศไทย
เป็นศูนย์กลางการปกครอง การศึกษา การคมนาคม การเงินการธนาคาร การพาณิชย์
การสื่อสาร และความเจริญของประเทศ"""
summary = summarize(text, n=2)
print(f"原文: {text[:50]}...")
print(f"关键词: {summary}")

# 16. 词向量 (Word Vector)
print("\n【16】词向量 (Word Vector)")
print("-" * 40)
try:
    from pythainlp.word_vector import thai2vec

    word = "กรุงเทพ"
    vector = thai2vec(word)
    print(f"  '{word}' 的词向量维度: {vector.shape}")
    print(f"  前5个值: {vector[:5]}")
except Exception as e:
    print(f"  (需要下载词向量模型: {e})")

# 17. 文本分类 (Text Classification)
print("\n【17】文本分类 (Text Classification)")
print("-" * 40)
print("  pythainlp 支持多种文本分类任务，包括:")
print("  - 情感分析")
print("  - 主题分类")
print("  - 语言检测")

# 18. 音标转换 (Phoneme Conversion)
print("\n【18】音标转换 (Phoneme Conversion)")
print("-" * 40)
from pythainlp.transliterate import transliterate

text = "สวัสดี"
try:
    ipa = transliterate(text, engine="thaig2p")
    print(f"  {text} -> {ipa}")
except Exception as e:
    print(f"  (需要额外模型: {e})")

print("\n" + "=" * 60)
print("           示例完成")
print("=" * 60)
