# ============================================================
# HYDROMEM Dynamics AI
# app.py — Main Unified Application
# الإصدار: v22.0
# ------------------------------------------------------------
# نقطة الدخول الوحيدة للمنصة.
# - يعتمد على plans.py حصراً للأسعار والباقات.
# - لا يحتوي أي سعر أو باقة مكتوبة يدوياً.
# - يعمل مباشرة عبر: streamlit run app.py
# ============================================================

import streamlit as st
import re
from datetime import datetime

# المصدر الوحيد للحقيقة
from plans import (
    PLANS,
    get_plan,
    get_price,
    all_plan_ids,
    plan_name,
    build_comparison_table,
    COMPARISON_HEADERS,
    SCIENTIFIC_DISCLAIMER,
)


# ============================================================
# 0) إعداد الصفحة
# ============================================================

st.set_page_config(
    page_title="HYDROMEM Dynamics AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 1) إعداد الجلسة
# ============================================================

def init_session():
    defaults = {
        "logged_in": False,
        "user": None,
        "admin_verified": False,
        "page": "🏠 الرئيسية",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# ============================================================
# 2) أدوات التحقق (بدون اتصال بقاعدة بيانات بعد)
# ============================================================

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

# ربط نوع الحساب بالباقة الافتراضية
ACCOUNT_TO_PLAN = {
    "individual": "individual",
    "researcher": "researcher",
    "laboratory": "laboratory",
    "university": "university",
    "hospital":   "hospital",
    "enterprise": "enterprise",
}


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))


def get_email_domain(email: str) -> str:
    return email.split("@")[-1].lower() if "@" in email else ""


def is_personal_email(email: str) -> bool:
    return get_email_domain(email) in PERSONAL_DOMAINS


def validate_registration(name, email, password, account_type, organization=None):
    """يرجع (ok: bool, msg: str, user_data: dict|None)"""

    if not name or len(name.strip()) < 2:
        return False, "❌ الرجاء إدخال الاسم الكامل.", None

    if not is_valid_email(email):
        return False, "❌ صيغة البريد غير صحيحة.", None

    if not password or len(password) < 8:
        return False, "❌ كلمة المرور يجب أن تكون 8 أحرف على الأقل.", None

    if account_type not in ACCOUNT_TYPES:
        return False, "❌ نوع الحساب غير معروف.", None

    plan_id = ACCOUNT_TO_PLAN[account_type]
    plan = get_plan(plan_id)

    # المؤسسات تحتاج اسم مؤسسة
    needs_org = account_type in (
        "laboratory", "university", "hospital", "enterprise"
    )
    if needs_org and (not organization or len(organization.strip()) < 3):
        return False, (
            f"❌ حساب {ACCOUNT_TYPES[account_type]} يتطلب اسم المؤسسة الرسمي."
        ), None

    # قواعد البريد
    rule = plan["email_rule"]
    if rule == "corporate" and is_personal_email(email):
        return False, (
            "🏢 باقة الشركة لا تقبل البريد الشخصي. "
            "استخدم بريد الشركة الرسمي."
        ), None

    if rule == "academic":
        domain = get_email_domain(email)
        ok = (
            domain.endswith(".edu")
            or "university" in domain
            or "college" in domain
            or "ac." in domain
        )
        if not ok:
            return False, (
                "🎓 باقة الجامعة تتطلب بريداً أكاديمياً رسمياً."
            ), None

    if rule == "organization" and is_personal_email(email):
        return False, (
            "🏥 باقة المستشفى تتطلب بريداً مؤسسياً رسمياً."
        ), None

    # بناء بيانات المستخدم
    user_data = {
        "name": name.strip(),
        "email": email.lower().strip(),
        "account_type": account_type,
        "organization": organization.strip() if organization else None,
        "plan": plan_id,
        "registered_at": datetime.utcnow().isoformat(),
    }

    return True, "✅ التسجيل سليم.", user_data


# ============================================================
# 3) صفحة تسجيل الدخول والتسجيل
# ============================================================

