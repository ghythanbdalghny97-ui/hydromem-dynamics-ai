import io
import re
import pandas as pd
import streamlit as st
from PIL import Image
from pypdf import PdfReader
import docx
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

# ==========================================
# 1. الإعدادات والثوابت
# ==========================================
PERSONAS = {
    "عام": "أنت مساعد ذكي شامل ومفيد.",
    "باحث علمي": "أنت مساعد بحثي أكاديمي. أجب بأسلوب علمي دقيق، واستخدم المعادلات الرياضية عند الحاجة.",
    "طبيب": "أنت مساعد طبي بحثي. اشرح الآليات الحيوية بدقة، وأضف تحذيراً طبياً في النهاية.",
    "مبرمج": "أنت مهندس برمجيات خبير. أجب بالأكواد الجاهزة (Python) واشرحها باختصار.",
    "محلل بيانات": "أنت خبير في تحليل البيانات. ركز على الإحصاء والنتائج الرقمية المستخرجة من الملفات."
}

# ==========================================
# 2. دوال المساعدة
# ==========================================
def fix_latex(text):
    """إصلاح أخطاء المعادلات الرياضية لمنع النصوص الحمراء"""
    text = text.replace(r"\$$4pt]", r"\\[4pt]").replace(r"\$$6pt]", r"\\[6pt]")
    text = text.replace(r"\[", "$$").replace(r"\]", "$$")
    text = text.replace(r"\end{cases}", "").replace(r"\begin{cases}", "")
    text = text.replace(r"\bigr]", "").replace(r"\bigl[", "")
    greek_letters = [r"\Theta", r"\eta", r"\beta", r"\gamma", r"\mu", r"\tau", r"\alpha", r"\lambda"]
    for letter in greek_letters:
        text = re.sub(r'(?<!\$)' + re.escape(letter) + r'(?!\$)', f'${letter}$', text)
    return text

def extract_text_from_file(uploaded_file):
    """استخراج النص من الملفات (PDF, Word, Excel, CSV, TXT)"""
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
                
        elif uploaded_file.type in ["text/plain", "text/csv"]:
            text = uploaded_file.getvalue().decode("utf-8")
            
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
                
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            text = df.to_string()
            
    except Exception as e:
        text = f"[خطأ في قراءة محتوى الملف: {e}]"
        
    return text

# ==========================================
# 3. الواجهة الرئيسية
# ==========================================
def chat_page():
    st.title("💬 HYDROMEM Chat AI")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None

    # --- الشريط الجانبي ---
    with st.sidebar:
        st.markdown("### ⚙️ إعدادات المحرك")
        model_choice = st.selectbox("النموذج:", ["Groq (سريع - نصوص)", "Gemini (يدعم الصور والملفات)"])
        persona = st.selectbox("شخصية المساعد:", list(PERSONAS.keys()))
        
        st.divider()
        st.markdown("### 📚 سجل المحادثات")
        if st.button("➕ محادثة جديدة", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_session_id = None
            st.rerun()
            
        user_email = st.session_state.user.get("email", "guest")
        sessions = supabase_utils.get_chat_sessions(user_email, limit=10)
        for s in sessions:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"📄 {s['title'][:20]}...", key=f"btn_{s['id']}", use_container_width=True):
                    data = supabase_utils.get_chat_session_by_id(s['id'])
                    if data:
                        st.session_state.messages = data['messages']
                        st.session_state.current_session_id = data['id']
                        st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{s['id']}"):
                    supabase_utils.delete_chat_session(s['id'])
                    st.rerun()
                    
        st.divider()
        st.markdown("### 📎 إرفاق ملفات")
        uploaded_file = st.file_uploader(
            "ارفع (PDF, Word, Excel, CSV, صور)", 
            type=["png", "jpg", "jpeg", "pdf", "csv", "xlsx", "txt", "docx"]
        )
        if uploaded_file:
            st.success(f"تم التجهيز: {uploaded_file.name}")

    # --- عرض الرسائل السابقة ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- الإدخال والرد ---
    if prompt := st.chat_input("اسأل HYDROMEM..."):
        
        # 1. تجهيز النص مع محتوى الملف
        full_prompt = prompt
        if uploaded_file:
            if not uploaded_file.type.startswith("image/"):
                extracted_text = extract_text_from_file(uploaded_file)
                # اقتطاع النص لتجنب تجاوز حدود الذكاء الاصطناعي
                full_prompt += f"\n\n[محتوى الملف المرفق ({uploaded_file.name})]:\n{extracted_text[:4000]}"
            elif model_choice.startswith("Groq"):
                st.warning("⚠️ Groq لا يدعم الصور. سيتم تحويلك تلقائياً إلى Gemini.")
                model_choice = "Gemini (يدعم الصور والملفات)"

        # 2. عرض رسالة المستخدم
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            if uploaded_file:
                st.caption(f"📎 مرفق: {uploaded_file.name}")

        # 3. توليد الرد
        with st.chat_message("assistant"):
            with st.status("🧠 جاري التفكير والتحليل...", expanded=False) as status:
                try:
                    response_text = ""
                    system_prompt = f"{PERSONAS[persona]}\n\nقواعد مهمة:\n- أجب باللغة العربية.\n- استخدم $$...$$ للمعادلات المستقلة و $...$ للمتغيرات.\n- لا تستخدم \\[ أو \\].\n- اختم إجابتك دائماً بـ (الخلاصة)."
                    
                    # المحرك الأول: Groq
                    if model_choice.startswith("Groq") and GROQ_AVAILABLE:
                        groq_key = st.secrets.get("GROQ_API_KEY", "")
                        if groq_key:
                            client = Groq(api_key=groq_key)
                            for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
                                try:
                                    res = client.chat.completions.create(
                                        model=model, max_tokens=4096,
                                        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": full_prompt}]
                                    )
                                    response_text = res.choices[0].message.content
                                    break
                                except Exception:
                                    continue
                    
                    # المحرك الثاني: Gemini (أو كبديل)
                    if not response_text and GEMINI_AVAILABLE:
                        gemini_key = st.secrets.get("GEMINI_API_KEY", "")
                        if gemini_key:
                            g_client = genai.Client(api_key=gemini_key)
                            contents = [full_prompt]
                            if uploaded_file and uploaded_file.type.startswith("image/"):
                                contents.append(Image.open(uploaded_file))
                            
                            g_res = g_client.models.generate_content(model="gemini-2.0-flash", contents=contents)
                            response_text = g_res.text

                    if not response_text:
                        response_text = "عذراً، لم أتمكن من الاتصال بمزودي الذكاء الاصطناعي. تأكد من مفاتيح API."

                    status.update(label="✅ اكتمل التحليل", state="complete", expanded=False)

                    # 4. تنسيق وعرض الرد
                    formatted_response = fix_latex(response_text)
                    st.markdown(formatted_response)
                    
                    # 5. الحفظ في قاعدة البيانات
                    st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                    
                    title = st.session_state.messages[0]["content"][:30] + "..."
                    sid = supabase_utils.save_chat_session(
                        user_email, title, st.session_state.messages, st.session_state.current_session_id
                    )
                    if sid: st.session_state.current_session_id = sid

                except Exception as e:
                    st.error(f"حدث خطأ غير متوقع: {e}")
