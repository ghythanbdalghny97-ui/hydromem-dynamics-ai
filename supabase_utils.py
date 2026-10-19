"""
HYDROMEM Dynamics AI
Supabase Database Utilities

Responsible for:
- Users database
- Authentication support
- Remember token
- Chat history
- Payments
- Teams
"""

import streamlit as st
from datetime import datetime


# ============================================================
# اتصال Supabase
# ============================================================

try:
    from supabase import create_client, Client

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    supabase: Client = create_client(url, key)

except Exception as e:
    supabase = None
    st.error(f"خطأ اتصال Supabase: {e}")



# ============================================================
# المستخدمون
# ============================================================

def get_user_by_email(email):

    if not supabase:
        return None

    try:

        result = (
            supabase
            .table("users")
            .select("*")
            .eq(
                "email",
                email.lower()
            )
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception as e:
        st.error("خطأ جلب المستخدم:")
        st.exception(e)

    return None



def create_user(user):

    if not supabase:
        st.error("❌ Supabase غير متصل")
        return False

    try:

        supabase.table(
            "users"
        ).insert(
            user
        ).execute()

        return True


    except Exception as e:

        st.error("❌ خطأ أثناء إنشاء المستخدم:")
        st.exception(e)

        return False



# ============================================================
# تسجيل الدخول التلقائي
# ============================================================

def update_user_token(email, token, expiry):

    if not supabase:
        return False

    try:

        supabase.table(
            "users"
        ).update(
            {
                "remember_token": token,
                "token_expiry": expiry
            }
        ).eq(
            "email",
            email.lower()
        ).execute()

        return True


    except Exception as e:

        st.error("خطأ تحديث التوكن:")
        st.exception(e)

        return False



def get_user_by_token(token):

    if not supabase:
        return None

    try:

        result = (
            supabase
            .table("users")
            .select("*")
            .eq(
                "remember_token",
                token
            )
            .execute()
        )

        if result.data:
            return result.data[0]


    except Exception as e:

        st.error("خطأ قراءة التوكن:")
        st.exception(e)


    return None



def clear_user_token(email):

    if not supabase:
        return False

    try:

        supabase.table(
            "users"
        ).update(
            {
                "remember_token": None,
                "token_expiry": None
            }
        ).eq(
            "email",
            email.lower()
        ).execute()

        return True


    except Exception as e:

        st.error("خطأ حذف التوكن:")
        st.exception(e)

        return False
