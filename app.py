import streamlit as st
import time
from datetime import datetime
from typing import Optional, List
from agent import run_agent
# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="MedSchedule · AI Appointment Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg: #0d1117;
    --surface: #161b22;
    --surface2: #1c2333;
    --border: #30363d;
    --accent: #2dd4bf;
    --accent2: #f59e0b;
    --danger: #f87171;
    --success: #4ade80;
    --text: #e6edf3;
    --muted: #7d8590;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

/* Hide default streamlit chrome */
#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }
.stDeployButton { display: none; }

/* Force sidebar visible and styled */
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    min-width: 280px !important;
    width: 280px !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}

/* App header */
.app-header {
    background: linear-gradient(135deg, #0d1117 0%, #1a2744 100%);
    border-bottom: 1px solid var(--border);
    padding: 1.5rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.app-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.8rem;
    color: var(--accent);
    margin: 0;
    letter-spacing: -0.5px;
}
.app-subtitle {
    font-size: 0.8rem;
    color: var(--muted);
    margin: 0;
    font-family: 'DM Mono', monospace;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Status badge */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
    letter-spacing: 0.5px;
}
.status-started    { background: #1c2333; color: #7d8590; border: 1px solid #30363d; }
.status-parsed     { background: #0d2137; color: #60a5fa; border: 1px solid #1d4ed8; }
.status-found      { background: #0d2e1f; color: #4ade80; border: 1px solid #16a34a; }
.status-not-found  { background: #2d1b0e; color: #fb923c; border: 1px solid #c2410c; }
.status-draft      { background: #2d2008; color: #fbbf24; border: 1px solid #d97706; }
.status-approved   { background: #0d2e1f; color: #4ade80; border: 1px solid #16a34a; }
.status-sent       { background: #0d2137; color: #60a5fa; border: 1px solid #1d4ed8; }
.status-confirmed  { background: #0d2e1f; color: #4ade80; border: 1px solid #16a34a; }

/* Mail card */
.mail-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    cursor: pointer;
    transition: all 0.15s ease;
    position: relative;
}
.mail-card:hover {
    border-color: var(--accent);
    background: var(--surface2);
}
.mail-card.active {
    border-color: var(--accent);
    border-left: 3px solid var(--accent);
    background: var(--surface2);
}
.mail-card.unread::before {
    content: '';
    position: absolute;
    left: -1px;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 60%;
    background: var(--accent);
    border-radius: 0 2px 2px 0;
}
.mail-sender {
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text);
}
.mail-subject {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.mail-time {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
}

/* Email viewer */
.email-viewer {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
}
.email-viewer-header {
    border-bottom: 1px solid var(--border);
    padding-bottom: 1rem;
    margin-bottom: 1rem;
}
.email-viewer-subject {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: var(--text);
}
.email-viewer-meta {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.4rem;
    font-family: 'DM Mono', monospace;
}
.email-body {
    font-size: 0.9rem;
    line-height: 1.7;
    color: #c9d1d9;
    white-space: pre-wrap;
}

/* Pipeline step */
.pipeline-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    font-size: 0.82rem;
}
.pipeline-step.done     { background: #0d2e1f; color: #4ade80; }
.pipeline-step.active   { background: #1a2744; color: #60a5fa; border: 1px solid #1d4ed8; }
.pipeline-step.pending  { background: var(--surface); color: var(--muted); }
.pipeline-step.error    { background: #2d1010; color: #f87171; }

/* Slot pill */
.slot-pill {
    display: inline-block;
    background: #0d2137;
    border: 1px solid #1d4ed8;
    color: #93c5fd;
    border-radius: 6px;
    padding: 4px 10px;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    margin: 3px;
}

/* Action button */
.stButton > button {
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    border-radius: 8px;
    border: none;
    transition: all 0.15s ease;
}

/* Approve button */
div[data-testid="column"]:nth-child(1) .stButton > button {
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
}
div[data-testid="column"]:nth-child(1) .stButton > button:hover {
    background: linear-gradient(135deg, #047857, #059669);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

/* Reject button */
div[data-testid="column"]:nth-child(2) .stButton > button {
    background: linear-gradient(135deg, #dc2626, #ef4444);
    color: white;
}

/* Info box */
.info-box {
    background: #0d2137;
    border: 1px solid #1d4ed8;
    border-radius: 10px;
    padding: 1rem;
    margin: 0.8rem 0;
}
.info-box-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #60a5fa;
    margin-bottom: 0.5rem;
}

/* Log entry */
.log-entry {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    padding: 3px 0;
    border-bottom: 1px solid #161b22;
}
.log-entry:last-child { border-bottom: none; }

/* Divider */
hr { border-color: var(--border); margin: 1.5rem 0; }

/* Sidebar — force visible */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    display: block !important;
    visibility: visible !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
    background: var(--surface) !important;
}
/* Sidebar toggle button — keep visible */
button[data-testid="collapsedControl"] {
    display: block !important;
    visibility: visible !important;
    color: var(--accent) !important;
}

/* Metric cards */
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}
.metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: var(--accent);
}
.metric-label {
    font-size: 0.75rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: 'DM Mono', monospace;
}

/* Scrollable containers */
.inbox-scroll {
    max-height: 500px;
    overflow-y: auto;
    padding-right: 4px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    if "inbox" not in st.session_state:
        st.session_state.inbox = []          # list of mail dicts
    if "selected_mail" not in st.session_state:
        st.session_state.selected_mail = None
    if "agent_state" not in st.session_state:
        st.session_state.agent_state = None
    if "pipeline_status" not in st.session_state:
        st.session_state.pipeline_status = {}
    if "available_slots" not in st.session_state:
        st.session_state.available_slots = [
            "2026-02-21 from 9:00AM to 10:00AM",
            "2026-02-21 from 10:00AM to 11:00AM",
            "2026-02-21 from 11:00AM to 12:00PM",
            "2026-02-21 from 1:00PM to 2:00PM",
            "2026-02-21 from 2:00PM to 3:00PM",
            "2026-02-21 from 3:00PM to 4:00PM",
            "2026-02-22 from 10:00AM to 11:00AM",
            "2026-02-22 from 1:00PM to 2:00PM",
            # "2026-02-22 from 2:00PM to 3:00PM",
            # "2026-02-22 from 3:00PM to 4:00PM",
        ]
    if "waiting_human" not in st.session_state:
        st.session_state.waiting_human = False
    if "draft_for_review" not in st.session_state:
        st.session_state.draft_for_review = None
    if "run_count" not in st.session_state:
        st.session_state.run_count = 0
    if "confirmed_count" not in st.session_state:
        st.session_state.confirmed_count = 0
    if "logs" not in st.session_state:
        st.session_state.logs = []

init_state()


# ─────────────────────────────────────────────
# MOCK AGENT (replace with real graph.invoke)
# ─────────────────────────────────────────────
def mock_run_agent(raw_email: str, available_slots: list):
    """
    Replace this with your actual: result = graph.invoke(initial_state)
    This mock simulates the pipeline for UI demonstration.
    """
    import random, re
    from datetime import datetime, timedelta

    logs = []
    logs.append("[scan_and_parse_email] Parsing incoming email...")

    # Fake parse
    name = "PatientX"
    for n in ["PatientX", "PatientY", "PatientZ"]:
        if n.lower() in raw_email.lower():
            name = n
            break

    age = random.randint(25, 60)
    email = f"{name.lower()}@gmail.com"
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    req_date = tomorrow.strftime("%Y-%m-%d") if random.random() > 0.5 else today.strftime("%Y-%m-%d")
    hours = [9, 10, 11, 13, 14, 15]
    req_hour = random.choice(hours)
    req_time = f"{req_hour:02d}:00 {'AM' if req_hour < 12 else 'PM'}"

    logs.append(f"[scan_and_parse_email] Parsed: {name}, age={age}, date={req_date}, time={req_time}")

    # Check availability (use real parse_slot if available)
    matched_slot = None
    remaining = list(available_slots)
    for slot in available_slots:
        if req_date in slot:
            slot_hour_match = re.search(r"(\d{1,2}):00(AM|PM)", slot, re.IGNORECASE)
            if slot_hour_match:
                sh = int(slot_hour_match.group(1))
                meridiem = slot_hour_match.group(2).upper()
                if meridiem == "PM" and sh != 12:
                    sh += 12
                if sh == req_hour:
                    matched_slot = slot
                    remaining.remove(slot)
                    break

    logs.append(f"[check_availability] matched={matched_slot}")

    same_date = [s for s in remaining if req_date in s]
    proposed = same_date[:3] if same_date else remaining[:3]

    result = {
        "patient_name": name,
        "patient_age": age,
        "patient_email": email,
        "requested_date": req_date,
        "requested_time": req_time,
        "selected_slot": matched_slot,
        "available_slots": remaining,
        "proposed_slots": proposed if not matched_slot else [],
        "status": "slot_found" if matched_slot else "slot_not_found",
        "logs": logs,
        "draft_email": None,
        "confirmation_email": None,
    }

    if matched_slot:
        result["confirmation_email"] = (
            f"Dear {name},\n\n"
            f"We are pleased to confirm your appointment:\n\n"
            f"📅  {matched_slot}\n\n"
            f"Please arrive 10 minutes early and bring any previous medical records.\n"
            f"To reschedule, contact us at least 24 hours in advance.\n\n"
            f"Warm regards,\nDr. Smith's Office"
        )
        logs.append(f"[book_appointment] Confirmation email generated for {name} at {matched_slot}")
    else:
        slot_list = "\n".join(f"  • {s}" for s in proposed)
        result["draft_email"] = (
            f"Dear {name},\n\n"
            f"We're sorry, but your requested slot ({req_date} at {req_time}) is unavailable.\n\n"
            f"We have the following alternative slots:\n{slot_list}\n\n"
            f"Please reply with your preferred option.\n\n"
            f"Regards,\nDr. Smith's Scheduling Team"
        )
        logs.append(f"[draft_new_slots_email] Draft created for {name} with {len(proposed)} proposed slots")

    return result


# ─────────────────────────────────────────────
# HELPER: add mail to inbox
# ─────────────────────────────────────────────
def add_to_inbox(sender, subject, body, mail_type="incoming", result=None):
    st.session_state.inbox.insert(0, {
        "id": len(st.session_state.inbox),
        "sender": sender,
        "subject": subject,
        "body": body,
        "time": datetime.now().strftime("%H:%M"),
        "type": mail_type,   # incoming | outgoing | confirmation | draft
        "read": False,
        "result": result,
    })


def status_badge(status: str) -> str:
    mapping = {
        "started":            ("status-started",   "⬜", "STARTED"),
        "email_parsed":       ("status-parsed",    "🔵", "PARSED"),
        "slot_found":         ("status-found",     "🟢", "SLOT FOUND"),
        "slot_not_found":     ("status-not-found", "🟠", "NO SLOT"),
        "draft_ready":        ("status-draft",     "🟡", "DRAFT READY"),
        "human_approved":     ("status-approved",  "🟢", "APPROVED"),
        "waiting_patient_response": ("status-sent","🔵", "WAITING"),
        "confirmation_sent":  ("status-confirmed", "🟢", "CONFIRMED"),
    }
    css, icon, label = mapping.get(status, ("status-started", "⬜", status.upper()))
    return f'<span class="status-badge {css}">{icon} {label}</span>'





# ─────────────────────────────────────────────
# MAIN LAYOUT
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div>
        <p class="app-title">MedSchedule</p>
        <p class="app-subtitle">AI-Powered Medical Appointment Agent · LangGraph Workflow</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar visibility hint
if not st.session_state.inbox:
    st.info("👈 Use the **sidebar on the left** to simulate patient emails and view available slots. If collapsed, click the **arrow `>`** at the top-left to expand it.")

# Human approval banner (shown when waiting)
if st.session_state.waiting_human and st.session_state.draft_for_review:
    draft = st.session_state.draft_for_review
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a1500,#2d2008);border:1px solid #d97706;
                border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;">
        <p style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#fbbf24;
                  letter-spacing:1px;text-transform:uppercase;margin:0 0 0.5rem 0;">
            🔔 Human Review Required — John, please review this draft
        </p>
        <p style="font-size:0.85rem;color:#e6edf3;margin:0;">
            A draft email has been generated for <strong>{draft.get('patient_name','Patient')}</strong>.
            Approve to send, or reject to revise.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_approve, col_reject, col_spacer = st.columns([1, 1, 4])
    with col_approve:
        if st.button("✅ Approve & Send", use_container_width=True):
            # Mark approved, add to inbox as outgoing, finalize
            add_to_inbox(
                sender="Dr. Smith's Office <doctor@gmail.com>",
                subject=f"Re: Appointment Request — Alternative Slots",
                body=draft.get("draft_email", ""),
                mail_type="outgoing",
                result=draft
            )
            st.session_state.logs.append("👤 John approved the draft ✓")
            st.session_state.logs.append("📤 Email sent to patient.")
            st.session_state.waiting_human = False
            st.session_state.draft_for_review = None
            st.session_state.run_count += 1
            st.rerun()
    with col_reject:
        if st.button("❌ Reject Draft", use_container_width=True):
            st.session_state.logs.append("👤 John rejected the draft ✗")
            st.session_state.waiting_human = False
            st.session_state.draft_for_review = None
            st.rerun()

# ── Four-column layout: Sidebar Controls | Inbox | Email View | Pipeline ──
sidebar_col, inbox_col, viewer_col, pipeline_col = st.columns([1, 1, 2, 1.2])

# ─── LEFT PANEL (replaces sidebar) ──────────
with sidebar_col:
    st.markdown("""
    <div style="padding: 0.5rem 0 1rem 0;">
        <p style="font-family:'DM Serif Display',serif; font-size:1.2rem; color:#2dd4bf; margin:0;">🏥 Controls</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.run_count}</div>
            <div class="metric-label">Done</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color:#4ade80;">{st.session_state.confirmed_count}</div>
            <div class="metric-label">Confirmed</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📨 Simulate Patient Email", use_container_width=True):
        import random
        names = ["PatientX", "PatientY", "PatientZ"]
        ages  = [28, 35, 42, 55, 61]
        name  = random.choice(names)
        age   = random.choice(ages)
        from datetime import timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        hours = [ "4:00 PM"]
        req_time = random.choice(hours)
        body = (
            f"From: {name.lower()}@gmail.com\n"
            f"To: doctor@gmail.com\n"
            f"Subject: Appointment Request\n\n"
            f"Dear Doctor,\n\n"
            f"My name is {name}, I am {age} years old.\n"
            f"I would like to book an appointment on {tomorrow} at {req_time}.\n\n"
            f"Best regards,\n{name}"
        )
        add_to_inbox(
            sender=f"{name} <{name.lower()}@gmail.com>",
            subject="Appointment Request",
            body=body,
            mail_type="incoming"
        )
        st.session_state.selected_mail = 0
        st.rerun()

    if st.button("🗑️ Clear Inbox", use_container_width=True):
        st.session_state.inbox = []
        st.session_state.selected_mail = None
        st.session_state.waiting_human = False
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p style="font-family:\'DM Mono\',monospace;font-size:0.7rem;color:#7d8590;letter-spacing:1px;text-transform:uppercase;">📅 Available Slots</p>', unsafe_allow_html=True)
    slots = st.session_state.available_slots
    if slots:
        for s in slots:
            st.markdown(f'<div class="slot-pill" style="display:block;margin:4px 0;">{s}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#f87171;font-size:0.8rem;">No slots remaining</p>', unsafe_allow_html=True)

# ─── INBOX ───────────────────────────────────
with inbox_col:
    st.markdown('<p style="font-family:\'DM Mono\',monospace;font-size:0.7rem;color:#7d8590;letter-spacing:1px;text-transform:uppercase;margin-bottom:0.8rem;">📬 Inbox</p>', unsafe_allow_html=True)

    if not st.session_state.inbox:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:#7d8590;">
            <p style="font-size:2rem;">📭</p>
            <p style="font-size:0.85rem;">No emails yet.<br>Click <em>Simulate Patient Email</em> in the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, mail in enumerate(st.session_state.inbox):
            type_icon = {"incoming": "📩", "outgoing": "📤", "confirmation": "✅", "draft": "📝"}.get(mail["type"], "📧")
            is_active = st.session_state.selected_mail == idx
            card_class = "mail-card active" if is_active else "mail-card"

            st.markdown(f"""
            <div class="{card_class}">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span class="mail-sender">{type_icon} {mail['sender'][:22]}...</span>
                    <span class="mail-time">{mail['time']}</span>
                </div>
                <div class="mail-subject">{mail['subject']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Open", key=f"open_mail_{idx}", use_container_width=True):
                st.session_state.selected_mail = idx
                st.rerun()


# ─── EMAIL VIEWER ────────────────────────────
with viewer_col:
    if st.session_state.selected_mail is not None and st.session_state.inbox:
        mail = st.session_state.inbox[st.session_state.selected_mail]
        result = mail.get("result")

        st.markdown(f"""
        <div class="email-viewer">
            <div class="email-viewer-header">
                <div class="email-viewer-subject">{mail['subject']}</div>
                <div class="email-viewer-meta">
                    From: {mail['sender']} &nbsp;·&nbsp; {mail['time']}
                    &nbsp;·&nbsp; {{"incoming":"📩 Received","outgoing":"📤 Sent","confirmation":"✅ Confirmed","draft":"📝 Draft"}}.get("{mail['type']}", "📧")
                </div>
            </div>
            <div class="email-body">{mail['body']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Process button for incoming emails
        if mail["type"] == "incoming" and result is None:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🤖 Run Agent on this Email", use_container_width=True, type="primary"):
                with st.spinner("Running LangGraph pipeline..."):
                    time.sleep(0.5)  # visual feedback

                    # ── Replace mock_run_agent with graph.invoke() ──
                    res = run_agent(
                        raw_email=mail["body"],
                        available_slots=st.session_state.available_slots
                    )

                    # Update slots
                    st.session_state.available_slots = res["available_slots"]
                    st.session_state.logs.extend(res["logs"])

                    # Tag mail with result
                    st.session_state.inbox[st.session_state.selected_mail]["result"] = res
                    st.session_state.inbox[st.session_state.selected_mail]["read"] = True

                    if res["status"] == "slot_found":
                        # Add confirmation email to inbox
                        add_to_inbox(
                            sender="Dr. Smith's Office <doctor@gmail.com>",
                            subject=f"Appointment Confirmed — {res['selected_slot']}",
                            body=res["confirmation_email"],
                            mail_type="confirmation",
                            result=res
                        )
                        st.session_state.confirmed_count += 1
                        st.session_state.run_count += 1

                    elif res["status"] == "slot_not_found":
                        # Hold for human review
                        st.session_state.waiting_human = True
                        st.session_state.draft_for_review = res

                    st.rerun()

        # Show parsed result if available
        if result:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="info-box">
                <div class="info-box-title">📋 Agent Result</div>
                <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.8rem;">
                    <span style="font-size:0.82rem;"><b>Patient:</b> {result.get('patient_name','—')}</span>
                    <span style="font-size:0.82rem;"><b>Age:</b> {result.get('patient_age','—')}</span>
                    <span style="font-size:0.82rem;"><b>Email:</b> {result.get('patient_email','—')}</span>
                </div>
                <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.8rem;">
                    <span style="font-size:0.82rem;"><b>Requested:</b> {result.get('requested_date','—')} at {result.get('requested_time','—')}</span>
                </div>
                {f'<div style="margin-top:0.5rem;"><b style="font-size:0.82rem;">✅ Confirmed Slot:</b><br><span class="slot-pill">{result.get("selected_slot","")}</span></div>' if result.get("selected_slot") else ""}
                {f'<div style="margin-top:0.5rem;"><b style="font-size:0.82rem;">🔄 Proposed Alternatives:</b><br>{"".join(f"<span class=\"slot-pill\">{s}</span>" for s in result.get("proposed_slots",[]))}</div>' if result.get("proposed_slots") else ""}
            </div>
            """, unsafe_allow_html=True)
            st.markdown(status_badge(result.get("status", "started")), unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                    height:400px;color:#7d8590;text-align:center;">
            <p style="font-size:3rem;">✉️</p>
            <p style="font-family:'DM Serif Display',serif;font-size:1.2rem;color:#c9d1d9;">Select an email to view</p>
            <p style="font-size:0.85rem;">Click an email from the inbox to open it here.</p>
        </div>
        """, unsafe_allow_html=True)


# ─── PIPELINE + LOGS ─────────────────────────
with pipeline_col:
    st.markdown('<p style="font-family:\'DM Mono\',monospace;font-size:0.7rem;color:#7d8590;letter-spacing:1px;text-transform:uppercase;margin-bottom:0.8rem;">⚙️ Pipeline Status</p>', unsafe_allow_html=True)

    # Determine current step from selected mail result
    current_status = "started"
    if st.session_state.selected_mail is not None and st.session_state.inbox:
        mail = st.session_state.inbox[st.session_state.selected_mail]
        if mail.get("result"):
            current_status = mail["result"].get("status", "started")
    if st.session_state.waiting_human:
        current_status = "draft_ready"

    steps = [
        ("scan_and_parse_email",    "1. Scan & Parse Email",         ["email_parsed","slot_found","slot_not_found","draft_ready","human_approved","waiting_patient_response","confirmation_sent"]),
        ("check_availability",      "2. Check Availability",         ["slot_found","slot_not_found","draft_ready","human_approved","waiting_patient_response","confirmation_sent"]),
        ("book_appointment",        "3a. Book Appointment ✅",       ["confirmation_sent"]),
        ("draft_new_slots_email",   "3b. Draft Alt. Slots Email",    ["draft_ready","human_approved","waiting_patient_response"]),
        ("human_review",            "4. John Reviews Draft 👤",      ["human_approved","waiting_patient_response"]),
        ("send_proposed_slots_email","5. Send to Patient",           ["waiting_patient_response"]),
    ]

    for step_key, label, done_statuses in steps:
        if current_status in done_statuses:
            css = "done"
            icon = "✓"
        elif (step_key == "draft_new_slots_email" and current_status == "draft_ready") or \
             (step_key == "human_review" and st.session_state.waiting_human):
            css = "active"
            icon = "▶"
        elif step_key == "check_availability" and current_status == "email_parsed":
            css = "active"
            icon = "▶"
        elif step_key == "scan_and_parse_email" and current_status == "started":
            css = "active"
            icon = "▶"
        else:
            css = "pending"
            icon = "○"

        st.markdown(f"""
        <div class="pipeline-step {css}">
            <span style="font-family:'DM Mono',monospace;font-size:0.9rem;">{icon}</span>
            <span>{label}</span>
        </div>
        """, unsafe_allow_html=True)

    # Logs
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p style="font-family:\'DM Mono\',monospace;font-size:0.7rem;color:#7d8590;letter-spacing:1px;text-transform:uppercase;margin-bottom:0.5rem;">📋 Activity Log</p>', unsafe_allow_html=True)

    all_logs = list(st.session_state.logs)
    if st.session_state.selected_mail is not None and st.session_state.inbox:
        mail = st.session_state.inbox[st.session_state.selected_mail]
        if mail.get("result") and mail["result"].get("logs"):
            all_logs = mail["result"]["logs"] + all_logs

    if all_logs:
        log_html = "".join(f'<div class="log-entry">{l}</div>' for l in reversed(all_logs[-20:]))
        st.markdown(f'<div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:0.8rem;max-height:300px;overflow-y:auto;">{log_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="font-size:0.8rem;color:#7d8590;">No activity yet.</p>', unsafe_allow_html=True)