import hashlib
import streamlit as st
from datetime import datetime, timedelta

def _get_client():
    try:
        from supabase import create_client
    except ImportError:
        return None
    url = st.secrets.get("SUPABASE_URL", "").strip()
    key = st.secrets.get("SUPABASE_KEY", "").strip()
    if not url or not key: return None
    try: return create_client(url, key)
    except Exception: return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user_db(email, password, name, account_type, org=None):
    client = _get_client()
    if not client: return False, "فشل الاتصال."
    try:
        if client.table("users").select("email").eq("email", email.lower()).execute().data:
            return False, "البريد مسجل مسبقاً."
        data = {
            "email": email.lower(), "password_hash": hash_password(password),
            "name": name, "account_type": account_type, "organization": org, "plan": account_type
        }
        client.table("users").insert(data).execute()
        return True, "تم إنشاء الحساب بنجاح."
    except Exception as e: return False, f"خطأ: {e}"

def login_user_db(email, password):
    client = _get_client()
    if not client: return None
    try:
        res = client.table("users").select("*").eq("email", email.lower()).eq("password_hash", hash_password(password)).execute()
        return res.data[0] if res.data else None
    except Exception: return None

def get_user_by_email(email):
    client = _get_client()
    if not client: return None
    try:
        res = client.table("users").select("*").eq("email", email.lower()).execute()
        return res.data[0] if res.data else None
    except Exception: return None

def update_user_plan(email, new_plan, expiry_date=None):
    client = _get_client()
    if not client: return False
    try:
        data = {"plan": new_plan}
        if expiry_date: data["expiry_date"] = expiry_date
        client.table("users").update(data).eq("email", email.lower()).execute()
        return True
    except Exception: return False

def increment_simulation(email):
    client = _get_client()
    if not client: return
    try:
        user = get_user_by_email(email)
        current = user.get("simulations_used") or 0
        client.table("users").update({"simulations_used": current + 1}).eq("email", email.lower()).execute()
    except Exception: pass

def add_team_member(owner_email, name, email, password, role, max_users):
    client = _get_client()
    if not client: return False, "فشل الاتصال."
    try:
        owner = get_user_by_email(owner_email)
        team_id = owner.get("team_id") or owner["id"]
        
        if not owner.get("team_id"):
            client.table("users").update({"team_id": team_id}).eq("email", owner_email.lower()).execute()
            
        members = client.table("users").select("id").eq("team_id", team_id).execute()
        if len(members.data) >= max_users:
            return False, f"وصلت للحد الأقصى ({max_users} مستخدمين)."
            
        if get_user_by_email(email): return False, "البريد مسجل مسبقاً."
            
        data = {
            "email": email.lower(), "password_hash": hash_password(password), "name": name,
            "account_type": owner.get("account_type"), "organization": owner.get("organization"),
            "plan": owner.get("plan"), "team_id": team_id, "role": role
        }
        client.table("users").insert(data).execute()
        return True, "تمت إضافة العضو."
    except Exception as e: return False, f"خطأ: {e}"

def get_team_members(team_id):
    client = _get_client()
    if not client: return []
    try:
        return client.table("users").select("name,email,role").eq("team_id", team_id).execute().data or []
    except Exception: return []

def submit_payment_request(email, plan, amount, receipt_ref):
    client = _get_client()
    if not client: return False, "فشل الاتصال."
    try:
        client.table("payments").insert({
            "user_email": email.lower(), "plan": plan, "amount": amount,
            "receipt_ref": receipt_ref, "status": "pending"
        }).execute()
        return True, "تم إرسال الطلب. بانتظار الإدارة."
    except Exception as e: return False, f"خطأ: {e}"

def get_pending_payments():
    client = _get_client()
    if not client: return []
    try:
        return client.table("payments").select("*").eq("status", "pending").order("created_at", desc=True).execute().data or []
    except Exception: return []

def approve_payment(payment_id, user_email, plan):
    client = _get_client()
    if not client: return False
    try:
        client.table("payments").update({"status": "approved"}).eq("id", payment_id).execute()
        expiry = (datetime.now() + timedelta(days=30)).isoformat()
        update_user_plan(user_email, plan, expiry)
        return True
    except Exception: return False