def render_auth_page():

    st.title("🧬 HYDROMEM Dynamics AI")
    st.caption("منصة ذكاء اصطناعي للمحاكاة والتحليل العلمي")

    st.divider()

    tab_login, tab_register = st.tabs(["🔐 دخول", "📝 تسجيل جديد"])

    # ----------------------------------------------------
    # تبويب الدخول
    # ----------------------------------------------------
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور", type="password")
            submitted = st.form_submit_button("دخول", use_container_width=True)

        if submitted:
            # ⚠️ هنا يتم الربط لاحقاً بقاعدة بيانات حقيقية.
            # الآن: يقبل أي بريد صالح ويحوله للوحة الفردي (وضع تجريبي).
            if not is_valid_email(email):
                st.error("❌ البريد غير صالح.")
            elif len(password) < 8:
                st.error("❌ كلمة المرور قصيرة.")
            else:
                st.session_state.logged_in = True
                st.session_state.user = {
                    "name": email.split("@")[0],
                    "email": email.lower(),
                    "account_type": "individual",
                    "plan": "individual",
                    "organization": None,
                }
                st.success("✅ تم الدخول (وضع تجريبي).")
                st.rerun()

        st.info(
            "ℹ️ وضع تجريبي: يتم قبول أي بريد صالح بدون قاعدة بيانات. "
            "سيتم الربط بـ Supabase لاحقاً."
        )

    # ----------------------------------------------------
    # تبويب التسجيل
    # ----------------------------------------------------
    with tab_register:
        with st.form("register_form"):
            name = st.text_input("الاسم الكامل")
            email = st.text_input("البريد الإلكتروني")
            password = st.text_input("كلمة المرور (8+)", type="password")

            account_type = st.selectbox(
                "نوع الحساب",
                options=list(ACCOUNT_TYPES.keys()),
                format_func=lambda k: ACCOUNT_TYPES[k],
            )

            organization = None
            if account_type in (
                "laboratory", "university", "hospital", "enterprise"
            ):
                organization = st.text_input("اسم المؤسسة الرسمي")

            submitted = st.form_submit_button(
                "إنشاء الحساب", use_container_width=True
            )

        if submitted:
            ok, msg, data = validate_registration(
                name, email, password, account_type, organization
            )
            if not ok:
                st.error(msg)
            else:
                st.success(msg)
                st.session_state.logged_in = True
                st.session_state.user = data
                st.rerun()


# ============================================================
# 4) الصفحة الرئيسية
# ============================================================

def render_home(user):
    plan_id = user.get("plan", "individual")
    plan = get_plan(plan_id)

    st.title("🏠 HYDROMEM Dynamics AI")
    st.caption(f"مرحباً {user['name']} — {plan['name_ar']}")

    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("👥 المستخدمون", plan["users"])
    with c2:
        st.metric("📂 المشاريع", plan["projects"])
    with c3:
        st.metric("⚙️ محاكاة/شهر", plan["simulations_monthly"])
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
        if st.button("💬 HYDROMEM Chat", use_container_width=True):
            st.info("قيد التطوير")
    with c2:
        if st.button("⚙️ محاكاة جديدة", use_container_width=True):
            st.info("قيد التطوير")
    with c3:
        if st.button("📄 تقاريري", use_container_width=True):
            st.info("قيد التطوير")

    st.divider()
    st.warning(SCIENTIFIC_DISCLAIMER)


# ============================================================
# 5) صفحة الباقات
# ============================================================

def render_pricing(user):
    current_plan = user.get("plan", "individual")

    st.title("💎 باقات HYDROMEM")
    st.caption("اختر الباقة المناسبة لمستوى استخدامك")

    st.divider()

    # اختيار دورة الفوترة
    cycle = st.radio(
        "دورة الفوترة",
        ["monthly", "yearly"],
        format_func=lambda x: "📅 شهري" if x == "monthly" else "💰 سنوي",
        horizontal=True,
    )

    st.divider()

    # عرض البطاقات
    plan_ids = all_plan_ids()

    row1 = st.columns(3)
    row2 = st.columns(3)

    def render_card(col, plan_id):
        plan = get_plan(plan_id)
        price = get_price(plan_id, cycle)

        with col:
            st.subheader(plan["name_ar"])
            st.caption(plan["audience"])

            st.metric(
                "شهري" if cycle == "monthly" else "سنوي",
                f"${price}",
            )

            for f in plan["features"][:5]:
                st.write(f)

            for r in plan["restrictions"][:3]:
                st.caption(r)

            if plan_id == current_plan:
                st.success("✅ باقتك الحالية")
            else:
                st.button(
                    f"🚀 ترقية إلى {plan['name_en']}",
                    key=f"btn_{plan_id}",
                    use_container_width=True,
                )

    render_card(row1[0], plan_ids[0])
    render_card(row1[1], plan_ids[1])
    render_card(row1[2], plan_ids[2])
    render_card(row2[0], plan_ids[3])
    render_card(row2[1], plan_ids[4])
    render_card(row2[2], plan_ids[5])

    st.divider()

    # جدول المقارنة
    st.subheader("📊 مقارنة سريعة")
    st.table([COMPARISON_HEADERS] + build_comparison_table())


# ============================================================
# 6) لوحة المستخدم (حسب الباقة)
# ============================================================

