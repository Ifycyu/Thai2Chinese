"""Internal API for word analysis."""
import logging
from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from app.models.schemas import (
    AnalyzeRequest, AnalyzeResponse,
    WordAnalysis, Example, CharacterInfo,
)
from app.services.tokenizer import segment_words
from app.services.ipa_service import get_ipa, get_romanize
from app.services.tone_analyzer import CONSONANT_CLASSES, TONE_MARKS
from app.services.analysis import analyze_word_syllables
from app.services.dictionary import dictionary
from app.utils.url_validator import validate_dict_api_url

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analyze"])

WORD_CLASS_ABBR = {
    "名词": "น.", "动词": "ก.", "形容词": "ว.", "代词": "สรร.",
    "副词": "วิ.", "介词": "บุ.", "连词": "สัน.", "感叹词": "อ.",
    "量词": "ล.", "数词": "วิเศษณ์", "助词": "อนุ.",
}


@router.get("/dict/{word}")
async def dict_lookup(
    word: str,
    x_dict_api: Optional[str] = Header(None),
):
    """Look up a single word in the dictionary."""
    dict_api_url = x_dict_api or ""
    if dict_api_url:
        _, error = validate_dict_api_url(dict_api_url)
        if error:
            raise HTTPException(status_code=400, detail=f"词典API地址不合法: {error}")

    entry = dictionary.get_full_entry(word, api_url=dict_api_url)
    return {
        "word": word,
        "chinese": entry.get("chinese", ""),
        "word_class": entry.get("word_class", "未知"),
        "examples": entry.get("examples", []),
        "compounds": entry.get("compounds", []),
    }


@router.get("/dict-raw/{word}")
async def dict_raw_lookup(
    word: str,
    x_dict_api: Optional[str] = Header(None),
):
    """Look up a word and return the raw dictionary API response."""
    dict_api_url = x_dict_api or ""
    if not dict_api_url:
        raise HTTPException(status_code=400, detail="未配置词典API地址")

    _, error = validate_dict_api_url(dict_api_url)
    if error:
        raise HTTPException(status_code=400, detail=f"词典API地址不合法: {error}")

    result = dictionary.lookup_raw_api(word, api_url=dict_api_url)
    if result is None:
        raise HTTPException(status_code=502, detail="词典API请求失败")

    return result


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    req: AnalyzeRequest,
    x_dict_api: Optional[str] = Header(None),
):
    """Analyze a Thai sentence: segmentation, dictionary, tone analysis."""
    sentence = req.sentence.strip()
    if not sentence:
        return AnalyzeResponse(original="", words=[])
    if len(sentence) > 500:
        return AnalyzeResponse(original=sentence, words=[])

    dict_api_url = x_dict_api or ""
    if dict_api_url:
        _, error = validate_dict_api_url(dict_api_url)
        if error:
            raise HTTPException(status_code=400, detail=f"词典API地址不合法: {error}")
    tokens = segment_words(sentence)
    words = []

    for token in tokens:
        entry = dictionary.get_full_entry(token, api_url=dict_api_url)
        ipa = get_ipa(token)
        rom = get_romanize(token)

        # Use shared analysis service
        syllables = analyze_word_syllables(token)

        # Character decomposition
        characters = []
        for ch in token:
            if ch in CONSONANT_CLASSES:
                characters.append(CharacterInfo(char=ch, role="consonant"))
            elif ch in TONE_MARKS:
                characters.append(CharacterInfo(char=ch, role="tone"))
            elif ch.strip():
                characters.append(CharacterInfo(char=ch, role="vowel"))

        phonetic = "[" + token + "]"

        word_class = entry.get("word_class", "未知")
        word_class_abbr = WORD_CLASS_ABBR.get(word_class, "")

        word_analysis = WordAnalysis(
            word=token,
            ipa=ipa,
            romanize=rom,
            phonetic=phonetic,
            word_class=word_class,
            word_class_abbr=word_class_abbr,
            chinese_def=entry.get("chinese", f"[未收录：{token}]"),
            characters=characters,
            syllables=syllables,
            examples=[Example(**ex) for ex in entry.get("examples", [])],
            compounds=entry.get("compounds", []),
        )
        words.append(word_analysis)

    logger.info(f"Analyzed sentence: {len(words)} words")
    return AnalyzeResponse(original=sentence, words=words)
