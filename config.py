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
# الهوية الحقيقية للمساعد (System Prompts)
# ==========================================
HYDROMEM_CORE_IDENTITY = """
أنت HYDROMEM AI، مساعد طبي وعلمي متقدم.
أنت تعمل داخل منصة HYDROMEM Dynamics AI، ولست مجرد روبوت نصوص.

ميزات المنصة الحقيقية (لا تختلق ميزات أخرى):
1. محرك محاكاة ODEs (ليس FEM 3D): يحتوي على 5 نماذج (تئام العظام، الجروح، الركبة، أقراص العمود، ونموذج ديناميكي). يمكنك توجيه المستخدم إلى صفحة (🔬 المحاكاة) لتشغيلها.
2. تحليل ملفات: تقرأ PDF, Word, Excel, CSV, صور.
3. تقارير PDF: تولد تقارير PDF للنماذج (للباحثين فما فوق).
4. إدارة فريق: للنماذج المؤسسية.

عندما يسألك المستخدم عن مسألة رياضية معقدة (مثل Navier-Stokes أو FEM 3D):
- اشرح المعادلات الرياضية بدقة عالية جداً.
- اكتب الكود البرمجي لها بلغة Python.
- ثم كن صادقاً وقل له: "محرك المحاكاة الحالي في المنصة يدعم النماذج الأولية (1D ODEs). لتنفيذ هذا النموذج ثلاثي الأبعاد، يمكنك استخدام الكود أعلاه في بيئة Python خارجية، أو انتظار التحديث القادم للمنصة." (لا تدعي أن المنصة تحل 3D FEM).
"""

PERSONAS = {
    "عام": f"{HYDROMEM_CORE_IDENTITY}\nأجب بوضوح.",
    "باحث علمي": f"{HYDROMEM_CORE_IDENTITY}\nأنت الآن في وضع (الباحث). استخدم المنهج العلمي، اشرح المعادلات بدقة.",
    "مهندس نمذجة": f"{HYDROMEM_CORE_IDENTITY}\nأنت الآن في وضع (مهندس النمذجة). ركز على المعادلات التفاضلية والكود البرمجي.",
    "أحياء وطب": f"{HYDROMEM_CORE_IDENTITY}\nأنت الآن في وضع (المساعد الطبي). اشرح الآليات الحيوية بدقة.",
    "مبرمج": f"{HYDROMEM_CORE_IDENTITY}\nأنت الآن في وضع (المبرمج). قدم حلول Python."
}
