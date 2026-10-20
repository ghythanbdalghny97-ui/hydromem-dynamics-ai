import streamlit as st
from datetime import datetime
import config

try:
    from supabase import create_client, Client
    supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
except Exception as e:
    supabase = None
    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")

# ------------ المستخدمون ------------
def get_user_by_email(email):
    if not supabase: return None
    res = supabase.table("users").select("*").eq("email", email.lower()).execute()
    return res.data[0] if res.data else None

def create_user(user_data):
    if not supabase: return False
    try:
        supabase.table("users").insert(user_data).execute()
        return True
    except: return False

def update_user(email, data):
    if not supabase: return False
    try:
        supabase.table("users").update(data).eq("email", email.lower()).execute()
        return True
    except: return False

def get_user_by_token(token):
    if not supabase: return None
    res = supabase.table("users").select("*").eq("remember_token", token).execute()
    return res.data[0] if res.data else None

# ------------ المحادثات ------------
def save_chat(email, title, messages, session_id=None):
    if not supabase: return None
    data = {"user_email": email, "title": title, "messages": messages, "updated_at": datetime.utcnow().isoformat()}
    if session_id:
        supabase.table("chat_sessions").update(data).eq("id", session_id).execute()
        return session_id
    res = supabase.table("chat_sessions").insert(data).execute()
    return res.data[0]["id"] if res.data else None

def get_chats(email, limit=10):
    if not supabase: return []
    res = supabase.table("chat_sessions").select("id,title").eq("user_email", email).order("updated_at", desc=True).limit(limit).execute()
    return res.data or []

def get_chat_by_id(session_id):
    if not supabase: return None
    res = supabase.table("chat_sessions").select("*").eq("id", session_id).execute()
    return res.data[0] if res.data else None

# ------------ المدفوعات ------------
def create_payment(email, plan, amount, ref):
    if not supabase: return False
    try:
        supabase.table("payments").insert({"user_email": email.lower(), "plan": plan, "amount": amount, "receipt_ref": ref, "status": "pending"}).execute()
        return True
    except: return False

def get_pending_payments():
    if not supabase: return []
    res = supabase.table("payments").select("*").eq("status", "pending").order("created_at", desc=True).execute()
    return res.data or []

# ------------ الفريق ------------
def get_team(team_id):
    if not supabase: return []
    res = supabase.table("users").select("name,email,role").eq("team_id", team_id).execute()
    return res.data or []
