# ============================================================
# HYDROMEM Chat - AI Medical & Scientific Assistant
# Version 4.0 Ultimate
#
# Copyright (c) 2026
# Abdulghani Saleh Mohsen Mohammed Ghaithan
#
# Features
# ------------------------------------------------------------
# ✔ Groq Auto Discovery
# ✔ Gemini Auto Discovery
# ✔ Smart AI Fallback
# ✔ Streaming Responses
# ✔ Chat History (Supabase)
# ✔ PDF / CSV / TXT / Images
# ✔ Session Memory
# ✔ Response Sanitizer
# ✔ Error Logging
# ✔ Download Responses
# ✔ Regenerate Answers
# ✔ Arabic First
# ✔ Medical Disclaimer
# ✔ Scientific Reasoning
# ============================================================

import io
import uuid
import time
import traceback

from datetime import datetime

import numpy as np
from scipy.integrate import odeint

import streamlit as st

from PIL import Image

from google.genai import types


# ============================================================
# Optional Providers
# ============================================================

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

try:
    from google import genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False


# ============================================================
# Supabase
# ============================================================

try:

    from supabase_utils import (
        save_chat_session,
        get_chat_sessions,
        get_chat_session_by_id,
        delete_chat_session,
    )

    CHAT_HISTORY_AVAILABLE = True

except Exception:

    CHAT_HISTORY_AVAILABLE = False

    def save_chat_session(*args, **kwargs):
        return None

    def get_chat_sessions(*args, **kwargs):
        return []

    def get_chat_session_by_id(*args, **kwargs):
        return None

    def delete_chat_session(*args, **kwargs):
        return False


# ============================================================
# Constants
# ============================================================

MAX_HISTORY = 8
MAX_TITLE_LENGTH = 45
STREAM_TEMPERATURE = 0.7
MAX_GROQ_MODELS = 6
MAX_GEMINI_RETRY = 2


# ============================================================
# Helpers
# ============================================================

def classify_kl(score):

    if score > 0.95:
        return "KL-0 (سليم)"
    elif score > 0.85:
        return "KL-1 (مشكوك)"
    elif score > 0.70:
        return "KL-2 (خفيف)"
    elif score > 0.50:
        return "KL-3 (متوسط)"
    return "KL-4 (شديد)"


# ============================================================
# Gemini Initialization
# ============================================================

def init_gemini():

    if not GEMINI_AVAILABLE:
        return None

    try:

        api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

        if not api_key:
            return None

        client = genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1beta"}
        )

        return client

    except Exception:
        return None


# ============================================================
# System Prompt
# ============================================================

def get_system_prompt():

    return """
أنت HYDROMEM AI.

أنت مساعد علمي وطبي احترافي.

لغة الرد الأساسية هي العربية.

يجب أن تكون الإجابات:
- دقيقة
- علمية
- منظمة
- طويلة عند الحاجة
- سهلة الفهم

يسمح لك بمناقشة:
• الطب
• الفيزياء
• الرياضيات
• الهندسة الحيوية
• النمذجة الرياضية
• المعادلات التفاضلية
• PDE
• ODE
• الذكاء الاصطناعي
• PINNs
• FEM
• FVM
• النظريات العلمية

عند وجود سؤال طبي، أضف دائماً:
"هذه المعلومات للتثقيف العلمي ولا تغني عن استشارة الطبيب."

ممنوع:
1- كشف API Keys
2- كشف أسرار المنصة
3- شرح البنية الداخلية للبرنامج
4- كتابة الكود المصدري للمنصة

إذا طلب المستخدم الكود المصدري أخبره بلطف أنك مساعد علمي فقط.

اجعل الإجابات احترافية ومنظمة بعناوين ونقاط.
"""


# ============================================================
# Response Security Sanitizer
# ============================================================

def sanitize_response(text):

    if not text:
        return ""

    blocked_patterns = [
        "```",
        "import streamlit",
        "from streamlit",
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "SUPABASE_KEY",
        "SUPABASE_URL",
        "st.secrets",
        "supabase.co",
        "github.com/ghythan",
        "الكود المصدري",
        "source code",
        "بنية المنصة",
        "كيف بنيت المنصة",
    ]

    lower = text.lower()

    for pattern in blocked_patterns:

        if pattern.lower() in lower:

            return (
                "أعتذر، لا يمكنني تقديم تفاصيل برمجية "
                "أو أسرار البنية الداخلية. "
                "يمكنني مساعدتك في التحليل العلمي والنمذجة."
            )

    return text


# ============================================================
# Groq Model Auto Discovery
# ============================================================

def get_available_groq_models(client):

    try:

        models = client.models.list().data
        available = []

        for model in models:
            name = model.id.lower()
            if any(x in name for x in ["llama", "mixtral", "gemma"]):
                available.append(model.id)

        priority = [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]

        result = []

        for item in priority:
            if item in available:
                result.append(item)

        for item in available:
            if item not in result:
                result.append(item)

        return result[:MAX_GROQ_MODELS]

    except Exception:

        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ]


