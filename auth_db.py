"""
HYDROMEM Dynamics AI
Authentication Database Module

Responsible for:
- User registration
- Login
- Password security
- Persistent login token
- Team management
"""

import hashlib
import secrets
from datetime import datetime, timedelta

import supabase_utils
import config


# ============================================================
# تشفير كلمات المرور
# ============================================================

def hash_password(password: str):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()



# ============================================================
# إنشاء حساب جديد
# ============================================================

def register_user_db(email, password, name, account_type, organization=""):

    existing = supabase_utils.get_user_by_email(email)

    if existing:
        return False, "الحساب موجود مسبقاً"


    password_hash = hash_password(password)


    user = {
        "email": email.lower(),
        "password": password_hash,
        "name": name,
        "account_type": account_type,
        "organization": organization,
        "plan": "individual",
        "team_id": None,
        "remember_token": None,
        "token_expiry": None,
        "created_at": datetime.utcnow().isoformat()
    }


    result = supabase_utils.create_user(user)


    if result:
        return True, "تم إنشاء الحساب بنجاح"

    return False, "حدث خطأ أثناء إنشاء الحساب"



# ============================================================
# تسجيل الدخول العادي
# ============================================================

def login_user_db(email, password):

    user = supabase_utils.get_user_by_email(
        email.lower()
    )


    if not user:
        return None


    password_hash = hash_password(password)


    if user.get("password") != password_hash:
        return None


    return user



# ============================================================
# إنشاء Remember Token
# ============================================================

def generate_remember_token(email):

    token = secrets.token_urlsafe(48)


    expiry = (
        datetime.utcnow()
        +
        timedelta(
            days=config.TOKEN_VALID_DAYS
        )
    )


    success = supabase_utils.update_user_token(
        email,
        token,
        expiry.isoformat()
    )


    if success:
        return token


    return None



# ============================================================
# تسجيل الدخول باستخدام التوكن
# ============================================================

def login_with_token(token):

    user = supabase_utils.get_user_by_token(token)


    if not user:
        return None


    expiry = user.get(
        "token_expiry"
    )


    if expiry:

        expiry_date = datetime.fromisoformat(
            expiry.replace("Z", "")
        )

        if datetime.utcnow() > expiry_date:

            supabase_utils.clear_user_token(
                user["email"]
            )

            return None


    return user



# ============================================================
# تسجيل الخروج
# ============================================================

def logout_user(email):

    return supabase_utils.clear_user_token(
        email
    )



# ============================================================
# جلب أعضاء الفريق
# ============================================================

def get_team_members(team_id):

    return supabase_utils.get_team_members(
        team_id
    )



# ============================================================
# إضافة عضو للفريق
# ============================================================

def add_team_member(
        owner_email,
        name,
        email,
        password,
        role,
        max_users
):

    members = supabase_utils.get_team_by_owner(
        owner_email
    )


    if len(members) >= max_users:
        return False, "تم تجاوز الحد المسموح"



    return register_user_db(
        email,
        password,
        name,
        role,
        ""
    )



# ============================================================
# طلب ترقية الاشتراك
# ============================================================

def submit_payment_request(
        email,
        plan,
        amount,
        receipt
):

    data = {

        "user_email": email,

        "plan": plan,

        "amount": amount,

        "receipt_ref": receipt,

        "status": "pending",

        "created_at":
            datetime.utcnow().isoformat()

    }


    return supabase_utils.create_payment_request(
        data
    )



# ============================================================
# إدارة الدفع
# ============================================================

def get_pending_payments():

    return supabase_utils.get_pending_payments()



def approve_payment(payment_id, email, plan):

    return supabase_utils.approve_payment(
        payment_id,
        email,
        plan
    )



# ============================================================
# تحديث بيانات المستخدم
# ============================================================

def get_user_by_email(email):

    return supabase_utils.get_user_by_email(
        email
    )
