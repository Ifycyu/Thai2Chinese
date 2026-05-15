from pythainlp.transliterate import romanize


def get_ipa(text: str) -> str:
    try:
        return romanize(text)
    except Exception:
        return ""
