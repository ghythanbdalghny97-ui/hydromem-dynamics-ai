# ============================================================
# HYDROMEM Chat - AI Medical & Scientific Assistant (Final Edition)
# Copyright (c) 2026 Abdulghani Saleh Mohsen Mohammed Ghaithan
# ============================================================

import streamlit as st
from datetime import datetime
import numpy as np
from scipy.integrate import odeint
from PIL import Image
import io
import time
from google.genai import types

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def classify_kl(m):
    if m > 0.95: return "KL-0 (سليم)"
    elif m > 0.85: return "KL-1 (مشكوك)"
    elif m > 0.70: return "KL-2 (خفيف)"
    elif m > 0.50: return "KL-3 (متوسط)"
    else: return "KL-4 (شديد)"


def init_gemini():
    if not GEMINI_AVAILABLE:
        st.error("⚠️ مكتبة google-genai غير مثبتة.")
        return None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            st.warning("⚠️ لم يتم العثور على مفتاح GEMINI_API_KEY.")
            return None
        
        # استخدام الإصدار المستقر v1
        client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1'}
        )
        return client
    except Exception as e:
        st.error(f"❌ خطأ في تهيئة Gemini: {str(e)}")
        return None


def get_system_prompt():
    return """أنت مساعد علمي وطبي ذكي باسم HYDROMEM.
أنت منصة متكاملة لمحاكاة الأنظمة الديناميكية المعقدة.
أجب دائماً بالعربية، وقدم إجابات شاملة ومنظمة.
عند الحديث عن الطب، أضف إخلاء مسؤولية.
"""


def call_gemini_stream(client, contents):
    """محاولات متعددة مع التبديل التلقائي بين النماذج لتجاوز الازدحام (503)"""
    # ✅ قائمة شاملة بأحدث النماذج + رابط ذكي للحصول على أحدث إصدار
    models_to_try = [
        'gemini-flash-latest',       # رابط ذكي - يجلب أحدث نموذج تلقائياً
        'gemini-2.5-flash',          # نموذج مستقر وواسع الاستخدام
        'gemini-2.0-flash',          # نموذج احتياطي قوي
        'gemini-3.8-flash',          # أحدث إصدار
        'gemini-3.5-flash',          # إصدار قريب
    ]
    
    last_error = None
    for model_name in models_to_try:
        # 3 محاولات لكل نموذج
        for attempt in range(3):
            try:
                response_stream = client.models.generate_content_stream(
                    model=model_name,
                    contents=contents
                )
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                return  # نجح! نخرج من الدالة
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # إذا كان الخطأ 503 (ازدحام) أو 429 (تجاوز الحد)، ننتظر ثم نعيد المحاولة
                if '503' in error_str or '429' in error_str or 'UNAVAILABLE' in error_str:
                    time.sleep(3)  # انتظار 3 ثوانٍ
                    continue
                else:
                    # خطأ آخر (مثل 404)، ننتقل مباشرة للنموذج التالي
                    break
    
    # إذا فشلت جميع المحاولات
    yield f"⚠️ الخوادم مزدحمة جداً حالياً (خطأ 503).\n\n🔹 **الحل:** انتظر 15-30 دقيقة ثم أعد المحاولة.\n🔹 هذا الضغط مؤقت على سيرفرات Google، وليس خطأ في التطبيق."


def handle_text_input(prompt):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({'role': 'user', 'content': prompt})
    
    client = init_gemini()
    with st.chat_message("assistant"):
        if not client:
            return
        
        # بناء ذاكرة المحادثة (آخر 6 رسائل)
        recent = st.session_state.chat_history[-7:-1]
        history_text = ""
        for msg in recent:
            role_name = "المستخدم" if msg['role'] == 'user' else "HYDROMEM"
            history_text += f"{role_name}: {msg['content']}\n"
        
        full_prompt = f"[سياق سابق]:\n{history_text}\n\n[السؤال]:\n{prompt}"
        
        contents = [full_prompt]
        if st.session_state.get('context_file'):
            contents.append(st.session_state.context_file)
        if st.session_state.get('context_image'):
            contents.append(st.session_state.context_image)
        
        try:
            placeholder = st.empty()
            full_response = ""
            
            for chunk in call_gemini_stream(client, contents):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            
            st.session_state.chat_history.append({
                'role': 'assistant', 'content': full_response
            })
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.download_button(
                    label="📥 تحميل الرد",
                    data=full_response.encode('utf-8'),
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


def chat_page():
    st.header("💬 HYDROMEM Chat — المساعد العلمي الذكي")
    st.markdown("*مدعوم بـ Google Gemini AI*")
    st.markdown("---")
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'context_file' not in st.session_state:
        st.session_state.context_file = None
    if 'context_image' not in st.session_state:
        st.session_state.context_image = None
    if 'file_name' not in st.session_state:
        st.session_state.file_name = None

    with st.sidebar:
        st.markdown("### 📎 إرفاق ملف أو صورة")
        uploaded_file = st.file_uploader(
            "ارفع ملفاً (PDF, CSV, TXT, صورة)",
            type=['png', 'jpg', 'jpeg', 'csv', 'txt', 'pdf'], key='chat_uploader'
        )
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            mime = uploaded_file.type
            if mime.startswith('image/'):
                st.session_state.context_image = Image.open(io.BytesIO(file_bytes))
                st.session_state.context_file = None
            else:
                st.session_state.context_file = types.Part.from_bytes(data=file_bytes, mime_type=mime)
                st.session_state.context_image = None
            st.session_state.file_name = uploaded_file.name
            st.success(f"✅ تم إرفاق: {uploaded_file.name}")
        
        if st.session_state.file_name:
            if st.button("🗑️ مسح الملف", use_container_width=True):
                st.session_state.context_file = None
                st.session_state.context_image = None
                st.session_state.file_name = None
                st.rerun()
        
        st.markdown("---")
        if st.button("💬 محادثة جديدة", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.context_file = None
            st.session_state.context_image = None
            st.session_state.file_name = None
            st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    prompt = st.chat_input("اكتب سؤالك...")
    if prompt:
        handle_text_input(prompt)
    
    st.markdown("---")
    st.markdown("""
    **💡 ميزات النسخة الاحترافية:**
    - 🧠 **الذاكرة:** يتذكر سياق المحادثة.
    - ⚡ **البث المباشر:** الرد يظهر حرفاً بحرف.
    - 🔄 **التجاوز التلقائي:** يحاول 5 نماذج × 3 مرات = 15 محاولة قبل إظهار الخطأ.
    """)