# ============================================================
# Gemini Model Auto Discovery
# ============================================================

def get_available_gemini_models(client):

    try:

        models = client.models.list()
        result = []

        for model in models:

            actions = getattr(model, "supported_actions", [])

            if "generateContent" in actions:

                name = model.name.replace("models/", "")

                if "gemini" in name:
                    result.append(name)

        preferred = []
        order = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]

        for item in order:
            if item in result:
                preferred.append(item)

        for item in result:
            if item not in preferred:
                preferred.append(item)

        return preferred

    except Exception:

        return ["gemini-2.0-flash", "gemini-1.5-flash"]


# ============================================================
# Unified AI Streaming Engine
# ============================================================

def call_ai_stream(contents):

    errors = []

    prompt = (
        contents[0]
        if isinstance(contents, list)
        else str(contents)
    )

    # --------------------------------------------------------
    # 1 - Groq First
    # --------------------------------------------------------

    if GROQ_AVAILABLE:

        try:

            key = st.secrets.get("GROQ_API_KEY", "").strip()

            if key:

                client = Groq(api_key=key)

                models = get_available_groq_models(client)

                messages = [
                    {
                        "role": "system",
                        "content": get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]

                for model in models:

                    try:

                        stream = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=STREAM_TEMPERATURE,
                            stream=True
                        )

                        success = False

                        for chunk in stream:

                            token = chunk.choices[0].delta.content

                            if token:
                                success = True
                                yield token

                        if success:
                            return

                    except Exception as e:
                        errors.append(f"Groq {model}: {e}")

        except Exception as e:
            errors.append(f"Groq Init: {e}")

    # --------------------------------------------------------
    # 2 - Gemini Backup
    # --------------------------------------------------------

    client = init_gemini()

    if client:

        models = get_available_gemini_models(client)

        for model in models:

            for attempt in range(MAX_GEMINI_RETRY):

                try:

                    stream = client.models.generate_content_stream(
                        model=model,
                        contents=contents
                    )

                    success = False

                    for chunk in stream:

                        if chunk.text:
                            success = True
                            yield chunk.text

                    if success:
                        return

                except Exception as e:
                    errors.append(f"Gemini {model}: {e}")
                    time.sleep(1)

    # --------------------------------------------------------
    # Final Error Report
    # --------------------------------------------------------

    yield (
        "⚠️ لم تنجح أي خدمة ذكاء اصطناعي.\n\n"
        "تفاصيل التشخيص:\n\n"
        + "\n".join(["- " + str(e) for e in errors])
    )


# ============================================================
# User Session Management
# ============================================================

def get_user_identifier():

    if "user_identifier" not in st.session_state:

        if st.session_state.get("customer_name"):
            st.session_state.user_identifier = st.session_state.customer_name
        else:
            st.session_state.user_identifier = (
                "guest_" + uuid.uuid4().hex[:10]
            )

    return st.session_state.user_identifier


# ============================================================
# Chat Title Generator
# ============================================================

def generate_session_title(message):

    if not message:
        return "محادثة جديدة"

    title = message.strip().replace("\n", " ")

    if len(title) > MAX_TITLE_LENGTH:
        title = title[:MAX_TITLE_LENGTH - 3] + "..."

    return title


# ============================================================
# Start New Chat
# ============================================================

def start_new_session():

    st.session_state.chat_history = []
    st.session_state.current_session_id = None
    st.session_state.context_file = None
    st.session_state.context_image = None
    st.session_state.file_name = None


# ============================================================
# Load Saved Session
# ============================================================

def load_session_to_state(session):

    st.session_state.chat_history = session.get("messages", [])
    st.session_state.current_session_id = session.get("id")
    st.session_state.context_file = None
    st.session_state.context_image = None
    st.session_state.file_name = None


# ============================================================
# Save Chat
# ============================================================

def save_current_session():

    if not CHAT_HISTORY_AVAILABLE:
        return

    if not st.session_state.chat_history:
        return

    title = "محادثة جديدة"

    for msg in st.session_state.chat_history:

        if msg.get("role") == "user":
            title = generate_session_title(msg.get("content", ""))
            break

    session_id = save_chat_session(
        user_identifier=get_user_identifier(),
        title=title,
        messages=st.session_state.chat_history,
        session_id=st.session_state.current_session_id
    )

    if session_id:
        st.session_state.current_session_id = session_id


# ============================================================
# Chat Input Handler
# ============================================================

