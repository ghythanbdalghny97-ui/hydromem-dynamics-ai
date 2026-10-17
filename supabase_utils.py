# ============================================================
# HYDROMEM Dynamics AI
# supabase_utils.py — Chat History & Admin Stats
# Version: v22.2 (Ultimate)
# ============================================================

from datetime import datetime
import streamlit as st


def _get_client():
    try:
        from supabase import create_client
    except ImportError:
        return None

    url = st.secrets.get("SUPABASE_URL", "").strip()
    key = st.secrets.get("SUPABASE_KEY", "").strip()

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception:
        return None


def save_chat_session(user_identifier, title, messages, session_id=None):
    client = _get_client()
    if not client:
        return None

    try:
        now = datetime.utcnow().isoformat()

        if session_id:
            result = (
                client.table("chat_sessions")
                .update({
                    "title": title,
                    "messages": messages,
                    "updated_at": now,
                })
                .eq("id", session_id)
                .execute()
            )
            if result.data:
                return session_id
            return None

        result = (
            client.table("chat_sessions")
            .insert({
                "user_identifier": user_identifier,
                "title": title,
                "messages": messages,
            })
            .execute()
        )

        if result.data and len(result.data) > 0:
            return result.data[0]["id"]

        return None

    except Exception:
        return None


def get_chat_sessions(user_identifier, limit=30):
    client = _get_client()
    if not client:
        return []

    try:
        result = (
            client.table("chat_sessions")
            .select("id,title,created_at,updated_at")
            .eq("user_identifier", user_identifier)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    except Exception:
        return []


def get_chat_session_by_id(session_id):
    client = _get_client()
    if not client or not session_id:
        return None

    try:
        result = (
            client.table("chat_sessions")
            .select("*")
            .eq("id", session_id)
            .execute()
        )

        if result.data and len(result.data) > 0:
            return result.data[0]

        return None

    except Exception:
        return None


def delete_chat_session(session_id):
    client = _get_client()
    if not client or not session_id:
        return False

    try:
        client.table("chat_sessions").delete().eq("id", session_id).execute()
        return True
    except Exception:
        return False


def is_available():
    return _get_client() is not None


# ============================================================
# Admin Stats (للوحة الإدارة)
# ============================================================

def get_admin_stats():
    """يجلب إحصائيات حقيقية للوحة الإدارة (عدد المستخدمين والمحادثات)"""
    client = _get_client()
    if not client:
        return {"users": 0, "sessions": 0}
    
    try:
        # جلب كل سجلات المحادثات لعدّها
        res = client.table("chat_sessions").select("user_identifier").execute()
        data = res.data or []
        
        # حساب عدد المستخدمين الفريدين
        unique_users = len(set([r["user_identifier"] for r in data if r.get("user_identifier")]))
        # حساب إجمالي المحادثات
        total_sessions = len(data)
        
        return {"users": unique_users, "sessions": total_sessions}
    except Exception:
        return {"users": 0, "sessions": 0}
