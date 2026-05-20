from pythainlp.transliterate import romanize, transliterate


def get_ipa(text: str) -> str:
    try:
        return transliterate(text)
    except Exception:
        return ""


def get_romanize(text: str) -> str:
    try:
        return romanize(text)
    except Exception:
        return ""
