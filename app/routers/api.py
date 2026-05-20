"""External API endpoints for third-party integration."""
import logging
from fastapi import APIRouter, Query, Header, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.tokenizer import segment_words
from app.services.ipa_service import get_ipa, get_romanize
from app.services.tone_analyzer import analyze_syllable
from app.services.analysis import analyze_word_syllables
from app.services.dictionary import dictionary
from app.utils.auth import get_api_key
from app.utils.url_validator import validate_dict_api_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["external-api"], dependencies=[Depends(get_api_key)])


# ========== Response Models ==========

class ToneInfo(BaseModel):
    tone: str
    tone_cn: str
    tone_number: int
    explanation: str


class SyllableInfo(BaseModel):
    text: str
    ipa: str
    romanize: str
    consonant: str
    consonant_class: str
    vowel: str
    vowel_length: str
    tone_mark: Optional[str]
    final_consonant: Optional[str]
    final_type: str
    tone: ToneInfo
    pronunciation_tip: str


class WordResult(BaseModel):
    word: str
    ipa: str
    romanize: str
    word_class: str
    chinese: str
    syllables: list[SyllableInfo]


class AnalyzeResponse(BaseModel):
    sentence: str
    words: list[WordResult]


class DictResponse(BaseModel):
    word: str
    ipa: str
    romanize: str
    chinese: str
    word_class: str
    syllables: list[SyllableInfo]
    examples: list
    compounds: list


class SplitResponse(BaseModel):
    sentence: str
    words: list[str]


# ========== Helper ==========

def _syllable_to_info(syl) -> SyllableInfo:
    """Convert SyllableAnalysis to SyllableInfo."""
    return SyllableInfo(
        text=syl.text,
        ipa=syl.ipa,
        romanize=syl.romanize,
        consonant=syl.consonant,
        consonant_class=syl.consonant_class,
        vowel=syl.vowel,
        vowel_length=syl.vowel_length,
        tone_mark=syl.tone_mark,
        final_consonant=syl.final_consonant,
        final_type=syl.final_type,
        tone=ToneInfo(
            tone=syl.tone,
            tone_cn=syl.tone_cn,
            tone_number=syl.tone_number,
            explanation=syl.tone_explanation,
        ),
        pronunciation_tip=syl.pronunciation_tip,
    )


# ========== API Endpoints ==========

@router.post("/analyze", response_model=AnalyzeResponse,
             summary="完整分析",
             description="输入泰语句子，返回分词、词义、声调分析等完整信息")
async def analyze(
    sentence: str = Query(..., description="泰语句子"),
    x_dict_api: Optional[str] = Header(None, description="词典API地址"),
):
    dict_api_url = x_dict_api or ""
    if dict_api_url:
        _, error = validate_dict_api_url(dict_api_url)
        if error:
            raise HTTPException(status_code=400, detail=f"词典API地址不合法: {error}")
    tokens = segment_words(sentence.strip())
    words = []

    for token in tokens:
        entry = dictionary.get_full_entry(token, api_url=dict_api_url)
        ipa = get_ipa(token)
        rom = get_romanize(token)
        syllables = analyze_word_syllables(token)

        words.append(WordResult(
            word=token,
            ipa=ipa,
            romanize=rom,
            word_class=entry.get("word_class", "未知"),
            chinese=entry.get("chinese", ""),
            syllables=[_syllable_to_info(s) for s in syllables],
        ))

    return AnalyzeResponse(sentence=sentence.strip(), words=words)


@router.get("/dict/{word}", response_model=DictResponse,
            summary="词典查询",
            description="查询单个泰语单词，返回释义和声调分析")
async def dict_lookup(
    word: str,
    x_dict_api: Optional[str] = Header(None, description="词典API地址"),
):
    dict_api_url = x_dict_api or ""
    if dict_api_url:
        _, error = validate_dict_api_url(dict_api_url)
        if error:
            raise HTTPException(status_code=400, detail=f"词典API地址不合法: {error}")
    entry = dictionary.get_full_entry(word, api_url=dict_api_url)
    ipa = get_ipa(word)
    rom = get_romanize(word)
    syllables = analyze_word_syllables(word)

    return DictResponse(
        word=word,
        ipa=ipa,
        romanize=rom,
        chinese=entry.get("chinese", ""),
        word_class=entry.get("word_class", "未知"),
        syllables=[_syllable_to_info(s) for s in syllables],
        examples=entry.get("examples", []),
        compounds=entry.get("compounds", []),
    )


@router.post("/split", response_model=SplitResponse,
             summary="分词",
             description="将泰语句子拆分为单词列表")
async def split(sentence: str = Query(..., description="泰语句子")):
    tokens = segment_words(sentence.strip())
    return SplitResponse(sentence=sentence.strip(), words=tokens)


@router.get("/tone/{word}",
            summary="声调分析",
            description="分析泰语单词的声调（自动拆分音节）")
async def tone(word: str):
    syllables = analyze_word_syllables(word)
    results = []
    for syl in syllables:
        results.append({
            "syllable": syl.text,
            "ipa": syl.ipa,
            "romanize": syl.romanize,
            "consonant": syl.consonant,
            "consonant_class": syl.consonant_class,
            "vowel": syl.vowel,
            "vowel_length": syl.vowel_length,
            "tone_mark": syl.tone_mark,
            "final_consonant": syl.final_consonant,
            "final_type": syl.final_type,
            "tone": syl.tone,
            "tone_cn": syl.tone_cn,
            "tone_number": syl.tone_number,
            "explanation": syl.tone_explanation,
            "pronunciation_tip": syl.pronunciation_tip,
        })
    return {"word": word, "syllables": results}


@router.post("/translate",
             summary="翻译",
             description="将泰语翻译成中文")
async def translate(
    sentence: str = Query(..., description="泰语句子"),
    x_translate_endpoint: Optional[str] = Header(None),
    x_translate_token: Optional[str] = Header(None),
    x_translate_model: Optional[str] = Header(None),
):
    from app.routers.translate import do_translate
    import os
    endpoint = x_translate_endpoint or os.environ.get("TRANSLATE_API_ENDPOINT", "")
    token = x_translate_token or os.environ.get("TRANSLATE_AUTH_TOKEN", "")
    model = x_translate_model or os.environ.get("TRANSLATE_MODEL", "mimo-v2.5-pro")
    result = await do_translate(sentence, endpoint, token, model)
    return {"original": sentence, "translated": result}
