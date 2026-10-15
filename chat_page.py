# ============================================================
# HYDROMEM Chat - AI Medical & Scientific Assistant (v2.8)
# Copyright (c) 2026 Abdulghani Saleh Mohsen Mohammed Ghaithan
# Features:
#   - Chat History
#   - Fixed Sanitizer
#   - Groq Integration (Using llama-3.3-70b-versatile)
#   - Gemini Fallback
# ============================================================

import streamlit as st
from datetime import datetime
import numpy as np
from scipy.integrate import odeint
from PIL import Image
import io
import time
import uuid
from google.genai import types

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from supabase_utils import (
        save_chat_session, get_chat_sessions,
        get_chat_session_by_id, delete_chat_session,
    )
    CHAT_HISTORY_AVAILABLE = True
except ImportError:
    CHAT_HISTORY_AVAILABLE = False
    def save_chat_session(*a, **k): return None
    def get_chat_sessions(*a, **k): return []
    def get_chat_session_by_id(*a, **k): return None
    def delete_chat_session(*a, **k): return False


def classify_kl(m):
    if m > 0.95: return "KL-0 (سليم)"
    elif m > 0.85: return "KL-1 (مشكوك)"
    elif m > 0.70: return "KL-2 (خفيف)"
    elif m > 0.50: return "KL-3 (متوسط)"
    else: return "KL-4 (شديد)"


def init_gemini():
    if not GEMINI_AVAILABLE:
        return None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            return None
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
        return client
    except Exception:
        return None


def get_system_prompt():
    return """أنت مساعد علمي وطبي ذكي باسم HYDROMEM.
أنت منصة متكاملة لمحاكاة الأنظمة الديناميكية المعقدة.
أجب دائماً بالعربية، وقدم إجابات شاملة ومنظمة.
عند الحديث عن الطب، أضف إخلاء مسؤولية.

✅ يمكنك بحرية مناقشة:
- المعادلات الرياضية والفيزيائية (ODEs, PDEs, Jacobian).
- النظريات العلمية (TBP-QM, Riemann Hypothesis, PINN).
- التحليل الرياضي والتفسير الفيزيائي.
- المقارنات العددية ونتائج المحاكاة.
- المفاهيم الطبية والهندسية الحيوية.

🔴 ممنوع منعاً باتاً:
1. كتابة أكواد برمجية كاملة أو استخدام code blocks.
2. شرح كيفية بناء المنصة أو البنية التحتية التقنية.
3. الكشف عن مفاتيح API أو كلمات المرور.

إذا سألك المستخدم عن الكود، اعتذر بلطف: "أنا مساعد علمي، لا أستطيع مناقشة التفاصيل البرمجية. لكن يمكنني مساعدتك في التحليل العلمي والرياضي."
"""


def sanitize_response(text):
    if not text:
        return text
    if "```" in text:
        return "أعتذر، لا يمكنني كتابة الأكواد البرمجية. أنا مساعد علمي وطبي مخصص للتحليل والمحاكاة."

    forbidden = [
        "import streamlit", "from streamlit", "pip install streamlit",
        "supabase_utils", "supabase.co", "SUPABASE_URL", "SUPABASE_KEY",
        "GEMINI_API_KEY", "GROQ_API_KEY", "st.secrets",
        "بنية المنصة", "البنية التحتية للمنصة", "كيف بنيت المنصة",
        "الكود المصدري للمنصة", "[github.com/ghythan](https://github.com/ghythan)",
    ]
    text_lower = text.lower()
    for kw in forbidden:
        if kw.lower() in text_lower:
            return "أعتذر، لا يمكنني مناقشة التفاصيل البرمجية أو البنية التحتية. أنا مساعد علمي وطبي."
    return text


