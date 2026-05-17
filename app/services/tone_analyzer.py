"""Thai tone analysis engine with Chinese explanations.

Determines the tone of each syllable by analyzing:
- Consonant class (mid/high/low)
- Vowel length (short/long)
- Tone mark (่ ้ ๊ ๋)
- Final consonant type (live/dead syllable)
- ห prefix promotion
"""

# 44 Thai consonants mapped to their class
CONSONANT_CLASSES = {
    # Mid class (เสียงกลาง) - 9
    "ก": "mid", "จ": "mid", "ฎ": "mid", "ฏ": "mid",
    "ด": "mid", "ต": "mid", "บ": "mid", "ป": "mid", "อ": "mid",
    # High class (เสียงสูง) - 10
    "ข": "high", "ฃ": "high", "ฉ": "high", "ถ": "high",
    "ผ": "high", "ฝ": "high", "ศ": "high", "ษ": "high",
    "ส": "high", "ห": "high",
    # Low class (เสียงต่ำ) - 25
    "ค": "low", "ฅ": "low", "ฆ": "low", "ง": "low",
    "ช": "low", "ซ": "low", "ฌ": "low", "ญ": "low",
    "ฑ": "low", "ฒ": "low", "ณ": "low", "ท": "low",
    "ธ": "low", "น": "low", "พ": "low", "ฟ": "low",
    "ภ": "low", "ม": "low", "ย": "low", "ร": "low",
    "ล": "low", "ว": "low", "ฬ": "low", "ฮ": "low",
}

TONE_MARKS = {
    "่": "mai_ek",       # ่
    "้": "mai_tho",      # ้
    "๊": "mai_tri",      # ๊
    "๋": "mai_jattawa",  # ๋
}

# Sonorant finals (live syllable)
LIVE_FINALS = set("งนมยวลญณฬ")
# Stop finals (dead syllable)
DEAD_FINALS = set("กดปบต")

# Short vowels in Thai script
SHORT_VOWELS = set("ิุะั็")
# Long vowels in Thai script
LONG_VOWELS = set("าีูเแโใไอ")

CLASS_CN = {"mid": "中辅音", "high": "高辅音", "low": "低辅音"}
TONE_CN = {
    "mid": "中声调", "low": "低声调", "falling": "降声调",
    "high": "高声调", "rising": "升声调",
}
# Thai tone numbers: สามัญ=1, เอก=2, โท=3, ตรี=4, จัตวา=5
TONE_NUMBER = {
    "mid": 1, "low": 2, "falling": 3, "high": 4, "rising": 5,
}
# Tone mark fixed numbers: ่=2, ้=3, ๊=4, ๋=5
TONE_MARK_NUMBER = {
    "mai_ek": 2, "mai_tho": 3, "mai_tri": 4, "mai_jattawa": 5,
}
MARK_CN = {
    "mai_ek": "ไม้เอก(่)", "mai_tho": "ไม้โท(้)",
    "mai_tri": "ไม้ตรี(๊)", "mai_jattawa": "ไม้จัตวา(๋)",
}

# Tone rule lookup: (consonant_class, tone_mark, final_type) -> tone
TONE_RULES = {
    # No tone mark
    ("mid", None, "live"): "mid",
    ("mid", None, "dead"): "low",
    ("high", None, "live"): "rising",
    ("high", None, "dead"): "low",
    ("low", None, "live"): "mid",
    ("low", None, "dead"): "high",
    # Mai Ek (่)
    ("mid", "mai_ek", "live"): "low",
    ("mid", "mai_ek", "dead"): "low",
    ("high", "mai_ek", "live"): "low",
    ("high", "mai_ek", "dead"): "low",
    ("low", "mai_ek", "live"): "falling",
    ("low", "mai_ek", "dead"): "falling",
    # Mai Tho (้)
    ("mid", "mai_tho", "live"): "falling",
    ("mid", "mai_tho", "dead"): "falling",
    ("high", "mai_tho", "live"): "falling",
    ("high", "mai_tho", "dead"): "falling",
    ("low", "mai_tho", "live"): "high",
    ("low", "mai_tho", "dead"): "high",
    # Mai Tri (๊)
    ("mid", "mai_tri", "live"): "high",
    ("mid", "mai_tri", "dead"): "high",
    ("low", "mai_tri", "live"): "high",
    ("low", "mai_tri", "dead"): "high",
    # Mai Jattawa (๋)
    ("mid", "mai_jattawa", "live"): "rising",
    ("mid", "mai_jattawa", "dead"): "rising",
    ("low", "mai_jattawa", "live"): "rising",
    ("low", "mai_jattawa", "dead"): "rising",
}

