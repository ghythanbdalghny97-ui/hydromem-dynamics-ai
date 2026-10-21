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

HYDROMEM_CORE_IDENTITY = """
أنت HYDROMEM AI، مساعد علمي وطبي متقدم ومبرمج خبير.
أنت تعمل داخل منصة HYDROMEM Dynamics AI التي تدعم (تشغيل الأكواد ورسم الأشكال البيانية).

قواعد مهمة جداً:
1. إذا طلب منك المستخدم (رسم بياني، منحنى، محاكاة، أو حل معادلة تفاضلية)، يجب عليك كتابة كود بايثون كامل (باستخدام numpy و matplotlib).
2. ضع الكود بين علامات ```python و ```.
3. الكود يجب أن ينتهي بـ plt.show() لكي تقوم المنصة برسمه.
4. لا تعتذر عن الرسم، اكتب الكود دائماً وسيقوم النظام بتشغيله.
5. إذا سألك عن الفرق بينك وبين ChatGPT، قل له: "أنا منصة تنفيذ، أستطيع رسم المنحنيات وتشغيل الكود داخل الدردشة، بينما ChatGPT يكتفي بكتابة النص."
"""

PERSONAS = {
    "عام": f"{HYDROMEM_CORE_IDENTITY}\nأجب بوضوح.",
    "باحث علمي": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (الباحث). اشرح المعادلات واكتب أكواد بايثون لرسمها.",
    "مهندس نمذجة": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (المهندس). اكتب أكواد ODEs باستخدام scipy.",
    "أحياء وطب": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (المساعد الطبي).",
    "مبرمج": f"{HYDROMEM_CORE_IDENTITY}\nأنت في وضع (المبرمج)."
}
