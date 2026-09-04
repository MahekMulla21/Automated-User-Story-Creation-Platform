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

TEMPLATES = [
    {"category": "Authentication", "title": "User Login & Signup",
     "desc": "Standard email/password authentication with account creation and session handling.",
     "text": "Users should be able to create an account using their email address and a password, and log back in later using those same credentials. The system should validate email format, enforce a minimum password strength, and keep the user signed in across sessions using a secure token. Users should also be able to log out from any device."},

    {"category": "Authentication", "title": "Password Reset",
     "desc": "Self-service password recovery via email link.",
     "text": "A user who has forgotten their password should be able to request a reset link by entering their registered email address. The system should send a time-limited, single-use link to that email. Clicking the link should let the user set a new password, and the old password should stop working immediately once the reset is complete."},

    {"category": "E-commerce", "title": "Shopping Cart",
     "desc": "Add, update, and remove items before checkout.",
     "text": "Customers browsing the store should be able to add products to a cart, adjust quantities, and remove items before checking out. The cart should persist if the customer navigates away and comes back, show a running subtotal, and warn the customer if an item's stock changes while it's in their cart."},

    {"category": "E-commerce", "title": "Checkout & Payment",
     "desc": "Multi-step checkout with address, shipping, and payment.",
     "text": "During checkout, a customer should be able to enter or select a shipping address, choose a shipping method, and pay using a credit card or saved payment method. The system should validate the address and card details, show an order summary before final confirmation, and email a receipt once payment succeeds."},

    {"category": "Payments", "title": "Subscription Billing",
     "desc": "Recurring billing for monthly/annual subscription plans.",
     "text": "Subscribers should be billed automatically on a recurring monthly or annual cycle depending on the plan they selected. The system should retry failed payments a limited number of times before suspending the account, notify the subscriber by email before and after each charge, and let them view their billing history."},

    {"category": "Notifications", "title": "Email & Push Alerts",
     "desc": "Configurable notification preferences across channels.",
     "text": "Users should receive notifications for key account activity — such as new messages, order updates, or security alerts — through email and push notifications. Users should be able to control which notification types they receive and through which channel, from a preferences page, without needing to contact support."},

    {"category": "Search", "title": "Product/Content Search & Filters",
     "desc": "Keyword search with filtering and sorting.",
     "text": "Users should be able to search for products or content using free-text keywords and narrow results using filters such as category, price range, and rating. Results should be sortable by relevance, price, and newest first, and the search should tolerate minor typos and return zero-result guidance when nothing matches."},

    {"category": "Admin", "title": "Admin Dashboard & User Management",
     "desc": "Internal tools for managing user accounts and permissions.",
     "text": "Administrators should have access to a dashboard listing all registered users, with the ability to search, view account details, suspend or reactivate accounts, and change a user's role or permission level. All administrative actions should be logged with a timestamp and the admin who performed them."},

    {"category": "Reporting", "title": "Sales/Usage Reports",
     "desc": "Exportable reports summarizing activity over a date range.",
     "text": "Business users should be able to generate a report summarizing sales or usage activity over a selected date range, broken down by day, product, or region as applicable. The report should be viewable on screen and exportable as a CSV or Excel file for further analysis."},

    {"category": "Onboarding", "title": "New User Onboarding Flow",
     "desc": "Guided first-run experience for new accounts.",
     "text": "First-time users should be guided through a short setup flow after registration — confirming their email, setting basic preferences, and completing their profile. Users should be able to skip optional steps and return to finish them later, and the flow should not reappear once completed."},

    {"category": "File Management", "title": "Document Upload & Storage",
     "desc": "Upload, organize, and retrieve files with access control.",
     "text": "Users should be able to upload documents up to a defined size limit, organize them into folders, and share individual files or folders with specific teammates. Only users with granted access should be able to view or download a shared file, and file owners should be able to revoke access at any time."},

    {"category": "Messaging", "title": "In-App Chat/Messaging",
     "desc": "Real-time direct messaging between users.",
     "text": "Users should be able to send and receive direct messages with other users in real time, see when a message has been delivered and read, and view their full conversation history. Users should also be able to block another user, which stops that user from sending further messages."},

    {"category": "Booking", "title": "Appointment Scheduling",
     "desc": "Book, reschedule, and cancel time-slot appointments.",
     "text": "Customers should be able to view available time slots for a service and book an appointment, receiving a confirmation email with the details. Customers should be able to reschedule or cancel an existing appointment up to a configurable cutoff time before it starts, and staff should see a calendar view of all upcoming bookings."},

    {"category": "Social", "title": "User Profiles & Follow System",
     "desc": "Public profiles with a follow/following relationship.",
     "text": "Each user should have a public profile showing their basic information and activity, which other users can view and choose to follow. Users should see a feed of activity from accounts they follow, and be able to unfollow at any time. Profile visibility should be configurable as public or private."},

    {"category": "Support", "title": "Helpdesk/Ticketing System",
     "desc": "Customer support ticket submission and tracking.",
     "text": "Customers should be able to submit a support ticket describing their issue, attach screenshots, and track its status (open, in progress, resolved). Support agents should be able to respond to tickets, change their status, and reassign them to another agent, with customers notified by email on any update."},

    {"category": "Inventory", "title": "Inventory & Stock Management",
     "desc": "Track stock levels and trigger low-stock alerts.",
     "text": "The system should track stock levels for each product across one or more warehouses, decrementing stock automatically as orders are placed. When stock for an item falls below a configurable threshold, the system should alert the relevant staff so they can reorder, and prevent overselling by blocking checkout for out-of-stock items."},

    {"category": "Subscription", "title": "Plan Upgrade/Downgrade",
     "desc": "Self-service plan changes with prorated billing.",
     "text": "Subscribers should be able to switch between available plans from their account settings. Upgrades should take effect immediately with a prorated charge for the remainder of the billing cycle, while downgrades should take effect at the start of the next billing cycle. The subscriber should see a clear summary of the change before confirming."},

    {"category": "User Profile", "title": "Account Settings & Preferences",
     "desc": "Manage personal info, security, and app preferences.",
     "text": "Users should be able to update their personal information (name, email, phone), change their password, and manage preferences such as language, timezone, and notification settings from a single account settings page. Changing the email address should require confirming the new address before it takes effect."},

    {"category": "Integration", "title": "Third-Party API Integration",
     "desc": "Connect an external service via API keys or OAuth.",
     "text": "Users should be able to connect a third-party service to their account using an API key or OAuth authorization, view the current connection status, and disconnect it at any time. The system should sync relevant data from the connected service on a schedule and surface a clear error state if the connection fails or the credentials expire."},

    {"category": "Security", "title": "Role-Based Access Control",
     "desc": "Restrict features and data by user role.",
     "text": "The system should support multiple user roles (e.g. admin, editor, viewer), each with a defined set of permissions controlling which features and data they can access. Attempting to access a restricted action should be blocked with a clear message, and administrators should be able to assign or change a user's role."},
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
    "history": [],
    "active_tab": "User Stories",
}
for _k, _v in _defaults.items():
    st.session_state.setdefault(_k, _v)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    /* ==========================================================
       DARK THEME PALETTE
       --bg-primary:     #0A1631
       --bg-secondary:   #101F42
       --bg-card:        #162750
       --bg-card-hover:  #1B3264
       --accent-primary: #5B8CFF
       --accent-secondary:#4F7DDB
       --border-color:   rgba(91, 140, 255, 0.25)
       --text-primary:   #FFFFFF
       --text-secondary: #C7D2FE
       --success-color:  #22C55E
       --warning-color:  #F59E0B
       ========================================================== */

    html, body {
        color-scheme: dark !important;
    }
    .stApp {
        color-scheme: dark !important;
        --primary-color: #5B8CFF;
        --background-color: #0A1631;
        --secondary-background-color: #162750;
        --text-color: #FFFFFF;
        background: linear-gradient(180deg, #0A1631 0%, #101F42 100%) !important;
    }
    .main .block-container,
    .main .block-container p,
    .main .block-container span,
    .main .block-container label,
    .main .block-container li,
    .main .block-container div {
        color: #C7D2FE;
    }

    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    h1, h2, h3, .display-font { font-family: 'Sora', sans-serif; }

    #MainMenu, footer { visibility: hidden; }

    div.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }

    /* ---------- Sidebar (unchanged) ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1330 0%, #131C40 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    section[data-testid="stSidebar"] * { color: #C9CEE3 !important; }
    section[data-testid="stSidebar"] .sidebar-brand {
        font-family: 'Sora', sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        line-height: 1.3;
        color: #FFFFFF !important;
        padding: 0.4rem 0 0.1rem 0;
    }
    section[data-testid="stSidebar"] .sidebar-tag {
        font-size: 0.72rem;
        color: #7C86B8 !important;
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
        color: #A6ADCF !important;
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
        color: #FFFFFF !important;
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

    /* ---------- Header ---------- */
    .app-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.3rem; }
    .app-header h1 { font-size:1.55rem; margin:0; color:#FFFFFF !important; }
    .app-header p { color:#C7D2FE !important; font-size:0.92rem; margin-top:0.15rem; }

    /* ---------- Stat cards ---------- */
    .stat-card {
        background:#162750; border:1px solid rgba(91,140,255,0.25); border-radius:14px;
        padding:1.1rem 1.2rem; height:100%;
        border-top: 3px solid #5B8CFF;
        box-shadow: 0 4px 18px rgba(0,0,0,0.25);
    }
    .stat-card .label { color:#C7D2FE !important; font-size:0.82rem; margin-bottom:0.15rem; }
    .stat-card .value { font-family:'Sora',sans-serif; font-size:1.55rem; font-weight:700; color:#FFFFFF !important; }
    .stat-card .sub { font-size:0.76rem; color:#22C55E !important; margin-top:0.15rem; }
    .stat-card .sub.neutral { color:#8CA0DA !important; }

    /* ---------- Requirement text area ---------- */
    div[data-testid="stTextArea"] textarea {
        border: 2.5px solid #5B8CFF !important;
        border-radius: 10px !important;
        background: #101F42 !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border: 1.5px solid #5B8CFF !important;
        box-shadow: 0 0 0 3px rgba(91,140,255,0.2) !important;
    }
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #8CA0DA !important;
        opacity: 1 !important;
    }

    /* ---------- Compact file uploader ---------- */
    div[data-testid="stFileUploader"] section {
        padding: 0.55rem 0.8rem !important;
        border: 1.5px dashed #5B8CFF !important;
        border-radius: 10px !important;
        background: #101F42 !important;
        min-height: unset !important;
    }
    div[data-testid="stFileUploader"] section > div { padding: 0 !important; }
    div[data-testid="stFileUploader"] section * { color: #C7D2FE !important; }
    div[data-testid="stFileUploader"] small,
    div[data-testid="stFileUploader"] small * {
        color: #A9B8E8 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stFileUploader"] button {
        border: 1px solid rgba(91,140,255,0.35) !important;
        color: #5B8CFF !important;
        background: #1B3264 !important;
        border-radius: 8px !important;
    }

    /* ---------- Boxed captions inside the upload card ----------
   Small bordered/background boxes around each line so they're
   clearly visible, matching the highlighted look. */
.upload-marker + div[data-testid="stVerticalBlockBorderWrapper"] small {
    display: inline-block;
    background: rgba(91,140,255,0.18) !important;
    border: 1px solid rgba(91,140,255,0.45) !important;
    border-radius: 6px;
    padding: 0.25rem 0.6rem;
}

.upload-marker + div[data-testid="stVerticalBlockBorderWrapper"] p:has(strong) {
    display: inline-block;
    background: rgba(91,140,255,0.18) !important;
    border: 1px solid rgba(91,140,255,0.45) !important;
    border-radius: 6px;
    padding: 0.25rem 0.6rem;
    margin-bottom: 0.5rem !important;
}


/* Boxed "Or upload a document" label */
.boxed-label {
    display: inline-block;
    font-weight: 700;
    background: rgba(91,140,255,0.18) !important;
    border: 1px solid rgba(91,140,255,0.45) !important;
    border-radius: 6px;
    padding: 0.25rem 0.6rem;
    margin-bottom: 0.5rem;
    color: #F1F5FF !important;
}
/* Boxed captions: "0 / 5000 characters" and "Max 200MB per file" line */
.upload-marker + div[data-testid="stVerticalBlockBorderWrapper"] small {
    display: inline-block;
    background: rgba(91,140,255,0.18) !important;
    border: 1px solid rgba(91,140,255,0.45) !important;
    border-radius: 6px;
    padding: 0.25rem 0.6rem;
    color: #F1F5FF !important;
    font-weight: 700 !important;
}

    /* ---------- Top header bar ---------- */
    header[data-testid="stHeader"] {
        background: #0A1631 !important;
        height: 0px;
    }
    div[data-testid="stDecoration"] { background: transparent !important; }
    div[data-testid="stToolbar"] { background: #0A1631 !important; }

    /* ---------- Unify Streamlit's native bordered containers with our panel look ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
        border-color: rgba(91,140,255,0.25) !important;
        background: #162750 !important;
    }

    /* ---------- Responsive output panel ---------- */
    @media (max-width: 768px) {
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"] > div[style*="overflow"] {
            max-height: 360px !important;
        }
    }

   /* ---------- Tab-style buttons (User Stories / Acceptance Criteria / JSON / Preview) ---------- */

/* Inactive buttons (type="secondary") */
div[data-testid="stButton"] button[kind="secondary"] {
    background: rgba(27,50,100,0.65) !important;
    border: 1px solid rgba(91,140,255,0.25) !important;
    border-top: 3px solid rgba(91,140,255,0.45) !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    color: #C7D2FE !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.25);
    transition: all 0.15s ease;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    border-color: #5B8CFF !important;
    background: #1B3264 !important;
    color: #FFFFFF !important;
}

/* Active button (type="primary") */
div[data-testid="stButton"] button[kind="primary"] {
    background: #1B3264 !important;
    border: 1px solid #5B8CFF !important;
    border-top: 3px solid #5B8CFF !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 0 1px #5B8CFF inset, 0 4px 14px rgba(91,140,255,0.25);
}

@media (max-width: 480px) {
    div[data-testid="stButton"] button[kind="secondary"],
    div[data-testid="stButton"] button[kind="primary"] {
        padding: 0.42rem 0.75rem !important;
        font-size: 0.78rem !important;
    }
}
    /* ---------- JSON output card ---------- */
    div[data-testid="stCodeBlock"] {
        border: 1px solid rgba(91,140,255,0.25) !important;
        border-radius: 10px !important;
        background: #0A1631 !important;
        max-height: 420px !important;
        overflow: auto !important;
    }
    div[data-testid="stCodeBlock"] pre {
        max-height: 420px !important;
        overflow: auto !important;
        white-space: pre !important;
        font-size: 0.82rem !important;
        line-height: 1.5 !important;
        color: #C7D2FE !important;
    }
    @media (max-width: 768px) {
        div[data-testid="stCodeBlock"] pre { font-size: 0.74rem !important; }
    }

    /* ---------- Expanders / captions ---------- */
    div[data-testid="stExpander"],
    div[data-testid="stExpander"] details,
    div[data-testid="stExpander"] summary {
        background-color: #162750 !important;
        border-color: rgba(91,140,255,0.25) !important;
    }
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary *,
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: #FFFFFF !important;
    }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        background-color: #101F42 !important;
        color: #C7D2FE !important;
    }
    .main .block-container small { color: #A9B8E8 !important; font-weight: 500; }

    /* ---------- Panels ---------- */
    .panel-title {
        display:flex; align-items:center; justify-content:space-between;
        margin-bottom:0.9rem;
    }
    .panel-title .left { display:flex; align-items:center; gap:8px; }
    .panel-title .step-badge {
        width:22px; height:22px; border-radius:6px; background:#5B8CFF; color:white !important;
        font-size:0.75rem; font-weight:700; display:flex; align-items:center; justify-content:center;
    }
    .panel-title h3 { margin:0; font-size:1.02rem; color:#FFFFFF !important; }

    .pipeline-row { display:flex; align-items:center; gap:10px; padding:0.42rem 0; }
    .pipeline-dot {
        width:26px; height:26px; border-radius:50%; flex-shrink:0;
        display:flex; align-items:center; justify-content:center; font-size:0.78rem;
    }
    .pipeline-dot.done { background:rgba(34,197,94,0.15); color:#22C55E !important; }
    .pipeline-dot.active { background:rgba(91,140,255,0.18); color:#5B8CFF !important; }
    .pipeline-dot.pending { background:rgba(255,255,255,0.06); color:#7C8AB8 !important; }
    .pipeline-text .title { font-size:0.86rem; font-weight:600; color:#FFFFFF !important; }
    .pipeline-text .sub { font-size:0.74rem; color:#8CA0DA !important; }

    .story-card {
        border:1px solid rgba(91,140,255,0.25); border-radius:12px; padding:0.9rem 1rem; margin-bottom:0.7rem;
        background:#1B3264; height:100%;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .story-card .top { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem;}
    .story-card .top .id { font-weight:700; color:#FFFFFF !important; font-size:0.92rem; }
    .badge {
        display:inline-block; font-size:0.7rem; font-weight:600; padding:0.15rem 0.55rem;
        border-radius:20px; margin-right:0.35rem;
    }
    .badge.priority-high { background:rgba(248,113,113,0.15); color:#F87171 !important; }
    .badge.priority-medium { background:rgba(245,158,11,0.15); color:#F59E0B !important; }
    .badge.priority-low { background:rgba(34,197,94,0.15); color:#22C55E !important; }
    .badge.module { background:rgba(91,140,255,0.15); color:#5B8CFF !important; }
    .badge.actor { background:rgba(56,189,248,0.15); color:#38BDF8 !important; }

    .feature-chip {
        display:inline-block; background:rgba(91,140,255,0.15); color:#5B8CFF !important; font-size:0.75rem;
        padding:0.2rem 0.6rem; border-radius:20px; margin:0.15rem 0.3rem 0.15rem 0;
        font-weight:500;
        border: 1px solid rgba(91,140,255,0.25);
    }

    /* ---------- Recent Generations / History table ---------- */
    .gen-table { width:100%; border-collapse:collapse; font-size:0.85rem; }
    .gen-table th {
        text-align:left; color:#C7D2FE !important; font-weight:600;
        padding:0.5rem 0.6rem; border-bottom:1px solid rgba(91,140,255,0.25);
    }
    .gen-table td {
        padding:0.6rem 0.6rem; border-bottom:1px solid rgba(255,255,255,0.06); color:#FFFFFF !important;
    }
    .status-badge {
        background:rgba(34,197,94,0.15); color:#22C55E !important; font-size:0.72rem; font-weight:600;
        padding:0.15rem 0.55rem; border-radius:20px;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg,#5B8CFF,#4F7DDB);
        color: #FFFFFF !important;
        border:none; font-weight:600; border-radius:9px; padding:0.6rem 1rem;
        box-shadow: 0 4px 14px rgba(91,140,255,0.3);
    }

    /* ---------- Fix clipped glow on primary buttons sitting in slim containers ----------
       NOTE: this used to force `overflow: visible !important` on EVERY
       [data-testid="column"] and [data-testid="stVerticalBlock"] on the page. That also
       overrode the inline `overflow: auto` Streamlit sets on the fixed-height results
       container (st.container(height=480)) used for the User Stories / Acceptance
       Criteria / JSON Output / Preview tabs, so that content spilled out of its box and
       visually collided with the download buttons rendered underneath it. Fixed by only
       giving primary buttons a little vertical margin, instead of touching overflow on
       their parent containers. */
    div.stButton > button[kind="primary"] {
        margin-top: 4px;
        margin-bottom: 4px;
    }

    /* ---------- Download buttons ---------- */
    div[data-testid="stDownloadButton"] > button,
    div.stDownloadButton > button {
        background: #5B8CFF !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 9px !important;
        padding: 0.6rem 1rem !important;
        box-shadow: 0 4px 14px rgba(91,140,255,0.25);
    }
    div[data-testid="stDownloadButton"] > button:hover,
    div.stDownloadButton > button:hover {
        background: #4F7DDB !important;
        color: #FFFFFF !important;
    }

    /* ---------- Alerts (warning / error / success / info) ---------- */
    div[data-testid="stAlert"] {
        background: #162750 !important;
        border: 1px solid rgba(91,140,255,0.25) !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stAlert"] * { color: #FFFFFF !important; }
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


def render_history_table(entries):
    """Builds the Recent Generations / History table. entries is expected
    newest-first."""
    if not entries:
        return (
            '<div style="text-align:center;color:#8CA0DA;padding:2.2rem 0.5rem;">'
            "No generations yet — results will appear here after you generate "
            "your first user stories."
            "</div>"
        )
    rows = []
    for i, e in enumerate(entries, start=1):
        rows.append(
            f"<tr><td>{i}</td><td>{e['requirement']}</td><td>{e['lang_display']}</td>"
            f"<td>{e['timestamp']}</td><td>{e['duration']}</td>"
            f"<td><span class=\"status-badge\">{e['status']}</span></td></tr>"
        )
    return (
        '<table class="gen-table"><thead><tr>'
        "<th>#</th><th>Requirement</th><th>Language</th>"
        "<th>Generated On</th><th>Time</th><th>Status</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


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
            <div class="desc">Transform software requirements into clear, structured, and professional user stories with intelligent AI assistance.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


header_l, header_r = st.columns([3, 1])
with header_l:
    st.markdown(
        '<div class="app-header"><div>'
        "<h1>Build Better Software Requirements</h1>"
        "<p>Transform your requirements into structured user stories and acceptance criteria with AI.</p>"
        "</div></div>",
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


if st.session_state.nav_page == "History":
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title"><div class="left"><h3>Generation History</h3></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            render_history_table(list(reversed(st.session_state.history))),
            unsafe_allow_html=True,
        )
    st.stop()


if st.session_state.nav_page == "Templates":
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title"><div class="left"><h3>Requirement Templates</h3></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#8CA0DA; font-size:0.85rem; margin-top:-0.4rem;">'
            "Start from a ready-made requirement instead of a blank page. Pick one below, "
            "adjust it to fit your product, and generate stories straight from it."
            "</p>",
            unsafe_allow_html=True,
        )

        for i in range(0, len(TEMPLATES), 2):
            pair = TEMPLATES[i:i + 2]
            t_cols = st.columns(2)
            for col, tpl in zip(t_cols, pair):
                with col:
                    st.markdown(
                        f"""<div class="story-card">
                        <div class="top"><span class="id">{tpl['title']}</span></div>
                        <div style="margin-bottom:0.5rem;">
                            <span class="badge module">{tpl['category']}</span>
                        </div>
                        <div style="font-size:0.85rem; color:#C7D2FE; margin-bottom:0.6rem;">{tpl['desc']}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    if st.button("Use This Template", key=f"tpl_{tpl['title']}", use_container_width=True):
                        st.session_state.pending_req_text = tpl["text"]
                        st.session_state.nav_page = "Dashboard"
                        st.rerun()
    st.stop()


if st.session_state.nav_page == "Analytics":
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title"><div class="left"><h3>Analytics</h3></div></div>',
            unsafe_allow_html=True,
        )

        history = st.session_state.history
        if not history:
            st.markdown(
                '<div style="text-align:center;color:#8CA0DA;padding:2.2rem 0.5rem;">'
                "No generations yet. Once you generate a few sets of user stories, this page "
                "will break down how you're using the platform."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            total_reqs = len(history)
            total_stories = sum(e.get("stories_count", 0) for e in history)
            durations = [float(e["duration"].rstrip("s")) for e in history if e.get("duration")]
            avg_duration = sum(durations) / len(durations) if durations else 0
            avg_stories = total_stories / total_reqs if total_reqs else 0

            a1, a2, a3, a4 = st.columns(4)
            with a1:
                st.markdown(
                    f"""<div class="stat-card"><div class="label">Total Requirements</div>
                    <div class="value">{total_reqs}</div>
                    <div class="sub neutral">Processed this session</div></div>""",
                    unsafe_allow_html=True,
                )
            with a2:
                st.markdown(
                    f"""<div class="stat-card"><div class="label">Total Stories Generated</div>
                    <div class="value">{total_stories}</div>
                    <div class="sub neutral">Across all requirements</div></div>""",
                    unsafe_allow_html=True,
                )
            with a3:
                st.markdown(
                    f"""<div class="stat-card"><div class="label">Avg. Stories / Requirement</div>
                    <div class="value">{avg_stories:.1f}</div>
                    <div class="sub neutral">Signal of requirement detail</div></div>""",
                    unsafe_allow_html=True,
                )
            with a4:
                st.markdown(
                    f"""<div class="stat-card"><div class="label">Avg. Generation Time</div>
                    <div class="value">{avg_duration:.1f}s</div>
                    <div class="sub neutral">Gemini response latency</div></div>""",
                    unsafe_allow_html=True,
                )

            st.write("")
            lang_counts = {}
            for e in history:
                lang_counts[e["lang_display"]] = lang_counts.get(e["lang_display"], 0) + 1

            chart_l, chart_r = st.columns(2)
            with chart_l:
                st.markdown(
                    '<div style="font-size:0.85rem;font-weight:600;color:#FFFFFF;margin-bottom:0.4rem;">'
                    "Requirement Language Breakdown</div>",
                    unsafe_allow_html=True,
                )
                st.bar_chart(lang_counts)
            with chart_r:
                st.markdown(
                    '<div style="font-size:0.85rem;font-weight:600;color:#FFFFFF;margin-bottom:0.4rem;">'
                    "Stories Generated Per Requirement</div>",
                    unsafe_allow_html=True,
                )
                st.bar_chart([e.get("stories_count", 0) for e in history])

            st.write("")
            st.markdown(
                '<div style="font-size:0.85rem;font-weight:600;color:#FFFFFF;margin-bottom:0.4rem;">'
                "Generation Time Trend</div>",
                unsafe_allow_html=True,
            )
            st.line_chart(durations)
    st.stop()


if st.session_state.nav_page == "Settings":
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title"><div class="left"><h3>How to Use This Platform</h3></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#8CA0DA; font-size:0.85rem; margin-top:-0.4rem;">'
            "A short walkthrough so you get useful output on the first try."
            "</p>",
            unsafe_allow_html=True,
        )

        with st.expander("1. Describe your requirement", expanded=True):
            st.markdown(
                "Write your requirement in plain language on the Dashboard, the way you'd "
                "describe it to a teammate. There's no need to format it as a user story yourself — "
                "just explain what the feature should do, who it's for, and any constraints that matter. "
                "More context (business rules, edge cases, who the users are) means more specific output."
            )
        with st.expander("2. Or upload an existing document"):
            st.markdown(
                "If the requirement already lives in a PRD, spec, or meeting notes, upload it directly "
                "as a PDF, Word document, PowerPoint, or Excel file instead of retyping it. The platform "
                "converts it to text automatically and drops it into the requirement box, which you can "
                "edit before generating."
            )
        with st.expander("3. Language handling"):
            st.markdown(
                "Requirements don't need to be in English. The platform detects the language "
                "automatically and translates it before sending it to the AI model, then reports "
                "the detected language back to you in the pipeline panel and in your history."
            )
        with st.expander("4. Review the AI Processing Pipeline"):
            st.markdown(
                "While a requirement is being processed, the middle panel shows each stage — "
                "language detection, translation, AI analysis, and story generation — so you can "
                "see what's happening and roughly how long it's taking."
            )
        with st.expander("5. Work with the output"):
            st.markdown(
                "Results are organized into four views: **User Stories**, **Acceptance Criteria** "
                "written as Given/When/Then scenarios, a raw **JSON Output** for developers, and a "
                "**Preview** formatted as Markdown. Switch between them using the buttons above the "
                "results panel."
            )
        with st.expander("6. Export your work"):
            st.markdown(
                "Download a generation as JSON, Excel, CSV, or Markdown using the buttons below the "
                "results panel — whichever format fits your team's tools, whether that's Jira, a "
                "spreadsheet, or a docs folder."
            )
        with st.expander("7. Use a template to get started faster"):
            st.markdown(
                "Not sure how to phrase a requirement? Head to **Templates** for 20 ready-made "
                "requirements across common product areas — authentication, payments, search, "
                "admin tooling, and more. Selecting one loads it into the Dashboard for you to edit."
            )
        with st.expander("8. Track your usage"):
            st.markdown(
                "Every generation is logged. Visit **History** for a full record, or **Analytics** "
                "for a breakdown of story counts, languages used, and generation times."
            )
    st.stop()


if st.session_state.nav_page == "Help & Docs":
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title"><div class="left"><h3>Help & Documentation</h3></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#8CA0DA; font-size:0.85rem; margin-top:-0.4rem;">'
            "Answers to the questions we hear most, plus a bit more on what's happening under the hood."
            "</p>",
            unsafe_allow_html=True,
        )

        with st.expander("About This Platform", expanded=False):
            st.markdown(
                "This platform turns raw software requirements into structured user stories and "
                "Gherkin-style acceptance criteria using Google's Gemini models. It's built for product "
                "managers, business analysts, and engineering teams who want a faster, more consistent "
                "starting point for backlog grooming — not a replacement for human review."
            )

        st.write("")
        st.markdown(
            '<div style="font-size:0.9rem;font-weight:700;color:#FFFFFF;margin:0.6rem 0 0.4rem;">'
            "Frequently Asked Questions</div>",
            unsafe_allow_html=True,
        )
        with st.expander("What file types can I upload?"):
            st.markdown("PDF, Word (.docx), PowerPoint (.pptx), and Excel (.xlsx), up to 200MB per file.")
        with st.expander("Which languages are supported?"):
            st.markdown(
                "Over 55 languages. The platform detects the language automatically and translates "
                "it to English before generation, so you don't need to translate anything yourself."
            )
        with st.expander("Are my requirements stored anywhere?"):
            st.markdown(
                "Requirements and results are kept in your browser session (visible under History "
                "and Analytics) for as long as the app is open, so you can revisit past generations "
                "without redoing the work."
            )
        with st.expander("Can I edit the generated stories?"):
            st.markdown(
                "Yes — treat the output as a first draft. Export to Excel, CSV, or Markdown and "
                "refine wording, priorities, or scope before moving stories into Jira, Linear, or "
                "wherever your team tracks work."
            )
        with st.expander("Why does generation sometimes take longer?"):
            st.markdown(
                "Mostly the length and complexity of the requirement, plus current response times "
                "from the underlying model. Vague or very long requirements tend to take longer — "
                "being specific usually speeds things up."
            )
        with st.expander("What if the output doesn't match what I expected?"):
            st.markdown(
                "Add more detail to the requirement — specific user roles, business rules, and edge "
                "cases all help. Starting from a template in **Templates** and adapting it tends to "
                "produce more consistent results than a very short prompt."
            )

        st.write("")
        
    st.stop()

if st.session_state.nav_page != "Dashboard":
    st.session_state.nav_page = "Dashboard"


col_input, col_pipeline, col_output = st.columns([1, 0.6, 1.8], gap="medium")

with col_input:
    with st.container(border=True):
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

        st.markdown('<span class="boxed-label">Or upload a document</span>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload requirement document",
            type=["pdf", "docx", "pptx", "xlsx"],
            label_visibility="collapsed",
        )
        st.caption("PDF, DOCX, PPTX, XLSX · Max 200MB per file")

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
    with st.container(border=True):
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
    with st.container(border=True):
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

        result = st.session_state.generated_result

        with st.container(height=480):
            if result is None:
                st.markdown(
                    """<div style="text-align:center; padding:2.4rem 0.5rem; color:#8CA0DA;">
                    <div style="font-size:0.88rem;">
                    Your generated user stories and acceptance criteria will appear here.</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                tab_labels = ["User Stories", "Acceptance Criteria", "JSON Output", "Preview"]
                tab_cols = st.columns(len(tab_labels))
                for tcol, tlabel in zip(tab_cols, tab_labels):
                    with tcol:
                        btn_type = "primary" if st.session_state.active_tab == tlabel else "secondary"
                        if st.button(tlabel, key=f"tabbtn_{tlabel}", type=btn_type, use_container_width=True):
                            st.session_state.active_tab = tlabel
                            st.rerun()

                active = st.session_state.active_tab

                if active == "User Stories":
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
                                    <div style="font-size:0.87rem; color:#C7D2FE;">{s['story']}</div>
                                    </div>""",
                                    unsafe_allow_html=True,
                                )

                elif active == "Acceptance Criteria":
                    for c in result["criteria"]:
                        with st.expander(f"{c['id']}", expanded=False):
                            for scenario in c["scenarios"]:
                                st.markdown(f"**Scenario: {scenario.get('scenario','')}**")
                                for step in scenario.get("steps", []):
                                    st.markdown(f"- **{step['keyword']}** {step['text']}")
                                st.markdown("")

                elif active == "JSON Output":
                    st.code(build_json_export(result), language="json")

                elif active == "Preview":
                    st.markdown(
                        f'<div style="max-height:400px;overflow:auto;padding:0.75rem 1rem;'
                        f'border:1px solid rgba(91,140,255,0.25);border-radius:10px;background:#101F42;color:#C7D2FE;">'
                        f'{build_md_export(result)}</div>',
                        unsafe_allow_html=True,
                    )
        
        if result is not None:
            d1, d2, d3, d4 = st.columns(4)
            with d1:
                st.download_button(
                    "Download JSON",
                    data=build_json_export(result),
                    file_name="user_stories_and_acceptance_criteria.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_json",
                )
            with d2:
                st.download_button(
                    "Download Excel",
                    data=build_xlsx_export(result),
                    file_name="user_stories_and_acceptance_criteria.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_xlsx",
                )
            with d3:
                st.download_button(
                    "Download CSV",
                    data=build_csv_export(result),
                    file_name="user_stories_and_acceptance_criteria.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_csv",
                )
            with d4:
                st.download_button(
                    "Download Markdown",
                    data=build_md_export(result),
                    file_name="user_stories_and_acceptance_criteria.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="dl_md",
                )

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
            st.session_state.active_tab = "User Stories"

            snippet = requirement_text.strip().replace("\n", " ")
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."
            lang_display = (
                f"{detected_lang.upper()} → EN" if detected_lang != "en" else "EN"
            )
            st.session_state.history.append({
                "requirement": snippet,
                "lang_display": lang_display,
                "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                "duration": f"{elapsed:.2f}s",
                "status": "Completed",
                "stories_count": len(result["stories"]),
            })

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
    st.write("")
    with st.container(border=True):
        st.markdown(
            '<div class="panel-title"><div class="left"><h3>Requirement Intelligence</h3></div></div>',
            unsafe_allow_html=True,
        )
        wc = len(st.session_state.req_box.split())
        cc = len(st.session_state.req_box)
        i1, i2, i3 = st.columns(3)
        with i1:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#C7D2FE;">Detected Language</div>'
                f'<div style="font-weight:700; font-size:1rem; color:#FFFFFF;">{st.session_state.detected_lang.upper()}</div>',
                unsafe_allow_html=True,
            )
        with i2:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#C7D2FE;">Requirement Length</div>'
                f'<div style="font-weight:700; font-size:1rem; color:#FFFFFF;">{wc} words · {cc} characters</div>',
                unsafe_allow_html=True,
            )
        with i3:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#C7D2FE;">Coverage</div>'
                f'<div style="font-weight:700; font-size:1rem; color:#FFFFFF;">'
                f'{result["coverage"]["epics"]} Epics · {result["coverage"]["features"]} Features · '
                f'{result["coverage"]["stories"]} Stories</div>',
                unsafe_allow_html=True,
            )

        st.write("")
        modules = sorted({s["feature"] for s in result["stories"]})
        chips = "".join(f'<span class="feature-chip">{m}</span>' for m in modules)
        st.markdown(
            f'<div style="font-size:0.78rem;color:#C7D2FE; margin-bottom:0.3rem;">Features Detected</div>{chips}',
            unsafe_allow_html=True,
        )

st.write("")
with st.container(border=True):
    rg_left, rg_right = st.columns([4, 1])
    with rg_left:
        st.markdown(
            '<div class="panel-title"><div class="left"><h3>Recent Generations</h3></div></div>',
            unsafe_allow_html=True,
        )
    with rg_right:
        if st.button("View All", key="view_all_history", use_container_width=True):
            st.session_state.nav_page = "History"
            st.rerun()

    recent = list(reversed(st.session_state.history))[:5]
    st.markdown(render_history_table(recent), unsafe_allow_html=True)