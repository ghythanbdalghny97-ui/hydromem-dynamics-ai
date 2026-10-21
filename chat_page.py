import streamlit as st
import pandas as pd
from PIL import Image
from pypdf import PdfReader
import docx
import re
import io
import contextlib
import matplotlib
matplotlib.use('Agg') # ضروري لتشغيل الرسوم في Streamlit
import matplotlib.pyplot as plt
import numpy as np
import scipy
import types
import supabase_utils
import config
from gtts import gTTS

# ==========================================
# 1. محرك تنفيذ الأكواد واستخراج النتائج
# ==========================================
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
            exec(code, {"np": np, "plt": plt, "scipy": scipy, "pd": pd}, local_vars)
        
        # استخراج الأرقام والجداول النهائية
        valid_vars = {}
        for k, v in local_vars.items():
            if isinstance(v, (int, float, str, bool, list, tuple, np.ndarray, pd.DataFrame)):
                if not isinstance(v, (types.ModuleType, type)):
                    if isinstance(v, np.ndarray) and v.size > 100:
                        continue # تجاهل المصفوفات الضخمة
                    valid_vars[k] = v

        return True, stdout.getvalue(), figs, valid_vars
    except Exception as e:
        return False, str(e), [], {}
    finally:
        plt.show = original_show

def speak_text(text):
    clean_text = re.sub(r'\$.*?\$', 'معادلة رياضية', text).replace("#", "").replace("*", "")
    tts = gTTS(text=clean_text[:3000], lang='ar')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    return audio_bytes

def extract_file(file):
    try:
        if file.name.endswith(".pdf"): return "".join([p.extract_text() for p in PdfReader(file).pages])
        elif file.name.endswith(".docx"): return "\n".join([p.text for p in docx.Document(file).paragraphs])
        elif file.name.endswith(".xlsx"): return pd.read_excel(file).to_string()
        elif file.name.endswith((".csv", ".txt")): return file.read().decode("utf-8")
    except Exception as e: return f"خطأ: {e}"
    return ""

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

# ==========================================
# 2. الأدوات المتقدمة
# ==========================================
QUICK_ACTIONS = {
    "🔍 بسّط الشرح": "أعد شرح الإجابة السابقة بأسلوب مبسط جداً لطالب جامعي.",
    "🧪 حوّل لبروتوكول": "حوّل الإجابة السابقة إلى بروتوكول تجريبي عملي (خطوات مرقمة).",
    "📚 أضف مراجع APA": "اقترح 3 مراجع علمية موثوقة بصيغة APA.",
    "🌐 ترجم للإنجليزية": "Translate the previous response into professional academic English.",
    "📝 اكتب ورقة علمية": "حوّل الإجابة السابقة إلى قسم (Results) جاهز للنشر.",
    "🎯 مستويات الثقة": "أعد الإجابة مع تصنيف كل معلومة: (مؤكد / محتمل / افتراضي).",
}

# ==========================================
# 3. الواجهة الرئيسية
# ==========================================
def render():
    st.title("💬 HYDROMEM Chat AI")
    if "messages" not in st.session_state: st.session_state.messages = []
    if "session_id" not in st.session_state: st.session_state.session_id = None

    with st.sidebar:
        st.subheader("⚙️ الإعدادات")
        model_choice = st.selectbox("المحرك", ["Groq (سريع)", "Gemini (صور وملفات)"])
        persona = st.selectbox("نوع المساعد", list(config.PERSONAS.keys()))
        ans_length = st.radio("طول الإجابة:", ["مفصلة (شاملة)", "مختصرة (مركزة)"])
        output_lang = st.radio("لغة الإجابة:", ["العربية", "English", "كلاهما"])
        uploaded_file = st.file_uploader("📎 رفع ملف للتحليل", type=config.SUPPORTED_FILES)
        
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

    # عرض الرسائل والأدوات
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            if msg["role"] == "assistant":
                # 1. تشغيل الكود واستخراج النتائج
                code_match = re.search(r"```python\n(.*?)```", msg["content"], re.DOTALL)
                if code_match:
                    if st.button("⚙️ تشغيل الكود واستخراج النتائج", key=f"run_code_{i}"):
                        with st.spinner("جاري التنفيذ والتحليل..."):
                            success, output, figs, valid_vars = execute_python_code(code_match.group(1))
                            if success:
                                st.success("✅ تم التنفيذ بنجاح!")
                                
                                # عرض الرسومات
                                for fig in figs:
                                    st.pyplot(fig)
                                
                                # عرض المطبوعات النصية
                                if output.strip():
                                    st.code(output, language="text")
                                
                                # عرض المتغيرات والنتائج العددية (جداول أو أرقام)
                                if valid_vars:
                                    st.write("### 📊 النتائج العددية المستخرجة من الكود:")
                                    for k, v in valid_vars.items():
                                        if isinstance(v, pd.DataFrame):
                                            st.write(f"**{k}:**")
                                            st.dataframe(v)
                                        elif isinstance(v, (int, float)):
                                            st.metric(label=k, value=f"{v:.4f}" if isinstance(v, float) else str(v))
                                        elif isinstance(v, (list, tuple)) and len(str(v)) < 100:
                                            st.write(f"**{k}:** {v}")
                                        elif isinstance(v, np.ndarray) and v.size <= 100:
                                            st.write(f"**{k}:** {v.tolist()}")
                            else:
                                st.error(f"❌ خطأ في الكود: {output}")
                
                # 2. الأدوات المتقدمة
                with st.expander("🛠️ أدوات متقدمة"):
                    st.write("**حوّل هذا الرد إلى:**")
                    cols = st.columns(3)
                    for idx, (label, instruction) in enumerate(QUICK_ACTIONS.items()):
                        with cols[idx % 3]:
                            if st.button(label, key=f"qa_{i}_{idx}"):
                                with st.spinner(f"جاري {label}..."):
                                    sys = f"{config.PERSONAS[persona]}\nأجب بالعربية بدقة."
                                    new_ans = call_ai(f"الإجابة السابقة: {msg['content']}\n\nالمطلوب: {instruction}", sys, model_choice, 2048)
                                    st.session_state.messages.append({"role": "assistant", "content": f"**[{label}]**\n\n{new_ans}"})
                                    st.rerun()
                    st.divider()
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("🔊 استمع للرد", key=f"tts_{i}"):
                            with st.spinner("جاري الصوت..."):
                                try: st.audio(speak_text(msg["content"]), format="audio/mp3")
                                except: st.error("تعذر الصوت")
                    with col_b:
                        st.code(msg["content"], language="markdown")

    # الإدخال النصي
    if prompt := st.chat_input("اطلب معادلة، رسماً بيانياً، أو ارفع ملفاً..."):
        full_prompt = prompt
        if uploaded_file: full_prompt += f"\n\n[محتوى الملف]:\n{extract_file(uploaded_file)}"

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 جاري التفكير..."):
                length_inst = "أجب إجابة مفصلة." if "مفصلة" in ans_length else "أجب إجابة مختصرة."
                lang_inst = {"العربية": "أجب بالعربية.", "English": "Answer in English.", "كلاهما": "أجب بالعربية ثم الإنجليزية."}[output_lang]
                system_prompt = f"{config.PERSONAS[persona]}\n{length_inst}\n{lang_inst}\nأجب بدقة. استخدم $$ للمعادلات. اختم بـ (الخلاصة)."
                
                answer = call_ai(full_prompt, system_prompt, model_choice)
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        title = st.session_state.messages[0]["content"][:40]
        st.session_state.session_id = supabase_utils.save_chat(email, title, st.session_state.messages, st.session_state.session_id)
        st.rerun()
