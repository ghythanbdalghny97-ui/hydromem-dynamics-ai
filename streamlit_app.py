import re
import streamlit as st
from datetime import datetime, timedelta
import auth_db

st.set_page_config(page_title="HYDROMEM Dynamics AI", page_icon="🧬", layout="wide")

PLANS = {
    "individual": {"name_ar": "👤 فردي", "price_m": 19, "users": 1},
    "researcher": {"name_ar": "🔬 باحث", "price_m": 79, "users": 1},
    "laboratory": {"name_ar": "🧪 مختبر", "price_m": 299, "users": 5},
    "university": {"name_ar": "🎓 جامعة", "price_m": 1500, "users": 50},
    "hospital": {"name_ar": "🏥 مستشفى", "price_m": 2500, "users": 100},
    "enterprise": {"name_ar": "🏢 شركة", "price_m": 5000, "users": 9999},
}

ACCOUNT_TYPES = {"individual": "👤 فردي", "researcher": "🔬 باحث", "laboratory": "🧪 مختبر", "university": "🎓 جامعة", "hospital": "🏥 مستشفى", "enterprise": "🏢 شركة"}

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user" not in st.session_state: st.session_state.user = None
if "admin_verified" not in st.session_state: st.session_state.admin_verified = False

# ============================================================
# نظام الدخول التلقائي (عبر المفتاح السري في الرابط)
# ============================================================
if not st.session_state.logged_in:
    token = st.query_params.get("token")
    if token:
        fresh_user = auth_db.login_with_token(token)
        if fresh_user:
            st.session_state.logged_in = True
            st.session_state.user = fresh_user
            st.rerun()

# ============================================================
# صفحة الدخول والتسجيل
# ============================================================
def render_auth():
    st.title("🧬 HYDROMEM Dynamics AI")
    tab1, tab2 = st.tabs(["🔐 دخول", "📝 تسجيل جديد"])
    
    with tab1:
        with st.form("login"):
            email = st.text_input("البريد")
            pwd = st.text_input("كلمة المرور", type="password")
            remember = st.checkbox("تذكرني دائماً (دخول تلقائي)", value=True)
            if st.form_submit_button("دخول", use_container_width=True):
                user = auth_db.login_user_db(email, pwd)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    
                    # إذا اختار "تذكرني"، ننشئ مفتاحاً سرياً ونضعه في الرابط
                    if remember:
                        token = auth_db.generate_remember_token(user["email"])
                        if token:
                            st.query_params["token"] = token
                    
                    st.rerun()
                else: st.error("بيانات خاطئة")
                    
    with tab2:
        with st.form("register"):
            name = st.text_input("الاسم")
            email = st.text_input("البريد")
            pwd = st.text_input("كلمة المرور (8+)", type="password")
            acc_type = st.selectbox("نوع الحساب", options=list(ACCOUNT_TYPES.keys()), format_func=lambda x: ACCOUNT_TYPES[x])
            org = st.text_input("المؤسسة (اختياري)")
            if st.form_submit_button("إنشاء حساب", use_container_width=True):
                if len(pwd) < 8: st.error("كلمة المرور قصيرة")
                else:
                    success, msg = auth_db.register_user_db(email, pwd, name, acc_type, org)
                    if success: st.success(msg + " يرجى الدخول.")
                    else: st.error(msg)

# ============================================================
# باقي الصفحات (الفريق، الدفع، الإدارة، الرئيسية)
# ============================================================
def page_team(user):
    st.title("👥 إدارة الفريق")
    max_u = PLANS.get(user['plan'], {}).get("users", 1)
    if max_u == 1:
        st.warning("باقتك لا تدعم إدارة الفريق.")
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

def render_admin():
    st.title("🔐 لوحة الإدارة")
    if st.button("🚪 خروج من الإدارة"):
        st.session_state.admin_verified = False
        fresh = auth_db.get_user_by_email(st.session_state.user["email"])
        if fresh: st.session_state.user = fresh
        st.rerun()
    pending = auth_db.get_pending_payments()
    if not pending: st.info("لا توجد طلبات جديدة.")
    for p in pending:
        with st.expander(f"{p.get('user_email')} - {p.get('plan')} - ${p.get('amount')}"):
            st.write(f"إيصال: {p.get('receipt_ref')}")
            if st.button("✅ موافقة", key=p['id']):
                if auth_db.approve_payment(p['id'], p.get('user_email'), p.get('plan')):
                    st.success("تم التفعيل!"); st.rerun()

def page_home(user):
    st.title("🏠 الرئيسية")
    st.success(f"أهلاً {user['name']}")
    st.metric("الباقة", PLANS.get(user['plan'], {}).get("name_ar", user['plan']))
    expiry = user.get("expiry_date")
    if expiry: st.info(f"الاشتراك ساري حتى: {expiry[:10]}")

# ============================================================
# الراوتر الرئيسي
# ============================================================
def main():
    if not st.session_state.logged_in:
        render_auth()
        return

    if st.session_state.admin_verified:
        render_admin()
        return

    user = st.session_state.user
    plan_info = PLANS.get(user['plan'], {"name_ar": user['plan'], "users": 1})

    with st.sidebar:
        st.title("🧬 HYDROMEM")
        st.info(f"الباقة: {plan_info['name_ar']}")
        
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.user = None
            if "token" in st.query_params: del st.query_params["token"]
            st.rerun()
            
        menu = ["🏠 الرئيسية", "💬 HYDROMEM Chat", "🔬 المحاكاة", "💳 ترقية الاشتراك"]
        if plan_info.get("users", 1) > 1: menu.insert(3, "👥 إدارة الفريق")
            
        page = st.radio("القائمة", menu)
        
        st.divider()
        with st.expander("🔒 الإدارة"):
            tok = st.text_input("المفتاح", type="password")
            if st.button("دخول"):
                if tok == st.secrets.get("ADMIN_MASTER_KEY", "CHANGE_ME"):
                    st.session_state.admin_verified = True
                    st.rerun()

    if page == "🏠 الرئيسية": page_home(user)
    elif page == "💬 HYDROMEM Chat":
        from chat_page import chat_page
        chat_page()
    elif page == "🔬 المحاكاة":
        from simulation import simulation_page
        simulation_page()
    elif page == "👥 إدارة الفريق": page_team(user)
    elif page == "💳 ترقية الاشتراك": page_payment(user)

if __name__ == "__main__":
    main()
