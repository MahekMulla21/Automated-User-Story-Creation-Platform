import csv
import io
import json
import os
import tempfile
import time
from datetime import datetime

import streamlit as st

from src.generator import generate
from src.document_converter import convert_document_to_markdown
from src.translator import translate_to_english


st.set_page_config(
    page_title="Automated User Story Creation Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAV_ITEMS = [
    "Dashboard",
    "History",
    "Templates",
    "Analytics",
    "Test Cases",
    "Settings",
    "Help & Docs",
]

PIPELINE_STEPS = [
    ("received", "Requirement Received"),
    ("lang", "Language Detection"),
    ("translate", "Translation"),
    ("analysis", "Gemini AI Analysis"),
    ("stories", "User Story & AC Generation"),
    ("export", "Export Ready"),
]


_defaults = {
    "req_box": "",
    "pending_req_text": None,
    "last_uploaded_file": None,
    "generated_result": None,
    "nav_page": "Dashboard",
    "detected_lang": "en",
    "last_duration": None,
    "session_requirements": 0,
    "session_stories": 0,
    "pipeline_status": {key: "pending" for key, _ in PIPELINE_STEPS},
}
for _k, _v in _defaults.items():
    st.session_state.setdefault(_k, _v)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .display-font { font-family: 'Sora', sans-serif; }

    #MainMenu, footer { visibility: hidden; }

    .stApp { background: #F4F6FB; }

    div.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1330 0%, #131C40 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    section[data-testid="stSidebar"] * { color: #C9CEE3; }
    section[data-testid="stSidebar"] .sidebar-brand {
        font-family: 'Sora', sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        line-height: 1.3;
        color: #FFFFFF;
        padding: 0.4rem 0 0.1rem 0;
    }
    section[data-testid="stSidebar"] .sidebar-tag {
        font-size: 0.72rem;
        color: #7C86B8;
        padding-bottom: 1.1rem;
        border-bottom: 1px solid rgba(255,255,255,0.07);
        margin-bottom: 0.9rem;
    }
    .nav-active {
        display:flex; align-items:center; gap:10px;
        background: linear-gradient(90deg, rgba(124,107,246,0.22), rgba(79,124,255,0.06));
        border-left: 3px solid #8B7CF6;
        border-radius: 8px;
        padding: 0.55rem 0.7rem;
        margin-bottom: 0.15rem;
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 0.92rem;
    }
    section[data-testid="stSidebar"] .stButton button {
        background: transparent;
        border: none;
        text-align: left;
        color: #A6ADCF;
        font-weight: 500;
        font-size: 0.92rem;
        padding: 0.55rem 0.7rem;
        border-left: 3px solid transparent;
        border-radius: 8px;
        width: 100%;
        margin-bottom: 0.15rem;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(255,255,255,0.05);
        color: #FFFFFF;
        border-left: 3px solid #4F7CFF;
    }
    .upgrade-card {
        background: linear-gradient(135deg,#5B4FE0,#3E63E0);
        border-radius: 12px;
        padding: 1rem;
        margin-top: 1rem;
        color: white !important;
    }
    .upgrade-card * { color: #EDEBFF !important; }
    .upgrade-card .title { font-weight: 700; font-size: 0.95rem; margin-bottom: 0.25rem; color:#fff !important;}
    .upgrade-card .desc { font-size: 0.78rem; line-height:1.35; opacity:0.9; margin-bottom:0.6rem;}
    .sidebar-profile {
        display:flex; align-items:center; gap:10px;
        border-top: 1px solid rgba(255,255,255,0.08);
        padding-top: 0.9rem; margin-top: 0.9rem;
    }
    .sidebar-profile .avatar {
        width:34px; height:34px; border-radius:50%;
        background: linear-gradient(135deg,#F2B4A6,#E88B8B);
        display:flex; align-items:center; justify-content:center;
        font-weight:700; color:#fff; font-size:0.85rem;
    }
    .sidebar-profile .name { font-weight:600; font-size:0.85rem; color:#fff; }
    .sidebar-profile .role { font-size:0.72rem; color:#8892C2; }

    /* ---------- Header ---------- */
    .app-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.3rem; }
    .app-header h1 { font-size:1.55rem; margin:0; color:#101828; }
    .app-header p { color:#667085; font-size:0.92rem; margin-top:0.15rem; }

    /* ---------- Stat cards ---------- */
    .stat-card {
        background:#FFFFFF; border:1px solid #EAECF3; border-radius:14px;
        padding:1.1rem 1.2rem; height:100%;
        border-top: 3px solid #6D5DF6;
    }
    .stat-card .label { color:#667085; font-size:0.82rem; margin-bottom:0.15rem; }
    .stat-card .value { font-family:'Sora',sans-serif; font-size:1.55rem; font-weight:700; color:#101828; }
    .stat-card .sub { font-size:0.76rem; color:#16A34A; margin-top:0.15rem; }
    .stat-card .sub.neutral { color:#94A3B8; }

    /* ---------- Requirement text area ---------- */
    div[data-testid="stTextArea"] textarea {
        border: 2.5px solid #6D5DF6 !important;
        border-radius: 10px !important;
        background: #FBFBFE !important;
        color: #1D2433 !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border: 1.5px solid #6D5DF6 !important;
        box-shadow: 0 0 0 3px rgba(109,93,246,0.15) !important;
    }

    /* ---------- Panels ---------- */
    .panel {
        background:#FFFFFF; border:1px solid #EAECF3; border-radius:14px;
        padding:1.15rem 1.25rem; height:100%;
    }
    .panel-title {
        display:flex; align-items:center; justify-content:space-between;
        margin-bottom:0.9rem;
    }
    .panel-title .left { display:flex; align-items:center; gap:8px; }
    .panel-title .step-badge {
        width:22px; height:22px; border-radius:6px; background:#6D5DF6; color:white;
        font-size:0.75rem; font-weight:700; display:flex; align-items:center; justify-content:center;
    }
    .panel-title h3 { margin:0; font-size:1.02rem; color:#101828; }

    .pipeline-row { display:flex; align-items:center; gap:10px; padding:0.42rem 0; }
    .pipeline-dot {
        width:26px; height:26px; border-radius:50%; flex-shrink:0;
        display:flex; align-items:center; justify-content:center; font-size:0.78rem;
    }
    .pipeline-dot.done { background:#E7F8EF; color:#16A34A; }
    .pipeline-dot.active { background:#E9E5FF; color:#6D5DF6; }
    .pipeline-dot.pending { background:#F1F2F6; color:#B0B7CE; }
    .pipeline-text .title { font-size:0.86rem; font-weight:600; color:#1D2433; }
    .pipeline-text .sub { font-size:0.74rem; color:#98A1BC; }

    .story-card {
        border:1px solid #EAECF3; border-radius:12px; padding:0.9rem 1rem; margin-bottom:0.7rem;
        background:#FBFBFE; height:100%;
    }
    .story-card .top { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem;}
    .story-card .top .id { font-weight:700; color:#101828; font-size:0.92rem; }
    .badge {
        display:inline-block; font-size:0.7rem; font-weight:600; padding:0.15rem 0.55rem;
        border-radius:20px; margin-right:0.35rem;
    }
    .badge.priority-high { background:#FDECEC; color:#DC2626; }
    .badge.priority-medium { background:#FEF6E7; color:#D97706; }
    .badge.priority-low { background:#EAF6EE; color:#16A34A; }
    .badge.module { background:#EEF0FF; color:#4F46E5; }
    .badge.actor { background:#EAF6FB; color:#0891B2; }

    .feature-chip {
        display:inline-block; background:#EEF0FF; color:#4F46E5; font-size:0.75rem;
        padding:0.2rem 0.6rem; border-radius:20px; margin:0.15rem 0.3rem 0.15rem 0;
        font-weight:500;
    }

    .arch-flow { display:flex; align-items:center; overflow-x:auto; gap:0.4rem; padding-top:0.3rem;}
    .arch-step { text-align:center; min-width:118px; }
    .arch-step .box {
        border:1px solid #EAECF3; border-radius:12px; padding:0.7rem 0.5rem; background:#FBFBFE;
        border-top: 3px solid #6D5DF6;
    }
    .arch-step .box .t { font-size:0.78rem; font-weight:700; color:#101828; margin-top:0.1rem; }
    .arch-step .box .s { font-size:0.68rem; color:#94A3B8; }
    .arch-arrow { color:#C6CBE0; font-size:1.1rem; padding: 0 0.1rem; }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg,#6D5DF6,#4F7CFF);
        border:none; font-weight:600; border-radius:9px; padding:0.6rem 1rem;
    }

    /* ---------- Download buttons (Iris Purple) ---------- */
    div[data-testid="stDownloadButton"] > button,
    div.stDownloadButton > button {
        background: #6D5DF6 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 9px !important;
        padding: 0.6rem 1rem !important;
    }
    div[data-testid="stDownloadButton"] > button:hover,
    div.stDownloadButton > button:hover {
        background: #5B4FE0 !important;
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def build_json_export(result):
    data = {
        "coverage": result["coverage"],
        "user_stories": result["stories"],
        "acceptance_criteria": result["criteria"],
    }
    return json.dumps(data, indent=2)


def build_csv_export(result):
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
    lines = ["## User Stories", ""]
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


def build_xlsx_export(result):
    """Real .xlsx built with openpyxl, which is already a project dependency
    (used by document_converter for reading uploaded spreadsheets)."""
    from openpyxl import Workbook

    wb = Workbook()
    ws1 = wb.active
    ws1.title = "User Stories"
    ws1.append(["Story ID", "Epic", "Feature", "Title", "Actor", "Priority", "User Story"])
    for s in result["stories"]:
        ws1.append([s["id"], s["epic"], s["feature"], s["title"], s.get("actor", ""), s["priority"], s["story"]])

    ws2 = wb.create_sheet("Acceptance Criteria")
    ws2.append(["Story ID", "Scenario", "Step Keyword", "Step Text"])
    for c in result["criteria"]:
        for scenario in c["scenarios"]:
            steps = scenario.get("steps", [])
            if steps:
                for step in steps:
                    ws2.append([c["id"], scenario.get("scenario", ""), step["keyword"], step["text"]])
            else:
                ws2.append([c["id"], scenario.get("scenario", ""), "", ""])

    for ws in (ws1, ws2):
        for col_cells in ws.columns:
            length = max(len(str(c.value)) if c.value else 0 for c in col_cells)
            ws.column_dimensions[col_cells[0].column_letter].width = min(max(length + 2, 12), 60)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def priority_badge(priority):
    p = (priority or "Medium").lower()
    cls = "priority-medium"
    if p == "high":
        cls = "priority-high"
    elif p == "low":
        cls = "priority-low"
    return f'<span class="badge {cls}">Priority: {priority}</span>'



with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">Automated User Story Creation Platform</div>'
        '<div class="sidebar-tag">AI Requirement to User Story Generator</div>',
        unsafe_allow_html=True,
    )

    for label in NAV_ITEMS:
        if label == st.session_state.nav_page:
            st.markdown(
                f'<div class="nav-active">{label}</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.button(label, key=f"nav_{label}", use_container_width=True):
                st.session_state.nav_page = label
                st.rerun()

    st.markdown(
        """
        <div class="upgrade-card">
            <div class="title">AI User Story Creation</div>
            <div class="desc">Transform software requirements into clear, structured, and professional user stories with intelligent AI assistance..</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    


header_l, header_r = st.columns([3, 1])
with header_l:
    st.markdown(
        '<div class="app-header"><div>'
        '<h1>Build Better Software Requirements </h1>'
        '<p>Transform your requirements into structured user stories and acceptance criteria with AI.</p>'
        '</div></div>',
        unsafe_allow_html=True,
    )
with header_r:
    st.write("")
    if st.button("New Requirement", type="primary", use_container_width=True):
        st.session_state.pending_req_text = ""
        st.session_state.generated_result = None
        st.session_state.last_uploaded_file = None
        st.session_state.pipeline_status = {key: "pending" for key, _ in PIPELINE_STEPS}
        st.session_state.nav_page = "Dashboard"
        st.rerun()


c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""<div class="stat-card">
        <div class="label">Requirements (this session)</div>
        <div class="value">{st.session_state.session_requirements}</div>
        <div class="sub neutral">Since app was opened</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""<div class="stat-card">
        <div class="label">User Stories (this session)</div>
        <div class="value">{st.session_state.session_stories}</div>
        <div class="sub neutral">Across all generations</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """<div class="stat-card">
        <div class="label">Languages Supported</div>
        <div class="value">55+</div>
        <div class="sub neutral">Auto-detected via langdetect</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c4:
    dur = f"{st.session_state.last_duration:.1f}s" if st.session_state.last_duration else "—"
    st.markdown(
        f"""<div class="stat-card">
        <div class="label">Last Generation Time</div>
        <div class="value">{dur}</div>
        <div class="sub neutral">Gemini response latency</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.write("")


if st.session_state.nav_page != "Dashboard":
    st.markdown(
        f"""<div class="panel" style="text-align:center; padding:3rem 1rem;">
        <h3 style="margin-top:0.6rem;">{st.session_state.nav_page}</h3>
        <p style="color:#667085; font-size:0.9rem;">This section isn't wired up yet in this build —
        the working generator lives on the Dashboard page.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    st.stop()


col_input, col_pipeline, col_output = st.columns([1, 0.6, 1.8], gap="medium")


with col_input:
    st.markdown(
        '<div class="panel-title"><div class="left">'
        '<div class="step-badge">1</div><h3>Enter Requirement</h3></div></div>',
        unsafe_allow_html=True,
    )

    
    if st.session_state.get("pending_req_text") is not None:
        st.session_state.req_box = st.session_state.pending_req_text
        st.session_state.pending_req_text = None

    st.text_area(
        "Requirement",
        key="req_box",
        height=190,
        max_chars=5000,
        placeholder="Type your software requirement here...",
        label_visibility="collapsed",
    )
    st.caption(f"{len(st.session_state.req_box)} / 5000 characters")

    st.markdown("**Or upload a document**")
    uploaded_file = st.file_uploader(
        "Upload requirement document",
        type=["pdf", "docx", "pptx", "xlsx"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None and st.session_state.last_uploaded_file != uploaded_file.name:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        try:
            with st.spinner("Converting document..."):
                requirement_text = convert_document_to_markdown(tmp_path)
            st.session_state.pending_req_text = requirement_text
            st.session_state.last_uploaded_file = uploaded_file.name
            st.success("Document uploaded and converted successfully.")
        except Exception as e:
            st.error(f"Failed to convert document: {e}")
        finally:
            os.remove(tmp_path)
        st.rerun()

    generate_clicked = st.button("Generate User Stories", type="primary", use_container_width=True)

with col_pipeline:
    st.markdown(
        '<div class="panel-title"><div class="left"><h3>AI Processing Pipeline</h3></div></div>',
        unsafe_allow_html=True,
    )
    pipeline_slot = st.empty()

    def render_pipeline():
        rows = []
        for key, label in PIPELINE_STEPS:
            status = st.session_state.pipeline_status.get(key, "pending")
            if status == "done":
                dot, sub = '<div class="pipeline-dot done">✓</div>', "Completed"
            elif status == "active":
                dot, sub = '<div class="pipeline-dot active">●</div>', "Processing..."
            elif status == "skipped":
                dot, sub = '<div class="pipeline-dot done">–</div>', "Not required"
            else:
                dot, sub = '<div class="pipeline-dot pending">○</div>', "Pending"
            rows.append(
                f'<div class="pipeline-row">{dot}'
                f'<div class="pipeline-text"><div class="title">{label}</div>'
                f'<div class="sub">{sub}</div></div></div>'
            )
        pipeline_slot.markdown("".join(rows), unsafe_allow_html=True)

    render_pipeline()

with col_output:
    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.markdown(
            '<div class="panel-title"><div class="left">'
            '<div class="step-badge">2</div><h3>Generated Output</h3></div></div>',
            unsafe_allow_html=True,
        )
    with header_right:
        if st.session_state.last_duration:
            st.caption(f"{st.session_state.last_duration:.2f}s")

    output_slot = st.container()

    def render_empty_output():
        with output_slot:
            st.markdown(
                """<div style="text-align:center; padding:2.4rem 0.5rem; color:#98A1BC;">
                <div style="margin-top:0.5rem; font-size:0.88rem;">
                Your generated user stories and acceptance criteria will appear here.</div>
                </div>""",
                unsafe_allow_html=True,
            )

    if st.session_state.generated_result is None:
        render_empty_output()


if generate_clicked:
    requirement_text = st.session_state.get("req_box", "")

    if not requirement_text.strip():
        st.warning("Please enter a requirement or upload a document.")
    else:
        status = st.session_state.pipeline_status
        status["received"] = "done"
        render_pipeline()

        status["lang"] = "active"
        render_pipeline()
        start = time.time()
        english_text, detected_lang = translate_to_english(requirement_text)
        st.session_state.detected_lang = detected_lang
        status["lang"] = "done"

        if detected_lang != "en":
            status["translate"] = "done"
        else:
            status["translate"] = "skipped"
        render_pipeline()

        status["analysis"] = "active"
        render_pipeline()

        try:
            with col_pipeline:
                with st.spinner("Calling Gemini..."):
                    result = generate(english_text)
            elapsed = time.time() - start

            status["analysis"] = "done"
            status["stories"] = "done"
            status["export"] = "done"
            render_pipeline()

            st.session_state.generated_result = result
            st.session_state.last_duration = elapsed
            st.session_state.session_requirements += 1
            st.session_state.session_stories += len(result["stories"])

        except RuntimeError as e:
            status["analysis"] = "pending"
            status["stories"] = "pending"
            status["export"] = "pending"
            render_pipeline()
            with col_output:
                st.error(str(e))
            st.session_state.generated_result = None

        st.rerun()


if st.session_state.generated_result:
    result = st.session_state.generated_result

    with col_output:
        tab_stories, tab_ac, tab_json, tab_preview = st.tabs(
            ["User Stories", "Acceptance Criteria", "JSON Output", "Preview"]
        )

        with tab_stories:
            stories = result["stories"]
           
            for i in range(0, len(stories), 2):
                pair = stories[i:i + 2]
                grid_cols = st.columns(2)
                for col, s in zip(grid_cols, pair):
                    with col:
                        st.markdown(
                            f"""<div class="story-card">
                            <div class="top"><span class="id">{s['id']} — {s['title']}</span>{priority_badge(s['priority'])}</div>
                            <div style="margin-bottom:0.4rem;">
                                <span class="badge module">{s['epic']} · {s['feature']}</span>
                                <span class="badge actor">{s.get('actor','')}</span>
                            </div>
                            <div style="font-size:0.87rem; color:#344054;">{s['story']}</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )

        with tab_ac:
            for c in result["criteria"]:
                with st.expander(f"{c['id']}", expanded=False):
                    for scenario in c["scenarios"]:
                        st.markdown(f"**Scenario: {scenario.get('scenario','')}**")
                        for step in scenario.get("steps", []):
                            st.markdown(f"- **{step['keyword']}** {step['text']}")
                        st.markdown("")

        with tab_json:
            json_str = build_json_export(result)
            st.code(json_str, language="json")

        with tab_preview:
            st.markdown(build_md_export(result))

   
    st.write("")
    intel_col, export_col = st.columns([2, 1], gap="medium")

    with intel_col:
        st.markdown(
            '<div class="panel-title"><div class="left"><h3>Requirement Intelligence</h3></div></div>',
            unsafe_allow_html=True,
        )
        wc = len(st.session_state.req_box.split())
        cc = len(st.session_state.req_box)
        i1, i2, i3 = st.columns(3)
        with i1:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#667085;">Detected Language</div>'
                f'<div style="font-weight:700; font-size:1rem;">{st.session_state.detected_lang.upper()}</div>',
                unsafe_allow_html=True,
            )
        with i2:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#667085;">Requirement Length</div>'
                f'<div style="font-weight:700; font-size:1rem;">{wc} words · {cc} characters</div>',
                unsafe_allow_html=True,
            )
        with i3:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#667085;">Coverage</div>'
                f'<div style="font-weight:700; font-size:1rem;">'
                f'{result["coverage"]["epics"]} Epics · {result["coverage"]["features"]} Features · '
                f'{result["coverage"]["stories"]} Stories</div>',
                unsafe_allow_html=True,
            )

        st.write("")
        modules = sorted({s["feature"] for s in result["stories"]})
        chips = "".join(f'<span class="feature-chip">{m}</span>' for m in modules)
        st.markdown(
            f'<div style="font-size:0.78rem;color:#667085; margin-bottom:0.3rem;">Features Detected</div>{chips}',
            unsafe_allow_html=True,
        )

    with export_col:
        st.markdown(
            '<div class="panel-title"><div class="left"><h3>Export Results</h3></div></div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download JSON",
            data=build_json_export(result),
            file_name="user_stories_and_acceptance_criteria.json",
            mime="application/json",
            use_container_width=True,
            key="dl_json",
        )
        st.download_button(
            "Download Excel (.xlsx)",
            data=build_xlsx_export(result),
            file_name="user_stories_and_acceptance_criteria.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_xlsx",
        )
        st.download_button(
            "Download CSV",
            data=build_csv_export(result),
            file_name="user_stories_and_acceptance_criteria.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_csv",
        )
        st.download_button(
            "Download Markdown",
            data=build_md_export(result),
            file_name="user_stories_and_acceptance_criteria.md",
            mime="text/markdown",
            use_container_width=True,
            key="dl_md",
        )
        st.caption("JSON can also be copied straight from the JSON Output tab.")


st.write("")
st.markdown(
    '<div class="panel-title"><div class="left"><h3>System Architecture Overview</h3></div></div>',
    unsafe_allow_html=True,
)

arch_steps = [
    ("User Input", "Web interface"),
    ("Language Detection", "langdetect"),
    ("Translation Engine", "deep-translator"),
    ("Gemini AI", "Analysis & structuring"),
    ("User Story Engine", "Epics → Features → Stories"),
    ("Acceptance Criteria", "Given / When / Then"),
    ("Export Layer", "JSON · CSV · XLSX · MD"),
]

flow_html = '<div class="arch-flow">'
for idx, (title, sub) in enumerate(arch_steps):
    flow_html += (
        f'<div class="arch-step"><div class="box">'
        f'<div class="t">{title}</div><div class="s">{sub}</div>'
        f'</div></div>'
    )
    if idx < len(arch_steps) - 1:
        flow_html += '<div class="arch-arrow">→</div>'
flow_html += "</div>"

st.markdown(f'<div class="panel">{flow_html}</div>', unsafe_allow_html=True)