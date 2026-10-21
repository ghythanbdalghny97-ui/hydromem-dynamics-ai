import streamlit as st
import auth_db
import config

# ==========================================
# إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="HYDROMEM Medical AI", 
    page_icon="logo.png", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# تخصيص التصميم (CSS) لصفحة الهبوط
# ==========================================
def load_css():
    st.markdown("""
    <style>
    /* خلفية الصفحة */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    /* تنسيق العناوين */
    .hero-title {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #00D9FF;
        margin-bottom: 10px;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #A0AAB5;
        margin-bottom: 30px;
    }
    /* بطاقات المميزات */
    .feature-card {
        background: #1E2329;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        border: 1px solid #2D333B;
        margin-bottom: 15px;
        height: 100%;
    }
    .feature-card h3 {
        color: #00D9FF;
    }
    /* زر الدخول */
    .stButton>button {
        width: 100%;
        background-color: #00D9FF;
        color: #0E1117;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 20px;
        border: none;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background-color: #00B0CC;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# تهيئة الجلسة
# ==========================================
if "user" not in st.session_state: st.session_state.user = None
if "admin_verified" not in st.session_state: st.session_state.admin_verified = False
if "show_login" not in st.session_state: st.session_state.show_login = False

# ==========================================
# 1. صفحة الهبوط (Landing Page)
# ==========================================
def landing_page():
    load_css()
    
    # الشعار (تأكد من رفع الصورة باسم logo.png)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.warning("⚠️ يرجى رفع الشعار باسم logo.png إلى المستودع.")

    st.markdown("<h1 class='hero-title'>HYDROMEM Medical AI</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hero-subtitle'>مساعدك الطبي الذكي ومنصة المحاكاة المتقدمة للأنظمة الديناميكية المعقدة</p>", unsafe_allow_html=True)
    
    st.divider()

    # المميزات
    st.markdown("### ✨ لماذا تختار HYDROMEM؟")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <h3>🧬 محاكاة ديناميكية</h3>
            <p>حل المعادلات التفاضلية ونمذجة التئام العظام، الجروح، والأنسجة الحيوية.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <h3>🤖 ذكاء اصطناعي مدمج</h3>
            <p>تحليل الملفات الطبية (PDF/Excel)، رسم المنحنيات، واستخراج النتائج العددية.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class='feature-card'>
            <h3>🏢 إدارة مؤسسية</h3>
            <p>إدارة فرق العمل، الصلاحيات، وتقارير PDF جاهزة للنشر العلمي.</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # الباقات
    st.markdown("### 💎 باقات تناسب الجميع")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("👤 **فردي**\n\n$19 / شهر\n\nللاستخدام الشخصي والتعلم.")
    with col2:
        st.success("🔬 **باحث**\n\n$79 / شهر\n\nتصدير تقارير PDF وتحليل الملفات.")
    with col3:
        st.warning("🏢 **شركة**\n\n$5000 / شهر\n\nإدارة فريق غير محدود وبيئة خاصة.")

    st.divider()

    # أزرار الدخول
    st.markdown("<h3 style='text-align:center;'>هل أنت مستعد لبدء رحلتك العلمية؟</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐 الدخول / إنشاء حساب", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()

# ==========================================
# 2. صفحة الدخول
# ==========================================
def login_page():
    st.title("🧬 HYDROMEM Medical AI")
    
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
# 3. لوحة الإدارة (Admin)
# ==========================================
def admin_panel():
    st.title("🔐 لوحة تحكم المسؤول")
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
                    st.error("يرجى إكمال البيانات.")
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

    # جعل القائمة الجانبية تعمل بعد الدخول
    st.session_state.initial_sidebar_state = "expanded"
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
