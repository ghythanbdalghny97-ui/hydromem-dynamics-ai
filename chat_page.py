import io
import streamlit as st
from PIL import Image
import supabase_utils

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

def fix_latex(text):
    """دالة لإصلاح أخطاء المعادلات الرياضية القادمة من الذكاء الاصطناعي"""
    text = text.replace(r"\$$4pt]", r"\\[4pt]")
    text = text.replace(r"\$$6pt]", r"\\[6pt]")
    text = text.replace(r"\[", "$$")
    text = text.replace(r"\]", "$$")
    return text

def chat_page():
    st.title("💬 HYDROMEM Chat AI")
    
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

    # --- عرض الرسائل السابقة بشكل جميل (مثل ChatGPT) ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- مربع الإدخال ---
    if prompt := st.chat_input("اسألني عن النمذجة الرياضية أو الطب..."):
        # إضافة وعرض رسالة المستخدم
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # عرض رد المساعد
        with st.chat_message("assistant"):
            with st.spinner("جاري التحليل..."):
                try:
                    response_text = ""
                    groq_key = st.secrets.get("GROQ_API_KEY", "")
                    
                    # استخدام Groq
                    if groq_key and GROQ_AVAILABLE:
                        client = Groq(api_key=groq_key)
                        models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
                        for model in models:
                            try:
                                completion = client.chat.completions.create(
                                    model=model,
                                    # 🌟 زيادة الحد الأقصى للرد
                                    max_tokens=4096, 
                                    messages=[
                                        # 🌟 إجبار الذكاء الاصطناعي على كتابة خلاصة وتنسيق المعادلات
                                        {"role": "system", "content": "أنت مساعد علمي. أجب باللغة العربية. استخدم $$...$$ للمعادلات المستقلة و $...$ للمعادلات المضمنة. لا تستخدم \\[ أو \\] أبداً. **يجب أن تنهي إجابتك دائماً بخلاصة قصيرة تحت عنوان (الخلاصة).**"},
                                        *st.session_state.messages
                                    ]
                                )
                                response_text = completion.choices[0].message.content
                                break
                            except Exception:
                                continue
                    
                    # بديل: Gemini
                    if not response_text and GEMINI_AVAILABLE:
                        gemini_key = st.secrets.get("GEMINI_API_KEY", "")
                        if gemini_key:
                            g_client = genai.Client(api_key=gemini_key)
                            contents = [prompt]
                            if uploaded_file and uploaded_file.type.startswith("image/"):
                                contents.append(Image.open(uploaded_file))
                            g_res = g_client.models.generate_content(model="gemini-2.0-flash", contents=contents)
                            response_text = g_res.text

                    if not response_text:
                        response_text = "عذراً، لم أتمكن من الاتصال بمزودي الذكاء الاصطناعي."

                    # إصلاح المعادلات الرياضية
                    formatted_response = fix_latex(response_text)
                    
                    # عرض الرد
                    st.markdown(formatted_response)
                    
                    # حفظ الرسالة
                    st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                    
                    title = st.session_state.messages[0]["content"][:30] + "..."
                    sid = supabase_utils.save_chat_session(
                        user_email, title, st.session_state.messages, st.session_state.current_session_id
                    )
                    if sid: st.session_state.current_session_id = sid

                except Exception as e:
                    st.error(f"حدث خطأ: {e}")