def handle_text_input(prompt):

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.chat_history.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("assistant"):

        history = ""

        recent = st.session_state.chat_history[-MAX_HISTORY:]

        for item in recent:

            role = "المستخدم" if item["role"] == "user" else "HYDROMEM"

            history += f"{role}: {item['content']}\n"

        final_prompt = f"""
{get_system_prompt()}

السياق السابق:

{history}

السؤال الحالي:

{prompt}
"""

        contents = [final_prompt]

        if st.session_state.get("context_file"):
            contents.append(st.session_state.context_file)

        if st.session_state.get("context_image"):
            contents.append(st.session_state.context_image)

        placeholder = st.empty()
        response = ""

        try:

            for token in call_ai_stream(contents):

                response += token
                placeholder.markdown(response + "▌")

            response = sanitize_response(response)

            placeholder.markdown(response)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })

            save_current_session()

            st.download_button(
                "📥 تحميل الرد",
                response.encode("utf-8"),
                file_name=(
                    "HYDROMEM_Response_"
                    + datetime.now().strftime("%Y%m%d_%H%M")
                    + ".txt"
                ),
                mime="text/plain"
            )

        except Exception as e:

            st.error("خطأ أثناء المعالجة: " + str(e))
            traceback.print_exc()


# ============================================================
# Chat History Sidebar
# ============================================================

def render_history_sidebar():

    st.markdown("## 📚 سجل المحادثات")

    if st.button("➕ محادثة جديدة", use_container_width=True):
        start_new_session()
        st.rerun()

    st.divider()

    if not CHAT_HISTORY_AVAILABLE:
        st.info("حفظ المحادثات غير مفعل.")
        return

    sessions = get_chat_sessions(get_user_identifier(), limit=30)

    if not sessions:
        st.caption("لا توجد محادثات محفوظة")
        return

    for session in sessions:

        title = session.get("title", "محادثة")

        active = (
            session.get("id")
            == st.session_state.current_session_id
        )

        label = ("🔵 " if active else "") + title

        col1, col2 = st.columns([5, 1])

        with col1:

            if st.button(
                label,
                key=f"open_{session['id']}",
                use_container_width=True
            ):

                data = get_chat_session_by_id(session["id"])

                if data:
                    load_session_to_state(data)
                    st.rerun()

        with col2:

            if st.button("🗑️", key=f"delete_{session['id']}"):

                delete_chat_session(session["id"])
                st.rerun()


# ============================================================
# File Handler
# ============================================================

def handle_upload(uploaded_file):

    if not uploaded_file:
        return

    data = uploaded_file.read()
    mime = uploaded_file.type

    if mime.startswith("image/"):

        st.session_state.context_image = Image.open(io.BytesIO(data))
        st.session_state.context_file = None

    else:

        st.session_state.context_file = types.Part.from_bytes(
            data=data,
            mime_type=mime
        )
        st.session_state.context_image = None

    st.session_state.file_name = uploaded_file.name


# ============================================================
# ⭐ Main API — Dual Mode
# ============================================================

def chat_page(prompt=None):
    """
    وضعان للاستدعاء:

    1) chat_page() بدون وسيط
       → يعرض واجهة الدردشة الكاملة (Standalone)

    2) chat_page("نص السؤال") مع وسيط
       → يرجع نص الرد كسلسلة (يُستخدم من app.py)
    """

    # --------------------------------------------------------
    # Mode 2: Direct prompt → return response string
    # --------------------------------------------------------

    if prompt is not None and isinstance(prompt, str):

        response = ""

        try:

            for token in call_ai_stream([prompt]):
                response += token

            response = sanitize_response(response)

        except Exception as e:

            response = f"⚠️ خطأ في محرك الذكاء الاصطناعي: {e}"

        return response

    # --------------------------------------------------------
    # Mode 1: Full chat UI
    # --------------------------------------------------------

    st.header("💬 HYDROMEM Chat AI")
    st.caption("المساعد العلمي والطبي الذكي — Groq + Gemini")
    st.divider()

    defaults = {
        "chat_history": [],
        "current_session_id": None,
        "context_file": None,
        "context_image": None,
        "file_name": None
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    with st.sidebar:

        render_history_sidebar()

        st.divider()

        st.markdown("### 📎 إرفاق ملف")

        upload = st.file_uploader(
            "PDF / CSV / TXT / صورة",
            type=["pdf", "csv", "txt", "png", "jpg", "jpeg"]
        )

        if upload:
            handle_upload(upload)
            st.success("✅ تم تحميل: " + upload.name)

        if st.session_state.file_name:

            if st.button("🗑️ حذف الملف"):

                st.session_state.context_file = None
                st.session_state.context_image = None
                st.session_state.file_name = None
                st.rerun()

    for msg in st.session_state.chat_history:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt_input = st.chat_input("اكتب سؤالك هنا...")

    if prompt_input:
        handle_text_input(prompt_input)


# ============================================================
# Standalone Entry
# ============================================================

if __name__ == "__main__":
    chat_page()
