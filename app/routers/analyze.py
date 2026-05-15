from fastapi import APIRouter, Header
from typing import Optional
from app.models.schemas import (
    AnalyzeRequest, AnalyzeResponse,
    WordAnalysis, SyllableAnalysis, Example, CharacterInfo,
)
from app.services.tokenizer import segment_words, segment_syllables
from app.services.ipa_service import get_ipa
from app.services.tone_analyzer import analyze_syllable, CONSONANT_CLASSES, TONE_MARKS, _is_consonant, detect_silent_prefix_split
from app.services.dictionary import dictionary

router = APIRouter(tags=["analyze"])


@router.get("/dict/{word}")
async def dict_lookup(
    word: str,
    x_dict_api: Optional[str] = Header(None),
):
    """Look up a single word in the dictionary."""
    entry = dictionary.get_full_entry(word, api_url=x_dict_api or "")
    return {
        "word": word,
        "chinese": entry.get("chinese", ""),
        "word_class": entry.get("word_class", "未知"),
        "examples": entry.get("examples", []),
        "compounds": entry.get("compounds", []),
    }


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    req: AnalyzeRequest,
    x_dict_api: Optional[str] = Header(None),
):
    sentence = req.sentence.strip()
    if not sentence:
        return AnalyzeResponse(original="", words=[])

    dict_api_url = x_dict_api or ""
    tokens = segment_words(sentence)
    words = []

    for token in tokens:
        # Dictionary lookup
        entry = dictionary.get_full_entry(token, api_url=dict_api_url)

        # IPA for the whole word
        ipa = get_ipa(token)

        # Syllable segmentation
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
            analysis = analyze_syllable(syl, promoted_consonants=promoted_consonants)
            # Get per-syllable IPA
            syl_ipa = get_ipa(syl)
            analysis["ipa"] = syl_ipa
            syllables.append(SyllableAnalysis(**analysis))

        # Character decomposition
        characters = []
        for ch in token:
            if ch in CONSONANT_CLASSES:
                characters.append(CharacterInfo(char=ch, role="consonant"))
            elif ch in TONE_MARKS:
                characters.append(CharacterInfo(char=ch, role="tone"))
            elif ch.strip():
                characters.append(CharacterInfo(char=ch, role="vowel"))

        # Phonetic display
        phonetic = "[" + token + "]"

        # Word class abbreviation
        word_class_abbr_map = {
            "名词": "น.", "动词": "ก.", "形容词": "ว.", "代词": "สรร.",
            "副词": "วิ.", "介词": "บุ.", "连词": "สัน.", "感叹词": "อ.",
            "量词": "ล.", "数词": "วิเศษณ์", "助词": "อนุ.",
        }
        word_class = entry.get("word_class", "未知")
        word_class_abbr = word_class_abbr_map.get(word_class, "")

        word_analysis = WordAnalysis(
            word=token,
            ipa=ipa,
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

    return AnalyzeResponse(original=sentence, words=words)
