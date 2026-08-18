from langdetect import detect, DetectorFactory, LangDetectException

DetectorFactory.seed = 0


def translate_to_english(text: str):
    """
    Returns (english_text, detected_lang_code).

    - If the text is already English, it's returned unchanged with "en".
    - If detection fails (e.g. text too short/ambiguous), it's treated
      as English rather than blocking generation.
    - If translation fails (e.g. no network), the original text is
      returned along with the detected language, so generation can still
      proceed with a best-effort prompt rather than erroring out.
    """
    text = text.strip()
    if not text:
        return text, "en"

    try:
        detected_lang = detect(text)
    except LangDetectException:
        return text, "en"

    if detected_lang == "en":
        return text, "en"

    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        if translated and translated.strip():
            return translated, detected_lang
    except Exception:
        pass

    return text, detected_lang