def render_dashboard(user):
    plan_id = user.get("plan", "individual")
    plan = get_plan(plan_id)

    st.title(f"📊 لوحة {plan['name_ar']}")
    st.caption(plan["audience"])

    st.divider()

    # مؤشرات الاستخدام
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("📂 المشاريع", f"0 / {plan['projects']}")
    with c2:
        st.metric(
            "⚙️ المحاكاة",
            f"0 / {plan['simulations_monthly']}",
        )
    with c3:
        st.metric("💾 التخزين", f"0 / {plan['storage_mb']} MB")

    st.divider()

    # لوحات خاصة حسب نوع الحساب
    if plan_id in ("laboratory", "university", "hospital", "enterprise"):
        st.subheader("👥 إدارة الفريق")
        st.info(
            f"لديك {plan['users']} مستخدم متاح. "
            "(إدارة الأعضاء قيد التطوير.)"
        )

    if plan["api"]:
        st.subheader("🔑 API")
        st.info("إدارة مفاتيح API قيد التطوير.")

    st.divider()
    st.warning(SCIENTIFIC_DISCLAIMER)


# ============================================================
# 7) لوحة الإدارة (مخفية)
# ============================================================

def render_admin_panel():
    """لا تُستدعى إلا بعد التحقق من Token الإدارة."""

    st.title("🔐 HYDROMEM Admin Control Center")
    st.caption("Private Owner Panel")
    st.success("✅ Administrator Mode Active")

    st.divider()

    # إحصائيات
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("المستخدمون", "0")
    with c2:
        st.metric("الاشتراكات النشطة", "0")
    with c3:
        st.metric("الإيراد الشهري", "$0")
    with c4:
        st.metric("حالة النظام", "🟢 Online")

    st.divider()

    # قائمة الباقات (من المصدر الوحيد)
    st.subheader("💎 الباقات الحالية")
    st.table([COMPARISON_HEADERS] + build_comparison_table())

    st.divider()

    # السجلات
    st.subheader("📋 System Logs")
    for log in [
        "AI Engine Started",
        "Database Connected (mock)",
        "Simulation Module Loaded",
        "Subscription Service Active",
    ]:
        st.success(log)

    st.divider()

    if st.button("🚪 خروج من وضع الإدارة"):
        st.session_state.admin_verified = False
        st.rerun()


# ============================================================
# 8) الشريط الجانبي والقائمة
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
                "🏠 الرئيسية",
                "📊 لوحتي",
                "💎 الباقات",
                "💬 HYDROMEM Chat",
                "⚙️ المحاكاة",
                "📄 التقارير",
            ],
            key="nav",
        )

        st.divider()

        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.admin_verified = False
            st.rerun()

        # --------------------------------------------
        # بوابة الإدارة (مخفية داخل الشريط الجانبي)
        # --------------------------------------------
        st.divider()
        with st.expander("🔒", expanded=False):
            token = st.text_input(
                "Admin Token",
                type="password",
                key="admin_token_input",
            )
            if st.button("دخول الإدارة", key="admin_login_btn"):
                saved = st.secrets.get("ADMIN_MASTER_KEY", "CHANGE_ME")
                if token and token == saved:
                    st.session_state.admin_verified = True
                    st.rerun()
                else:
                    st.error("❌ رفض الدخول")

    return page


# ============================================================
# 9) الراوتر الرئيسي
# ============================================================

def main():

    # ----------------------------------------------------
    # حالة 1: غير مسجل
    # ----------------------------------------------------
    if not st.session_state.logged_in:
        render_auth_page()
        return

    user = st.session_state.user

    # ----------------------------------------------------
    # حالة 2: مسؤول (Admin)
    # ----------------------------------------------------
    if st.session_state.admin_verified:
        render_admin_panel()
        return

    # ----------------------------------------------------
    # حالة 3: مستخدم عادي
    # ----------------------------------------------------
    page = render_sidebar(user)

    if page == "🏠 الرئيسية":
        render_home(user)

    elif page == "📊 لوحتي":
        render_dashboard(user)

    elif page == "💎 الباقات":
        render_pricing(user)

    elif page == "💬 HYDROMEM Chat":
        st.title("💬 HYDROMEM Chat")
        st.info("قيد التطوير.")

    elif page == "⚙️ المحاكاة":
        st.title("⚙️ المحاكاة الديناميكية")
        st.info("قيد التطوير.")

    elif page == "📄 التقارير":
        st.title("📄 التقارير")
        st.info("قيد التطوير.")


# ============================================================
# التشغيل
# ============================================================

if __name__ == "__main__":
    main()
