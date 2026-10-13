# ============================================================
# HYDROMEM Chat - AI Medical & Scientific Assistant (Pro Edition)
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
            st.warning("⚠️ لم يتم العثور على مفتاح GEMINI_API_KEY في الإعدادات.")
            return None
        
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        st.error(f"❌ خطأ في تهيئة Gemini: {str(e)}")
        return None


def get_system_prompt():
    return """أنت مساعد علمي وطبي ذكي باسم HYDROMEM.
أنت منصة متكاملة لمحاكاة الأنظمة الديناميكية المعقدة.
تتميز بالدقة العلمية، والردود المنظمة، والقدرة على تحليل المعادلات والصور والملفات.
أجب دائماً بالعربية، وقدم إجابات شاملة ومنظمة، واذكر المراجع إذا أمكن.
عند الحديث عن الطب، أضف إخلاء مسؤولية.
"""


def call_gemini_stream(client, contents):
    """استدعاء Gemini API مع البث المباشر (Streaming)"""
    try:
        response_stream = client.models.generate_content_stream(
            model='gemini-3.8-flash',
            contents=contents
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        # حل احتياطي في حال فشل النموذج السريع
        try:
            response_stream = client.models.generate_content_stream(
                model='gemini-3.1-flash',
                contents=contents
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e2:
            yield f"❌ فشل الاتصال: {str(e2)}"


def handle_text_input(prompt):
    """معالجة إدخال النص مع الذاكرة والبث المباشر"""
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.chat_history.append({'role': 'user', 'content': prompt})
    
    client = init_gemini()
    with st.chat_message("assistant"):
        if not client:
            return
        
        # 1. بناء ذاكرة المحادثة (آخر 6 رسائل) لكي يتذكر السياق
        recent_history = st.session_state.chat_history[-7:-1] # استثناء السؤال الحالي
        history_text = ""
        for msg in recent_history:
            role_name = "المستخدم" if msg['role'] == 'user' else "HYDROMEM"
            history_text += f"{role_name}: {msg['content']}\n"
        
        # 2. تجهيز المحتوى (الذاكرة + السؤال الحالي + المرفقات)
        full_prompt = f"""
        [سياق المحادثة السابقة]:
        {history_text}
        
        [سؤال المستخدم الحالي]:
        {prompt}
        """
        
        contents = [full_prompt]
        if st.session_state.get('context_file'):
            contents.append(st.session_state.context_file)
        if st.session_state.get('context_image'):
            contents.append(st.session_state.context_image)
        
        try:
            # 3. عرض الرد بشكل متدفق (مثل ChatGPT)
            response_placeholder = st.empty()
            full_response = ""
            
            for chunk in call_gemini_stream(client, contents):
                full_response += chunk
                # إضافة مؤشر وهمي أثناء الكتابة
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            st.session_state.chat_history.append({
                'role': 'assistant', 'content': full_response
            })
            
            # أزرار التحكم بالرد
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
                if st.button("🔄 إعادة توليد الرد", key=f"regen_{datetime.now().timestamp()}"):
                    # حذف آخر رد وإعادة المحاولة
                    st.session_state.chat_history.pop()
                    st.rerun()
                    
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")


def chat_page():
    st.header("💬 HYDROMEM Chat — المساعد العلمي الذكي")
    st.markdown("*النسخة الاحترافية: مدعومة بالذاكرة والبث المباشر*")
    st.markdown("---")
    
    # تهيئة الذاكرة (Session State)
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'context_file' not in st.session_state:
        st.session_state.context_file = None
    if 'context_image' not in st.session_state:
        st.session_state.context_image = None
    if 'file_name' not in st.session_state:
        st.session_state.file_name = None

    # ==========================================
    # الشريط الجانبي: رفع الملفات وإدارتها
    # ==========================================
    with st.sidebar:
        st.markdown("### 📎 إرفاق ملف أو صورة")
        st.info("قم برفع الملف هنا، ثم اسأل ما تريد عنه في الأسفل.")
        
        uploaded_file = st.file_uploader(
            "ارفع صورة أو ملف (PDF, CSV, TXT, PNG, JPG)",
            type=['png', 'jpg', 'jpeg', 'csv', 'txt', 'pdf'], 
            key='chat_uploader'
        )
        
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            mime = uploaded_file.type
            
            if mime.startswith('image/'):
                image = Image.open(io.BytesIO(file_bytes))
                st.session_state.context_image = image
                st.session_state.context_file = None
                st.session_state.file_name = uploaded_file.name
            else:
                file_part = types.Part.from_bytes(data=file_bytes, mime_type=mime)
                st.session_state.context_file = file_part
                st.session_state.context_image = None
                st.session_state.file_name = uploaded_file.name
            
            st.success(f"✅ تم إرفاق: {uploaded_file.name}")
        
        if st.session_state.file_name:
            if st.button("🗑️ مسح الملف المرفق", use_container_width=True):
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

    # ==========================================
    # عرض سجل المحادثة
    # ==========================================
    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # ==========================================
    # صندوق الدردشة
    # ==========================================
    prompt = st.chat_input("اكتب سؤالك، أو اطلب تحليل الملف المرفق...")
    if prompt:
        handle_text_input(prompt)
    
    st.markdown("---")
    st.markdown("""
    **💡 ميزات النسخة الاحترافية:**
    - 🧠 **الذاكرة:** يتذكر سياق المحادثة السابقة (آخر 6 رسائل).
    - ⚡ **البث المباشر:** الرد يظهر حرفاً بحرف (مثل ChatGPT).
    - 🔄 **إعادة التوليد:** يمكنك طلب رد جديد إذا لم يعجبك الرد الأول.
    """)
