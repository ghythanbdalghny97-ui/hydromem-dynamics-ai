# ============================================================
# HYDROMEM Chat - AI Medical & Scientific Assistant
# Copyright (c) 2026 Abdulghani Saleh Mohsen Mohammed Ghaithan
# ============================================================

import streamlit as st
from datetime import datetime
import numpy as np
from scipy.integrate import odeint
from PIL import Image
import io

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
        st.error("⚠️ مكتبة google-genai غير مثبتة. يرجى إضافتها إلى requirements.txt")
        return None
    try:
        # استخدام .get() والتحقق من عدم وجود مسافات فارغة
        api_key = st.secrets.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            st.warning("⚠️ لم يتم العثور على مفتاح GEMINI_API_KEY في إعدادات Streamlit Secrets. يرجى إضافته.")
            return None
        
        # تهيئة العميل بشكل صحيح
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        st.error(f"❌ خطأ في تهيئة Gemini: {str(e)}")
        return None


def detect_question_type(prompt):
    p = prompt.lower()
    is_equation = any(k in p for k in [
        'معادلة', 'equation', 'dy/dx', 'dA/dt', 'dN/dt', 'حل', 'solve',
        'اشتقاق', 'تكامل', 'derivative', 'integral', 'نهاية', 'limit'
    ])
    is_research = any(k in p for k in [
        'بحث', 'research', 'ورقة', 'paper', 'مرجع', 'reference',
        'دراسة', 'study', 'منهجية', 'methodology', 'أطروحة'
    ])
    is_code = any(k in p for k in [
        'كود', 'code', 'python', 'برنامج', 'برمجة', 'خوارزمية', 'algorithm'
    ])
    return is_equation, is_research, is_code


def get_system_prompt():
    return """أنت مساعد علمي وطبي ذكي باسم HYDROMEM.

قدراتك:
1. حل المعادلات الرياضية (تفاضلية، تكاملية، جبرية) بالتفصيل
2. كتابة أبحاث علمية كاملة (مقدمة، منهجية، نتائج، خاتمة، مراجع)
3. توليد أكواد Python قابلة للتشغيل
4. تحليل الصور الطبية والعلمية
5. تحليل الملفات (CSV، TXT)
6. تقديم توصيات طبية إرشادية

قواعد مهمة:
- أجب دائماً بالعربية
- اذكر المصادر والمراجع
- قدم الأرقام بدقة
- عند الحديث عن الطب: أضف إخلاء مسؤولية
- عند حل المعادلات: أظهر الخطوات
"""


def call_gemini(client, prompt, image=None):
    """استدعاء Gemini API بالطريقة الصحيحة"""
    contents = [prompt, image] if image else prompt
    
    # ✅ قائمة النماذج المحدثة والصحيحة (تم إزالة gemini-pro القديم)
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro-latest'
    ]
    
    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            last_error = e
            continue
    
    raise Exception(f"فشل الاتصال بجميع النماذج: {str(last_error)}")


def handle_text_input(prompt):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.chat_history.append({'role': 'user', 'content': prompt})
    
    client = init_gemini()
    with st.chat_message("assistant"):
        if not client:
            return
        
        is_equation, is_research, is_code = detect_question_type(prompt)
        extra = ""
        if is_equation:
            extra = "\n\nقدم: 1) نوع المعادلة 2) شرح كل حد 3) الحل خطوة بخطوة 4) كود Python 5) مراجع"
        elif is_research:
            extra = "\n\nقدم: 1) عنوان 2) ملخص 3) مقدمة 4) معادلات 5) منهجية 6) نتائج 7) مراجع"
        elif is_code:
            extra = "\n\nقدم: 1) شرح 2) كود Python كامل 3) شرح الأجزاء 4) مثال 5) تحسينات"
        
        try:
            with st.spinner("🤖 جاري التحليل..."):
                full_prompt = f"{get_system_prompt()}\n\n{extra}\n\nسؤال: {prompt}"
                response_text = call_gemini(client, full_prompt)
                st.markdown(response_text)
                st.session_state.chat_history.append({
                    'role': 'assistant', 'content': response_text
                })
                st.download_button(
                    label="📥 تحميل الرد",
                    data=response_text.encode('utf-8'),
                    file_name=f"HYDROMEM_Response_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key=f"dl_{datetime.now().timestamp()}"
                )
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")


