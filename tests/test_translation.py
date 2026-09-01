# tests/test_translation.py

from src.translator import translate_to_english


def test_english_text():
    text = "User can login"

    translated, lang = translate_to_english(text)

    assert lang == "en"


def test_hindi_translation():
    text = "उपयोगकर्ता लॉगिन कर सके"

    translated, lang = translate_to_english(text)

    assert lang == "hi"


def test_marathi_translation():
    text = "वापरकर्ता लॉगिन करू शकतो"

    translated, lang = translate_to_english(text)

    assert lang == "mr"


def test_empty_translation():

    translated, lang = translate_to_english("")

    assert translated == ""


def test_whitespace_translation():

    translated, lang = translate_to_english("     ")

    assert translated.strip() == ""