# ============================================================
# HYDROMEM Chat - AI Scientific & Medical Assistant
# Version 5.1 — Speed Optimized
#
# Copyright (c) 2026
# Abdulghani Saleh Mohsen Mohammed Ghaithan
# All Rights Reserved
#
# Dual Mode:
#   chat_page()          → Full Chat UI
#   chat_page("سؤال")    → Returns response string
# ============================================================

import io
import uuid
import time
import traceback
from datetime import datetime

import streamlit as st
from PIL import Image


# ============================================================
# Optional AI Providers
# ============================================================

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False
    types = None


# ============================================================
# Optional Supabase Chat History
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

    def save_chat_session(*a, **k): return None
    def get_chat_sessions(*a, **k): return []
    def get_chat_session_by_id(*a, **k): return None
    def delete_chat_session(*a, **k): return False


# ============================================================
# Constants (تم تعديلها لتسريع الرد)
# ============================================================

MAX_TITLE_LENGTH = 45
STREAM_TEMPERATURE = 0.7
MAX_GROQ_MODELS = 2  # تم التقليل لتسريع الاستجابة
MAX_GEMINI_RETRY = 2

MEDICAL_DISCLAIMER = (
    "هذه المعلومات للتثقيف العلمي "
    "ولا تغني عن استشارة الطبيب."
)

SCIENTIFIC_DISCLAIMER = (
    "⚠️ HYDROMEM أداة محاكاة حسابية. "
    "النتائج تحتاج تحققاً تجريبياً قبل التطبيق الواقعي."
)


# ============================================================
# Plan-Based Chat Features
# ============================================================

CHAT_FEATURES = {
    "individual": {
        "file_upload": False,
        "history_save": False,
        "max_history_msgs": 4,
    },
    "researcher": {
        "file_upload": True,
        "history_save": True,
        "max_history_msgs": 8,
    },
    "laboratory": {
        "file_upload": True,
        "history_save": True,
        "max_history_msgs": 12,
    },
    "university": {
        "file_upload": True,
        "history_save": True,
        "max_history_msgs": 16,
    },
    "hospital": {
        "file_upload": True,
        "history_save": True,
        "max_history_msgs": 16,
    },
    "enterprise": {
        "file_upload": True,
        "history_save": True,
        "max_history_msgs": 20,
    },
}


def current_plan_id():
    user = st.session_state.get("user") or {}
    return user.get("plan", "individual")


def has_feature(key):
    pid = current_plan_id()
    return bool(CHAT_FEATURES.get(pid, {}).get(key, False))


def history_limit():
    pid = current_plan_id()
    return CHAT_FEATURES.get(pid, {}).get("max_history_msgs", 4)


# ============================================================
# Gemini Client
# ============================================================

def init_gemini():
    if not GEMINI_AVAILABLE:
        return None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            return None
        return genai.Client(
            api_key=api_key,
            http_options={"api_version": "v1beta"},
        )
    except Exception:
        return None


# ============================================================
# System Prompt
# ============================================================

def get_system_prompt():
    return """
أنت HYDROMEM AI — مساعد علمي وطبي احترافي.

القواعد:
- لغة الرد الأساسية: العربية.
- كن دقيقاً، علمياً، منظماً، وواضحاً.
- استخدم العناوين والنقاط عند الحاجة.
- أضف أمثلة ومعادلات عند المناسبة.

المجالات:
• الطب والبيولوجيا
• الفيزياء والرياضيات
• الهندسة الحيوية
• النمذجة الرياضية (ODE / PDE)
• الذكاء الاصطناعي و PINNs
• FEM / FVM

عند أي سؤال طبي، أضف في النهاية:
"هذه المعلومات للتثقيف العلمي ولا تغني عن استشارة الطبيب."

ممنوع:
1. كشف API Keys أو الأسرار.
2. كشف البنية الداخلية للمنصة.
3. كتابة الكود المصدري للمنصة.
""".strip()


# ============================================================
# Response Sanitizer
# ============================================================

BLOCKED_PATTERNS = [
    "```python",
    "```toml",
    "import streamlit",
    "from streamlit",
    "import supabase",
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "SUPABASE_KEY",
    "SUPABASE_URL",
    "st.secrets",
    "supabase.co",
    "الكود المصدري",
    "source code",
    "بنية المنصة",
    "اعطني الكود",
]


def sanitize_response(text):
    if not text:
        return ""
    lower = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in lower:
            return (
                "أعتذر، لا يمكنني تقديم تفاصيل برمجية أو أسرار داخلية. "
                "يمكنني مساعدتك في الجانب العلمي والتحليلي."
            )
    return text


# ============================================================
# Groq Models Discovery (تم تعديلها لتسريع الرد)
# ============================================================

