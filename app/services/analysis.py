"""Shared analysis service for word/syllable processing."""
import logging
from app.services.tokenizer import segment_syllables
from app.services.tone_analyzer import (
    analyze_syllable, detect_silent_prefix_split, detect_implicit_vowel,
    CONSONANT_CLASSES, TONE_MARKS, _is_consonant
)
from app.services.ipa_service import get_ipa
from app.models.schemas import SyllableAnalysis, ToneInfo

logger = logging.getLogger(__name__)


def analyze_word_syllables(word: str) -> list[SyllableAnalysis]:
    """Analyze a word and return syllable breakdown with tone analysis.

    Handles:
    - Normal syllable segmentation
    - Silent prefix (前引字) detection
    - Implicit vowel (隐含元音) detection
    - Consonant promotion (ห นำ style)
    """
    # Step 1: Segment into syllables
    syllables_raw = segment_syllables(word)
    if not syllables_raw:
        syllables_raw = [word]

    # Step 2: Check for silent prefix pattern (前引字)
    if len(syllables_raw) == 1:
        manual_split = detect_silent_prefix_split(word)
        if manual_split:
            syllables_raw = manual_split

    # Step 3: Check for implicit vowel (隐含元音 -ะ)
    new_syllables = []
    for syl in syllables_raw:
        if len(syl) >= 2:
            implicit_split = detect_implicit_vowel(syl)
            if implicit_split:
                new_syllables.extend(implicit_split)
            else:
                new_syllables.append(syl)
        else:
            new_syllables.append(syl)
    syllables_raw = new_syllables

    # Step 4: Detect consonant promotion (ห นำ style)
    promoted_consonants = set()
    token_chars = list(word)
    for i in range(len(token_chars) - 1):
        if _is_consonant(token_chars[i]) and _is_consonant(token_chars[i + 1]):
            cls_curr = CONSONANT_CLASSES.get(token_chars[i])
            cls_next = CONSONANT_CLASSES.get(token_chars[i + 1])
            if cls_curr == "high" and cls_next == "low":
                promoted_consonants.add(token_chars[i + 1])

    # Step 5: Analyze each syllable
    syllables = []
    for syl in syllables_raw:
        analysis = analyze_syllable(syl, promoted_consonants=promoted_consonants)
        syl_ipa = get_ipa(syl)
        analysis["ipa"] = syl_ipa
        syllables.append(SyllableAnalysis(**analysis))

    return syllables
