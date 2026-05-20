"""Shared analysis service for word/syllable processing."""
import logging
from app.services.tokenizer import segment_syllables
from app.services.tone_analyzer import (
    analyze_syllable, detect_silent_prefix_split, detect_implicit_vowel,
    CONSONANT_CLASSES, TONE_MARKS, VOWEL_AFTER_CONSONANT, _is_consonant, _is_tone_mark, VALID_CLUSTERS
)
from app.services.ipa_service import get_ipa, get_romanize
from app.models.schemas import SyllableAnalysis

logger = logging.getLogger(__name__)


def _merge_cluster_syllables(syllables: list[str], word: str) -> list[str]:
    """Merge syllables that were incorrectly split inside a consonant cluster.

    When pythainlp splits a cluster like ตร into ตะ+รง, we detect that
    the first two consonants of the original word form a valid cluster
    and merge the syllables back together.
    """
    if len(syllables) < 2:
        return syllables

    # Find first two consonants in the original word
    first_consonant = None
    second_consonant = None
    for ch in word:
        if _is_consonant(ch):
            if first_consonant is None:
                first_consonant = ch
            elif second_consonant is None:
                second_consonant = ch
                break

    if first_consonant and second_consonant:
        cluster = first_consonant + second_consonant
        if cluster in VALID_CLUSTERS:
            # Check if the split happened inside this cluster
            # The first syllable should contain only the first consonant (+ implicit vowel)
            syl0 = syllables[0]
            syl1 = syllables[1]
            # If first syllable is just first_consonant + implicit vowel (ั or ะ), merge
            if syl0 in (first_consonant + "ั", first_consonant + "ะ"):
                merged = first_consonant + syl1
                return [merged] + syllables[2:]

    return syllables


def _split_initial_silent_o(word: str) -> list[str] | None:
    """Split words where อ at the start is NOT silent but pronounced as 'a'.

    When a word starts with อ followed by a consonant, and there's a tone mark
    between that consonant and the vowel, the initial อ is pronounced as a
    separate syllable.

    Example: อร่อย -> ['อะ', 'ร่อย'] (อ pronounced as 'a', tone mark before vowel)
    Example: อยู่ -> None (อ is silent, vowel directly after consonant)
    """
    chars = list(word)
    if len(chars) < 4 or chars[0] != "อ":
        return None

    # Find the second consonant
    second_consonant_idx = -1
    for i in range(1, len(chars)):
        if _is_consonant(chars[i]):
            second_consonant_idx = i
            break

    if second_consonant_idx < 0:
        return None

    # Check if there's a tone mark before the next vowel
    has_tone_before_vowel = False
    for i in range(second_consonant_idx + 1, len(chars)):
        ch = chars[i]
        if _is_tone_mark(ch):
            has_tone_before_vowel = True
            continue
        if ch in VOWEL_AFTER_CONSONANT:
            # Found vowel - if we saw a tone mark before, split
            break
        if _is_consonant(ch):
            break

    if not has_tone_before_vowel:
        return None  # อ is silent (like อยู่)

    # Split: first syllable is อะ, rest is the second syllable
    return ["อะ", word[1:]]


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

    # Step 1.3: Split words where initial อ is pronounced (not silent)
    if len(syllables_raw) == 1:
        initial_split = _split_initial_silent_o(word)
        if initial_split:
            syllables_raw = initial_split

    # Step 1.5: Merge syllables split inside consonant clusters
    syllables_raw = _merge_cluster_syllables(syllables_raw, word)

    # Step 2: Check for silent prefix pattern (前引字) in each syllable
    expanded = []
    for syl in syllables_raw:
        if len(syl) >= 2:
            prefix_split = detect_silent_prefix_split(syl)
            if prefix_split:
                expanded.extend(prefix_split)
            else:
                expanded.append(syl)
        else:
            expanded.append(syl)
    syllables_raw = expanded

    # Step 3: Check for implicit vowel (隐含元音 -ะ) only on single-syllable words
    # Don't re-split syllables that pythainlp already segmented correctly
    if len(syllables_raw) == 1 and len(syllables_raw[0]) >= 3:
        implicit_split = detect_implicit_vowel(syllables_raw[0])
        if implicit_split:
            syllables_raw = implicit_split

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
        analysis["ipa"] = get_ipa(syl)
        analysis["romanize"] = get_romanize(syl)
        syllables.append(SyllableAnalysis(**analysis))

    return syllables
