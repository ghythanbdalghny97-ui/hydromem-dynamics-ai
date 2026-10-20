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

PERSONAS = {
    "عام": "أنت مساعد ذكاء اصطناعي شامل. أجب بوضوح.",
    "باحث علمي": "أنت مساعد بحثي أكاديمي. استخدم المنهج العلمي واشرح المعادلات بدقة.",
    "مهندس نمذجة": "أنت متخصص في النمذجة الرياضية والتحليل العددي والاستقرار.",
    "أحياء وطب": "أنت مساعد بحثي في الأنظمة الحيوية. اشرح الآليات بدقة.",
    "مبرمج": "أنت مهندس برمجيات. قدم حلول Python عملية."
}

# ============================================================
# نظام الباقات (الأسعار والمميزات)
# ============================================================
PLANS = {
    "individual": {
        "name": "👤 فردي", "price_m": 19, "max_users": 1, "allow_pdf": False,
        "features": ["دردشة ذكية", "محاكاة أساسية", "بدون تصدير PDF", "مستخدم واحد"]
    },
    "researcher": {
        "name": "🔬 باحث", "price_m": 79, "max_users": 1, "allow_pdf": True,
        "features": ["نماذج متقدمة", "تصدير تقارير PDF", "تحليل الملفات", "مستخدم واحد"]
    },
    "laboratory": {
        "name": "🧪 مختبر", "price_m": 299, "max_users": 5, "allow_pdf": True,
        "features": ["كل مميزات الباحث", "إدارة فريق (5 مستخدمين)", "مشاريع مشتركة"]
    },
    "university": {
        "name": "🎓 جامعة", "price_m": 1500, "max_users": 50, "allow_pdf": True,
        "features": ["كل مميزات المختبر", "50 مستخدم", "دعم مؤسسي", "لوحة طلاب"]
    },
    "enterprise": {
        "name": "🏢 شركة", "price_m": 5000, "max_users": 9999, "allow_pdf": True,
        "features": ["كل المميزات", "مستخدمين غير محدودين", "بيئة خاصة", "أولوية دعم"]
    }
}