def call_ai_stream(contents_list):
    prompt_text = contents_list[0] if isinstance(contents_list, list) else str(contents_list)
    
    # ----------------- 1. محاولة Groq (الأساسي والفائق السرعة) -----------------
    if GROQ_AVAILABLE:
        groq_key = st.secrets.get("GROQ_API_KEY", "").strip()
        if groq_key:
            try:
                client_groq = Groq(api_key=groq_key)
                system_prompt = get_system_prompt()
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_text}
                ]
                
                stream = client_groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7,
                    stream=True
                )
                
                has_content = False
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        has_content = True
                        yield chunk.choices[0].delta.content
                if has_content:
                    return
            except Exception as groq_err:
                yield f"\n⚠️ [تنبيه Groq]: {str(groq_err)}\nجاري الانتقال لـ Gemini...\n\n"

    # ----------------- 2. محاولة Gemini (الاحتياطي) -----------------
    client_gemini = init_gemini()
    if not client_gemini:
        yield "⚠️ لم يتم العثور على مفتاح Gemini الصحيح."
        return

    models_to_try = [
        'gemini-1.5-flash',
        'gemini-2.0-flash',
    ]

    for model_name in models_to_try:
        for attempt in range(3):
            try:
                stream = client_gemini.models.generate_content_stream(
                    model=model_name, contents=contents_list)
                for chunk in stream:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as e:
                err = str(e)
                if ('503' in err or '429' in err or
                        'UNAVAILABLE' in err or 'overloaded' in err.lower()):
                    time.sleep(2)
                    continue
                else:
                    break

    yield ("⚠️ فشلت جميع المحاولات. تحقق من صحة المفاتيح والأذونات.")


def get_user_identifier():
    if 'user_identifier' not in st.session_state:
        if st.session_state.get('customer_name'):
            st.session_state.user_identifier = st.session_state.customer_name
        else:
            st.session_state.user_identifier = f"guest_{uuid.uuid4().hex[:8]}"
    return st.session_state.user_identifier


def generate_session_title(first_message):
    title = (first_message or "").strip().replace("\n", " ")
    if len(title) > 45:
        title = title[:42] + "..."
    return title if title else "محادثة جديدة"


def start_new_session():
    st.session_state.chat_history = []
    st.session_state.current_session_id = None
    st.session_state.context_file = None
    st.session_state.context_image = None
    st.session_state.file_name = None


def load_session_to_state(session):
    st.session_state.chat_history = session.get('messages', [])
    st.session_state.current_session_id = session.get('id')
    st.session_state.context_file = None
    st.session_state.context_image = None
    st.session_state.file_name = None


def save_current_session():
    if not CHAT_HISTORY_AVAILABLE:
        return
    if not st.session_state.chat_history:
        return
    user_id = get_user_identifier()
    title = "محادثة جديدة"
    for msg in st.session_state.chat_history:
        if msg.get('role') == 'user':
            title = generate_session_title(msg.get('content', ''))
            break
    session_id = save_chat_session(
        user_identifier=user_id, title=title,
        messages=st.session_state.chat_history,
        session_id=st.session_state.current_session_id
    )
    if session_id:
        st.session_state.current_session_id = session_id


def handle_text_input(prompt):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({'role': 'user', 'content': prompt})

    with st.chat_message("assistant"):
        recent = st.session_state.chat_history[-7:-1]
        history_text = ""
        for msg in recent:
            role_name = "المستخدم" if msg['role'] == 'user' else "HYDROMEM"
            history_text += f"{role_name}: {msg['content']}\n"

        system_prompt = get_system_prompt()
        full_prompt = (f"[تعليمات النظام]:\n{system_prompt}\n\n"
                       f"[سياق سابق]:\n{history_text}\n\n"
                       f"[السؤال]:\n{prompt}")

        contents = [full_prompt]
        if st.session_state.get('context_file'):
            contents.append(st.session_state.context_file)
        if st.session_state.get('context_image'):
            contents.append(st.session_state.context_image)

        try:
            placeholder = st.empty()
            full_response = ""
            for chunk in call_ai_stream(contents):
                full_response += chunk
                placeholder.markdown(full_response + "▌")

            final = sanitize_response(full_response)
            placeholder.markdown(final)
            st.session_state.chat_history.append({'role': 'assistant', 'content': final})
            save_current_session()

            col1, col2 = st.columns([1, 4])
            with col1:
                st.download_button(
                    label="📥 تحميل الرد",
                    data=final.encode('utf-8'),
                    file_name=f"HYDROMEM_Response_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key=f"dl_{datetime.now().timestamp()}"
                )
            with col2:
                if st.button("🔄 إعادة توليد", key=f"re_{datetime.now().timestamp()}"):
                    st.session_state.chat_history.pop()
                    st.rerun()
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")


