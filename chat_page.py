import streamlit as st
import pandas as pd
from PIL import Image
from pypdf import PdfReader
import docx
import re
import io
import supabase_utils
import config
from gtts import gTTS

# ==========================================
# دوال المساعدة
# ==========================================
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

def transcribe_audio(audio_bytes):
    """تحويل الصوت إلى نص باستخدام Groq Whisper"""
    try:
        from groq import Groq
        client = Groq(api_key=config.GROQ_API_KEY)
        transcription = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model="whisper-large-v3",
            language="ar"
        )
        return transcription.text
    except Exception as e:
        return f"خطأ في تفريغ الصوت: {e}"

def call_ai(full_prompt, system_prompt, model_choice, max_tokens, temp=0.7):
    """دالة موحدة لاستدعاء الذكاء الاصطناعي"""
    try:
        if model_choice.startswith("Groq") and config.GROQ_API_KEY:
            from groq import Groq
            client = Groq(api_key=config.GROQ_API_KEY)
            res = client.chat.completions.create(
                model=config.GROQ_MODELS[0], 
                max_tokens=max_tokens,
                temperature=temp,
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
# أزرار الأتمتة السريعة (تتفوق على ChatGPT)
# ==========================================
QUICK_ACTIONS = {
    "🔍 بسّط الشرح": "أعد شرح الإجابة السابقة بأسلوب مبسط جداً لطالب جامعي، دون فقدان الدقة العلمية.",
    "🧪 حوّل لبروتوكول": "حوّل الإجابة السابقة إلى بروتوكول تجريبي عملي (خطوات مرقمة، المواد، المعايير، والاحتياطات).",
    "📚 أضف مراجع APA": "اقترح 3-5 مراجع علمية موثوقة بصيغة APA مرتبطة بهذا الموضوع.",
    "🌐 ترجم للإنجليزية": "Translate the previous response into professional academic English suitable for a peer-reviewed journal.",
    "📝 اكتب ورقة علمية": "حوّل الإجابة السابقة إلى قسم (Results) أو (Discussion) جاهز للنشر في ورقة علمية محكمة.",
    "🎯 مستويات الثقة": "أعد الإجابة مع تصنيف كل معلومة: (مؤكد علمياً / محتمل / افتراضي).",
}

# ==========================================
# الواجهة الرئيسية
# ==========================================
def render():
    st.title("💬 HYDROMEM Chat AI")
    if "messages" not in st.session_state: st.session_state.messages = []
    if "session_id" not in st.session_state: st.session_state.session_id = None
    if "last_prompt" not in st.session_state: st.session_state.last_prompt = ""
    if "last_file_ctx" not in st.session_state: st.session_state.last_file_ctx = ""

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

    # ==========================================
    # عرض الرسائل + الأزرار السريعة
    # ==========================================
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # أدوات تحت ردود المساعد
            if msg["role"] == "assistant":
                with st.expander("🛠️ أدوات متقدمة"):
                    # أزرار الأتمتة السريعة
                    st.write("**حوّل هذا الرد إلى:**")
                    cols = st.columns(3)
                    for idx, (label, instruction) in enumerate(QUICK_ACTIONS.items()):
                        with cols[idx % 3]:
                            if st.button(label, key=f"qa_{i}_{idx}"):
                                with st.spinner(f"جاري {label}..."):
                                    sys = f"{config.PERSONAS[persona]}\nأجب بالعربية بدقة."
                                    new_answer = call_ai(
                                        f"الإجابة السابقة: {msg['content']}\n\nالمطلوب: {instruction}",
                                        sys, model_choice, 2048
                                    )
                                    st.session_state.messages.append({"role": "assistant", "content": f"**[{label}]**\n\n{fix_latex(new_answer)}"})
                                    st.rerun()
                    
                    st.divider()
                    # الصوت والنسخ
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("🔊 استمع للرد", key=f"tts_{i}"):
                            with st.spinner("جاري تحويل النص إلى صوت..."):
                                try:
                                    audio_data = speak_text(msg["content"])
                                    st.audio(audio_data, format="audio/mp3")
                                except Exception as e: st.error(f"تعذر الصوت: {e}")
                    with col_b:
                        # مربع نصي لزر النسخ
                        st.code(msg["content"], language="markdown")

    # ==========================================
    # إعادة التوليد (Regenerate)
    # ==========================================
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        if st.button("🔄 إعادة توليد الرد الأخير (بطريقة مختلفة)"):
            # حذف الرد الأخير
            st.session_state.messages.pop()
            # إعادة التوليد
            with st.spinner("جاري إعادة الصياغة..."):
                length_instruction = "أجب إجابة مفصلة وشاملة." if "مفصلة" in ans_length else "أجب إجابة مختصرة."
                lang_instruction = {"العربية": "أجب بالعربية.", "English": "Answer in English.", "كلاهما": "أجب بالعربية ثم بالإنجليزية."}[output_lang]
                system_prompt = f"{config.PERSONAS[persona]}\n{length_instruction}\n{lang_instruction}\nاستخدم $$ للمعادلات. اختم بـ (الخلاصة)."
                new_answer = call_ai(st.session_state.last_prompt, system_prompt, model_choice, 4096, temp=0.9) # حرارة أعلى = إبداع أكثر
                st.session_state.messages.append({"role": "assistant", "content": fix_latex(new_answer)})
                st.rerun()

    # ==========================================
    # الإدخال (نص + صوت)
    # ==========================================
    # 🎤 الإدخال الصوتي
    audio_input = None
    try:
        audio_input = st.audio_input("🎤 أو اكتب سؤالك بصوتك (اضغط للتسجيل)")
    except: pass
    
    if audio_input:
        with st.spinner("جاري تفريغ الصوت..."):
            text_from_voice = transcribe_audio(audio_input.getvalue())
            if text_from_voice and not text_from_voice.startswith("خطأ"):
                st.success(f"📝 تم التعرف على: {text_from_voice}")
                if st.button("📤 إرسال هذا السؤال"):
                    st.session_state.messages.append({"role": "user", "content": text_from_voice})
                    st.session_state.last_prompt = text_from_voice
                    st.rerun()

    # 💬 الإدخال النصي
    if prompt := st.chat_input("اسأل HYDROMEM أو استخدم الميكروفون أعلاه..."):
        full_prompt = prompt
        if uploaded_file and not uploaded_file.type.startswith("image/"):
            file_content = extract_file(uploaded_file)
            full_prompt += f"\n\n[محتوى الملف المرفق]:\n{file_content[:4000]}"
            st.toast(f"✅ تمت قراءة: {uploaded_file.name}")

        st.session_state.last_prompt = full_prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 جاري التحليل..."):
                length_instruction = "أجب إجابة مفصلة وشاملة مع المعادلات." if "مفصلة" in ans_length else "أجب إجابة مختصرة."
                lang_instruction = {"العربية": "أجب بالعربية.", "English": "Answer in English.", "كلاهما": "أجب بالعربية ثم بالإنجليزية."}[output_lang]
                system_prompt = f"{config.PERSONAS[persona]}\n{length_instruction}\n{lang_instruction}\nأجب بدقة. استخدم $$ للمعادلات. اختم بـ (الخلاصة)."
                
                answer = call_ai(full_prompt, system_prompt, model_choice, 4096)
                formatted_answer = fix_latex(answer)
                st.markdown(formatted_answer)

        st.session_state.messages.append({"role": "assistant", "content": formatted_answer})
        title = st.session_state.messages[0]["content"][:40]
        st.session_state.session_id = supabase_utils.save_chat(email, title, st.session_state.messages, st.session_state.session_id)
        st.rerun()
