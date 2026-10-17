# ============================================================
# HYDROMEM Dynamics AI
# streamlit_app.py — Main Application v22.1
# Persistent Login via Cookies
# ============================================================

import re
import uuid
from datetime import datetime, timedelta

import streamlit as st

# Cookie Manager (يُثبت من requirements.txt)
try:
    import extra_streamlit_components as stx
    COOKIES_AVAILABLE = True
except ImportError:
    COOKIES_AVAILABLE = False


# ============================================================
# إعداد الصفحة
# ============================================================

st.set_page_config(
    page_title="HYDROMEM Dynamics AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# الباقات
# ============================================================

PLANS = {
    "individual": {
        "name_ar": "👤 فردي",
        "audience": "للاستخدام الشخصي والتعلم",
        "price_monthly": 19, "price_yearly": 190,
        "users": 1, "projects": 5, "simulations": 50,
        "api": False, "team": False, "commercial": False,
        "email_rule": "any",
        "features": [
            "🤖 HYDROMEM Chat", "⚙️ نماذج أساسية",
            "📊 50 محاكاة شهرياً", "📂 5 مشاريع",
        ],
    },
    "researcher": {
        "name_ar": "🔬 باحث",
        "audience": "للباحثين المستقلين",
        "price_monthly": 79, "price_yearly": 790,
        "users": 1, "projects": 50, "simulations": 2000,
        "api": "limited", "team": False, "commercial": "research_only",
        "email_rule": "any",
        "features": [
            "✅ كل مميزات الفرد", "🧬 نماذج بحثية متقدمة",
            "📈 تحليل الاستقرار", "📄 تقارير PDF علمية",
        ],
    },
    "laboratory": {
        "name_ar": "🧪 مختبر",
        "audience": "للمختبرات البحثية",
        "price_monthly": 299, "price_yearly": 2990,
        "users": 5, "projects": 200, "simulations": 10000,
        "api": "limited", "team": True, "commercial": "contract",
        "email_rule": "any",
        "features": [
            "✅ كل مميزات الباحث", "👥 5 مستخدمين",
            "📂 مساحة مشاريع مشتركة", "📋 سجل التجارب",
        ],
    },
    "university": {
        "name_ar": "🎓 جامعة",
        "audience": "للمؤسسات الأكاديمية",
        "price_monthly": 1500, "price_yearly": 15000,
        "users": 50, "projects": 1000, "simulations": 100000,
        "api": True, "team": True, "commercial": "academic_only",
        "email_rule": "academic",
        "features": [
            "✅ كل مميزات المختبر", "👥 50 مستخدم",
            "🎓 إدارة الباحثين والطلاب", "🔑 API أكاديمي",
        ],
    },
    "hospital": {
        "name_ar": "🏥 مستشفى",
        "audience": "للمؤسسات الطبية",
        "price_monthly": 2500, "price_yearly": 25000,
        "users": 100, "projects": 1000, "simulations": 100000,
        "api": True, "team": True, "commercial": "medical_research",
        "email_rule": "organization",
        "features": [
            "✅ كل مميزات الجامعة", "👥 100 مستخدم",
            "🩺 نماذج طبية متخصصة", "🏥 إدارة الأقسام",
        ],
    },
    "enterprise": {
        "name_ar": "🏢 شركة",
        "audience": "للشركات",
        "price_monthly": 5000, "price_yearly": 50000,
        "users": "∞", "projects": "∞", "simulations": "∞",
        "api": "full", "team": True, "commercial": True,
        "email_rule": "corporate",
        "features": [
            "✅ كل مميزات المستشفى", "👥 مستخدمون غير محدودين",
            "🔑 API كامل", "🏢 بيئة خاصة",
        ],
    },
}

PLAN_ORDER = list(PLANS.keys())

SCIENTIFIC_DISCLAIMER = (
    "⚠️ HYDROMEM أداة محاكاة حسابية. "
    "النتائج تحتاج تحققاً تجريبياً قبل التطبيق الواقعي. "
    "لا تُستخدم للتشخيص الطبي."
)


# ============================================================
# Cookies Manager
# ============================================================

if COOKIES_AVAILABLE:
    cookie_manager = stx.CookieManager(key="hydromem_cookies")
else:
    cookie_manager = None


COOKIE_KEY = "hydromem_session"
COOKIE_EXPIRY_DAYS = 30


def save_session_to_cookie(user):
    """يحفظ الجلسة في المتصفح لمدة 30 يوماً."""
    if not COOKIES_AVAILABLE or cookie_manager is None:
        return
    try:
        import json
        data = json.dumps(user, ensure_ascii=False)
        cookie_manager.set(
            COOKIE_KEY,
            data,
            expires_at=datetime.now() + timedelta(days=COOKIE_EXPIRY_DAYS),
            key="set_session",
        )
    except Exception:
        pass


def load_session_from_cookie():
    """يقرأ الجلسة من المتصفح إذا وجدت."""
    if not COOKIES_AVAILABLE or cookie_manager is None:
        return None
    try:
        import json
        raw = cookie_manager.get(COOKIE_KEY)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


def delete_session_cookie():
    """يحذف الجلسة من المتصفح."""
    if not COOKIES_AVAILABLE or cookie_manager is None:
        return
    try:
        cookie_manager.delete(COOKIE_KEY, key="del_session")
    except Exception:
        pass


# ============================================================
# دوال مساعدة
# ============================================================

def get_plan(plan_id):
    return PLANS.get(plan_id)


PERSONAL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com",
    "outlook.com", "icloud.com", "protonmail.com",
    "live.com", "aol.com",
}

