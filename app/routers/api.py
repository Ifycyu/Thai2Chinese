"""External API endpoints for Thai word analysis."""
from fastapi import APIRouter, Query, Header
from pydantic import BaseModel
from typing import Optional
from app.services.tokenizer import segment_words, segment_syllables
from app.services.ipa_service import get_ipa
from app.services.tone_analyzer import analyze_syllable, CONSONANT_CLASSES, _is_consonant, detect_silent_prefix_split
from app.services.dictionary import dictionary

router = APIRouter(prefix="/v1", tags=["external-api"])


# ========== Response Models ==========

class ToneInfo(BaseModel):
    tone: str
    tone_cn: str
    tone_number: int
    explanation: str


class SyllableInfo(BaseModel):
    text: str
    ipa: str
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
    word_class: str
    chinese: str
    syllables: list[SyllableInfo]


class AnalyzeResponse(BaseModel):
    sentence: str
    words: list[WordResult]


class DictResponse(BaseModel):
    word: str
    ipa: str
    chinese: str
    word_class: str
    syllables: list[SyllableInfo]
    examples: list
    compounds: list


class SplitResponse(BaseModel):
    sentence: str
    words: list[str]


# ========== API Endpoints ==========

@router.post("/analyze", response_model=AnalyzeResponse,
             summary="完整分析",
             description="输入泰语句子，返回分词、词义、声调分析等完整信息")
async def analyze(
    sentence: str = Query(..., description="泰语句子"),
    x_dict_api: Optional[str] = Header(None, description="词典API地址"),
):
    tokens = segment_words(sentence.strip())
    words = []
    dict_api_url = x_dict_api or ""

    for token in tokens:
        entry = dictionary.get_full_entry(token, api_url=dict_api_url)
        ipa = get_ipa(token)

        syllables_raw = segment_syllables(token)
        if not syllables_raw:
            syllables_raw = [token]

        # Check for silent prefix pattern (前引字)
        if len(syllables_raw) == 1:
            manual_split = detect_silent_prefix_split(token)
            if manual_split:
                syllables_raw = manual_split

        # Detect consonant promotion (ห นำ style)
        promoted_consonants = set()
        token_chars = list(token)
        for i in range(len(token_chars) - 1):
            if _is_consonant(token_chars[i]) and _is_consonant(token_chars[i + 1]):
                cls_curr = CONSONANT_CLASSES.get(token_chars[i])
                cls_next = CONSONANT_CLASSES.get(token_chars[i + 1])
                if cls_curr == "high" and cls_next == "low":
                    promoted_consonants.add(token_chars[i + 1])

        syllables = []
        for syl in syllables_raw:
            a = analyze_syllable(syl, promoted_consonants=promoted_consonants)
            a["ipa"] = get_ipa(syl)
            syllables.append(SyllableInfo(
                text=a["text"],
                ipa=a["ipa"],
                consonant=a["consonant"],
                consonant_class=a["consonant_class"],
                vowel=a["vowel"],
                vowel_length=a["vowel_length"],
                tone_mark=a["tone_mark"],
                final_consonant=a["final_consonant"],
                final_type=a["final_type"],
                tone=ToneInfo(
                    tone=a["tone"],
                    tone_cn=a["tone_cn"],
                    tone_number=a["tone_number"],
                    explanation=a["tone_explanation"],
                ),
                pronunciation_tip=a["pronunciation_tip"],
            ))

        words.append(WordResult(
            word=token,
            ipa=ipa,
            word_class=entry.get("word_class", "未知"),
            chinese=entry.get("chinese", ""),
            syllables=syllables,
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
    entry = dictionary.get_full_entry(word, api_url=dict_api_url)
    ipa = get_ipa(word)

    syllables_raw = segment_syllables(word)
    if not syllables_raw:
        syllables_raw = [word]

    # Check for silent prefix pattern (前引字)
    if len(syllables_raw) == 1:
        manual_split = detect_silent_prefix_split(word)
        if manual_split:
            syllables_raw = manual_split

    # Detect consonant promotion (ห นำ style)
    promoted_consonants = set()
    word_chars = list(word)
    for i in range(len(word_chars) - 1):
        if _is_consonant(word_chars[i]) and _is_consonant(word_chars[i + 1]):
            cls_curr = CONSONANT_CLASSES.get(word_chars[i])
            cls_next = CONSONANT_CLASSES.get(word_chars[i + 1])
            if cls_curr == "high" and cls_next == "low":
                promoted_consonants.add(word_chars[i + 1])

    syllables = []
    for syl in syllables_raw:
        a = analyze_syllable(syl, promoted_consonants=promoted_consonants)
        a["ipa"] = get_ipa(syl)
        syllables.append(SyllableInfo(
            text=a["text"],
            ipa=a["ipa"],
            consonant=a["consonant"],
            consonant_class=a["consonant_class"],
            vowel=a["vowel"],
            vowel_length=a["vowel_length"],
            tone_mark=a["tone_mark"],
            final_consonant=a["final_consonant"],
            final_type=a["final_type"],
            tone=ToneInfo(
                tone=a["tone"],
                tone_cn=a["tone_cn"],
                tone_number=a["tone_number"],
                explanation=a["tone_explanation"],
            ),
            pronunciation_tip=a["pronunciation_tip"],
        ))

    return DictResponse(
        word=word,
        ipa=ipa,
        chinese=entry.get("chinese", ""),
        word_class=entry.get("word_class", "未知"),
        syllables=syllables,
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
    syllables = segment_syllables(word)
    if not syllables:
        syllables = [word]

    results = []
    for syl in syllables:
        a = analyze_syllable(syl)
        results.append({
            "syllable": syl,
            "ipa": get_ipa(syl),
            "consonant": a["consonant"],
            "consonant_class": a["consonant_class"],
            "vowel": a["vowel"],
            "vowel_length": a["vowel_length"],
            "tone_mark": a["tone_mark"],
            "final_consonant": a["final_consonant"],
            "final_type": a["final_type"],
            "tone": a["tone"],
            "tone_cn": a["tone_cn"],
            "tone_number": a["tone_number"],
            "explanation": a["tone_explanation"],
            "pronunciation_tip": a["pronunciation_tip"],
        })

    return {"word": word, "syllables": results}


@router.post("/translate",
             summary="翻译",
             description="将泰语翻译成中文")
async def translate(
    sentence: str = Query(..., description="泰语句子"),
    x_translate_endpoint: Optional[str] = Header(None, description="翻译API端点"),
    x_translate_token: Optional[str] = Header(None, description="认证Token"),
    x_translate_model: Optional[str] = Header(None, description="模型名称"),
):
    from app.routers.translate import do_translate
    import os
    endpoint = x_translate_endpoint or os.environ.get("TRANSLATE_API_ENDPOINT", "")
    token = x_translate_token or os.environ.get("TRANSLATE_AUTH_TOKEN", "")
    model = x_translate_model or os.environ.get("TRANSLATE_MODEL", "mimo-v2.5-pro")
    result = do_translate(sentence, endpoint, token, model)
    return {"original": sentence, "translated": result}
