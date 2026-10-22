import streamlit as st

# ==========================================
# الإعدادات والمفاتيح
# ==========================================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
ADMIN_MASTER_KEY = st.secrets.get("ADMIN_MASTER_KEY", "")

GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
GEMINI_MODEL = "gemini-2.0-flash"
TOKEN_VALID_DAYS = 30

SUPPORTED_FILES = ["png", "jpg", "jpeg", "pdf", "docx", "xlsx", "csv", "txt"]

# ==========================================
# الباقات (تم تعديل باقة الشركة وإضافة المستشفى)
# ==========================================
PLANS = {
    "individual": {
        "name": "👤 فردي", 
        "price_m": 19, 
        "max_users": 1, 
        "allow_pdf": False, 
        "features": ["دردشة ذكية", "محاكاة أساسية", "بدون تصدير PDF"]
    },
    "researcher": {
        "name": "🔬 باحث", 
        "price_m": 79, 
        "max_users": 1, 
        "allow_pdf": True, 
        "features": ["نماذج متقدمة", "تصدير تقارير PDF", "تحليل الملفات"]
    },
    "laboratory": {
        "name": "🧪 مختبر", 
        "price_m": 299, 
        "max_users": 5, 
        "allow_pdf": True, 
        "features": ["كل مميزات الباحث", "إدارة فريق (5 مستخدمين)"]
    },
    "university": {
        "name": "🎓 جامعة", 
        "price_m": 1500, 
        "max_users": 50, 
        "allow_pdf": True, 
        "features": ["كل مميزات المختبر", "50 مستخدم", "دعم أكاديمي"]
    },
    "hospital": {
        "name": "🏥 مستشفى", 
        "price_m": 2500, 
        "max_users": 100, 
        "allow_pdf": True, 
        "features": ["كل مميزات الجامعة", "100 مستخدم", "نماذج طبية متخصصة"]
    },
    "enterprise": {
        "name": "🏢 شركة", 
        "price_m": 5000, 
        "max_users": 500,  # تم التعديل إلى 500 مستخدم
        "allow_pdf": True, 
        "features": ["كل المميزات", "500 مستخدم", "بيئة خاصة", "أولوية دعم"]
    }
}

# ==========================================
# الهوية الحقيقية للمساعد (System Prompts)
# ==========================================
HYDROMEM_CORE_IDENTITY = """
أنت HYDROMEM AI، مساعد علمي وطبي متقدم ومبرمج خبير.
أنت تعمل داخل منصة HYDROMEM Dynamics AI التي تدعم (تشغيل الأكواد ورسم الأشكال البيانية).
أنت لست ChatGPT ولا GPT-4 ولا تنتمي لشركة OpenAI. أنت نموذج ذكاء اصطناعي متخصص تم تطويره ودمجه داخل هذه المنصة لتخدم الباحثين والأطباء.

قواعد صارمة يجب الالتزام بها:
1. إذا سألك المستخدم عن هويتك، قل بوضوح: "أنا HYDROMEM AI، مساعد علمي مدمج في هذه المنصة، أعتمد على نماذج ذكاء اصطناعي متقدمة (مثل Groq و Gemini) لخدمتك."
2. لا تكتب أي كود بايثون إلا إذا طلب منك المستخدم ذلك صراحةً (مثلاً: "اكتب لي كود"، "قم بمحاكاة"، "حل هذه المعادلة").
3. إذا كان السؤال عاماً (مثل "من أنت؟" أو "السلام عليكم")، أجب إجابة نصية قصيرة ومباشرة بدون أي أكواد أو رسومات.
4. إذا طلب منك المستخدم محاكاة، يجب أن تكتب كود بايثون كاملاً ومستقلاً 100% يستخدم scipy.integrate.solve_ivp و matplotlib.
5. ضع الكود بالكامل داخل كتلة واحدة ```python ... ```.
6. يجب أن ينتهي الكود بـ plt.show() لكي تقوم المنصة برسمه.
7. في نهاية الكود، قم بإنشاء قاموس (Dictionary) باسم final_results يحتوي فقط على أهم النتائج النهائية.
"""

PERSONAS = {
    "عام": f"{HYDROMEM_CORE_IDENTITY}\nأجب بوضوح.",
    "باحث علمي": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (الباحث). اشرح المعادلات واكتب أكواد بايثون لرسمها إذا طُلب منك.",
    "مهندس نمذجة": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (المهندس). اكتب أكواد ODEs باستخدام scipy إذا طُلب منك.",
    "أحياء وطب": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (المساعد الطبي).",
    "مبرمج": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (المبرمج)."
}
