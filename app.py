import streamlit as st
import tempfile
import os
import re
import json
import csv
import io
from src.generator import generate
from src.document_converter import convert_document_to_markdown
from src.translator import translate_to_english


def parse_acceptance_criteria(raw_text):
    """Parses raw Given/When/Then/And text into structured scenarios.
    'And' clauses are merged into the preceding Given/When/Then step
    instead of being treated as separate bullets."""

    scenario_blocks = [s.strip() for s in re.split(r'Scenario\s*\d*\s*:', raw_text, flags=re.IGNORECASE) if s.strip()]

    scenarios = []
    for index, block in enumerate(scenario_blocks):
        title_match = re.match(r'^(.*?)(?=\b(Given|When|Then|And)\b)', block, flags=re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match and title_match.group(1).strip() else f"Scenario {index + 1}"

        body_text = block[len(title):].strip() if title_match else block

        step_pattern = re.compile(
            r'\b(Given|When|Then|And)\b\s+(.*?)(?=\b(Given|When|Then|And)\b|$)',
            flags=re.IGNORECASE | re.DOTALL
        )

        steps = []
        for match in step_pattern.finditer(body_text):
            keyword = match.group(1).capitalize()
            text = match.group(2).strip().rstrip('.')

            if not text:
                continue

            if keyword == "And" and steps:
                steps[-1]["text"] += f" and {text}"
            else:
                steps.append({"keyword": keyword, "text": text})

        scenarios.append({
            "id": index + 1,
            "title": title,
            "steps": steps
        })

    return scenarios


def render_result(result_text):
    """Splits result into User Story / Acceptance Criteria and renders
    Acceptance Criteria as bold Given/When/Then bullets, matching the
    target format with spacing between scenarios.

    Returns (header_text, scenarios) so the caller can also offer the
    parsed content as downloadable files."""

    parts = re.split(r'Acceptance Criteria:?', result_text, flags=re.IGNORECASE)

    header_text = parts[0].strip()
    st.markdown(header_text)

    scenarios = []
    if len(parts) > 1:
        st.markdown("## Acceptance Criteria")
        scenarios = parse_acceptance_criteria(parts[1])

        for scenario in scenarios:
            st.markdown(f"**Scenario {scenario['id']}: {scenario['title']}**")

            bullet_lines = "\n".join(
                f"- **{step['keyword']}** {step['text']}" for step in scenario["steps"]
            )
            st.markdown(bullet_lines)
            st.markdown("")

    return header_text, scenarios


def build_json_export(header_text, scenarios):
    """Builds a JSON string containing the user story and acceptance criteria."""
    data = {
        "user_story": header_text,
        "acceptance_criteria": scenarios
    }
    return json.dumps(data, indent=2)


def build_csv_export(header_text, scenarios):
    """Builds a CSV string containing the user story and acceptance criteria."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["User Story"])
    writer.writerow([header_text])
    writer.writerow([])

    writer.writerow(["Scenario ID", "Scenario Title", "Step Keyword", "Step Text"])
    for scenario in scenarios:
        if scenario["steps"]:
            for step in scenario["steps"]:
                writer.writerow([scenario["id"], scenario["title"], step["keyword"], step["text"]])
        else:
            writer.writerow([scenario["id"], scenario["title"], "", ""])

    return output.getvalue()


st.title("Automated User Story  and Acceptance Criteria Creation Platform")

if "req_box" not in st.session_state:
    st.session_state.req_box = ""

if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

if "generated_result" not in st.session_state:
    st.session_state.generated_result = None

text_area_slot = st.empty()
uploader_slot = st.empty()

with uploader_slot.container():
    uploaded_file = st.file_uploader(
        "Upload Requirement Document (Optional)",
        type=["pdf", "docx", "pptx", "xlsx"]
    )

if uploaded_file is not None:
    if st.session_state.last_uploaded_file != uploaded_file.name:
        suffix = os.path.splitext(uploaded_file.name)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            requirement_text = convert_document_to_markdown(tmp_path)
            st.session_state.req_box = requirement_text
            st.session_state.last_uploaded_file = uploaded_file.name
            st.success("Document uploaded and converted successfully!")
        except Exception as e:
            st.error(f"Failed to convert document: {e}")
        finally:
            os.remove(tmp_path)

        st.rerun()

with text_area_slot.container():
    st.text_area(
        "Enter Requirement",
        key="req_box",
        height=200,
        placeholder="Type your software requirement here..."
    )

if st.button("Generate"):
    final_text = st.session_state.get("req_box", "")

    if final_text.strip():
        english_text, detected_lang = translate_to_english(final_text)
        if detected_lang != "en":
            st.info(f"Detected input language: **{detected_lang}**. Translated to English before generating.")
        st.session_state.generated_result = generate(english_text)
    else:
        st.session_state.generated_result = None
        st.warning("Please enter a requirement or upload a document.")

if st.session_state.generated_result:
    header_text, scenarios = render_result(st.session_state.generated_result)

    st.markdown("---")
    download_col1, download_col2 = st.columns(2)

    with download_col1:
        st.download_button(
            label="Download as JSON",
            data=build_json_export(header_text, scenarios),
            file_name="user_story_and_acceptance_criteria.json",
            mime="application/json",
            key="download_json_btn"
        )

    with download_col2:
        st.download_button(
            label="Download as CSV",
            data=build_csv_export(header_text, scenarios),
            file_name="user_story_and_acceptance_criteria.csv",
            mime="text/csv",
            key="download_csv_btn"
        )
