import streamlit as st
import auth_db
import config

st.set_page_config(page_title="HYDROMEM Dynamics AI", page_icon="🧬", layout="wide")

if "user" not in st.session_state: st.session_state.user = None
if "admin_verified" not in st.session_state: st.session_state.admin_verified = False
if "show_login" not in st.session_state: st.session_state.show_login = False

# الدخول التلقائي (عبر التوكن)
if not st.session_state.user:
    token = st.query_params.get("token")
    if token:
        from supabase_utils import get_user_by_token
        user = get_user_by_token(token)
        if user:
            st.session_state.user = user
            st.session_state.show_login = True
            st.rerun()

# ==========================================
# 1. صفحة الهبوط (Landing Page)
# ==========================================
def landing_page():
    st.title("🧬 HYDROMEM Dynamics AI")
    st.subheader("مساعدك الطبي الذكي ومنصة المحاكاة المتقدمة للأنظمة الديناميكية")
    st.write("---")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("### لماذا HYDROMEM؟")
        st.markdown("""
        * **بيئة عمل متكاملة:** لا نكتفي بكتابة الكود، بل **ننفذه** ونرسم المنحنيات ونستخرج الأرقام.
        * **نماذج طبية:** محاكاة التئام العظام، الجروح، والركبة.
        * **تحليل الملفات:** ارفع PDF أو Excel ودع الذكاء الاصطناعي يحلله.
        * **تقارير PDF:** احصل على تقارير جاهزة للنشر في الأبحاث العلمية.
        * **دعم مؤسسي:** إدارة الفريق والصلاحيات للجامعات والمختبرات.
        """)
    with col2:
        st.info("💡 **جرّب مجاناً:** يمكنك التسجيل الآن والحصول على تجربة محدودة (الباقة الفردية).")

    st.write("---")
    st.subheader("💎 باقات الاشتراك")
    
    cols = st.columns(3)
    plans_to_show = ["individual", "researcher", "laboratory"]
    for i, pid in enumerate(plans_to_show):
        p = config.PLANS[pid]
        with cols[i]:
            st.markdown(f"### {p['name']}")
            st.write(f"**${p['price_m']} / شهر**")
            for f in p['features'][:3]:
                st.write(f"✅ {f}")
            if st.button(f"اشترك في {p['name']}", key=f"btn_{pid}", use_container_width=True):
                st.session_state.show_login = True
                st.rerun()

    st.write("---")
    if st.button("🔐 الدخول / إنشاء حساب", use_container_width=True, type="primary"):
        st.session_state.show_login = True
        st.rerun()

# ==========================================
# 2. صفحة الدخول والتسجيل
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
            remember = st.checkbox("تذكرني (دخول تلقائي)", value=True)
            if st.form_submit_button("دخول", use_container_width=True):
                user = auth_db.login(email, pwd)
                if user:
                    st.session_state.user = user
                    if remember:
                        token = auth_db.generate_token(email)
                        if token: st.query_params["token"] = token
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
# 3. لوحة الإدارة
# ==========================================
def admin_panel():
    st.title("🔐 لوحة تحكم المسؤول")
    st.caption("خاصة بمالك المنصة فقط.")
    if st.button("🚪 خروج من الإدارة"):
        st.session_state.admin_verified = False
        st.rerun()
    st.divider()
    st.subheader("💳 طلبات الدفع المعلقة")
    from supabase_utils import get_pending_payments
    pending = get_pending_payments()
    
    if not pending: st.info("لا توجد طلبات جديدة.")
    for p in pending:
        with st.expander(f"{p['user_email']} - {p['plan']} - ${p['amount']}"):
            st.write(f"إيصال: {p.get('receipt_ref')}")
            if st.button("✅ موافقة وتفعيل", key=p['id']):
                if auth_db.approve_payment(p['id'], p['user_email'], p['plan']):
                    st.success("تم تفعيل الباقة!")
                    st.rerun()

# ==========================================
# 4. صفحات المستخدم
# ==========================================
def home_page(user):
    st.title("🏠 HYDROMEM Dashboard")
    st.success(f"مرحباً {user.get('name','')}")
    plan_info = config.PLANS.get(user.get("plan", "individual"), config.PLANS["individual"])
    
    col1, col2 = st.columns(2)
    col1.metric("نوع الحساب", plan_info["name"])
    col2.metric("حالة الاشتراك", "نشط ✅" if user.get("expiry_date") else "نشط")
    
    st.divider()
    st.subheader("✨ مميزات باقتك:")
    for f in plan_info["features"]: st.write(f"✅ {f}")

