"""SwiftShip Customer Support — Streamlit Chat UI.

This app connects to the ADK server running at http://127.0.0.1:8080
and provides a beautiful chat interface for the customer support agent.

Run:
    uv run streamlit run chatbot_ui.py
"""

import uuid

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ADK_BASE = "http://127.0.0.1:8080"
APP_NAME = "app"
USER_ID = "user"

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="SwiftShip Support",
    page_icon="🚀",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Custom CSS — dark premium look
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }

    /* Header */
    .chat-header {
        background: linear-gradient(90deg, #6c63ff, #48cae4);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: 0 8px 32px rgba(108,99,255,0.3);
    }
    .chat-header h1 {
        color: white;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
    }
    .chat-header p {
        color: rgba(255,255,255,0.85);
        font-size: 0.85rem;
        margin: 2px 0 0 0;
    }

    /* Category badges */
    .badge-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }
    .badge {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        color: white;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.78rem;
        font-weight: 500;
    }

    /* User message bubble */
    .msg-user {
        background: linear-gradient(135deg, #6c63ff, #48cae4);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0 8px 60px;
        font-size: 0.95rem;
        box-shadow: 0 4px 15px rgba(108,99,255,0.3);
        line-height: 1.5;
    }

    /* Bot message bubble */
    .msg-bot {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        color: #e2e8f0;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 60px 8px 0;
        font-size: 0.95rem;
        line-height: 1.6;
        backdrop-filter: blur(10px);
    }

    /* Typing indicator */
    .typing {
        color: rgba(255,255,255,0.5);
        font-size: 0.85rem;
        font-style: italic;
        padding: 8px 0;
    }

    /* Input area */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px 16px !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: rgba(255,255,255,0.4) !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6c63ff !important;
        box-shadow: 0 0 0 3px rgba(108,99,255,0.25) !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6c63ff, #48cae4) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(108,99,255,0.4) !important;
    }

    /* Divider */
    hr {
        border-color: rgba(255,255,255,0.1) !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# ADK helpers
# ---------------------------------------------------------------------------


def create_session() -> str:
    """Create a new ADK session and return its ID."""
    url = f"{ADK_BASE}/apps/{APP_NAME}/users/{USER_ID}/sessions"
    resp = requests.post(url, json={}, timeout=10)
    resp.raise_for_status()
    return resp.json()["id"]


def send_message(session_id: str, text: str) -> str:
    """Send a message to the ADK agent and return its text reply."""
    url = f"{ADK_BASE}/run"
    payload = {
        "app_name": APP_NAME,
        "user_id": USER_ID,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": text}],
        },
        "streaming": False,
    }
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()

    events = resp.json()

    # Nodes that do classification/routing — their text output is NOT the
    # final user-facing reply and must be skipped.
    SKIP_AUTHORS = {"query_classifier", "route_decision"}

    final_reply = None

    for event in events:
        author = event.get("author", "")
        if author in SKIP_AUTHORS:
            continue

        # ── LlmAgent reply: lives in content.parts[].text ──
        content = event.get("content") or {}
        role = content.get("role", "")
        if role == "model":
            for part in content.get("parts", []):
                txt = part.get("text", "").strip()
                if txt:
                    final_reply = txt  # keep updating — we want the last one

        # ── FunctionNode reply: lives in event["output"] as a plain string ──
        output = event.get("output")
        if output and isinstance(output, str) and author not in SKIP_AUTHORS:
            final_reply = output.strip()

    return final_reply or "_(No response received)_"


# ---------------------------------------------------------------------------
# Ensure session exists
# ---------------------------------------------------------------------------

if st.session_state.session_id is None:
    try:
        st.session_state.session_id = create_session()
    except Exception as e:
        st.error(f"❌ Cannot connect to ADK server at {ADK_BASE}. Make sure it is running!\n\nError: {e}")
        st.stop()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="chat-header">
        <div style="font-size:2.4rem;">🚀</div>
        <div>
            <h1>SwiftShip Support</h1>
            <p>AI-powered customer support • Available 24/7</p>
        </div>
    </div>
    <div class="badge-row">
        <span class="badge">📦 Shipping Rates</span>
        <span class="badge">🔄 Returns & Refunds</span>
        <span class="badge">💳 Billing</span>
        <span class="badge">🔍 Package Tracking</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Chat history display
# ---------------------------------------------------------------------------

chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="msg-bot">
            👋 Hello! I'm SwiftShip's AI support assistant.<br><br>
            I can help you with:<br>
            &nbsp;&nbsp;• 📦 <b>Shipping</b> — rates, tracking, delivery times<br>
            &nbsp;&nbsp;• 🔄 <b>Returns & Refunds</b> — returns policy, refund status<br>
            &nbsp;&nbsp;• 💳 <b>Billing</b> — payments, invoices, charges<br><br>
            How can I help you today?
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="msg-user">{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                # Convert newlines to <br> for HTML display
                content_html = msg["content"].replace("\n", "<br>")
                st.markdown(
                    f'<div class="msg-bot">{content_html}</div>',
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------------------------
# Input form
# ---------------------------------------------------------------------------

st.markdown("<hr>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([6, 1, 1])

with col1:
    user_input = st.text_input(
        label="message",
        placeholder="Ask about shipping, returns, billing...",
        label_visibility="collapsed",
        key="chat_input",
    )

with col2:
    send_btn = st.button("Send ➤", use_container_width=True)

with col3:
    if st.button("🔄 New", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

# ---------------------------------------------------------------------------
# Handle send
# ---------------------------------------------------------------------------

if (send_btn or user_input) and user_input.strip():
    user_text = user_input.strip()

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_text})

    # Show typing indicator & call agent
    with st.spinner("SwiftShip AI is thinking... 💭"):
        try:
            reply = send_message(st.session_state.session_id, user_text)
        except Exception as e:
            reply = f"⚠️ Error connecting to agent: {e}"

    # Add bot reply to history
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Rerun to display the new messages
    st.rerun()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div style="text-align:center; color:rgba(255,255,255,0.3); font-size:0.75rem; margin-top:24px;">
        Powered by Google ADK 2.3 • SwiftShip Customer Support AI
    </div>
    """,
    unsafe_allow_html=True,
)