# Vowel pattern detection: ordered by specificity (longer patterns first)
# Each entry: (pattern_chars_set, vowel_name, length)
# length: "short", "long", "special" (พิเศษ)
# We detect vowels by looking at characters around the initial consonant
# Use "-" to represent vowel position instead of "อ" carrier
VOWEL_AFTER_CONSONANT = {
    # These are vowel marks that appear after the consonant
    "ะ": ("-ะ", "short"),      # ะ - short a
    "ั": ("-ั", "short"),      #ั  - short a (mai han-akat)
    "า": ("-า", "long"),       # า - long a
    "ำ": ("-ำ", "special"),    # ำ - am (special)
    "ิ": ("-ิ", "short"),      #ิ  - short i
    "ี": ("-ี", "long"),       #ี  - long i
    "ึ": ("-ึ", "short"),      #ึ  - short ue
    "ื": ("-ื", "long"),       #ื  - long ue
    "ุ": ("-ุ", "short"),      #ุ  - short u (phinthu)
    "ู": ("-ู", "long"),       #ู  - long u
    "เ": ("เ-", "long"),       # เ - e (leading vowel)
    "แ": ("แ-", "long"),       # แ - ae (leading vowel)
    "โ": ("โ-", "long"),       # โ - o (leading vowel)
    "ใ": ("ใ-", "special"),    # ใ - ai (special)
    "ไ": ("ไ-", "special"),    # ไ - ai (special)
    "ๅ": ("-ๅ", "long"),       # ๅ - long y
}

VOWEL_ABOVE = {"ั", "ิ", "ี", "ึ", "ื"}
VOWEL_BELOW = {"ุ", "ู"}


def _is_consonant(ch: str) -> bool:
    return ch in CONSONANT_CLASSES


def _is_vowel(ch: str) -> bool:
    return ch in VOWEL_AFTER_CONSONANT


def _is_tone_mark(ch: str) -> bool:
    return ch in TONE_MARKS


def _is_diacritic(ch: str) -> bool:
    """Check if character is a vowel or tone mark."""
    return _is_vowel(ch) or _is_tone_mark(ch) or ch == "ํ"  # ํ nikkhahit


def detect_silent_prefix_split(word: str) -> list[str] | None:
    """Detect if a word has a silent high-class prefix (前引字) and split into syllables.

    Rules:
    - ห as prefix: silent, promotes following consonant, NO separate syllable
    - Other high-class consonants (ส, ข, etc.): split only if NO vowel between them

    Example: สนุก → [สะ, นุk] (ส is silent prefix, no vowel between ส and น)
    Example: ฉัน → [ฉัน] (ฉ is initial consonant, ั vowel between ฉ and น)
    Example: หมา → [หมา] (ห is silent prefix, no split)

    Returns: List of syllables if pattern found, None otherwise.
    """
    chars = list(word)
    if len(chars) < 3:
        return None

    # Find first two consonants and check for vowels between them
    first_consonant = None
    first_idx = -1
    second_consonant = None
    second_idx = -1
    has_vowel_between = False

    for i, ch in enumerate(chars):
        if _is_consonant(ch):
            if first_consonant is None:
                first_consonant = ch
                first_idx = i
            elif second_consonant is None:
                second_consonant = ch
                second_idx = i
                break
        elif ch in VOWEL_AFTER_CONSONANT or _is_tone_mark(ch):
            if first_consonant is not None and second_consonant is None:
                has_vowel_between = True

    if first_consonant is None or second_consonant is None:
        return None

    # If there's a vowel between the consonants, it's not a silent prefix
    # It's a normal syllable with initial + vowel + final
    if has_vowel_between:
        return None

    # Check if first is high-class and second is low-class
    cls_first = CONSONANT_CLASSES.get(first_consonant)
    cls_second = CONSONANT_CLASSES.get(second_consonant)

    if cls_first == "high" and cls_second == "low":
        # ห as prefix: silent, no separate syllable
        if first_consonant == "ห":
            return None
        # Other high-class consonants with no vowel between: split
        syl1 = first_consonant + "ะ"
        syl2 = "".join(chars[first_idx + 1:])
        return [syl1, syl2]

    return None


