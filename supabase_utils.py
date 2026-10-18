"""
HYDROMEM Dynamics AI
Supabase Database Utilities

Database operations:
- Users
- Chat history
- Payments
- Subscriptions
"""

from datetime import datetime

from supabase import create_client, Client

import config


# ============================================================
# إنشاء اتصال Supabase
# ============================================================

_supabase = None


def get_client():

    global _supabase

    if _supabase is None:

        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            return None

        _supabase = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_KEY
        )

    return _supabase



# ============================================================
# USERS
# ============================================================


def create_user(user):

    client = get_client()

    if not client:
        return False


    try:

        result = (
            client
            .table("users")
            .insert(user)
            .execute()
        )

        return bool(result.data)

    except Exception as e:

        print("Create user error:", e)

        return False



def get_user_by_email(email):

    client = get_client()

    if not client:
        return None


    try:

        result = (
            client
            .table("users")
            .select("*")
            .eq(
                "email",
                email.lower()
            )
            .single()
            .execute()
        )

        return result.data


    except Exception:

        return None



def update_user_token(
        email,
        token,
        expiry
):

    client = get_client()

    if not client:
        return False


    try:

        result = (
            client
            .table("users")
            .update(
                {
                    "remember_token": token,
                    "token_expiry": expiry
                }
            )
            .eq(
                "email",
                email
            )
            .execute()
        )


        return bool(result.data)


    except Exception:

        return False



def get_user_by_token(token):

    client = get_client()

    if not client:
        return None


    try:

        result = (
            client
            .table("users")
            .select("*")
            .eq(
                "remember_token",
                token
            )
            .single()
            .execute()
        )

        return result.data


    except Exception:

        return None



def clear_user_token(email):

    client = get_client()

    if not client:
        return False


    try:

        (
            client
            .table("users")
            .update(
                {
                    "remember_token": None,
                    "token_expiry": None
                }
            )
            .eq(
                "email",
                email
            )
            .execute()
        )

        return True


    except Exception:

        return False



# ============================================================
# CHAT HISTORY
# ============================================================


def save_chat_session(
        email,
        title,
        messages,
        session_id=None
):

    client = get_client()

    if not client:
        return None


    try:

        data = {

            "user_email": email,

            "title": title,

            "messages": messages,

            "updated_at":
                datetime.utcnow().isoformat()

        }


        if session_id:

            result = (
                client
                .table("chat_sessions")
                .update(data)
                .eq(
                    "id",
                    session_id
                )
                .execute()
            )

            return session_id


        else:

            result = (
                client
                .table("chat_sessions")
                .insert(data)
                .execute()
            )


            if result.data:

                return result.data[0]["id"]


    except Exception as e:

        print("Save chat error:", e)


    return None



def get_chat_sessions(
        email,
        limit=10
):

    client = get_client()

    if not client:
        return []


    try:

        result = (

            client
            .table("chat_sessions")
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


    except Exception:

        return []



def get_chat_session_by_id(
        session_id
):

    client = get_client()

    if not client:
        return None


    try:

        result = (

            client
            .table("chat_sessions")
            .select("*")
            .eq(
                "id",
                session_id
            )
            .single()
            .execute()

        )

        return result.data


    except Exception:

        return None



def delete_chat_session(
        session_id
):

    client = get_client()

    if not client:
        return False


    try:

        (
            client
            .table("chat_sessions")
            .delete()
            .eq(
                "id",
                session_id
            )
            .execute()
        )

        return True


    except Exception:

        return False



# ============================================================
# PAYMENTS
# ============================================================


def create_payment_request(data):

    client = get_client()

    if not client:
        return False


    try:

        result = (
            client
            .table("payments")
            .insert(data)
            .execute()
        )

        return bool(result.data)


    except Exception:

        return False



def get_pending_payments():

    client = get_client()

    if not client:
        return []


    try:

        result = (

            client
            .table("payments")
            .select("*")
            .eq(
                "status",
                "pending"
            )
            .execute()

        )

        return result.data or []


    except Exception:

        return []



def approve_payment(
        payment_id,
        email,
        plan
):

    client = get_client()

    if not client:
        return False


    try:

        client.table("payments").update(
            {
                "status": "approved"
            }
        ).eq(
            "id",
            payment_id
        ).execute()


        client.table("users").update(
            {
                "plan": plan
            }
        ).eq(
            "email",
            email
        ).execute()


        return True


    except Exception:

        return False



# ============================================================
# TEAM
# ============================================================


def get_team_members(team_id):

    client = get_client()

    if not client:
        return []


    try:

        result = (

            client
            .table("users")
            .select(
                "name,email,account_type"
            )
            .eq(
                "team_id",
                team_id
            )
            .execute()

        )

        return result.data or []


    except Exception:

        return []



def get_team_by_owner(email):

    user = get_user_by_email(email)

    if not user:
        return []

    return get_team_members(
        user.get("team_id") or user.get("id")
    )
