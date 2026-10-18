import io
import uuid
import time
from datetime import datetime
import streamlit as st
from PIL import Image
import supabase_utils

# استيراد مكتبات الذكاء الاصطناعي
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

def clean_math(text):
    """دالة لإصلاح صيغة المعادلات الرياضية لتظهر بشكل جميل"""
    text = text.replace("\\[", "$$").replace("\\]", "$$")
    text = text.replace("[ ", "$$").replace(" ]", "$$")
    return text

def chat_page():
    st.title("💬 HYDROMEM Chat AI")
    
    # إعداد الجلسة
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None

    # --- الشريط الجانبي لسجل المحادثات ورفع الملفات ---
    with st.sidebar:
        st.markdown("## 📚 سجل المحادثات")
        if st.button("➕ محادثة جديدة", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_session_id = None
            st.rerun()
            
        user_email = st.session_state.user.get("email", "guest")
        sessions = supabase_utils.get_chat_sessions(user_email, limit=10)
        for s in sessions:
            if st.button(f"📄 {s['title'][:20]}...", key=s['id'], use_container_width=True):
                data = supabase_utils.get_chat_session_by_id(s['id'])
                if data:
                    st.session_state.messages = data['messages']
                    st.session_state.current_session_id = data['id']
                    st.rerun()
                    
        st.divider()
        st.markdown("## 📎 إرفاق ملف")
        uploaded_file = st.file_uploader("ارفع صورة أو PDF", type=["png", "jpg", "jpeg", "pdf", "csv"])
        
        if uploaded_file:
            st.success(f"تم رفع: {uploaded_file.name}")

    # --- عرض الرسائل السابقة ---
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # زر نسخ الرد (يظهر فقط لردود المساعد)
            if msg["role"] == "assistant":
                st.code(msg["content"], language="text", line_numbers=False)
                st.caption("⬆️ يمكنك نسخ الرد من المربع أعلاه.")

    # --- مربع الإدخال ---
    if prompt := st.chat_input("اسألني عن النمذجة الرياضية أو الطب..."):
        # إضافة رسالة المستخدم
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # رد المساعد
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("جاري التفكير... ⏳")
            
            try:
                response_text = ""
                
                # 1. محاولة استخدام Groq (سريع ونصي)
                groq_key = st.secrets.get("GROQ_API_KEY", "")
                if groq_key and GROQ_AVAILABLE:
                    client = Groq(api_key=groq_key)
                    models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
                    for model in models:
                        try:
                            completion = client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": "أنت مساعد علمي. أجب باللغة العربية. استخدم $$ للمعادلات."},
                                    *st.session_state.messages
                                ]
                            )
                            response_text = completion.choices[0].message.content
                            break
                        except Exception:
                            continue
                            
                # 2. استخدام Gemini كبديل (يدعم الصور)
                if not response_text and GEMINI_AVAILABLE and uploaded_file:
                    gemini_key = st.secrets.get("GEMINI_API_KEY", "")
                    if gemini_key:
                        g_client = genai.Client(api_key=gemini_key)
                        contents = [prompt]
                        
                        # إذا كان الملف صورة، نرسله لـ Gemini
                        if uploaded_file.type.startswith("image/"):
                            img = Image.open(uploaded_file)
                            contents.append(img)
                            
                        g_res = g_client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=contents
                        )
                        response_text = g_res.text

                # 3. إذا فشل كل شيء
                if not response_text:
                    response_text = "عذراً، لم أتمكن من الاتصال بمزودي الذكاء الاصطناعي. يرجى المحاولة لاحقاً."

                # تنسيق المعادلات وعرضها
                formatted_response = clean_math(response_text)
                message_placeholder.markdown(formatted_response)
                st.code(formatted_response, language="text", line_numbers=False)
                st.caption("⬆️ زر النسخ في أعلى المربع.")

                # حفظ الرسالة
                st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                
                # حفظ في سجل Supabase
                title = st.session_state.messages[0]["content"][:30] + "..."
                sid = supabase_utils.save_chat_session(
                    user_email, title, st.session_state.messages, st.session_state.current_session_id
                )
                if sid:
                    st.session_state.current_session_id = sid

            except Exception as e:
                message_placeholder.error(f"حدث خطأ: {e}")