# Valid consonant clusters in Thai
VALID_CLUSTERS = {
    "กร", "กล", "กว", "ขร", "ขล", "ขว", "คร", "คล", "คว",
    "ปร", "ปล", "พร", "พล", "ทร", "ศร", "ศล", "ศว",
    "สร", "สก", "สต", "สบ", "สพ", "สน", "สม", "สย", "สว",
}


def detect_implicit_vowel(word: str) -> list[str] | None:
    """Detect implicit vowel -ะ between consonants that can't form clusters.

    Rule: When two consonants are written together and cannot form a
    consonant cluster or前引 structure, insert implicit vowel -ะ between them.

    Example: พยายาม → [พะ, ยา, ยาม] (พ and ย can't form cluster)
    Example: ตำรวจ → [ตำ, รวจ] (ต and ร can form cluster ตร)

    Returns: List of syllables if implicit vowel found, None otherwise.
    """
    chars = list(word)
    if len(chars) < 3:
        return None

    # Find first two consonants
    first_consonant = None
    first_idx = -1
    second_consonant = None
    second_idx = -1
    has_vowel_between = False

    for i, ch in enumerate(chars):
        if _is_consonant(ch):
            if first_consonant is None:
                first_consonant = ch
                first_idx = i
            elif second_consonant is None:
                second_consonant = ch
                second_idx = i
                break
        elif ch in VOWEL_AFTER_CONSONANT or _is_tone_mark(ch):
            if first_consonant is not None and second_consonant is None:
                has_vowel_between = True

    if first_consonant is None or second_consonant is None:
        return None

    # If there's a vowel between, no implicit vowel needed
    if has_vowel_between:
        return None

    # Check if they form a valid cluster
    cluster = first_consonant + second_consonant
    if cluster in VALID_CLUSTERS:
        return None

    # Check if it's a前引 structure (high class + low class)
    cls_first = CONSONANT_CLASSES.get(first_consonant)
    cls_second = CONSONANT_CLASSES.get(second_consonant)
    if cls_first == "high" and cls_second == "low":
        return None  # This is handled by detect_silent_prefix_split

    # They can't form a cluster - insert implicit -ะ
    syl1 = first_consonant + "ะ"
    syl2 = "".join(chars[first_idx + 1:])
    return [syl1, syl2]


