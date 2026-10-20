import streamlit as st
import pandas as pd
from PIL import Image
from pypdf import PdfReader
import docx
import re
import supabase_utils
import config
from gtts import gTTS
import io

def fix_latex(text):
    text = text.replace(r"\[", "$$").replace(r"\]", "$$")
    text = text.replace(r"\begin{cases}", "").replace(r"\end{cases}", "")
    greek = [r"\Theta", r"\eta", r"\beta", r"\gamma", r"\mu", r"\tau", r"\alpha", r"\lambda"]
    for g in greek:
        text = re.sub(r'(?<!\$)' + re.escape(g) + r'(?!\$)', lambda m: f'${g}$', text)
    return text

def extract_file(file):
    try:
        if file.name.endswith(".pdf"): return "".join([p.extract_text() for p in PdfReader(file).pages])
        elif file.name.endswith(".docx"): return "\n".join([p.text for p in docx.Document(file).paragraphs])
        elif file.name.endswith(".xlsx"): return pd.read_excel(file).to_string()
        elif file.name.endswith((".csv", ".txt")): return file.read().decode("utf-8")
    except Exception as e: return f"خطأ في قراءة الملف: {e}"
    return ""

def speak_text(text):
    clean_text = re.sub(r'\$.*?\$', 'معادلة رياضية', text).replace("#", "").replace("*", "")
    tts = gTTS(text=clean_text[:3000], lang='ar')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes

def render():
    st.title("💬 HYDROMEM Chat AI")
    if "messages" not in st.session_state: st.session_state.messages = []
    if "session_id" not in st.session_state: st.session_state.session_id = None

    with st.sidebar:
        st.subheader("⚙️ الإعدادات")
        model = st.selectbox("المحرك", ["Groq (سريع)", "Gemini (صور وملفات)"])
        persona = st.selectbox("نوع المساعد", list(config.PERSONAS.keys()))
        ans_length = st.radio("طول الإجابة المطلوب:", ["مفصلة (شاملة)", "مختصرة (مركزة)"])
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
            if msg["role"] == "assistant":
                if st.button("🔊 استمع للرد", key=f"audio_{hash(msg['content'])}"):
                    with st.spinner("جاري تحويل النص إلى صوت..."):
                        try:
                            audio_data = speak_text(msg["content"])
                            st.audio(audio_data, format="audio/mp3")
                        except: st.error("تعذر تشغيل الصوت.")

    # الإدخال
    if prompt := st.chat_input("اسأل أو اطلب محاكاة (مثلاً: قم بمحاكاة التئام العظام)"):
        full_prompt = prompt
        if uploaded_file and not uploaded_file.type.startswith("image/"):
            full_prompt += f"\n\n[محتوى الملف المرفق]:\n{extract_file(uploaded_file)}"

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 جاري التحليل..."):
                answer = ""
                length_instruction = "أجب إجابة مفصلة وشاملة." if "مفصلة" in ans_length else "أجب إجابة مختصرة جداً."
                
                # 🌟 ربط الدردشة بالمحاكاة (الإجابة الذكية)
                system_prompt = f"{config.PERSONAS[persona]}\n{length_instruction}\nأجب باللغة العربية. استخدم $$ للمعادلات. اختم بـ (الخلاصة)."
                
                if "محاكاة" in prompt or "simulation" in prompt.lower() or "تطبيق" in prompt:
                     answer = "بصفتي HYDROMEM AI، أستطيع إجراء المحاكاة لك فوراً! يرجى التوجه إلى صفحة **🔬 المحاكاة** من القائمة الجانبية، حيث وفرت لك 5 تطبيقات (النموذج الديناميكي، التئام العظام، التئام الجروح، خشونة الركبة، وأقراص العمود الفقري). أدخل الأرقام هناك واحصل على الرسوم البيانية والتقارير."
                else:
                    try:
                        if model.startswith("Groq") and config.GROQ_API_KEY:
                            from groq import Groq
                            client = Groq(api_key=config.GROQ_API_KEY)
                            tokens = 4096 if "مفصلة" in ans_length else 1024
                            res = client.chat.completions.create(
                                model=config.GROQ_MODELS[0], max_tokens=tokens,
                                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": full_prompt}]
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
                        else: answer = "الرجاء التأكد من مفاتيح API."
                    except Exception as e: answer = f"حدث خطأ: {e}"

                formatted_answer = fix_latex(answer)
                st.markdown(formatted_answer)
                
                if st.button("🔊 استمع للرد", key="new_audio"):
                    with st.spinner("جاري تحويل النص إلى صوت..."):
                        try:
                            audio_data = speak_text(formatted_answer)
                            st.audio(audio_data, format="audio/mp3")
                        except: pass

        st.session_state.messages.append({"role": "assistant", "content": formatted_answer})
        title = st.session_state.messages[0]["content"][:40]
        st.session_state.session_id = supabase_utils.save_chat(email, title, st.session_state.messages, st.session_state.session_id)