def render_history_sidebar():
    st.markdown("### 📚 سجل المحادثات")
    if st.button("➕ محادثة جديدة", use_container_width=True,
                 type="primary", key="new_chat_btn"):
        start_new_session()
        st.rerun()
    st.markdown("---")

    if not CHAT_HISTORY_AVAILABLE:
        st.info("💡 لتفعيل حفظ المحادثات، أضف دوال chat_sessions إلى supabase_utils.py")
        return

    user_id = get_user_identifier()
    sessions = get_chat_sessions(user_id, limit=30)

    if not sessions:
        st.caption("لا توجد محادثات محفوظة بعد")
        return

    from collections import OrderedDict
    grouped = OrderedDict()
    now = datetime.now()

    for s in sessions:
        try:
            updated = datetime.fromisoformat(
                s['updated_at'].replace('Z', '+00:00')
            ).replace(tzinfo=None)
        except Exception:
            updated = now
        diff_days = (now.date() - updated.date()).days
        if diff_days == 0:
            group = "اليوم"
        elif diff_days == 1:
            group = "أمس"
        elif diff_days < 7:
            group = "هذا الأسبوع"
        else:
            group = updated.strftime("%B %Y")
        grouped.setdefault(group, []).append(s)

    for group_name, items in grouped.items():
        st.markdown(f"**{group_name}**")
        for s in items:
            title = s.get('title', 'محادثة')
            is_current = (s['id'] == st.session_state.current_session_id)
            prefix = "🔵 " if is_current else ""
            col_a, col_b = st.columns([5, 1])
            with col_a:
                if st.button(f"{prefix}{title}", key=f"sess_{s['id']}",
                             use_container_width=True):
                    full_session = get_chat_session_by_id(s['id'])
                    if full_session:
                        load_session_to_state(full_session)
                        st.rerun()
            with col_b:
                if st.button("🗑️", key=f"del_{s['id']}", help="حذف"):
                    delete_chat_session(s['id'])
                    if st.session_state.current_session_id == s['id']:
                        start_new_session()
                    st.rerun()
        st.markdown("")


def chat_page():
    st.header("💬 HYDROMEM Chat — المساعد العلمي الذكي")
    st.markdown("*مدعوم بـ Groq و Google Gemini*")
    st.markdown("---")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'context_file' not in st.session_state:
        st.session_state.context_file = None
    if 'context_image' not in st.session_state:
        st.session_state.context_image = None
    if 'file_name' not in st.session_state:
        st.session_state.file_name = None

    with st.sidebar:
        render_history_sidebar()
        st.markdown("---")
        st.markdown("### 📎 إرفاق ملف أو صورة")
        uploaded_file = st.file_uploader(
            "ارفع ملفاً (PDF, CSV, TXT, صورة)",
            type=['png', 'jpg', 'jpeg', 'csv', 'txt', 'pdf'],
            key='chat_uploader'
        )
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            mime = uploaded_file.type
            if mime.startswith('image/'):
                st.session_state.context_image = Image.open(io.BytesIO(file_bytes))
                st.session_state.context_file = None
            else:
                st.session_state.context_file = types.Part.from_bytes(
                    data=file_bytes, mime_type=mime)
                st.session_state.context_image = None
            st.session_state.file_name = uploaded_file.name
            st.success(f"✅ تم إرفاق: {uploaded_file.name}")

        if st.session_state.file_name:
            if st.button("🗑️ مسح الملف", use_container_width=True):
                st.session_state.context_file = None
                st.session_state.context_image = None
                st.session_state.file_name = None
                st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    st.markdown("---")
    prompt = st.chat_input("اكتب سؤالك...")
    if prompt:
        handle_text_input(prompt)
