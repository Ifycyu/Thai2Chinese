"""Shared analysis service for word/syllable processing."""
import logging
from app.services.tokenizer import segment_syllables
from app.services.tone_analyzer import (
    analyze_syllable, detect_silent_prefix_split, detect_implicit_vowel,
    CONSONANT_CLASSES, TONE_MARKS, _is_consonant, VALID_CLUSTERS
)
from app.services.ipa_service import get_ipa
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
