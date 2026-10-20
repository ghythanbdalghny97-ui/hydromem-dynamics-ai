"""
HYDROMEM Dynamics AI
Main Application
Version: v22.0 (Final)
"""

import streamlit as st
import auth_db

# ============================================================
# إعداد الصفحة
# ============================================================
st.set_page_config(
    page_title="HYDROMEM Dynamics AI",
    page_icon="🧬",
    layout="wide"
)

# ============================================================
# إعدادات الباقات
# ============================================================
PLANS = {
    "individual": {"name_ar": "👤 فردي", "price_m": 19, "users": 1},
    "researcher": {"name_ar": "🔬 باحث", "price_m": 79, "users": 1},
    "laboratory": {"name_ar": "🧪 مختبر", "price_m": 299, "users": 5},
    "university": {"name_ar": "🎓 جامعة", "price_m": 1500, "users": 50},
    "hospital": {"name_ar": "🏥 مستشفى", "price_m": 2500, "users": 100},
    "enterprise": {"name_ar": "🏢 شركة", "price_m": 5000, "users": 9999},
}

# ============================================================
# Session State
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "admin_verified" not in st.session_state:
    st.session_state.admin_verified = False

# ============================================================
# تسجيل الدخول التلقائي
# ============================================================
def auto_login():
    if st.session_state.logged_in:
        return
    token = st.query_params.get("token")
    if token:
        user = auth_db.login_with_token(token)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()

