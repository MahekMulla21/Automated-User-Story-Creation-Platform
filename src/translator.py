from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator


DetectorFactory.seed = 0

MAX_CHUNK_CHARS = 4500


def _detect_lang(text: str) -> str:
    """Detects the ISO 639-1 language code of the text. Falls back to
    'en' if detection fails (e.g. text too short or ambiguous)."""
    try:
        return detect(text)
    except Exception:
        return "en"


def _chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS):
    """Splits text into newline-preserving chunks, each under max_chars.
    Keeps blank lines out (they carry no translatable content) but
    preserves line order."""
    lines = [line for line in text.split("\n") if line.strip()]

    chunks = []
    current = []
    current_len = 0

    for line in lines:
        # +1 accounts for the newline that will join this line to the chunk
        if current and current_len + len(line) + 1 > max_chars:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line) + 1

    if current:
        chunks.append("\n".join(current))

    return chunks


def _translate_chunk(chunk: str, source_lang: str) -> str:
    """Translates a single chunk of text to English using the Google
    Translate web endpoint (via deep-translator). No local model is
    loaded, so this has a negligible memory footprint compared to a
    local transformer model — well suited to low-RAM deployments."""
    return GoogleTranslator(source=source_lang, target="en").translate(chunk)


def translate_to_english(text: str):
    """
    Detects the language of `text` and translates it to English if needed.

    Returns:
        (english_text, detected_iso_code)

        If the text is empty or already detected as English, the original
        text is returned unchanged and no translation call is made.

        If translation fails for any reason (network issue, unsupported
        language, etc.), the original text is returned unchanged along
        with the detected language code, so the caller can decide how to
        proceed instead of crashing.
    """
    if not text or not text.strip():
        return text, "en"

    iso_code = _detect_lang(text)
    if iso_code == "en":
        return text, "en"

    chunks = _chunk_text(text)
    if not chunks:
        return text, iso_code

    try:
        translated_chunks = [
            _translate_chunk(chunk, iso_code) for chunk in chunks
        ]
    except Exception:
        return text, iso_code

    return "\n".join(translated_chunks), iso_code