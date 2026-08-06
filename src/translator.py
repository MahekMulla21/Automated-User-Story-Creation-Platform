import streamlit as st
from langdetect import detect, DetectorFactory
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


DetectorFactory.seed = 0

MODEL_NAME = "facebook/nllb-200-distilled-600M"
TARGET_LANG = "eng_Latn"


ISO_TO_NLLB = {
    "af": "afr_Latn", "am": "amh_Ethi", "ar": "arb_Arab", "az": "azj_Latn",
    "be": "bel_Cyrl", "bg": "bul_Cyrl", "bn": "ben_Beng", "bs": "bos_Latn",
    "ca": "cat_Latn", "cs": "ces_Latn", "cy": "cym_Latn", "da": "dan_Latn",
    "de": "deu_Latn", "el": "ell_Grek", "en": "eng_Latn", "eo": "epo_Latn",
    "es": "spa_Latn", "et": "est_Latn", "eu": "eus_Latn", "fa": "pes_Arab",
    "fi": "fin_Latn", "fr": "fra_Latn", "ga": "gle_Latn", "gu": "guj_Gujr",
    "he": "heb_Hebr", "hi": "hin_Deva", "hr": "hrv_Latn", "hu": "hun_Latn",
    "hy": "hye_Armn", "id": "ind_Latn", "is": "isl_Latn", "it": "ita_Latn",
    "ja": "jpn_Jpan", "ka": "kat_Geor", "kk": "kaz_Cyrl", "km": "khm_Khmr",
    "kn": "kan_Knda", "ko": "kor_Hang", "lt": "lit_Latn", "lv": "lvs_Latn",
    "mk": "mkd_Cyrl", "ml": "mal_Mlym", "mn": "khk_Cyrl", "mr": "mar_Deva",
    "ms": "zsm_Latn", "ne": "npi_Deva", "nl": "nld_Latn", "no": "nob_Latn",
    "pa": "pan_Guru", "pl": "pol_Latn", "pt": "por_Latn", "ro": "ron_Latn",
    "ru": "rus_Cyrl", "si": "sin_Sinh", "sk": "slk_Latn", "sl": "slv_Latn",
    "sq": "als_Latn", "sr": "srp_Cyrl", "sv": "swe_Latn", "sw": "swh_Latn",
    "ta": "tam_Taml", "te": "tel_Telu", "th": "tha_Thai", "tl": "tgl_Latn",
    "tr": "tur_Latn", "uk": "ukr_Cyrl", "ur": "urd_Arab", "vi": "vie_Latn",
    "zh-cn": "zho_Hans", "zh-tw": "zho_Hant", "zh": "zho_Hans",
}


@st.cache_resource(show_spinner="Loading translation model (first run only, ~2.4GB)...")
def _load_translator():
    """Loads and caches the tokenizer + model for the lifetime of the app
    process, so it's only downloaded/loaded once, not on every rerun."""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return tokenizer, model


def _detect_lang(text: str) -> str:
    """Detects the ISO 639-1 language code of the text. Falls back to
    'en' if detection fails (e.g. text too short or ambiguous)."""
    try:
        return detect(text)
    except Exception:
        return "en"


def _translate_chunk(chunk: str, tokenizer, model, nllb_code: str) -> str:
    """Translates a single chunk of text using model.generate() directly.

    We call generate() ourselves instead of using the transformers
    pipeline() helper, because newer transformers versions have
    restructured/removed the "translation" pipeline task alias (this is
    what throws the "Unknown task translation" KeyError). Calling
    generate() with forced_bos_token_id is the underlying mechanism the
    pipeline used anyway, and it's stable across transformers versions.
    """
    tokenizer.src_lang = nllb_code
    inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)

    target_lang_id = tokenizer.convert_tokens_to_ids(TARGET_LANG)

    generated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=target_lang_id,
        max_length=512,
    )

    return tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]


def translate_to_english(text: str):
    """
    Detects the language of `text` and translates it to English if needed.

    Returns:
        (english_text, detected_iso_code)

        If the text is empty or already detected as English, the original
        text is returned unchanged and the model is never loaded.
    """
    if not text or not text.strip():
        return text, "en"

    iso_code = _detect_lang(text)
    if iso_code == "en":
        return text, "en"

    nllb_code = ISO_TO_NLLB.get(iso_code, "eng_Latn")

    tokenizer, model = _load_translator()

    chunks = [chunk for chunk in text.split("\n") if chunk.strip()]

    if not chunks:
        return text, iso_code

    translated_chunks = [
        _translate_chunk(chunk, tokenizer, model, nllb_code) for chunk in chunks
    ]

    return "\n".join(translated_chunks), iso_code
