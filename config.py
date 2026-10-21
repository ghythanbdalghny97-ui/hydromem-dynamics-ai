import streamlit as st

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
ADMIN_MASTER_KEY = st.secrets.get("ADMIN_MASTER_KEY", "")

GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
GEMINI_MODEL = "gemini-2.0-flash"
TOKEN_VALID_DAYS = 30

SUPPORTED_FILES = ["png", "jpg", "jpeg", "pdf", "docx", "xlsx", "csv", "txt"]

PLANS = {
    "individual": {"name": "👤 فردي", "price_m": 19, "max_users": 1, "allow_pdf": False, "features": ["دردشة ذكية", "محاكاة أساسية", "بدون تصدير PDF"]},
    "researcher": {"name": "🔬 باحث", "price_m": 79, "max_users": 1, "allow_pdf": True, "features": ["نماذج متقدمة", "تصدير تقارير PDF", "تحليل الملفات"]},
    "laboratory": {"name": "🧪 مختبر", "price_m": 299, "max_users": 5, "allow_pdf": True, "features": ["كل مميزات الباحث", "إدارة فريق (5 مستخدمين)"]},
    "university": {"name": "🎓 جامعة", "price_m": 1500, "max_users": 50, "allow_pdf": True, "features": ["كل مميزات المختبر", "50 مستخدم"]},
    "enterprise": {"name": "🏢 شركة", "price_m": 5000, "max_users": 9999, "allow_pdf": True, "features": ["كل المميزات", "مستخدمين غير محدودين"]}
}

# ==========================================
# 🧠 العقل المدبر: تعليمات صارمة لكتابة الكود
# ==========================================
HYDROMEM_CORE_IDENTITY = """
أنت HYDROMEM AI، مساعد علمي وطبي متقدم ومبرمج خبير.
أنت تعمل داخل منصة HYDROMEM Dynamics AI التي تدعم (تشغيل الأكواد ورسم الأشكال البيانية).

قواعد صارمة لكتابة الأكواد:
1. إذا طلب منك المستخدم (رسم بياني، حل معادلة، محاكاة)، يجب أن تكتب كود بايثون كاملاً ومستقلاً 100%.
2. لا تفترض أبداً أن هناك كوداً سابقاً تم تشغيله. اكتب دائماً: استدعاء المكتبات (import)، تعريف المعاملات، المعادلات، والرسم.
3. ضع الكود بالكامل داخل كتلة واحدة ```python ... ```.
4. يجب أن ينتهي الكود بـ plt.show() لكي تقوم المنصة برسمه.
5. في نهاية الكود، قم بإنشاء قاموس (Dictionary) باسم final_results يحتوي فقط على أهم النتائج النهائية التي يحتاجها الباحث. 
   مثال: final_results = {"Final Osteoblasts": O[-1], "Final Osteoclasts": C[-1]}
"""

PERSONAS = {
    "عام": f"{HYDROMEM_CORE_IDENTITY}\nأجب بوضوح.",
    "باحث علمي": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (الباحث). اشرح المعادلات واكتب أكواد بايثون لرسمها.",
    "مهندس نمذجة": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (المهندس). اكتب أكواد ODEs باستخدام scipy.",
    "أحياء وطب": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (المساعد الطبي).",
    "مبرمج": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (المبرمج)."
}
