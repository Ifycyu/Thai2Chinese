from pydantic import BaseModel
from typing import Optional


class SyllableAnalysis(BaseModel):
    text: str
    ipa: str
    consonant: str
    consonant_class: str  # "mid" | "high" | "low"
    consonant_class_cn: str  # "中辅音" | "高辅音" | "低辅音"
    vowel: str
    vowel_length: str  # "short" | "long"
    tone_mark: Optional[str]
    tone_mark_cn: Optional[str]  # Chinese name of tone mark
    final_consonant: Optional[str]
    final_type: str  # "live" | "dead"
    ho_prefix: bool
    tone: str  # "mid" | "low" | "falling" | "high" | "rising"
    tone_cn: str  # "中声调" | "低声调" | "降声调" | "高声调" | "升声调"
    tone_number: int  # 1-5
    tone_explanation: str
    pronunciation_tip: str  # e.g. "短促", "长音 + 收尾"


class CharacterInfo(BaseModel):
    char: str
    role: str  # "consonant" | "vowel" | "tone" | "final"


class Example(BaseModel):
    thai: str
    chinese: str


class WordAnalysis(BaseModel):
    word: str
    ipa: str
    phonetic: str  # with tone marks like [tà-làat]
    word_class: str
    word_class_abbr: str  # Thai abbreviation like น., ก.
    chinese_def: str
    characters: list[CharacterInfo]  # character decomposition
    syllables: list[SyllableAnalysis]
    examples: list[Example]
    compounds: list[str]


class AnalyzeRequest(BaseModel):
    sentence: str


class AnalyzeResponse(BaseModel):
    original: str
    words: list[WordAnalysis]
