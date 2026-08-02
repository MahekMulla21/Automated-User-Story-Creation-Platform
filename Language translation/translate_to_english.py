#!/usr/bin/env python3
"""
translate_to_english.py

Open-source machine translation to English using Meta's NLLB-200 model
(facebook/nllb-200-distilled-600M) via Hugging Face Transformers.

Detects the source language automatically (langdetect) and translates
text from ~100+ languages into English. No paid APIs required.

Usage:
    # Translate a single string
    python translate_to_english.py --text "Bonjour tout le monde"

    # Translate a text file (one segment per line)
    python translate_to_english.py --file input.txt --out output.txt

    # Force a known source language instead of auto-detecting
    python translate_to_english.py --text "Bonjour" --src fra_Latn

    # Interactive mode
    python translate_to_english.py

Install dependencies first:
    pip install -r requirements.txt --break-system-packages
"""

import argparse
import sys

from langdetect import detect, DetectorFactory
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

# Make langdetect deterministic
DetectorFactory.seed = 0

MODEL_NAME = "facebook/nllb-200-distilled-600M"
TARGET_LANG = "eng_Latn"

# Map langdetect's ISO 639-1 codes to NLLB's FLORES-200 codes.
# Extend this dict if you need a language that's missing.
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


def detect_nllb_lang(text: str) -> str:
    """Detect source language and map it to an NLLB FLORES-200 code."""
    try:
        iso_code = detect(text)
    except Exception:
        iso_code = "en"
    nllb_code = ISO_TO_NLLB.get(iso_code)
    if nllb_code is None:
        print(f"[warn] Could not map detected language '{iso_code}' to NLLB code; "
              f"defaulting to English.", file=sys.stderr)
        nllb_code = "eng_Latn"
    return nllb_code


def load_translator():
    print(f"[info] Loading model '{MODEL_NAME}' (first run downloads ~2.4GB)...",
          file=sys.stderr)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return tokenizer, model


def translate(text: str, tokenizer, model, src_lang: str = None) -> str:
    if not text.strip():
        return ""

    source_lang = src_lang or detect_nllb_lang(text)
    tokenizer.src_lang = source_lang

    translator = pipeline(
        "translation",
        model=model,
        tokenizer=tokenizer,
        src_lang=source_lang,
        tgt_lang=TARGET_LANG,
        max_length=400,
    )
    result = translator(text)
    return result[0]["translation_text"]


def main():
    parser = argparse.ArgumentParser(description="Translate text to English (open-source, offline).")
    parser.add_argument("--text", type=str, help="Text to translate.")
    parser.add_argument("--file", type=str, help="Path to a text file (translated line by line).")
    parser.add_argument("--out", type=str, help="Output file path (used with --file).")
    parser.add_argument("--src", type=str, default=None,
                         help="Force source language as an NLLB code (e.g., fra_Latn). "
                              "Skips auto-detection.")
    args = parser.parse_args()

    tokenizer, model = load_translator()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]

        translations = []
        for i, line in enumerate(lines, 1):
            if not line.strip():
                translations.append("")
                continue
            eng = translate(line, tokenizer, model, args.src)
            print(f"[{i}/{len(lines)}] {line}  ->  {eng}")
            translations.append(eng)

        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write("\n".join(translations))
            print(f"\n[info] Wrote translations to {args.out}")

    elif args.text:
        print(translate(args.text, tokenizer, model, args.src))

    else:
        print("Interactive mode. Type text to translate, or 'quit' to exit.")
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if line.lower() in ("quit", "exit"):
                break
            if not line:
                continue
            print(translate(line, tokenizer, model, args.src))


if __name__ == "__main__":
    main()