# ============================================================
# صفحة الدخول والتسجيل
# ============================================================
def login_page():
    st.title("🧬 HYDROMEM Dynamics AI")
    st.write("منصة محاكاة ونمذجة للأنظمة الديناميكية المعقدة.")
    
    tab1, tab2 = st.tabs(["🔐 دخول", "📝 تسجيل جديد"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور", type="password")
            remember = st.checkbox("تذكرني (دخول تلقائي)", value=True)
            submit = st.form_submit_button("دخول", use_container_width=True)

            if submit:
                user = auth_db.login_user_db(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    if remember:
                        token = auth_db.generate_remember_token(email)
                        if token:
                            st.query_params["token"] = token
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة")

    with tab2:
        with st.form("register_form"):
            name = st.text_input("الاسم")
            email = st.text_input("البريد")
            password = st.text_input("كلمة المرور", type="password")
            account = st.selectbox("نوع الحساب", list(PLANS.keys()), format_func=lambda x: PLANS[x]["name_ar"])
            submit = st.form_submit_button("إنشاء حساب", use_container_width=True)

            if submit:
                if len(password) < 8:
                    st.error("كلمة المرور يجب أن تكون 8 أحرف على الأقل")
                else:
                    ok, msg = auth_db.register_user_db(email, password, name, account, "")
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# ============================================================
# الصفحات
# ============================================================
def home_page(user):
    st.title("🏠 HYDROMEM Dashboard")
    st.success(f"مرحباً {user.get('name','')}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("الحساب", user.get("account_type", "-"))
    with col2:
        st.metric("الخطة", PLANS.get(user.get("plan", "individual"), {"name_ar": "فردي"})["name_ar"])
    with col3:
        st.metric("الإصدار", "v22.0")

def page_payment(user):
    st.title("💳 ترقية الاشتراك")
    plan_id = st.selectbox("اختر الباقة", options=list(PLANS.keys()), format_func=lambda x: PLANS[x]["name_ar"])
    st.write(f"المطلوب: **${PLANS[plan_id]['price_m']}**")
    st.info("حول المبلغ إلى: الجادلي (2312718) - عبدالغني غيثان")
    
    with st.form("pay"):
        ref = st.text_input("رقم إيصال التحويل")
        if st.form_submit_button("أرسل الطلب"):
            if ref:
                succ, msg = auth_db.submit_payment_request(user['email'], plan_id, PLANS[plan_id]['price_m'], ref)
                if succ: st.success(msg)
                else: st.error(msg)

def page_team(user):
    st.title("👥 إدارة الفريق")
    max_u = PLANS.get(user['plan'], {}).get("users", 1)
    if max_u == 1:
        st.warning("باقتك لا تدعم إدارة الفريق. يرجى الترقية.")
        return
    team_id = user.get("team_id") or user["id"]
    members = auth_db.get_team_members(team_id)
    if not members: members = [{"name": user['name'], "email": user['email'], "role": "owner"}]
    
    st.subheader(f"الأعضاء ({len(members)}/{max_u})")
    st.table(members)
    
    if len(members) < max_u:
        with st.form("add_member"):
            st.subheader("➕ إضافة عضو")
            name = st.text_input("الاسم")
            email = st.text_input("البريد")
            pwd = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("إضافة"):
                succ, msg = auth_db.add_team_member(user['email'], name, email, pwd, "researcher", max_u)
                if succ: st.success(msg); st.rerun()
                else: st.error(msg)

# ============================================================
# لوحة الإدارة (Admin Panel)
# ============================================================
def render_admin():
    st.title("🔐 لوحة تحكم المسؤول")
    st.caption("هذه الصفحة مخصصة لمالك المنصة فقط.")
    
    if st.button("🚪 خروج من الإدارة"):
        st.session_state.admin_verified = False
        st.rerun()
        
    st.divider()
    st.subheader("💳 طلبات الدفع المعلقة")
    pending = auth_db.get_pending_payments()
    
    if not pending:
        st.info("لا توجد طلبات دفع جديدة.")
    else:
        for p in pending:
            with st.expander(f"طلب: {p.get('user_email')} - باقة {p.get('plan')} - ${p.get('amount')}"):
                st.write(f"رقم الإيصال: **{p.get('receipt_ref')}**")
                if st.button("✅ موافقة وتفعيل الباقة", key=p['id']):
                    if auth_db.approve_payment(p['id'], p.get('user_email'), p.get('plan')):
                        st.success("تم التفعيل بنجاح!")
                        st.rerun()
                    else:
                        st.error("حدث خطأ.")

# ============================================================
# التطبيق الرئيسي
# ============================================================
def main():
    auto_login()

    if not st.session_state.logged_in:
        login_page()
        return

    # إذا كان المدير قد تحقق، نعرض لوحة الإدارة ونوقف باقي الكود
    if st.session_state.admin_verified:
        render_admin()
        return

    user = st.session_state.user

    with st.sidebar:
        st.title("🧬 HYDROMEM")
        st.write(user.get("email"))
        
        # القائمة الرئيسية
        page = st.radio("القائمة", [
            "🏠 الرئيسية",
            "💬 HYDROMEM Chat",
            "🔬 المحاكاة",
            "💳 ترقية الاشتراك",
            "👥 إدارة الفريق"
        ])

        st.divider()
        
        # زر تسجيل الخروج
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.user = None
            if "token" in st.query_params:
                del st.query_params["token"]
            st.rerun()

        st.divider()
        
        # 🌟 سر لوحة الإدارة: موجود هنا في القائمة الجانبية
        with st.expander("🔒 الإدارة"):
            tok = st.text_input("مفتاح الدخول", type="password")
            if st.button("دخول كمدير"):
                if tok == st.secrets.get("ADMIN_MASTER_KEY", "CHANGE_ME"):
                    st.session_state.admin_verified = True
                    st.rerun()
                else:
                    st.error("مفتاح غير صحيح")

    # توجيه الصفحات
    if page == "🏠 الرئيسية":
        home_page(user)
    elif page == "💬 HYDROMEM Chat":
        from chat_page import chat_page
        chat_page()
    elif page == "🔬 المحاكاة":
        from simulation import simulation_page
        simulation_page()
    elif page == "💳 ترقية الاشتراك":
        page_payment(user)
    elif page == "👥 إدارة الفريق":
        page_team(user)

if __name__ == "__main__":
    main()
