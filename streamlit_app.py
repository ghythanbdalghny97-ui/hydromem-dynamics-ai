"""
HYDROMEM Dynamics AI
Main Application

Version: v16.0
"""

import streamlit as st

import auth_db
import config



# ============================================================
# إعداد الصفحة
# ============================================================

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🧬",
    layout="wide"
)



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


    token = st.query_params.get(
        "token"
    )


    if token:

        user = auth_db.login_with_token(
            token
        )


        if user:

            st.session_state.logged_in = True

            st.session_state.user = user

            st.rerun()



# ============================================================
# صفحة الدخول
# ============================================================

def login_page():


    st.title(
        "🧬 HYDROMEM Dynamics AI"
    )


    st.write(
        config.APP_DESCRIPTION
    )


    tab1, tab2 = st.tabs(
        [
            "🔐 دخول",
            "📝 تسجيل جديد"
        ]
    )


    with tab1:


        with st.form(
            "login_form"
        ):


            email = st.text_input(
                "البريد الإلكتروني"
            )


            password = st.text_input(
                "كلمة المرور",
                type="password"
            )


            remember = st.checkbox(
                "تذكرني (دخول تلقائي)",
                value=True
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


                    st.session_state.logged_in=True

                    st.session_state.user=user



                    if remember:


                        token = (
                            auth_db
                            .generate_remember_token(
                                email
                            )
                        )


                        if token:

                            st.query_params[
                                "token"
                            ] = token



                    st.rerun()


                else:

                    st.error(
                        "بيانات الدخول غير صحيحة"
                    )



    with tab2:


        with st.form(
            "register_form"
        ):


            name = st.text_input(
                "الاسم"
            )


            email = st.text_input(
                "البريد"
            )


            password = st.text_input(
                "كلمة المرور",
                type="password"
            )


            account = st.selectbox(
                "نوع الحساب",
                [
                    "individual",
                    "researcher",
                    "laboratory",
                    "university",
                    "hospital",
                    "enterprise"
                ]
            )


            submit = st.form_submit_button(
                "إنشاء حساب",
                use_container_width=True
            )


            if submit:


                if len(password)<8:

                    st.error(
                        "كلمة المرور يجب أن تكون 8 أحرف على الأقل"
                    )


                else:

                    ok,msg = (
                        auth_db
                        .register_user_db(
                            email,
                            password,
                            name,
                            account,
                            ""
                        )
                    )


                    if ok:

                        st.success(
                            msg
                        )

                    else:

                        st.error(
                            msg
                        )



# ============================================================
# الصفحة الرئيسية
# ============================================================

def home_page(user):


    st.title(
        "🏠 HYDROMEM Dashboard"
    )


    st.success(
        f"مرحباً {user.get('name','')}"
    )


    col1,col2,col3 = st.columns(3)


    with col1:

        st.metric(
            "الحساب",
            user.get(
                "account_type",
                "-"
            )
        )


    with col2:

        st.metric(
            "الخطة",
            user.get(
                "plan",
                "Free"
            )
        )


    with col3:

        st.metric(
            "الإصدار",
            config.APP_VERSION
        )



    st.info(
        """
        استخدم القائمة الجانبية للوصول إلى:
        
        💬 HYDROMEM Chat
        
        🔬 المحاكاة الديناميكية
        
        💳 الاشتراكات
        
        """
    )



# ============================================================
# التطبيق الرئيسي
# ============================================================

def main():


    auto_login()


    if not st.session_state.logged_in:

        login_page()

        return



    user = st.session_state.user



    with st.sidebar:


        st.title(
            "🧬 HYDROMEM"
        )


        st.write(
            user.get(
                "email"
            )
        )


        page = st.radio(

            "القائمة",

            [

                "🏠 الرئيسية",

                "💬 HYDROMEM Chat",

                "🔬 المحاكاة"

            ]

        )



        st.divider()


        if st.button(
            "🚪 تسجيل الخروج"
        ):


            st.session_state.logged_in=False

            st.session_state.user=None


            if "token" in st.query_params:

                del st.query_params["token"]


            st.rerun()



    if page=="🏠 الرئيسية":

        home_page(user)



    elif page=="💬 HYDROMEM Chat":

        from chat_page import chat_page

        chat_page()



    elif page=="🔬 المحاكاة":

        from simulation import simulation_page

        simulation_page()




if __name__=="__main__":

    main()