def get_groq_models(client):
    try:
        models = client.models.list().data
        available = [
            m.id for m in models
            if any(x in m.id.lower() for x in ("llama", "mixtral", "gemma"))
        ]
        # 8B هو الأسرع، 70B أذكى لكن أبطأ
        priority = [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
        ]
        result = [m for m in priority if m in available]
        result += [m for m in available if m not in result]
        return result[:MAX_GROQ_MODELS]
    except Exception:
        return [
            "llama-3.1-8b-instant",
            "llama-3.3-70b-versatile",
        ]


# ============================================================
# Gemini Models Discovery
# ============================================================

def get_gemini_models(client):
    try:
        models = client.models.list()
        result = []
        for model in models:
            actions = getattr(model, "supported_actions", [])
            if "generateContent" in actions:
                name = model.name.replace("models/", "")
                if "gemini" in name:
                    result.append(name)
        order = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        preferred = [m for m in order if m in result]
        preferred += [m for m in result if m not in preferred]
        return preferred
    except Exception:
        return ["gemini-2.0-flash", "gemini-1.5-flash"]


# ============================================================
# Unified Streaming Engine
# ============================================================

def call_ai_stream(contents):
    errors = []

    prompt = (
        contents[0] if isinstance(contents, list) else str(contents)
    )

    # 1) Groq (الأسرع)
    if GROQ_AVAILABLE:
        try:
            key = st.secrets.get("GROQ_API_KEY", "").strip()
            if key:
                client = Groq(api_key=key)
                models = get_groq_models(client)
                messages = [
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "user", "content": prompt},
                ]
                for model in models:
                    try:
                        stream = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=STREAM_TEMPERATURE,
                            stream=True,
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

    # 2) Gemini Fallback
    client = init_gemini()
    if client:
        models = get_gemini_models(client)
        for model in models:
            for _ in range(MAX_GEMINI_RETRY):
                try:
                    stream = client.models.generate_content_stream(
                        model=model,
                        contents=contents,
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

    # 3) All failed
    yield (
        "⚠️ لم تنجح أي خدمة ذكاء اصطناعي حالياً.\n\n"
        "**التشخيص:**\n\n"
        + "\n".join([f"- {e}" for e in errors])
    )


# ============================================================
# User Identifier
# ============================================================

def get_user_identifier():
    user = st.session_state.get("user")
    if user and user.get("email"):
        return user["email"]
    if "user_identifier" not in st.session_state:
        st.session_state.user_identifier = (
            "guest_" + uuid.uuid4().hex[:10]
        )
    return st.session_state.user_identifier


# ============================================================
# Session Title
# ============================================================

def generate_title(message):
    if not message:
        return "محادثة جديدة"
    title = message.strip().replace("\n", " ")
    if len(title) > MAX_TITLE_LENGTH:
        title = title[:MAX_TITLE_LENGTH - 3] + "..."
    return title


# ============================================================
# Session State
# ============================================================

def ensure_state():
    defaults = {
        "chat_history": [],
        "current_session_id": None,
        "context_file": None,
        "context_image": None,
        "file_name": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def start_new_session():
    st.session_state.chat_history = []
    st.session_state.current_session_id = None
    st.session_state.context_file = None
    st.session_state.context_image = None
    st.session_state.file_name = None


def load_session(session):
    st.session_state.chat_history = session.get("messages", [])
    st.session_state.current_session_id = session.get("id")
    st.session_state.context_file = None
    st.session_state.context_image = None
    st.session_state.file_name = None


# ============================================================
# Save Session
# ============================================================

def save_session():
    if not CHAT_HISTORY_AVAILABLE:
        return
    if not has_feature("history_save"):
        return
    if not st.session_state.chat_history:
        return

    title = "محادثة جديدة"
    for msg in st.session_state.chat_history:
        if msg.get("role") == "user":
            title = generate_title(msg.get("content", ""))
            break

    sid = save_chat_session(
        user_identifier=get_user_identifier(),
        title=title,
        messages=st.session_state.chat_history,
        session_id=st.session_state.current_session_id,
    )
    if sid:
        st.session_state.current_session_id = sid


# ============================================================
# File Upload
# ============================================================

def handle_upload(uploaded_file):
    if not uploaded_file:
        return

    if not has_feature("file_upload"):
        st.warning(
            "🔒 رفع الملفات متاح في باقة الباحث وما فوق."
        )
        return

    data = uploaded_file.read()
    mime = uploaded_file.type

    if mime.startswith("image/"):
        st.session_state.context_image = Image.open(io.BytesIO(data))
        st.session_state.context_file = None
    else:
        if types is not None:
            st.session_state.context_file = types.Part.from_bytes(
                data=data,
                mime_type=mime,
            )
        st.session_state.context_image = None

    st.session_state.file_name = uploaded_file.name


# ============================================================
# History Sidebar
# ============================================================

def render_history_sidebar():
    st.markdown("## 📚 سجل المحادثات")

    if st.button("➕ محادثة جديدة", use_container_width=True):
        start_new_session()
        st.rerun()

    st.divider()

    if not CHAT_HISTORY_AVAILABLE:
        st.caption("ℹ️ حفظ السجل غير مفعّل.")
        return

    if not has_feature("history_save"):
        st.info("🔒 حفظ السجل متاح من باقة الباحث وما فوق.")
        return

    sessions = get_chat_sessions(get_user_identifier(), limit=30)

    if not sessions:
        st.caption("لا توجد محادثات محفوظة.")
        return

    for session in sessions:
        title = session.get("title", "محادثة")
        active = session.get("id") == st.session_state.current_session_id
        label = ("🔵 " if active else "") + title

        c1, c2 = st.columns([5, 1])
        with c1:
            if st.button(label, key=f"open_{session['id']}",
                         use_container_width=True):
                data = get_chat_session_by_id(session["id"])
                if data:
                    load_session(data)
                    st.rerun()
        with c2:
            if st.button("🗑️", key=f"del_{session['id']}"):
                delete_chat_session(session["id"])
                st.rerun()


# ============================================================
# Handle Input
# ============================================================

def handle_input(prompt):
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.chat_history.append({
        "role": "user", "content": prompt,
    })

    max_ctx = history_limit()
    recent = st.session_state.chat_history[-max_ctx:]

    history_str = ""
    for item in recent:
        role = "المستخدم" if item["role"] == "user" else "HYDROMEM"
        history_str += f"{role}: {item['content']}\n"

    final_prompt = f"""
{get_system_prompt()}

--- السياق ---
{history_str}

--- السؤال ---
{prompt}
""".strip()

    contents = [final_prompt]
    if st.session_state.get("context_file"):
        contents.append(st.session_state.context_file)
    if st.session_state.get("context_image"):
        contents.append(st.session_state.context_image)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        response = ""

        try:
            for token in call_ai_stream(contents):
                response += token
                placeholder.markdown(response + "▌")

            response = sanitize_response(response)
            placeholder.markdown(response)

            st.session_state.chat_history.append({
                "role": "assistant", "content": response,
            })

            save_session()

            st.download_button(
                "📥 تحميل الرد",
                response.encode("utf-8"),
                file_name=(
                    "HYDROMEM_Response_"
                    + datetime.now().strftime("%Y%m%d_%H%M")
                    + ".txt"
                ),
                mime="text/plain",
            )

        except Exception as e:
            st.error(f"خطأ: {e}")
            traceback.print_exc()


# ============================================================
# Main API — Dual Mode
# ============================================================

def chat_page(prompt=None):
    """
    chat_page()       → واجهة كاملة
    chat_page("...")  → يعيد نص الرد
    """

    # Mode 2: prompt → string
    if prompt is not None and isinstance(prompt, str):
        response = ""
        try:
            for token in call_ai_stream([prompt]):
                response += token
            response = sanitize_response(response)
        except Exception as e:
            response = f"⚠️ خطأ: {e}"
        return response

    # Mode 1: UI
    ensure_state()

    plan_id = current_plan_id()

    st.header("💬 HYDROMEM Chat AI")
    st.caption(
        f"المساعد العلمي والطبي — الباقة: {plan_id}"
    )
    st.divider()

    with st.sidebar:
        render_history_sidebar()
        st.divider()
        st.markdown("### 📎 إرفاق ملف")

        if has_feature("file_upload"):
            upload = st.file_uploader(
                "PDF / CSV / TXT / صورة",
                type=["pdf", "csv", "txt", "png", "jpg", "jpeg"],
            )
            if upload:
                handle_upload(upload)
                st.success("✅ تم التحميل: " + upload.name)

            if st.session_state.get("file_name"):
                st.caption(f"📄 {st.session_state.file_name}")
                if st.button("🗑️ حذف الملف"):
                    st.session_state.context_file = None
                    st.session_state.context_image = None
                    st.session_state.file_name = None
                    st.rerun()
        else:
            st.info("🔒 رفع الملفات متاح من باقة الباحث وما فوق.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt_input = st.chat_input("اكتب سؤالك هنا...")
    if prompt_input:
        handle_input(prompt_input)

    st.divider()
    st.warning(SCIENTIFIC_DISCLAIMER)


# ============================================================
# Standalone
# ============================================================

if __name__ == "__main__":
    chat_page()
