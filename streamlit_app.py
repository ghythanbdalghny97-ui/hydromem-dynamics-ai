import re
import streamlit as st
from datetime import datetime, timedelta
import auth_db

try:
    import extra_streamlit_components as stx
    COOKIES_AVAILABLE = True
except ImportError:
    COOKIES_AVAILABLE = False

st.set_page_config(page_title="HYDROMEM Dynamics AI", page_icon="🧬", layout="wide")

PLANS = {
    "individual": {"name_ar": "👤 فردي", "price_m": 19, "price_y": 190, "users": 1},
    "researcher": {"name_ar": "🔬 باحث", "price_m": 79, "price_y": 790, "users": 1},
    "laboratory": {"name_ar": "🧪 مختبر", "price_m": 299, "price_y": 2990, "users": 5},
    "university": {"name_ar": "🎓 جامعة", "price_m": 1500, "price_y": 15000, "users": 50},
    "hospital": {"name_ar": "🏥 مستشفى", "price_m": 2500, "price_y": 25000, "users": 100},
    "enterprise": {"name_ar": "🏢 شركة", "price_m": 5000, "price_y": 50000, "users": "∞"},
}
PLAN_ORDER = list(PLANS.keys())

ACCOUNT_TYPES = {
    "individual": "👤 فردي", "researcher": "🔬 باحث",
    "laboratory": "🧪 مختبر", "university": "🎓 جامعة",
    "hospital": "🏥 مستشفى", "enterprise": "🏢 شركة",
}

SCIENTIFIC_DISCLAIMER = "⚠️ HYDROMEM أداة محاكاة حسابية. النتائج تحتاج تحققاً تجريبياً قبل التطبيق الواقعي."

# ============================================================
# إدارة الجلسة والكوكيز (تسجيل دخول دائم)
# ============================================================
if COOKIES_AVAILABLE:
    cookie_manager = stx.CookieManager(key="hydromem_cookies")
else:
    cookie_manager = None

COOKIE_KEY = "hydromem_session"
COOKIE_EXPIRY_DAYS = 30

def save_session_to_cookie(user):
    if not COOKIES_AVAILABLE or cookie_manager is None: return
    try:
        import json
        data = json.dumps(user, ensure_ascii=False, default=str)
        cookie_manager.set(COOKIE_KEY, data, expires_at=datetime.now() + timedelta(days=COOKIE_EXPIRY_DAYS), key="set_session")
    except Exception: pass

def load_session_from_cookie():
    if not COOKIES_AVAILABLE or cookie_manager is None: return None
    try:
        import json
        raw = cookie_manager.get(COOKIE_KEY)
        if raw: return json.loads(raw)
    except Exception: pass
    return None

def delete_session_cookie():
    if not COOKIES_AVAILABLE or cookie_manager is None: return
    try: cookie_manager.delete(COOKIE_KEY, key="del_session")
    except Exception: pass

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user" not in st.session_state: st.session_state.user = None
if "admin_verified" not in st.session_state: st.session_state.admin_verified = False

# ============================================================
# استعادة الجلسة تلقائياً عند فتح التطبيق
# ============================================================
if not st.session_state.logged_in:
    saved = load_session_from_cookie()
    if saved and saved.get("email"):
        # جلب أحدث البيانات من قاعدة البيانات (لتحديث الباقة إذا تمت الموافقة عليها)
        fresh_user = auth_db.get_user_by_email(saved["email"])
        if fresh_user:
            st.session_state.logged_in = True
            st.session_state.user = fresh_user
            save_session_to_cookie(fresh_user) # تحديث الكوكيز
            st.rerun()
        else:
            delete_session_cookie()

# ============================================================
# دوال مساعدة
# ============================================================
def is_valid_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))