ACCOUNT_TYPES = {
    "individual": "👤 فردي",
    "researcher": "🔬 باحث",
    "laboratory": "🧪 مختبر",
    "university": "🎓 جامعة",
    "hospital":   "🏥 مستشفى",
    "enterprise": "🏢 شركة",
}


def is_valid_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))


def get_domain(email):
    return email.split("@")[-1].lower() if "@" in email else ""


def is_personal(email):
    return get_domain(email) in PERSONAL_DOMAINS


def validate_registration(name, email, password, account_type, org=None):
    if not name or len(name.strip()) < 2:
        return False, "❌ الرجاء إدخال الاسم الكامل."
    if not is_valid_email(email):
        return False, "❌ صيغة البريد غير صحيحة."
    if not password or len(password) < 8:
        return False, "❌ كلمة المرور يجب أن تكون 8 أحرف على الأقل."
    if account_type not in ACCOUNT_TYPES:
        return False, "❌ نوع الحساب غير معروف."

    plan = get_plan(account_type)
    needs_org = account_type in (
        "laboratory", "university", "hospital", "enterprise"
    )
    if needs_org and (not org or len(org.strip()) < 3):
        return False, f"❌ حساب {ACCOUNT_TYPES[account_type]} يتطلب اسم المؤسسة."

    rule = plan["email_rule"]
    if rule == "corporate" and is_personal(email):
        return False, "🏢 باقة الشركة لا تقبل البريد الشخصي."
    if rule == "academic":
        d = get_domain(email)
        if not (d.endswith(".edu") or "university" in d
                or "college" in d or "ac." in d):
            return False, "🎓 باقة الجامعة تتطلب بريداً أكاديمياً."
    if rule == "organization" and is_personal(email):
        return False, "🏥 باقة المستشفى تتطلب بريداً مؤسسياً."

    return True, "✅ التسجيل سليم."


# ============================================================
# تهيئة الجلسة (مع Cookies)
# ============================================================

