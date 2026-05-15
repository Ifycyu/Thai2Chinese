from pythainlp.tokenize import word_tokenize, syllable_tokenize


def segment_words(sentence: str) -> list[str]:
    # Use attacut (deep learning) for finer granularity
    # Falls back to newmm if attacut fails
    try:
        tokens = word_tokenize(sentence, engine="attacut")
    except Exception:
        tokens = word_tokenize(sentence, engine="newmm")
    return [t for t in tokens if t.strip()]


def segment_syllables(word: str) -> list[str]:
    return syllable_tokenize(word)
