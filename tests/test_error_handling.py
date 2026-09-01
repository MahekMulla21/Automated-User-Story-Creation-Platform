# tests/test_error_handling.py

from src.translator import translate_to_english


def test_empty_input():

    translated, lang = translate_to_english("")

    assert translated == ""


def test_invalid_input():

    translated, lang = translate_to_english("@@@@@@@")

    assert translated is not None