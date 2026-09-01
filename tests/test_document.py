# tests/test_document.py

import os


def test_pdf_extension():

    filename = "requirement.pdf"

    assert filename.endswith(".pdf")


def test_docx_extension():

    filename = "requirement.docx"

    assert filename.endswith(".docx")


def test_pptx_extension():

    filename = "requirement.pptx"

    assert filename.endswith(".pptx")