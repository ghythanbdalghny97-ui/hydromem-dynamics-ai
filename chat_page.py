import streamlit as st
import pandas as pd
from PIL import Image
from pypdf import PdfReader
import docx
import re
import io
import contextlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import scipy
import asyncio
import nest_asyncio
import edge_tts
import supabase_utils
import config

nest_asyncio.apply()

# ==========================================
# دوال المساعدة
# ==========================================
def execute_python_code(code):
    exec_env = {"np": np, "plt": plt, "scipy": scipy, "pd": pd}
    stdout = io.StringIO()
    figs = []

    def custom_show(*args, **kwargs):
        figs.append(plt.gcf())
        plt.close('all')

    original_show = plt.show
    plt.show = custom_show

    try:
        with contextlib.redirect_stdout(stdout):
            exec(code, exec_env)

        final_results_dict = exec_env.get("final_results", {})
        
        if not final_results_dict:
            valid_vars = {}
            ignore_list = ["k1", "k2", "k3", "t_start", "t_end", "t_eval", "t_span", "num_pts", "y0", "O0", "C0", "fig", "ax"]
            for k, v in exec_env.items():
                if k.startswith('_') or k in ["np", "plt", "scipy", "pd"] or k in ignore_list:
                    continue
                if isinstance(v, (int, float, str, bool, list, tuple, np.ndarray, pd.DataFrame)):
                    if isinstance(v, np.ndarray) and v.size > 100: continue
                    valid_vars[k] = v
            final_results_dict = valid_vars

        return True, stdout.getvalue(), figs, final_results_dict
    except Exception as e:
        return False, str(e), [], {}
    finally:
        plt.show = original_show

def generate_audio_bytes(text, voice_id):
    clean_text = re.sub(r'\$.*?\$', 'معادلة رياضية', text).replace("#", "").replace("*", "")
    clean_text = clean_text[:3000] 
    
    async def _generate():
        communicate = edge_tts.Communicate(clean_text, voice_id)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    return asyncio.run(_generate())

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
# دوال Callbacks (تمنع انهيار المتصفح)
# ==========================================
def handle_quick_action(action_type, instruction, msg_content, persona, model_choice):
    with st.spinner(f"جاري {action_type}..."):
        sys = f"{config.PERSONAS[persona]}\nأجب بالعربية بدقة."
        new_ans = call_ai(f"الإجابة السابقة: {msg_content}\n\nالمطلوب: {instruction}", sys, model_choice, 2048)
        st.session_state.messages.append({"role": "assistant", "content": f"**[{action_type}]**\n\n{new_ans}"})

def handle_audio_generation(msg_content, voice_id, index):
    try:
        audio_data = generate_audio_bytes(msg_content, voice_id)
        st.session_state[f"audio_{index}"] = audio_data
    except Exception as e:
        st.error(f"تعذر الصوت: {e}")

def handle_run_code(code, index):
    success, output, figs, valid_vars = execute_python_code(code)
    st.session_state[f"code_result_{index}"] = {
        "success": success, "output": output, "figs": figs, "valid_vars": valid_vars
    }

# ==========================================
# الواجهة
# ==========================================
QUICK_ACTIONS = {
    "🔍 بسّط الشرح": "أعد شرح الإجابة السابقة بأسلوب مبسط جداً لطالب جامعي.",
    "🧪 حوّل لبروتوكول": "حوّل الإجابة السابقة إلى بروتوكول تجريبي عملي (خطوات مرقمة).",
    "📚 أضف مراجع APA": "اقترح 3 مراجع علمية موثوقة بصيغة APA.",
    "🌐 ترجم للإنجليزية": "Translate the previous response into professional academic English.",
    "📝 اكتب ورقة علمية": "حوّل الإجابة السابقة إلى قسم (Results) جاهز للنشر.",
}

