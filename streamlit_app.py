import streamlit as st
import auth_db
import config

st.set_page_config(page_title="HYDROMEM Dynamics AI", page_icon="🧬", layout="wide")

if "user" not in st.session_state: st.session_state.user = None
if "admin_verified" not in st.session_state: st.session_state.admin_verified = False
if "show_login" not in st.session_state: st.session_state.show_login = False

# ==========================================
# 1. صفحة الهبوط
# ==========================================
def landing_page():
    st.title("🧬 HYDROMEM Dynamics AI")
    st.subheader("مساعدك الطبي الذكي ومنصة المحاكاة المتقدمة للأنظمة الديناميكية")
    st.write("---")
    if st.button("🔐 الدخول / إنشاء حساب", use_container_width=True, type="primary"):
        st.session_state.show_login = True
        st.rerun()

# ==========================================
# 2. صفحة الدخول
# ==========================================
def login_page():
    st.title("🧬 HYDROMEM Dynamics AI")
    if st.button("⬅️ العودة للصفحة الرئيسية"):
        st.session_state.show_login = False
        st.rerun()
        
    tab1, tab2 = st.tabs(["🔐 دخول", "📝 تسجيل جديد"])
    
    with tab1:
        with st.form("login"):
            email = st.text_input("البريد الإلكتروني")
            pwd = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول", use_container_width=True):
                user = auth_db.login(email, pwd)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else: st.error("بيانات الدخول غير صحيحة")
                
    with tab2:
        with st.form("register"):
            name = st.text_input("الاسم الكامل")
            email = st.text_input("البريد الإلكتروني")
            pwd = st.text_input("كلمة المرور (8+)", type="password")
            plan = st.selectbox("الباقة", options=list(config.PLANS.keys()), format_func=lambda x: config.PLANS[x]["name"])
            if st.form_submit_button("تسجيل", use_container_width=True):
                ok, msg = auth_db.register(email, pwd, name, plan)
                if ok:
                    st.success(msg)
                    user = auth_db.login(email, pwd)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                else: 
                    st.error(msg)

# ==========================================
# 3. صفحات المستخدم
# ==========================================
def home_page(user):
    st.title("🏠 HYDROMEM Dashboard")
    st.success(f"مرحباً {user.get('name','')}")
    plan_info = config.PLANS.get(user.get("plan", "individual"), config.PLANS["individual"])
    col1, col2 = st.columns(2)
    col1.metric("نوع الحساب", plan_info["name"])
    col2.metric("حالة الاشتراك", "نشط ✅")

def payment_page(user):
    st.title("💳 ترقية الاشتراك")
    selected = st.selectbox("اختر الباقة", options=list(config.PLANS.keys()), format_func=lambda x: config.PLANS[x]["name"])
    st.info("الدفع عبر الجادلي: 2312718")
    with st.form("pay"):
        ref = st.text_input("رقم إيصال التحويل")
        if st.form_submit_button("إرسال الطلب"):
            if ref:
                auth_db.submit_payment(user['email'], selected, 100, ref)
                st.success("تم الإرسال.")

def team_page(user):
    st.title("👥 إدارة الفريق")
    max_u = config.PLANS.get(user['plan'], {}).get("max_users", 1)
    if max_u == 1:
        st.warning("باقتك لا تدعم إدارة الفريق.")
        return
    st.info("قيد التطوير.")

# ==========================================
# 4. التطبيق الرئيسي
# ==========================================
def main():
    if not st.session_state.user:
        if st.session_state.show_login: login_page()
        else: landing_page()
        return
        
    if st.session_state.admin_verified:
        st.title("لوحة الإدارة")
        return
        
    user = st.session_state.user
    plan_info = config.PLANS.get(user.get("plan", "individual"), config.PLANS["individual"])

    with st.sidebar:
        st.title("🧬 HYDROMEM")
        st.success(f"**{user['name']}**\n\nالباقة: {plan_info['name']}")
        menu = ["🏠 الرئيسية", "💬 HYDROMEM Chat", "🔬 المحاكاة", "💳 ترقية الاشتراك"]
        if plan_info["max_users"] > 1: menu.append("👥 إدارة الفريق")
            
        page = st.radio("القائمة", menu)
        st.divider()
        
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.user = None
            st.session_state.show_login = False
            st.rerun()

    if page == "🏠 الرئيسية": home_page(user)
    elif page == "💬 HYDROMEM Chat":
        import chat_page; chat_page.render()
    elif page == "🔬 المحاكاة":
        import simulation; simulation.render()
    elif page == "💳 ترقية الاشتراك": payment_page(user)
    elif page == "👥 إدارة الفريق": team_page(user)

if __name__ == "__main__":
    main()
