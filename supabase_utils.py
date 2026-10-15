# ============================================================
# HYDROMEM Dynamics AI - Supabase Utilities (v2.0)
# Copyright (c) 2026 Abdulghani Saleh Mohsen Mohammed Ghaithan
# ============================================================
# Features:
#   - Customer management (add, list, activate, delete)
#   - Subscription & payment tracking
#   - Statistics
#   - Chat sessions history (NEW)
# ============================================================

from supabase import create_client
from datetime import datetime, timedelta
import secrets
import string

_supabase_client = None


# ============================================================
#              Initialization
# ============================================================

def init_supabase(url, key):
    global _supabase_client
    try:
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception:
        return None


def get_supabase():
    return _supabase_client


# ============================================================
#              Customer Management
# ============================================================

def generate_activation_code(plan):
    prefix_map = {
        "weekly": "GH-WK",
        "monthly": "GH-MO",
        "yearly": "GH-YR",
        "pro_monthly": "GH-PM",
        "pro_yearly": "GH-PY",
        "university": "GH-UNI",
        "hospital": "GH-HOS",
        "pharma": "GH-PHR"
    }
    prefix = prefix_map.get(plan, "GH-XX")
    random_part = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits)
        for _ in range(6)
    )
    return f"{prefix}-2026-{random_part}"


def add_customer(name, phone, email, plan, amount, notes=""):
    sb = get_supabase()
    if not sb:
        return False, "لا يوجد اتصال بقاعدة البيانات"
    try:
        code = generate_activation_code(plan)
        duration_map = {
            "weekly": 7, "monthly": 30, "yearly": 365,
            "pro_monthly": 30, "pro_yearly": 365,
            "university": 365, "hospital": 365, "pharma": 365
        }
        days = duration_map.get(plan, 30)
        end_date = datetime.now() + timedelta(days=days)
        result = sb.table('customers').insert({
            'name': name,
            'phone': phone,
            'email': email or None,
            'plan': plan,
            'amount': amount,
            'activation_code': code,
            'end_date': end_date.isoformat(),
            'status': 'active',
            'notes': notes or None
        }).execute()
        customer_id = result.data[0]['id']
        sb.table('payments').insert({
            'customer_id': customer_id,
            'amount': amount,
            'currency': 'USD',
            'method': 'Al-Jadai',
            'reference': f"Transfer-{datetime.now().strftime('%Y%m%d%H%M')}"
        }).execute()
        sb.table('activity_log').insert({
            'customer_id': customer_id,
            'action': 'new_subscription',
            'details': f'اشتراك جديد في باقة {plan} بمبلغ {amount}'
        }).execute()
        return True, {
            'code': code,
            'customer_id': customer_id,
            'name': name,
            'phone': phone,
            'days': days
        }
    except Exception as e:
        return False, str(e)


def get_all_customers():
    sb = get_supabase()
    if not sb:
        return []
    try:
        result = sb.table('customers').select('*').order('end_date').execute()
        return result.data
    except Exception:
        return []


def get_expiring_customers(days=7):
    sb = get_supabase()
    if not sb:
        return []
    try:
        now = datetime.now()
        threshold = now + timedelta(days=days)
        result = sb.table('customers').select('*')\
            .eq('status', 'active')\
            .lte('end_date', threshold.isoformat())\
            .gte('end_date', now.isoformat())\
            .execute()
        return result.data
    except Exception:
        return []


def get_customer_by_code(code):
    sb = get_supabase()
    if not sb:
        return None
    try:
        result = sb.table('customers').select('*')\
            .eq('activation_code', code.strip().upper())\
            .execute()
        if result.data:
            return result.data[0]
        return None
    except Exception:
        return None


def activate_subscription(code):
    customer = get_customer_by_code(code)
    if not customer:
        return False, "كود غير صحيح"
    if customer['status'] != 'active':
        return False, "الحساب غير مفعّل. تواصل مع الدعم"
    try:
        end = datetime.fromisoformat(customer['end_date'].replace('Z', '+00:00'))
        if datetime.now() > end.replace(tzinfo=None):
            return False, "انتهى صلاحية الاشتراك"
    except Exception:
        pass
    return True, customer


def update_customer_status(customer_id, status):
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table('customers').update({'status': status})\
            .eq('id', customer_id).execute()
        return True
    except Exception:
        return False


def delete_customer(customer_id):
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table('payments').delete().eq('customer_id', customer_id).execute()
        sb.table('activity_log').delete().eq('customer_id', customer_id).execute()
        sb.table('customers').delete().eq('id', customer_id).execute()
        return True
    except Exception:
        return False


def get_stats():
    sb = get_supabase()
    if not sb:
        return {'total': 0, 'active': 0, 'expiring': 0, 'revenue': 0, 'connected': False}
    try:
        all_customers = get_all_customers()
        total = len(all_customers)
        active = len([c for c in all_customers if c['status'] == 'active'])
        expiring = len(get_expiring_customers(7))
        revenue = sum([float(c.get('amount', 0) or 0) for c in all_customers])
        return {
            'total': total, 'active': active,
            'expiring': expiring, 'revenue': revenue,
            'connected': True
        }
    except Exception:
        return {'total': 0, 'active': 0, 'expiring': 0, 'revenue': 0, 'connected': False}


# ============================================================
#              Chat Sessions Management (NEW)
# ============================================================

def save_chat_session(user_identifier, title, messages, session_id=None):
    """Save or update a chat session"""
    sb = get_supabase()
    if not sb:
        return None
    try:
        if session_id:
            response = sb.table("chat_sessions").update({
                "title": title,
                "messages": messages,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", session_id).execute()
        else:
            response = sb.table("chat_sessions").insert({
                "user_identifier": user_identifier,
                "title": title,
                "messages": messages
            }).execute()
        if response.data:
            return response.data[0].get('id')
        return None
    except Exception as e:
        print(f"⚠️ save_chat_session error: {e}")
        return None


def get_chat_sessions(user_identifier, limit=30):
    """Get recent chat sessions for a user"""
    sb = get_supabase()
    if not sb:
        return []
    try:
        response = (sb.table("chat_sessions")
                    .select("id,title,updated_at,created_at")
                    .eq("user_identifier", user_identifier)
                    .order("updated_at", desc=True)
                    .limit(limit).execute())
        return response.data if response.data else []
    except Exception as e:
        print(f"⚠️ get_chat_sessions error: {e}")
        return []


def get_chat_session_by_id(session_id):
    """Get a full chat session with messages"""
    sb = get_supabase()
    if not sb:
        return None
    try:
        response = (sb.table("chat_sessions")
                    .select("*")
                    .eq("id", session_id).execute())
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"⚠️ get_chat_session_by_id error: {e}")
        return None


def delete_chat_session(session_id):
    """Delete a chat session"""
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("chat_sessions").delete().eq("id", session_id).execute()
        return True
    except Exception as e:
        print(f"⚠️ delete_chat_session error: {e}")
        return False
