import streamlit as st
import pandas as pd
from PIL import Image
from pypdf import PdfReader
import docx
import re
import supabase_utils
import config

def fix_latex(text):
    # إصلاح المعادلات الرياضية لظهور جميل
    text = text.replace(r"\[", "$$").replace(r"\]", "$$")
    greek = [r"\Theta", r"\eta", r"\beta", r"\gamma", r"\mu", r"\tau"]
    for g in greek:
        text = re.sub(r'(?<!\$)' + re.escape(g) + r'(?!\$)', lambda m: f'${g}$', text)
    return text

def extract_file(file):
    try:
        if file.name.endswith(".pdf"):
            return "".join([p.extract_text() for p in PdfReader(file).pages])
        elif file.name.endswith(".docx"):
            return "\n".join([p.text for p in docx.Document(file).paragraphs])
        elif file.name.endswith(".xlsx"):
            return pd.read_excel(file).to_string()
        elif file.name.endswith((".csv", ".txt")):
            return file.read().decode("utf-8")
    except Exception as e: return f"خطأ في قراءة الملف: {e}"
    return ""

def render():
    st.title("💬 HYDROMEM Chat AI")
    if "messages" not in st.session_state: st.session_state.messages = []
    if "session_id" not in st.session_state: st.session_state.session_id = None

    with st.sidebar:
        st.subheader("⚙️ الإعدادات")
        model = st.selectbox("المحرك", ["Groq (سريع)", "Gemini (صور وملفات)"])
        persona = st.selectbox("نوع المساعد", list(config.PERSONAS.keys()))
        st.divider()
        uploaded_file = st.file_uploader("📎 رفع ملف", type=config.SUPPORTED_FILES)
        st.divider()
        st.subheader("📚 المحادثات السابقة")
        
        email = st.session_state.user.get("email")
        for s in supabase_utils.get_chats(email):
            if st.button(s["title"][:20]+"...", key=s["id"]):
                old = supabase_utils.get_chat_by_id(s["id"])
                if old:
                    st.session_state.messages = old["messages"]
                    st.session_state.session_id = old["id"]
                    st.rerun()
        if st.button("➕ محادثة جديدة"):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()

    # عرض الرسائل
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # الإدخال
    if prompt := st.chat_input("اكتب سؤالك هنا..."):
        full_prompt = prompt
        if uploaded_file and not uploaded_file.type.startswith("image/"):
            full_prompt += f"\n\n[محتوى الملف]:\n{extract_file(uploaded_file)}"

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 جاري التحليل..."):
                answer = ""
                system = f"{config.PERSONAS[persona]}\nأجب باللغة العربية. استخدم $$ للمعادلات. اختم بـ (الخلاصة)."
                try:
                    if model.startswith("Groq") and config.GROQ_API_KEY:
                        from groq import Groq
                        client = Groq(api_key=config.GROQ_API_KEY)
                        res = client.chat.completions.create(
                            model=config.GROQ_MODELS[0], max_tokens=4096,
                            messages=[{"role": "system", "content": system}, {"role": "user", "content": full_prompt}]
                        )
                        answer = res.choices[0].message.content
                    elif config.GEMINI_API_KEY:
                        from google import genai
                        client = genai.Client(api_key=config.GEMINI_API_KEY)
                        contents = [full_prompt]
                        if uploaded_file and uploaded_file.type.startswith("image/"):
                            contents.append(Image.open(uploaded_file))
                        res = client.models.generate_content(model=config.GEMINI_MODEL, contents=contents)
                        answer = res.text
                    else:
                        answer = "الرجاء التأكد من مفاتيح API في الإعدادات."
                except Exception as e:
                    answer = f"حدث خطأ: {e}"

                st.markdown(fix_latex(answer))
        
        st.session_state.messages.append({"role": "assistant", "content": fix_latex(answer)})
        # حفظ المحادثة
        title = st.session_state.messages[0]["content"][:40]
        st.session_state.session_id = supabase_utils.save_chat(email, title, st.session_state.messages, st.session_state.session_id)
