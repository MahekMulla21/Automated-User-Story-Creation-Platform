import streamlit as st
import tempfile
import os
import json
import csv
import io
from src.generator import generate
from src.document_converter import convert_document_to_markdown
from src.translator import translate_to_english


def render_result(result):
    """
    Renders the generator.generate() result: ALL User Stories first,
    then ALL Acceptance Criteria below them.

    CHANGE: previously this parsed raw markdown text with a regex-based
    Given/When/Then parser (parse_acceptance_criteria). generate() now
    returns pre-structured JSON, so no parsing happens here at all.
    """
    stories = result["stories"]
    criteria = result["criteria"]
    coverage = result["coverage"]

    st.markdown(
        f"**Epics:** {coverage['epics']}  |  "
        f"**Features:** {coverage['features']}  |  "
        f"**User Stories:** {coverage['stories']}"
    )
    st.markdown("---")

    st.markdown("## User Stories")
    for s in stories:
        st.markdown(
            f"**{s['id']} — {s['title']}**  \n"
            f"*Epic: {s['epic']} · Feature: {s['feature']} · Priority: {s['priority']}*"
        )
        st.markdown(s["story"])
        st.markdown("")

    st.markdown("---")
    st.markdown("## Acceptance Criteria")
    for c in criteria:
        st.markdown(f"**{c['id']}**")
        for scenario in c["scenarios"]:
            st.markdown(f"**Scenario: {scenario.get('scenario', '')}**")
            bullet_lines = "\n".join(
                f"- **{step['keyword']}** {step['text']}"
                for step in scenario.get("steps", [])
            )
            st.markdown(bullet_lines)
            st.markdown("")


def build_json_export(result):
    """Builds a JSON string containing all user stories and acceptance criteria."""
    data = {
        "coverage": result["coverage"],
        "user_stories": result["stories"],
        "acceptance_criteria": result["criteria"],
    }
    return json.dumps(data, indent=2)


def build_csv_export(result):
    """Builds a CSV string containing all user stories and acceptance criteria."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Story ID", "Epic", "Feature", "Title", "Priority", "User Story"])
    for s in result["stories"]:
        writer.writerow([s["id"], s["epic"], s["feature"], s["title"], s["priority"], s["story"]])

    writer.writerow([])
    writer.writerow(["Story ID", "Scenario", "Step Keyword", "Step Text"])
    for c in result["criteria"]:
        for scenario in c["scenarios"]:
            steps = scenario.get("steps", [])
            if steps:
                for step in steps:
                    writer.writerow([c["id"], scenario.get("scenario", ""), step["keyword"], step["text"]])
            else:
                writer.writerow([c["id"], scenario.get("scenario", ""), "", ""])

    return output.getvalue()


def build_md_export(result):
    """Builds a Markdown string with all user stories, then all acceptance
    criteria, matching the order rendered in the app."""
    lines = []
    lines.append("## User Stories")
    lines.append("")
    for s in result["stories"]:
        lines.append(f"**{s['id']} — {s['title']}**  ")
        lines.append(f"*Epic: {s['epic']} · Feature: {s['feature']} · Priority: {s['priority']}*")
        lines.append("")
        lines.append(s["story"])
        lines.append("")

    lines.append("## Acceptance Criteria")
    lines.append("")
    for c in result["criteria"]:
        lines.append(f"**{c['id']}**")
        lines.append("")
        for scenario in c["scenarios"]:
            lines.append(f"**Scenario: {scenario.get('scenario', '')}**")
            lines.append("")
            for step in scenario.get("steps", []):
                lines.append(f"- **{step['keyword']}** {step['text']}")
            lines.append("")

    return "\n".join(lines)


st.title("Automated User Story Creation Platform")

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

        try:
            with st.spinner("Generating user stories..."):
                st.session_state.generated_result = generate(english_text)
        except RuntimeError as e:
            st.session_state.generated_result = None
            st.error(str(e))
    else:
        st.session_state.generated_result = None
        st.warning("Please enter a requirement or upload a document.")

if st.session_state.generated_result:
    result = st.session_state.generated_result
    render_result(result)

    st.markdown("---")
    download_col1, download_col2, download_col3 = st.columns(3)

    with download_col1:
        st.download_button(
            label="Download as JSON",
            data=build_json_export(result),
            file_name="user_stories_and_acceptance_criteria.json",
            mime="application/json",
            key="download_json_btn"
        )

    with download_col2:
        st.download_button(
            label="Download as CSV",
            data=build_csv_export(result),
            file_name="user_stories_and_acceptance_criteria.csv",
            mime="text/csv",
            key="download_csv_btn"
        )

    with download_col3:
        st.download_button(
            label="Download as Markdown",
            data=build_md_export(result),
            file_name="user_stories_and_acceptance_criteria.md",
            mime="text/markdown",
            key="download_md_btn"
        )
