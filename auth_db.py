# ============================================================
# HYDROMEM Dynamics AI
# auth_db.py — User Authentication & Payments Database
# ============================================================

import hashlib
import streamlit as st
from datetime import datetime

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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user_db(email, password, name, account_type, org=None):
    client = _get_client()
    if not client:
        return False, "فشل الاتصال بقاعدة البيانات."
    try:
        existing = client.table("users").select("email").eq("email", email.lower()).execute()
        if existing.data:
            return False, "هذا البريد مسجل مسبقاً."
        data = {
            "email": email.lower(),
            "password_hash": hash_password(password),
            "name": name,
            "account_type": account_type,
            "organization": org,
            "plan": account_type
        }
        client.table("users").insert(data).execute()
        return True, "تم إنشاء الحساب بنجاح."
    except Exception as e:
        return False, f"خطأ: {e}"

def login_user_db(email, password):
    client = _get_client()
    if not client:
        return None
    try:
        pwd_hash = hash_password(password)
        res = client.table("users").select("*").eq("email", email.lower()).eq("password_hash", pwd_hash).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception:
        return None

def update_user_plan(email, new_plan):
    client = _get_client()
    if not client:
        return False
    try:
        client.table("users").update({"plan": new_plan}).eq("email", email.lower()).execute()
        return True
    except Exception:
        return False

def submit_payment_request(email, plan, amount, receipt_ref):
    client = _get_client()
    if not client:
        return False, "فشل الاتصال."
    try:
        data = {
            "user_email": email.lower(),
            "plan": plan,
            "amount": amount,
            "receipt_ref": receipt_ref
        }
        client.table("payments").insert(data).execute()
        return True, "تم إرسال طلب الدفع. بانتظار تأكيد الإدارة."
    except Exception as e:
        return False, f"خطأ: {e}"

def get_pending_payments():
    client = _get_client()
    if not client:
        return []
    try:
        res = client.table("payments").select("*").eq("status", "pending").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def approve_payment(payment_id, user_email, plan):
    client = _get_client()
    if not client:
        return False
    try:
        client.table("payments").update({"status": "approved"}).eq("id", payment_id).execute()
        update_user_plan(user_email, plan)
        return True
    except Exception:
        return False