def init_session():
    defaults = {
        "logged_in": False,
        "user": None,
        "admin_verified": False,
        "cookies_checked": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# محاولة استعادة الجلسة من المتصفح مرة واحدة فقط
if not st.session_state.logged_in and not st.session_state.cookies_checked:
    st.session_state.cookies_checked = True
    saved = load_session_from_cookie()
    if saved:
        st.session_state.logged_in = True
        st.session_state.user = saved
        st.rerun()


# ============================================================
# صفحة الدخول والتسجيل
# ============================================================

def render_auth():
    st.title("🧬 HYDROMEM Dynamics AI")
    st.caption("منصة ذكاء اصطناعي للمحاكاة والتحليل العلمي")
    st.divider()

    tab_login, tab_register = st.tabs(["🔐 دخول", "📝 تسجيل جديد"])

    with tab_login:
        with st.form("login"):
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور", type="password")
            remember = st.checkbox(
                "ابقني مسجلاً لمدة 30 يوماً", value=True
            )
            ok = st.form_submit_button("دخول", use_container_width=True)

        if ok:
            if not is_valid_email(email):
                st.error("❌ البريد غير صالح.")
            elif len(password) < 8:
                st.error("❌ كلمة المرور قصيرة.")
            else:
                user_data = {
                    "name": email.split("@")[0],
                    "email": email.lower(),
                    "account_type": "individual",
                    "plan": "individual",
                    "organization": None,
                }
                st.session_state.logged_in = True
                st.session_state.user = user_data

                if remember:
                    save_session_to_cookie(user_data)

                st.success("✅ تم الدخول")
                st.rerun()

        st.info(
            "ℹ️ وضع تجريبي: أي بريد صالح يعمل حالياً. "
            "سيتم ربط Supabase Auth لاحقاً."
        )

    with tab_register:
        with st.form("register"):
            name = st.text_input("الاسم الكامل")
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور (8+)", type="password")
            account_type = st.selectbox(
                "نوع الحساب",
                options=list(ACCOUNT_TYPES.keys()),
                format_func=lambda k: ACCOUNT_TYPES[k],
            )
            org = None
            if account_type in ("laboratory", "university",
                                "hospital", "enterprise"):
                org = st.text_input("اسم المؤسسة الرسمي")

            ok = st.form_submit_button(
                "إنشاء الحساب", use_container_width=True
            )

        if ok:
            valid, msg = validate_registration(
                name, email, password, account_type, org
            )
            if not valid:
                st.error(msg)
            else:
                user_data = {
                    "name": name.strip(),
                    "email": email.lower(),
                    "account_type": account_type,
                    "plan": account_type,
                    "organization": org.strip() if org else None,
                    "registered_at": datetime.utcnow().isoformat(),
                }
                st.session_state.logged_in = True
                st.session_state.user = user_data
                save_session_to_cookie(user_data)
                st.success(msg)
                st.rerun()


# ============================================================
# الشريط الجانبي
# ============================================================

def render_sidebar(user):
    plan_id = user.get("plan", "individual")
    plan = get_plan(plan_id)

    with st.sidebar:
        st.title("🧬 HYDROMEM")
        st.caption(f"**{user['name']}**")
        st.info(f"الباقة: **{plan['name_ar']}**")
        st.divider()

        page = st.radio(
            "القائمة",
            [
                "🏠 الرئيسية", "📊 لوحتي",
                "💎 الباقات", "💬 HYDROMEM Chat",
                "📄 التقارير",
            ],
            key="nav",
        )

        st.divider()

        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            delete_session_cookie()
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.admin_verified = False
            st.session_state.cookies_checked = False
            st.rerun()

        st.divider()

        with st.expander("🔒", expanded=False):
            token = st.text_input(
                "Admin Token", type="password", key="admin_token"
            )
            if st.button("دخول الإدارة", key="admin_btn"):
                saved = st.secrets.get("ADMIN_MASTER_KEY", "CHANGE_ME")
                if token and token == saved:
                    st.session_state.admin_verified = True
                    st.rerun()
                else:
                    st.error("❌ مرفوض")

    return page


# ============================================================
# الصفحات
# ============================================================

def page_home(user):
    plan = get_plan(user.get("plan", "individual"))
    st.title("🏠 HYDROMEM Dynamics AI")
    st.caption(f"مرحباً {user['name']} — {plan['name_ar']}")
    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("👥 المستخدمون", plan["users"])
    with c2:
        st.metric("📂 المشاريع", plan["projects"])
    with c3:
        st.metric("⚙️ محاكاة/شهر", plan["simulations"])
    with c4:
        api_label = (
            "✅ كامل" if plan["api"] == "full"
            else "⚠️ محدود" if plan["api"] == "limited"
            else "❌"
        )
        st.metric("🔑 API", api_label)

    st.divider()
    st.subheader("🚀 ابدأ الآن")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("💬 HYDROMEM Chat", use_container_width=True)
    with c2:
        st.button("⚙️ محاكاة جديدة", use_container_width=True)
    with c3:
        st.button("📄 تقاريري", use_container_width=True)

    st.divider()
    st.warning(SCIENTIFIC_DISCLAIMER)


def page_dashboard(user):
    plan = get_plan(user.get("plan", "individual"))
    st.title(f"📊 لوحة {plan['name_ar']}")
    st.caption(plan["audience"])
    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("📂 المشاريع", f"0 / {plan['projects']}")
    with c2:
        st.metric("⚙️ المحاكاة", f"0 / {plan['simulations']}")
    with c3:
        st.metric("💾 التخزين", "0 MB")

    st.divider()
    if plan["team"]:
        st.subheader("👥 إدارة الفريق")
        st.info(f"لديك {plan['users']} مستخدم متاح.")
    if plan["api"]:
        st.subheader("🔑 API")
        st.info("إدارة مفاتيح API قيد التطوير.")

    st.warning(SCIENTIFIC_DISCLAIMER)


def page_pricing(user):
    current = user.get("plan", "individual")
    st.title("💎 باقات HYDROMEM")
    st.caption("اختر الباقة المناسبة")
    st.divider()

    cycle = st.radio(
        "دورة الفوترة",
        ["monthly", "yearly"],
        format_func=lambda x: "📅 شهري" if x == "monthly" else "💰 سنوي",
        horizontal=True,
    )
    st.divider()

    def card(col, pid):
        plan = get_plan(pid)
        price = (
            plan["price_monthly"] if cycle == "monthly"
            else plan["price_yearly"]
        )
        with col:
            st.subheader(plan["name_ar"])
            st.caption(plan["audience"])
            st.metric("السعر", f"${price}")
            for f in plan["features"][:4]:
                st.write(f)
            if pid == current:
                st.success("✅ باقتك الحالية")
            else:
                st.button(
                    "🚀 ترقية",
                    key=f"btn_{pid}",
                    use_container_width=True,
                )

    r1 = st.columns(3)
    r2 = st.columns(3)
    card(r1[0], PLAN_ORDER[0])
    card(r1[1], PLAN_ORDER[1])
    card(r1[2], PLAN_ORDER[2])
    card(r2[0], PLAN_ORDER[3])
    card(r2[1], PLAN_ORDER[4])
    card(r2[2], PLAN_ORDER[5])


def page_chat(user):
    try:
        from chat_page import chat_page
        chat_page()
    except ImportError:
        st.title("💬 HYDROMEM Chat")
        st.info("📌 ملف `chat_page.py` غير موجود أو لا يعمل.")


def page_reports(user):
    st.title("📄 التقارير")
    st.info("قيد التطوير.")


# ============================================================
# لوحة الإدارة
# ============================================================

def render_admin():
    st.title("🔐 HYDROMEM Admin Control Center")
    st.caption("Private Owner Panel")
    st.success("✅ Administrator Mode Active")
    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("المستخدمون", "0")
    with c2:
        st.metric("الاشتراكات", "0")
    with c3:
        st.metric("الإيراد الشهري", "$0")
    with c4:
        st.metric("الحالة", "🟢 Online")

    st.divider()
    st.subheader("💎 الباقات الحالية")
    rows = [["الباقة", "شهري", "سنوي", "المستخدمون"]]
    for pid in PLAN_ORDER:
        p = get_plan(pid)
        rows.append([
            p["name_ar"],
            f"${p['price_monthly']}",
            f"${p['price_yearly']}",
            p["users"],
        ])
    st.table(rows)

    st.divider()
    st.subheader("📋 System Logs")
    for log in [
        "AI Engine Started",
        "Database Connected (mock)",
        "Simulation Module Loaded",
        "Subscription Service Active",
    ]:
        st.success(log)

    st.divider()
    if st.button("🚪 خروج من الإدارة"):
        st.session_state.admin_verified = False
        st.rerun()


# ============================================================
# الراوتر
# ============================================================

def main():
    if not st.session_state.logged_in:
        render_auth()
        return

    if st.session_state.admin_verified:
        render_admin()
        return

    user = st.session_state.user
    page = render_sidebar(user)

    if page == "🏠 الرئيسية":
        page_home(user)
    elif page == "📊 لوحتي":
        page_dashboard(user)
    elif page == "💎 الباقات":
        page_pricing(user)
    elif page == "💬 HYDROMEM Chat":
        page_chat(user)
    elif page == "📄 التقارير":
        page_reports(user)


if __name__ == "__main__":
    main()
