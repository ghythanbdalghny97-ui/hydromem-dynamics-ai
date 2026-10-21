import streamlit as st
import pandas as pd
from PIL import Image
from pypdf import PdfReader
import docx
import re
import io
import contextlib
import matplotlib
matplotlib.use('Agg') # ضروري لبيئة Streamlit
import matplotlib.pyplot as plt
import numpy as np
import scipy
import supabase_utils
import config
from gtts import gTTS

# دالة لتنفيذ كود بايثون بأمان والتقاط الرسوم البيانية
def execute_python_code(code):
    local_vars = {}
    stdout = io.StringIO()
    figs = []

    def custom_show(*args, **kwargs):
        figs.append(plt.gcf())
        plt.close('all')

    original_show = plt.show
    plt.show = custom_show

    try:
        with contextlib.redirect_stdout(stdout):
            # تنفيذ الكود مع تمرير المكتبات الأساسية
            exec(code, {"np": np, "plt": plt, "scipy": scipy, "pd": pd}, local_vars)
        return True, stdout.getvalue(), figs
    except Exception as e:
        return False, str(e), []
    finally:
        plt.show = original_show

def fix_latex(text):
    text = text.replace(r"\[", "$$").replace(r"\]", "$$")
    text = text.replace(r"\begin{cases}", "").replace(r"\end{cases}", "")
    return text

def extract_file(file):
    try:
        if file.name.endswith(".pdf"): return "".join([p.extract_text() for p in PdfReader(file).pages])
        elif file.name.endswith(".docx"): return "\n".join([p.text for p in docx.Document(file).paragraphs])
        elif file.name.endswith(".xlsx"): return pd.read_excel(file).to_string()
        elif file.name.endswith((".csv", ".txt")): return file.read().decode("utf-8")
    except Exception as e: return f"خطأ: {e}"
    return ""

def speak_text(text):
    clean_text = re.sub(r'\$.*?\$', 'معادلة رياضية', text).replace("#", "").replace("*", "")
    tts = gTTS(text=clean_text[:3000], lang='ar')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes

def call_ai(full_prompt, system_prompt, model_choice, max_tokens=4096):
    try:
        if model_choice.startswith("Groq") and config.GROQ_API_KEY:
            from groq import Groq
            client = Groq(api_key=config.GROQ_API_KEY)
            res = client.chat.completions.create(
                model=config.GROQ_MODELS[0], max_tokens=max_tokens,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": full_prompt}]
            )
            return res.choices[0].message.content
        elif config.GEMINI_API_KEY:
            from google import genai
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            res = client.models.generate_content(model=config.GEMINI_MODEL, contents=full_prompt)
            return res.text
        return "الرجاء التأكد من مفاتيح API."
    except Exception as e:
        return f"حدث خطأ: {e}"

def render():
    st.title("💬 HYDROMEM Chat AI")
    if "messages" not in st.session_state: st.session_state.messages = []
    if "session_id" not in st.session_state: st.session_state.session_id = None

    with st.sidebar:
        st.subheader("⚙️ الإعدادات")
        model_choice = st.selectbox("المحرك", ["Groq (سريع)", "Gemini (صور وملفات)"])
        persona = st.selectbox("نوع المساعد", list(config.PERSONAS.keys()))
        uploaded_file = st.file_uploader("📎 رفع ملف", type=config.SUPPORTED_FILES)

    # عرض الرسائل
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # 🔥 الميزة الجديدة: التقاط الكود من رد الذكاء الاصطناعي وتشغيله
            if msg["role"] == "assistant":
                code_match = re.search(r"```python\n(.*?)```", msg["content"], re.DOTALL)
                if code_match:
                    code_to_run = code_match.group(1)
                    if st.button("⚙️ تشغيل الكود ورسم النتائج", key=f"run_code_{i}"):
                        with st.spinner("جاري تنفيذ الكود ورسم الأشكال..."):
                            success, output, figs = execute_python_code(code_to_run)
                            if success:
                                st.success("✅ تم التنفيذ بنجاح!")
                                if output:
                                    st.code(output, language="text")
                                for fig in figs:
                                    st.pyplot(fig)
                            else:
                                st.error(f"❌ خطأ في الكود: {output}")

                # زر الصوت
                if st.button("🔊 استمع للرد", key=f"tts_{i}"):
                    with st.spinner("جاري الصوت..."):
                        try:
                            audio_data = speak_text(msg["content"])
                            st.audio(audio_data, format="audio/mp3")
                        except: pass

    # الإدخال
    if prompt := st.chat_input("اطلب معادلة، رسماً بيانياً، أو ارفع ملفاً..."):
        full_prompt = prompt
        if uploaded_file:
            full_prompt += f"\n\n[محتوى الملف]:\n{extract_file(uploaded_file)}"

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 جاري التفكير..."):
                system_prompt = f"{config.PERSONAS[persona]}\nأجب بالعربية. استخدم $$ للمعادلات. اختم بـ (الخلاصة)."
                answer = call_ai(full_prompt, system_prompt, model_choice)
                formatted_answer = fix_latex(answer)
                st.markdown(formatted_answer)

        st.session_state.messages.append({"role": "assistant", "content": formatted_answer})
        title = st.session_state.messages[0]["content"][:40]
        st.session_state.session_id = supabase_utils.save_chat(st.session_state.user.get("email"), title, st.session_state.messages, st.session_state.session_id)
        st.rerun()