def render_auth():
    st.title("🧬 HYDROMEM Dynamics AI")
    st.caption("منصة ذكاء اصطناعي للمحاكاة والتحليل العلمي")
    
    tab1, tab2 = st.tabs(["🔐 دخول", "📝 تسجيل جديد"])
    
    with tab1:
        with st.form("login"):
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور", type="password")
            remember = st.checkbox("ابقني مسجلاً لمدة 30 يوماً", value=True)
            submit = st.form_submit_button("دخول", use_container_width=True)
            
        if submit:
            if not is_valid_email(email):
                st.error("بريد غير صالح")
            else:
                user = auth_db.login_user_db(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    if remember: save_session_to_cookie(user)
                    st.rerun()
                else:
                    st.error("بيانات الدخول خاطئة.")
                    
    with tab2:
        with st.form("register"):
            name = st.text_input("الاسم الكامل")
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور (8+)", type="password")
            acc_type = st.selectbox("نوع الحساب", options=list(ACCOUNT_TYPES.keys()), format_func=lambda x: ACCOUNT_TYPES[x])
            org = st.text_input("اسم المؤسسة (إذا كنت مؤسسة)")
            submit = st.form_submit_button("إنشاء الحساب", use_container_width=True)
            
        if submit:
            if not is_valid_email(email) or len(password) < 8 or len(name) < 2:
                st.error("تأكد من صحة البيانات (بريد صالح، كلمة مرور 8+، اسم صحيح).")
            else:
                success, msg = auth_db.register_user_db(email, password, name, acc_type, org)
                if success:
                    st.success(msg + " يرجى تسجيل الدخول الآن.")
                else:
                    st.error(msg)

def page_payment(user):
    st.title("💳 ترقية الاشتراك")
    st.info("الدفع الإلكتروني بالبطاقات قيد التفعيل. حالياً يمكنك الدفع عبر تحويل محلي (الجادلي) ورفع رقم الإيصال.")
    
    plan_id = st.selectbox("اختر الباقة", options=PLAN_ORDER, format_func=lambda x: PLANS[x]["name_ar"])
    plan = PLANS[plan_id]
    st.write(f"المبلغ المطلوب (شهري): **${plan['price_m']}**")
    
    st.divider()
    st.subheader("🏦 بيانات التحويل (الجادلي)")
    st.markdown("""
    - **اسم الحساب:** عبدالغني صالح محسن محمد غيثان
    - **رقم الحساب:** `2312718`
    - **رقم الهاتف:** `+967 772 757 477`
    """)
    
    st.divider()
    st.subheader("📝 تأكيد الدفع")
    with st.form("payment_form"):
        receipt_ref = st.text_input("رقم عملية التحويل (من تطبيق الجادلي)")
        submit = st.form_submit_button("لقد قمت بالتحويل", use_container_width=True)
        
    if submit:
        if not receipt_ref:
            st.error("يرجى إدخال رقم العملية.")
        else:
            success, msg = auth_db.submit_payment_request(user["email"], plan_id, plan["price_m"], receipt_ref)
            if success: st.success(msg)
            else: st.error(msg)

def render_admin():
    st.title("🔐 HYDROMEM Admin Center")
    if st.button("🚪 خروج من الإدارة"):
        st.session_state.admin_verified = False
        st.rerun()
        
    st.divider()
    st.subheader("💳 طلبات الدفع المعلقة (الجادلي)")
    pending = auth_db.get_pending_payments()
    
    if not pending:
        st.info("لا توجد طلبات دفع جديدة بانتظار المراجعة.")
    else:
        for p in pending:
            with st.expander(f"طلب: {p['user_email']} - باقة {p['plan']} - ${p['amount']}"):
                st.write(f"رقم الإيصال: **{p['receipt_ref']}**")
                st.write(f"التاريخ: {p['created_at']}")
                if st.button("✅ موافقة وتفعيل الباقة", key=p['id']):
                    if auth_db.approve_payment(p['id'], p['user_email'], p['plan']):
                        st.success("تم التفعيل بنجاح! يرجى الطلب من العميل إعادة تسجيل الدخول.")
                        st.rerun()
                    else:
                        st.error("حدث خطأ أثناء التفعيل.")

def page_home(user):
    st.title("🏠 الرئيسية")
    st.success(f"مرحباً بك {user['name']} في HYDROMEM Dynamics AI")
    plan = PLANS.get(user['plan'], {"name_ar": user['plan']})
    st.metric("باقتك الحالية", plan['name_ar'])
    st.divider()
    st.warning(SCIENTIFIC_DISCLAIMER)

def page_chat(user):
    try:
        from chat_page import chat_page
        chat_page()
    except ImportError:
        st.title("💬 HYDROMEM Chat")
        st.warning("ملف chat_page.py غير موجود.")

def page_simulation(user):
    try:
        from simulation import simulation_page
        simulation_page()
    except ImportError:
        st.title("🔬 المحاكاة")
        st.warning("ملف simulation.py غير موجود. يرجى إنشاؤه أولاً.")

def main():
    if not st.session_state.logged_in:
        render_auth()
        return

    if st.session_state.admin_verified:
        render_admin()
        return

    user = st.session_state.user

    with st.sidebar:
        st.title("🧬 HYDROMEM")
        st.caption(f"**{user['name']}**")
        plan = PLANS.get(user['plan'], {"name_ar": user['plan']})
        st.info(f"الباقة: **{plan['name_ar']}**")
        
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            delete_session_cookie()
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.admin_verified = False
            st.rerun()
            
        page = st.radio("القائمة", ["🏠 الرئيسية", "💬 HYDROMEM Chat", "🔬 المحاكاة", "💳 ترقية الاشتراك"])
        
        st.divider()
        with st.expander("🔒 الإدارة"):
            tok = st.text_input("مفتاح الإدارة", type="password")
            if st.button("دخول"):
                if tok == st.secrets.get("ADMIN_MASTER_KEY", "CHANGE_ME"):
                    st.session_state.admin_verified = True
                    st.rerun()
                else:
                    st.error("مرفوض")

    if page == "🏠 الرئيسية":
        page_home(user)
    elif page == "💬 HYDROMEM Chat":
        page_chat(user)
    elif page == "🔬 المحاكاة":
        page_simulation(user)
    elif page == "💳 ترقية الاشتراك":
        page_payment(user)

if __name__ == "__main__":
    main()