def handle_image_input(uploaded_image):
    image = Image.open(uploaded_image)
    with st.chat_message("user"):
        st.markdown(f"📷 [صورة]: {uploaded_image.name}")
        st.image(image, width=400)
    st.session_state.chat_history.append({
        'role': 'user', 'content': f"📷 صورة: {uploaded_image.name}", 'image': image
    })
    
    client = init_gemini()
    with st.chat_message("assistant"):
        if not client:
            return
        try:
            with st.spinner("🔬 جاري تحليل الصورة..."):
                response_text = call_gemini(
                    client,
                    "حلل هذه الصورة بالتفصيل بالعربية. إذا كانت طبية: حدد المنطقة وصف ما تراه. إذا كانت معادلة: اقرأها وحلها. إذا كانت رسم بياني: صف البيانات.",
                    image
                )
                st.markdown("### 🔬 تحليل الصورة")
                st.markdown(response_text)
                st.session_state.chat_history.append({
                    'role': 'assistant', 'content': response_text
                })
                st.download_button(
                    label="📥 تحميل التحليل",
                    data=response_text.encode('utf-8'),
                    file_name=f"HYDROMEM_Image_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key=f"img_dl_{datetime.now().timestamp()}"
                )
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")


def handle_file_input(uploaded_file):
    try:
        content = uploaded_file.read().decode('utf-8', errors='ignore')
    except:
        content = "غير قادر على قراءة الملف"
    
    with st.chat_message("user"):
        st.markdown(f"📎 [ملف]: {uploaded_file.name}")
        st.code(content[:1000] + "..." if len(content) > 1000 else content)
    st.session_state.chat_history.append({
        'role': 'user', 'content': f"📎 ملف: {uploaded_file.name}"
    })
    
    client = init_gemini()
    with st.chat_message("assistant"):
        if not client:
            return
        try:
            with st.spinner("📊 جاري تحليل الملف..."):
                prompt = f"""
{get_system_prompt()}

حلل هذا الملف:
اسم الملف: {uploaded_file.name}
المحتوى: {content[:5000]}

قدم: 1) ملخص 2) البيانات الرئيسية 3) التحليل الإحصائي 4) التفسير 5) التوصيات
"""
                response_text = call_gemini(client, prompt)
                st.markdown("### 📊 تحليل الملف")
                st.markdown(response_text)
                st.session_state.chat_history.append({
                    'role': 'assistant', 'content': response_text
                })
                st.download_button(
                    label="📥 تحميل التحليل",
                    data=response_text.encode('utf-8'),
                    file_name=f"HYDROMEM_File_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key=f"file_dl_{datetime.now().timestamp()}"
                )
        except Exception as e:
            st.error(f"❌ خطأ: {str(e)}")


def chat_page():
    st.header("💬 HYDROMEM Chat — المساعد العلمي الذكي")
    st.markdown("*مدعوم بـ Google Gemini AI*")
    st.markdown("---")
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    with st.sidebar:
        st.markdown("### 💬 HYDROMEM Chat")
        st.info("""
        **يمكنك:**
        - 📝 كتابة سؤال أو معادلة
        - 🖼️ رفع صورة (MRI، معادلة)
        - 📎 رفع ملف (CSV، TXT)
        
        **المساعد يجيب على:**
        - الرياضيات والفيزياء
        - الكيمياء والأحياء
        - الطب والتنبؤ
        - البرمجة والبحث
        """)
        if st.button("🗑️ محادثة جديدة", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            if msg.get('image'):
                st.image(msg['image'], width=300)
    
    tab1, tab2, tab3 = st.tabs(["💬 نص / معادلة", "🖼️ صورة", "📎 ملف"])
    
    with tab1:
        prompt = st.chat_input("اكتب سؤالك، معادلة، أو طلب بحث...")
        if prompt:
            handle_text_input(prompt)
    
    with tab2:
        uploaded_image = st.file_uploader(
            "ارفع صورة (MRI / أشعة / معادلة / رسم بياني)",
            type=['png', 'jpg', 'jpeg'], key='chat_img'
        )
        if uploaded_image:
            if st.button("🔍 تحليل الصورة", key='analyze_img'):
                handle_image_input(uploaded_image)
    
    with tab3:
        uploaded_file = st.file_uploader(
            "ارفع ملف (CSV / TXT)",
            type=['csv', 'txt'], key='chat_file'
        )
        if uploaded_file:
            if st.button("📊 تحليل الملف", key='analyze_file'):
                handle_file_input(uploaded_file)
    
    st.markdown("---")
    st.markdown("""
    **💡 أمثلة:**
    - "اشرح وحل المعادلة: dN/dt = rN(1-N/K)"
    - "اكتب بحثاً عن تأثير الحرارة على البكتيريا"
    - "اكتب كود Python لحل معادلة تفاضلية"
    """)
