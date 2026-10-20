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
    # تحديث حالة الدفع وتحديث باقة المستخدم ونوع الحساب
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
