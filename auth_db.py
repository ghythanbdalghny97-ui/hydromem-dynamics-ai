import hashlib
import uuid
from datetime import datetime, timedelta
import supabase_utils
import config

def hash_pwd(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

def register(email, pwd, name, account_type):
    if supabase_utils.get_user_by_email(email):
        return False, "البريد مسجل مسبقاً."
    if len(pwd) < 8:
        return False, "كلمة المرور يجب أن تكون 8 أحرف على الأقل."
    
    user = {
        "email": email.lower(), "password_hash": hash_pwd(pwd),
        "name": name, "account_type": account_type, "plan": account_type
    }
    if supabase_utils.create_user(user):
        return True, "تم إنشاء الحساب بنجاح."
    return False, "حدث خطأ في الاتصال بقاعدة البيانات."

def login(email, pwd):
    user = supabase_utils.get_user_by_email(email)
    if user and user.get("password_hash") == hash_pwd(pwd):
        return user
    return None

def generate_token(email):
    token = str(uuid.uuid4())
    expiry = (datetime.utcnow() + timedelta(days=config.TOKEN_VALID_DAYS)).isoformat()
    supabase_utils.update_user(email, {"remember_token": token, "token_expiry": expiry})
    return token

def submit_payment(email, plan, amount, ref):
    if supabase_utils.create_payment(email, plan, amount, ref):
        return True, "تم إرسال طلب الدفع بنجاح. بانتظار الإدارة."
    return False, "فشل في إرسال الطلب."

def approve_payment(payment_id, email, plan):
    expiry = (datetime.utcnow() + timedelta(days=30)).isoformat()
    success = supabase_utils.update_user(email, {"plan": plan, "account_type": plan, "expiry_date": expiry})
    if success:
        try:
            from supabase import create_client
            client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            client.table("payments").update({"status": "approved"}).eq("id", payment_id).execute()
        except: pass
        return True
    return False

def add_team_member(owner_email, member_name, member_email, member_pwd, member_role):
    owner = supabase_utils.get_user_by_email(owner_email)
    if not owner: return False, "المالك غير موجود."
    
    plan_info = config.PLANS.get(owner.get("plan", "individual"), config.PLANS["individual"])
    max_users = plan_info.get("max_users", 1)
    
    team_id = owner.get("team_id") or owner["id"]
    
    if not owner.get("team_id"):
        supabase_utils.update_user(owner_email, {"team_id": team_id})
    
    current_members = supabase_utils.get_team(team_id)
    if len(current_members) >= max_users:
        return False, f"وصلت للحد الأقصى ({max_users} مستخدمين)."
        
    if supabase_utils.get_user_by_email(member_email):
        return False, "البريد الإلكتروني مسجل مسبقاً في المنصة."
        
    pwd_hash = hash_pwd(member_pwd)
    success = supabase_utils.add_user_to_team(
        team_id, member_email, pwd_hash, member_name, member_role, 
        owner.get("plan"), owner.get("account_type")
    )
    
    if success: return True, "تمت إضافة العضو بنجاح."
    return False, "حدث خطأ أثناء الإضافة."