def payment_page(user):
    st.title("💳 ترقية الاشتراك")
    selected = st.selectbox("اختر الباقة", options=list(config.PLANS.keys()), format_func=lambda x: config.PLANS[x]["name"])
    plan = config.PLANS[selected]
    
    st.subheader("مميزات هذه الباقة:")
    for f in plan["features"]: st.write(f"✔️ {f}")
    
    st.write(f"المطلوب: **${plan['price_m']}**")
    st.info("حول المبلغ إلى: الجادلي (2312718) - عبدالغني غيثان")
    
    with st.form("pay"):
        ref = st.text_input("رقم إيصال التحويل")
        if st.form_submit_button("إرسال الطلب"):
            if ref:
                succ, msg = auth_db.submit_payment(user['email'], selected, plan['price_m'], ref)
                if succ: st.success(msg)
                else: st.error(msg)

def team_page(user):
    st.title("👥 إدارة الفريق")
    max_u = config.PLANS.get(user['plan'], {}).get("max_users", 1)
    if max_u == 1:
        st.warning("باقتك لا تدعم إدارة الفريق. يرجى الترقية.")
        return
    
    team_id = user.get("team_id") or user["id"]
    from supabase_utils import get_team
    members = get_team(team_id)
    
    if not any(m['email'] == user['email'] for m in members):
        members.insert(0, {"name": user['name'], "email": user['email'], "role": "owner"})
        
    st.subheader(f"الأعضاء الحاليون ({len(members)} / {max_u})")
    st.table(members)
    
    st.divider()
    st.subheader("➕ إضافة عضو جديد")
    
    if len(members) >= max_u:
        st.error("لقد وصلت للحد الأقصى لباقتك.")
    else:
        with st.form("add_member"):
            m_name = st.text_input("اسم العضو")
            m_email = st.text_input("البريد الإلكتروني")
            m_pwd = st.text_input("كلمة المرور (8+)", type="password")
            m_role = st.selectbox("الصلاحية", ["researcher", "viewer", "admin"])
            
            if st.form_submit_button("إضافة العضو"):
                if not m_name or not m_email or len(m_pwd) < 8:
                    st.error("يرجى إكمال البيانات (كلمة مرور 8 أحرف على الأقل).")
                else:
                    ok, msg = auth_db.add_team_member(user['email'], m_name, m_email, m_pwd, m_role)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

# ==========================================
# 5. التطبيق الرئيسي والراوتر
# ==========================================
def main():
    if not st.session_state.user:
        if st.session_state.show_login:
            login_page()
        else:
            landing_page()
        return
        
    if st.session_state.admin_verified:
        admin_panel()
        return
        
    user = st.session_state.user
    plan_info = config.PLANS.get(user.get("plan", "individual"), config.PLANS["individual"])

    with st.sidebar:
        st.title("🧬 HYDROMEM")
        st.success(f"**{user['name']}**\n\nالباقة: {plan_info['name']}")
        
        menu = ["🏠 الرئيسية", "💬 HYDROMEM Chat", "🔬 المحاكاة", "💳 ترقية الاشتراك"]
        if plan_info["max_users"] > 1:
            menu.append("👥 إدارة الفريق")
            
        page = st.radio("القائمة", menu)
        st.divider()
        
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.user = None
            st.session_state.show_login = False
            if "token" in st.query_params: del st.query_params["token"]
            st.rerun()
            
        st.divider()
        with st.expander("🔒 الإدارة"):
            if st.text_input("المفتاح", type="password") == config.ADMIN_MASTER_KEY:
                st.session_state.admin_verified = True
                st.rerun()

    if page == "🏠 الرئيسية": home_page(user)
    elif page == "💬 HYDROMEM Chat":
        import chat_page
        chat_page.render()
    elif page == "🔬 المحاكاة":
        import simulation
        simulation.render()
    elif page == "💳 ترقية الاشتراك": payment_page(user)
    elif page == "👥 إدارة الفريق": team_page(user)

if __name__ == "__main__":
    main()
