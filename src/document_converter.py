from markitdown import MarkItDown

def convert_document_to_markdown(file_path, output_md_path=None):
    """
    Converts any supported document (PDF, DOCX, XLSX, etc.)
    into Markdown text using Microsoft MarkItDown.
    Optionally writes the result to output_md_path.
    """
    md = MarkItDown()
    result = md.convert(file_path)
    text = result.text_content

    if output_md_path:
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(text)

    return text