def analyze_syllable(syllable: str, promoted_consonants: set = None) -> dict:
    """Analyze a single Thai syllable and return tone analysis with Chinese explanation.

    Args:
        syllable: Thai syllable text
        promoted_consonants: Set of consonants promoted by high-class prefix (ห นำ etc.)
    """
    chars = list(syllable)
    if not chars:
        return _empty_result(syllable)

    # Step 1: Find initial consonant
    initial_consonant = None
    initial_idx = -1
    for i, ch in enumerate(chars):
        if _is_consonant(ch):
            initial_consonant = ch
            initial_idx = i
            break

    if initial_consonant is None:
        return _empty_result(syllable)

    # Step 2: Determine consonant class and check for ห prefix
    ho_prefix = False
    effective_consonant = initial_consonant
    consonant_class = CONSONANT_CLASSES[initial_consonant]

    # Check for leading vowel (เ, แ, โ, ใ, ไ) before consonant
    leading_vowel = None
    leading_vowel_name = None
    leading_vowel_length = None
    for i in range(initial_idx):
        if chars[i] in ("เ", "แ", "โ", "ใ", "ไ"):
            leading_vowel = chars[i]
            info = VOWEL_AFTER_CONSONANT[chars[i]]
            leading_vowel_name = info[0]
            leading_vowel_length = info[1]
            break

    # Check for ห prefix: if initial consonant is ห and next consonant is low class
    if initial_consonant == "ห":
        for j in range(initial_idx + 1, len(chars)):
            if _is_consonant(chars[j]):
                if CONSONANT_CLASSES.get(chars[j]) == "low":
                    ho_prefix = True
                    effective_consonant = chars[j]
                    consonant_class = "high"  # promoted
                break
            if _is_vowel(chars[j]):
                continue  # skip vowels between ห and next consonant
            break

    # Check for promoted consonants (from word-level high-class prefix like ส-น)
    if promoted_consonants and initial_consonant in promoted_consonants:
        consonant_class = "high"  # promoted by preceding high-class consonant

    # Step 3: Detect tone mark
    tone_mark = None
    tone_mark_name = None
    for ch in chars:
        if _is_tone_mark(ch):
            tone_mark = ch  # Store actual Thai character
            tone_mark_name = TONE_MARKS[ch]  # Store English name for lookup
            break

    # Step 4: Detect vowel and length
    vowel_chars = []
    vowel_name = None
    vowel_length = "short"

    # Get characters after the initial consonant (or cluster)
    after_consonant = chars[initial_idx + 1:]
    # Get characters before the initial consonant (for leading vowels)
    before_consonant = chars[:initial_idx]

    # Collect vowel marks after consonant (skip tone marks and consonant clusters)
    vowel_marks_found = []
    i = 0
    while i < len(after_consonant):
        ch = after_consonant[i]
        if _is_tone_mark(ch):
            i += 1
            continue
        if ch in VOWEL_AFTER_CONSONANT:
            vowel_marks_found.append(ch)
            i += 1
            continue
        if _is_consonant(ch):
            # Check if this consonant is part of a cluster
            # (followed by vowel mark or tone mark)
            if i + 1 < len(after_consonant):
                next_ch = after_consonant[i + 1]
                if _is_tone_mark(next_ch) or next_ch in VOWEL_AFTER_CONSONANT:
                    # Part of cluster, skip
                    i += 1
                    continue
            # Not part of cluster, stop
            break
        i += 1

    # Check for complex patterns with leading vowel เ
    if leading_vowel == "เ":
        if "ี" in vowel_marks_found and "ย" in chars[initial_idx + 1:]:
            # เ-ีย pattern (ia)
            vowel_name = "เ-ีย"
            vowel_length = "long"
        elif "ื" in vowel_marks_found and "อ" in chars[initial_idx + 1:]:
            # เ-ือ pattern (uea)
            vowel_name = "เ-ือ"
            vowel_length = "long"
        elif "าะ" in "".join(vowel_marks_found):
            # เ-าะ pattern (short ɔ)
            vowel_name = "เ-าะ"
            vowel_length = "short"
        elif "า" in vowel_marks_found:
            # เ-า pattern (ao)
            vowel_name = "เ-า"
            vowel_length = "special"
        elif "ิ" in vowel_marks_found:
            # เ-ิ pattern (short e, like เดิน)
            vowel_name = "เ-ิ"
            vowel_length = "short"
        else:
            # Simple เ vowel
            vowel_name = "เ-"
            vowel_length = "long"
    elif leading_vowel:
        # Other leading vowels (แ, โ, ใ, ไ)
        vowel_name = leading_vowel_name
        vowel_length = leading_vowel_length
    else:
        # No leading vowel - check for patterns after consonant
        # Find the last vowel mark position to check what follows it
        last_vowel_idx = -1
        for i, ch in enumerate(after_consonant):
            if ch in VOWEL_AFTER_CONSONANT or _is_tone_mark(ch):
                last_vowel_idx = i

        # Check what follows the last vowel mark
        chars_after_vowel = after_consonant[last_vowel_idx + 1:] if last_vowel_idx >= 0 else []

        if "ั" in vowel_marks_found and "ว" in chars_after_vowel:
            # ัว pattern (ua)
            vowel_name = "-ัว"
            vowel_length = "long"
        elif "ิ" in vowel_marks_found and "ว" in chars_after_vowel:
            # ิว pattern (io)
            vowel_name = "-ิว"
            vowel_length = "long"
        elif "ํ" in chars and "า" in chars:
            # -ำ pattern (am)
            vowel_name = "-ำ"
            vowel_length = "long"
        elif "ั" in vowel_marks_found and "ย" in chars[initial_idx + 1:]:
            # -ัย pattern (ai)
            vowel_name = "-ัย"
            vowel_length = "short"
        elif vowel_marks_found:
            ch = vowel_marks_found[0]
            # Check if there's a final consonant after the vowel
            has_final = False
            for j in range(len(vowel_marks_found)):
                idx_in_after = after_consonant.index(vowel_marks_found[j]) if vowel_marks_found[j] in after_consonant else -1
                if idx_in_after >= 0:
                    remaining = after_consonant[idx_in_after + 1:]
                    for rc in remaining:
                        if _is_consonant(rc):
                            has_final = True
                            break
                    break

            # Show base form when vowel is modified by final consonant
            if ch == "ั" and has_final:
                # ั is modified form of -ะ before final consonant
                vowel_name = "-ะ"
                vowel_length = "short"
            elif ch == "ิ" and has_final and leading_vowel == "เ":
                # เ-ิ is modified form of เ-อะ before final consonant
                vowel_name = "เอ-อะ"
                vowel_length = "short"
            else:
                info = VOWEL_AFTER_CONSONANT[ch]
                vowel_name = info[0]
                vowel_length = info[1]
        else:
            # No vowel mark found - default to long a
            vowel_name = "-า"
            vowel_length = "long"

    # Check for nikkhahit (ํ) which can indicate nasalization
    has_nikkhahit = "ํ" in chars

    # Step 5: Find final consonant
    # The effective consonant is the main consonant of the syllable
    main_consonant = effective_consonant if ho_prefix else initial_consonant
    final_consonant = None

    # Consonants that can be part of vowel patterns (not finals)
    vowel_part_consonants = set()
    if vowel_name in ("เอีย", "เอือ"):
        vowel_part_consonants.add("ย")
        vowel_part_consonants.add("อ")
    if vowel_name in ("อัว", "ิว"):
        vowel_part_consonants.add("ว")

    # Scan from the end, skip vowel/tone marks, find the last consonant that isn't the main one
    for ch in reversed(chars):
        if _is_tone_mark(ch) or ch in VOWEL_AFTER_CONSONANT or ch == "ํ":
            continue
        if _is_consonant(ch):
            if ch != main_consonant and ch not in vowel_part_consonants:
                final_consonant = ch
            break

    # Step 6: Classify final type (live vs dead)
    final_type = "live"
    if final_consonant:
        if final_consonant in LIVE_FINALS:
            final_type = "live"
        elif final_consonant in DEAD_FINALS:
            final_type = "dead"
        else:
            final_type = "live"
    else:
        # No final consonant: depends on vowel length
        # Short vowel alone = dead, long vowel alone = live
        final_type = "live" if vowel_length == "long" else "dead"

    # Special case: if vowel mark ะ is present, it's always dead
    if "ะ" in chars:
        final_type = "dead"
        vowel_length = "short"

    # Step 7: Determine tone
    effective_class = consonant_class

    # Special vowel rules:
    # ฤ/อำ → treat as short vowel (follow normal rules)
    # ฤา → treat as long vowel (follow normal rules)
    # ไ/ใ/เา → fixed 5th tone (rising), completely overrides normal rules
    # ขำ → exception, becomes 5th tone (rising)
    is_fixed_rising = vowel_name in ("ไ-", "ใ-", "เ-า") and not tone_mark_name
    is_kham_exception = syllable == "ขำ"

    if is_fixed_rising or is_kham_exception:
        # ไ/ใ/เา without tone mark → always rising (5th tone)
        # ขำ → exception, rising (5th tone)
        tone = "rising"
    else:
        # Normal tone rules
        tone = TONE_RULES.get((effective_class, tone_mark_name, final_type), "mid")

    # Step 8: Generate Chinese explanation
    explanation = _generate_explanation(
        initial_consonant=initial_consonant,
        effective_consonant=effective_consonant if ho_prefix else None,
        consonant_class=consonant_class,
        ho_prefix=ho_prefix,
        vowel_name=vowel_name,
        vowel_length=vowel_length,
        tone_mark=tone_mark,
        tone_mark_name=tone_mark_name,
        final_consonant=final_consonant,
        final_type=final_type,
        tone=tone,
    )

    # Step 9: Generate pronunciation tip
    pronunciation_tip = _generate_pronunciation_tip(vowel_length, final_consonant, final_type)

    return {
        "text": syllable,
        "ipa": "",
        "consonant": effective_consonant,
        "consonant_class": consonant_class,
        "consonant_class_cn": CLASS_CN[consonant_class],
        "vowel": vowel_name,
        "vowel_length": vowel_length,
        "tone_mark": tone_mark,
        "tone_mark_cn": MARK_CN.get(tone_mark_name),
        "final_consonant": final_consonant,
        "final_type": final_type,
        "ho_prefix": ho_prefix,
        "tone": tone,
        "tone_cn": TONE_CN[tone],
        "tone_number": TONE_NUMBER[tone],
        "tone_explanation": explanation,
        "pronunciation_tip": pronunciation_tip,
    }


