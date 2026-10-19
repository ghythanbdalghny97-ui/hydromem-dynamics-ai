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
    st.error("❌ خطأ اتصال Supabase")
    st.exception(e)



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
            .eq("email", email.lower())
            .execute()
        )

        if result.data:
            return result.data[0]

    except Exception as e:
        st.error("❌ خطأ جلب المستخدم")
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

        st.error("❌ خطأ أثناء إنشاء المستخدم في قاعدة البيانات")
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

        st.error("❌ خطأ تحديث رمز الدخول")
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

        st.error("❌ خطأ قراءة رمز الدخول")
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

        st.error("❌ خطأ حذف رمز الدخول")
        st.exception(e)

        return False



# ============================================================
# المحادثات
# ============================================================

def save_chat_session(email, title, messages, session_id=None):

    if not supabase:
        return None

    try:

        data = {
            "user_email": email,
            "title": title,
            "messages": messages,
            "updated_at": datetime.utcnow().isoformat()
        }


        if session_id:

            supabase.table(
                "chat_sessions"
            ).update(
                data
            ).eq(
                "id",
                session_id
            ).execute()

            return session_id


        result = (
            supabase.table(
                "chat_sessions"
            )
            .insert(data)
            .execute()
        )


        if result.data:
            return result.data[0]["id"]


    except Exception as e:

        st.error("❌ خطأ حفظ المحادثة")
        st.exception(e)


    return None



def get_chat_sessions(email, limit=10):

    if not supabase:
        return []

    try:

        result = (
            supabase.table(
                "chat_sessions"
            )
            .select("*")
            .eq(
                "user_email",
                email
            )
            .order(
                "updated_at",
                desc=True
            )
            .limit(limit)
            .execute()
        )

        return result.data or []


    except Exception as e:

        st.error("❌ خطأ جلب المحادثات")
        st.exception(e)

    return []



def get_chat_session_by_id(session_id):

    if not supabase:
        return None

    try:

        result = (
            supabase.table(
                "chat_sessions"
            )
            .select("*")
            .eq(
                "id",
                session_id
            )
            .execute()
        )

        if result.data:
            return result.data[0]


    except Exception as e:

        st.error("❌ خطأ فتح المحادثة")
        st.exception(e)


    return None



def delete_chat_session(session_id):

    if not supabase:
        return False

    try:

        supabase.table(
            "chat_sessions"
        ).delete().eq(
            "id",
            session_id
        ).execute()

        return True


    except Exception as e:

        st.error("❌ خطأ حذف المحادثة")
        st.exception(e)

    return False



# ============================================================
# الفرق
# ============================================================

def get_team_members(team_id):

    if not supabase:
        return []

    try:

        result = (
            supabase.table("users")
            .select("*")
            .eq(
                "team_id",
                team_id
            )
            .execute()
        )

        return result.data or []


    except Exception as e:

        st.error("❌ خطأ جلب الفريق")
        st.exception(e)

    return []



def get_team_by_owner(email):

    user = get_user_by_email(email)

    if not user:
        return []

    return get_team_members(
        user.get("team_id") or user.get("id")
    )



# ============================================================
# الدفع والاشتراكات
# ============================================================

def create_payment_request(data):

    if not supabase:
        return False

    try:

        supabase.table(
            "payments"
        ).insert(
            data
        ).execute()

        return True


    except Exception as e:

        st.error("❌ خطأ إنشاء طلب الدفع")
        st.exception(e)

    return False



def get_pending_payments():

    if not supabase:
        return []

    try:

        result = (
            supabase.table(
                "payments"
            )
            .select("*")
            .eq(
                "status",
                "pending"
            )
            .execute()
        )

        return result.data or []


    except Exception as e:

        st.error("❌ خطأ جلب المدفوعات")
        st.exception(e)

    return []



def approve_payment(payment_id, email, plan):

    if not supabase:
        return False

    try:

        supabase.table(
            "payments"
        ).update(
            {
                "status": "approved"
            }
        ).eq(
            "id",
            payment_id
        ).execute()


        supabase.table(
            "users"
        ).update(
            {
                "plan": plan
            }
        ).eq(
            "email",
            email
        ).execute()


        return True


    except Exception as e:

        st.error("❌ خطأ تفعيل الاشتراك")
        st.exception(e)

    return False