def render():
    st.title("💬 HYDROMEM Chat AI")
    if "messages" not in st.session_state: st.session_state.messages = []
    if "session_id" not in st.session_state: st.session_state.session_id = None

    with st.sidebar:
        st.subheader("⚙️ الإعدادات")
        model_choice = st.selectbox("المحرك", ["Groq (سريع)", "Gemini (صور وملفات)"])
        persona = st.selectbox("نوع المساعد", list(config.PERSONAS.keys()))
        
        voices = {
            "🇾🇪 يمني (صنعاء - ذكر)": "ar-YE-SanaNeural",
            "🇾🇪 يمني (صنعاء - أنثى)": "ar-YE-AminaNeural",
            "🇸🇦 فصحى/سعودي (ذكر)": "ar-SA-HamedNeural",
            "🇸🇦 فصحى/سعودي (أنثى)": "ar-SA-ZariyahNeural",
            "🇪🇬 مصري (ذكر)": "ar-EG-ShakirNeural",
            "🇪🇬 مصري (أنثى)": "ar-EG-SalmaNeural",
            "🇦🇪 إماراتي (ذكر)": "ar-AE-HamdanNeural",
            "🇦🇪 إماراتي (أنثى)": "ar-AE-FatimaNeural",
        }
        selected_voice_name = st.selectbox("🎙️ صوت القراءة:", list(voices.keys()))
        selected_voice_id = voices[selected_voice_name]

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

    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            if msg["role"] == "assistant":
                code_match = re.search(r"```python\n(.*?)```", msg["content"], re.DOTALL)
                if code_match:
                    # زر تشغيل الكود يعتمد على Callback
                    st.button("⚙️ تشغيل الكود واستخراج النتائج", key=f"run_code_{i}", on_click=handle_run_code, args=(code_match.group(1), i))
                    
                    # عرض النتيجة المحفوظة في الحالة (إن وجدت)
                    if f"code_result_{i}" in st.session_state:
                        res = st.session_state[f"code_result_{i}"]
                        if res["success"]:
                            st.success("✅ تم التنفيذ بنجاح!")
                            for fig in res["figs"]: st.pyplot(fig)
                            if res["output"].strip(): st.code(res["output"], language="text")
                            if res["valid_vars"]:
                                st.write("### 📊 النتائج النهائية:")
                                for k, v in res["valid_vars"].items():
                                    if isinstance(v, (int, float)):
                                        st.metric(label=k, value=f"{v:.4f}" if isinstance(v, float) else str(v))
                                    else:
                                        st.write(f"**{k}:** {v}")
                        else:
                            st.error(f"❌ خطأ في الكود: {res['output']}")

                with st.expander("🛠️ أدوات متقدمة"):
                    st.write("**حوّل هذا الرد إلى:**")
                    cols = st.columns(3)
                    for idx, (label, instruction) in enumerate(QUICK_ACTIONS.items()):
                        with cols[idx % 3]:
                            st.button(label, key=f"qa_{i}_{idx}", on_click=handle_quick_action, args=(label, instruction, msg["content"], persona, model_choice))
                    
                    st.divider()
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.button("🔊 استمع للرد", key=f"tts_{i}", on_click=handle_audio_generation, args=(msg["content"], selected_voice_id, i))
                        if f"audio_{i}" in st.session_state:
                            st.audio(st.session_state[f"audio_{i}"], format="audio/mp3")
                    with col_b:
                        st.code(msg["content"], language="markdown")

    if prompt := st.chat_input("اطلب معادلة، محاكاة، أو ارفع ملفاً..."):
        full_prompt = prompt
        if uploaded_file: full_prompt += f"\n\n[محتوى الملف]:\n{extract_file(uploaded_file)}"

        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"): 
            st.markdown(prompt)

        with st.chat_message("assistant"):
            length_inst = "أجب إجابة مفصلة." if "مفصلة" in ans_length else "أجب إجابة مختصرة."
            lang_inst = {"العربية": "أجب بالعربية.", "English": "Answer in English.", "كلاهما": "أجب بالعربية ثم الإنجليزية."}[output_lang]
            system_prompt = f"{config.PERSONAS[persona]}\n{length_inst}\n{lang_inst}\nأجب بدقة. استخدم $$ للمعادلات."
            
            answer = call_ai(full_prompt, system_prompt, model_choice)
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        title = st.session_state.messages[0]["content"][:40]
        st.session_state.session_id = supabase_utils.save_chat(email, title, st.session_state.messages, st.session_state.session_id)
        st.rerun()