def _generate_explanation(
    initial_consonant, effective_consonant, consonant_class,
    ho_prefix, vowel_name, vowel_length,
    tone_mark, tone_mark_name, final_consonant, final_type, tone
) -> str:
    parts = []

    # 1. Consonant
    if ho_prefix and effective_consonant:
        parts.append(
            f"低辅音 '{effective_consonant}' 前有高辅音 ห 引导(ห นำ)，提升为高辅音规则"
        )
    else:
        cls = CLASS_CN[consonant_class]
        parts.append(f"{cls} '{initial_consonant}'")

    # 2. Vowel
    if vowel_length == "short":
        length_cn = "短"
    elif vowel_length == "special":
        length_cn = "特殊"
    else:
        length_cn = "长"
    parts.append(f"{length_cn}元音 '{vowel_name}'")

    # 3. Final type
    if final_consonant:
        ft = "清尾音" if final_type == "live" else "浊尾音"
        parts.append(f"{ft} (以 '{final_consonant}' 结尾)")

    # 4. Tone mark (with fixed tone mark number)
    if tone_mark and tone_mark_name:
        mark_num = TONE_MARK_NUMBER.get(tone_mark_name, 0)
        parts.append(f"◌{tone_mark} 第{mark_num}声调")

    # 5. Result (with arrow, no + before it)
    tone_num = TONE_NUMBER[tone]
    tone_name = TONE_CN[tone]
    result = " + ".join(parts) + f"  → 第{tone_num}调（{tone_name}）"

    return result


def _generate_pronunciation_tip(vowel_length: str, final_consonant: str | None, final_type: str) -> str:
    """Generate pronunciation tip like '短促', '长音 + 收尾'."""
    if vowel_length == "short":
        if final_consonant:
            return f"短音 + 收尾({final_consonant})"
        return "短促"
    elif vowel_length == "special":
        if final_consonant:
            return f"特殊元音 + 收尾({final_consonant})"
        return "特殊元音"
    else:
        if final_consonant:
            return f"长音 + 收尾({final_consonant})"
        return "长音"


def _empty_result(syllable: str) -> dict:
    return {
        "text": syllable,
        "ipa": "",
        "consonant": "",
        "consonant_class": "mid",
        "consonant_class_cn": "中辅音",
        "vowel": "",
        "vowel_length": "long",
        "tone_mark": None,
        "tone_mark_cn": None,
        "final_consonant": None,
        "final_type": "live",
        "ho_prefix": False,
        "tone": "mid",
        "tone_cn": "中声调",
        "tone_number": 1,
        "tone_explanation": "无法分析",
        "pronunciation_tip": "",
    }
