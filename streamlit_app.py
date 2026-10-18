# ============================================================
# HYDROMEM Dynamics AI v15.6
# Main Application Router
# ============================================================

import streamlit as st
from datetime import datetime

from database import auth_db
from config import PLANS, ACCOUNT_TYPES


# ------------------------------------------------------------
# إعداد الصفحة
# ------------------------------------------------------------

st.set_page_config(
    page_title="HYDROMEM Dynamics AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ------------------------------------------------------------
# Session State
# ------------------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "admin_verified" not in st.session_state:
    st.session_state.admin_verified = False


# ------------------------------------------------------------
# التحقق من انتهاء الاشتراك
# ------------------------------------------------------------

def check_subscription(user):

    expiry = user.get("expiry_date")

    if not expiry:
        return True

    try:
        expiry_date = datetime.fromisoformat(expiry)

        if expiry_date < datetime.now():
            st.warning(
                "⚠️ انتهى الاشتراك. يرجى ترقية الحساب."
            )
            return False

    except Exception:
        pass

    return True


# ------------------------------------------------------------
# تسجيل الدخول
# ------------------------------------------------------------

def login_page():

    st.title("🧬 HYDROMEM Dynamics AI")

    tab_login, tab_register = st.tabs(
        ["🔐 دخول", "📝 إنشاء حساب"]
    )


    with tab_login:

        with st.form("login_form"):

            email = st.text_input(
                "البريد الإلكتروني"
            )

            password = st.text_input(
                "كلمة المرور",
                type="password"
            )

            remember = st.checkbox(
                "تذكرني"
            )


            submit = st.form_submit_button(
                "دخول",
                use_container_width=True
            )


            if submit:

                user = auth_db.login_user_db(
                    email,
                    password
                )


                if user:

                    st.session_state.logged_in = True
                    st.session_state.user = user


                    if remember:

                        token = auth_db.generate_remember_token(
                            email
                        )

                        if token:
                            st.query_params["token"] = token


                    st.rerun()


                else:

                    st.error(
                        "بيانات الدخول غير صحيحة"
                    )



    with tab_register:

        with st.form("register_form"):

            name = st.text_input(
                "الاسم"
            )

            email = st.text_input(
                "البريد الإلكتروني"
            )

            password = st.text_input(
                "كلمة المرور",
                type="password"
            )

            account_type = st.selectbox(
                "نوع الحساب",
                options=list(ACCOUNT_TYPES.keys()),
                format_func=lambda x:
                ACCOUNT_TYPES[x]
            )

            organization = st.text_input(
                "المؤسسة"
            )


            submit = st.form_submit_button(
                "إنشاء حساب",
                use_container_width=True
            )


            if submit:

                if len(password) < 8:

                    st.error(
                        "كلمة المرور يجب أن تكون 8 أحرف على الأقل"
                    )

                else:

                    ok, msg = auth_db.register_user_db(
                        email,
                        password,
                        name,
                        account_type,
                        organization
                    )


                    if ok:

                        st.success(
                            msg
                        )

                    else:

                        st.error(
                            msg
                        )


# ------------------------------------------------------------
# الصفحة الرئيسية
# ------------------------------------------------------------

def home_page(user):

    st.title("🏠 HYDROMEM Dynamics AI")

    st.success(
        f"مرحباً {user.get('name','')}"
    )


    plan = user.get(
        "plan",
        "individual"
    )


    st.metric(
        "الباقة الحالية",
        PLANS[plan]["name_ar"]
    )


    st.info(
        "منصة محاكاة حاسوبية للأنظمة المعقدة"
    )



# ------------------------------------------------------------
# القائمة الجانبية
# ------------------------------------------------------------

def sidebar(user):

    with st.sidebar:

        st.title(
            "🧬 HYDROMEM"
        )


        plan = user.get(
            "plan",
            "individual"
        )


        st.info(
            PLANS[plan]["name_ar"]
        )


        if st.button(
            "🚪 تسجيل الخروج"
        ):

            st.session_state.logged_in = False
            st.session_state.user = None

            if "token" in st.query_params:
                del st.query_params["token"]

            st.rerun()



        menu = st.radio(
            "القائمة",
            [
                "🏠 الرئيسية",
                "💬 HYDROMEM Chat",
                "🔬 المحاكاة",
                "🧬 النماذج الحيوية",
                "📁 الملفات",
                "💳 الاشتراك"
            ]
        )


        return menu



# ------------------------------------------------------------
# تشغيل الصفحات
# ------------------------------------------------------------

def router(page,user):


    if page == "🏠 الرئيسية":

        home_page(user)



    elif page == "💬 HYDROMEM Chat":

        from pages.chat_page import chat_page

        chat_page()



    elif page == "🔬 المحاكاة":

        from pages.simulation import simulation_page

        simulation_page()



    elif page == "🧬 النماذج الحيوية":

        from pages.biological_models import biological_page

        biological_page()



    elif page == "📁 الملفات":

        from pages.files import files_page

        files_page()



    elif page == "💳 الاشتراك":

        from pages.payment import payment_page

        payment_page()



# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():


    if not st.session_state.logged_in:

        login_page()

        return



    user = st.session_state.user


    if not check_subscription(user):

        return



    page = sidebar(user)


    router(
        page,
        user
    )



if __name__ == "__main__":

    main()
