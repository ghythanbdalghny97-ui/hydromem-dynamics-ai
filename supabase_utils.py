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
    if not client: return None
    try:
        now = datetime.utcnow().isoformat()
        if session_id:
            result = client.table("chat_sessions").update({
                "title": title, "messages": messages, "updated_at": now,
            }).eq("id", session_id).execute()
            return session_id if result.data else None
        
        result = client.table("chat_sessions").insert({
            "user_identifier": user_identifier, "title": title, "messages": messages,
        }).execute()
        return result.data[0]["id"] if result.data else None
    except Exception:
        return None

def get_chat_sessions(user_identifier, limit=30):
    client = _get_client()
    if not client: return []
    try:
        res = client.table("chat_sessions").select("id,title,updated_at").eq("user_identifier", user_identifier).order("updated_at", desc=True).limit(limit).execute()
        return res.data or []
    except Exception:
        return []

def get_chat_session_by_id(session_id):
    client = _get_client()
    if not client or not session_id: return None
    try:
        res = client.table("chat_sessions").select("*").eq("id", session_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def delete_chat_session(session_id):
    client = _get_client()
    if not client or not session_id: return False
    try:
        client.table("chat_sessions").delete().eq("id", session_id).execute()
        return True
    except Exception:
        return False
