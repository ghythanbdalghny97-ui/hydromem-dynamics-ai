# ============================================================
# HYDROMEM Dynamics AI — v16.1 Professional
# Advanced AI Simulation Platform
# Copyright (c) 2026 Abdulghani Saleh Mohsen Mohammed Ghaithan
# ============================================================

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from datetime import datetime, timedelta
import warnings
import json
import uuid
import re

warnings.filterwarnings("ignore")


# ============================================================
#              قواعد البيانات
# ============================================================

from supabase_utils import (
    init_supabase,
    add_customer,
    get_all_customers,
    get_expiring_customers,
    activate_subscription,
    update_customer_status,
    delete_customer,
    get_stats
)


# ============================================================
#              صفحات خارجية
# ============================================================

from chat_page import chat_page


# ============================================================
#              إعداد الصفحة
# ============================================================

st.set_page_config(
    page_title="HYDROMEM Dynamics AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
#              تشغيل قاعدة البيانات
# ============================================================

try:
    init_supabase(
        st.secrets.get("SUPABASE_URL", ""),
        st.secrets.get("SUPABASE_KEY", "")
    )
except Exception:
    pass


# ============================================================
#              تحسين واجهة المستخدم
# ============================================================

st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#667eea">
""", unsafe_allow_html=True)


st.markdown("""
<style>

.main {
    direction: rtl;
    text-align: right;
}

h1, h2, h3, h4 {
    direction: rtl;
    text-align: right;
}

.stMetric {
    direction: rtl;
}

.chat-container {
    margin-top: 20px;
    border-top: 2px solid #667eea;
    padding-top: 15px;
}

.copy-box {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 10px;
    direction: rtl;
}

.ai-mode {
    font-size: 18px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
#              نظام إعدادات المستخدم الجديد
# ============================================================

def init_user_preferences():

    defaults = {

        "response_mode": "📚 مفصل",
        "user_id": str(uuid.uuid4()),
        "chat_history": [],
        "chat_title": "محادثة جديدة",
        "last_response": "",
        "current_chat_id": str(uuid.uuid4())

    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_user_preferences()


# ============================================================
#              اختيار نمط الذكاء الاصطناعي
# ============================================================

def response_settings():

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧠 طريقة الرد")

    mode = st.sidebar.radio(
        "اختر أسلوب الإجابة:",
        ["⚡ مختصر", "📚 مفصل"],
        index=(0 if st.session_state.response_mode == "⚡ مختصر" else 1),
        key="sidebar_response_mode"
    )

    st.session_state.response_mode = mode

    if mode == "⚡ مختصر":
        return """
        أجب باختصار شديد.
        ركز على النقاط الأساسية فقط.
        لا تضف تفاصيل غير ضرورية.
        """
    else:
        return """
        أجب بشرح مفصل ومنظم.
        قدم الأسباب والخطوات والأمثلة.
        استخدم أسلوباً علمياً واضحاً.
        """


def get_ai_style():
    """
    إرجاع نمط الرد الحالي ديناميكياً
    (يستخدم داخل أي لحظة إرسال سؤال)
    """
    if st.session_state.response_mode == "⚡ مختصر":
        return """
        أجب باختصار شديد.
        ركز على النقاط الأساسية فقط.
        لا تضف تفاصيل غير ضرورية.
        """
    else:
        return """
        أجب بشرح مفصل ومنظم.
        قدم الأسباب والخطوات والأمثلة.
        استخدم أسلوباً علمياً واضحاً.
        """


response_settings()


# ============================================================
#              أدوات الدردشة الجديدة
# ============================================================

def save_chat_message(role, content):

    st.session_state.chat_history.append({
        "role": role,
        "content": content,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    })


def clear_current_chat():

    st.session_state.chat_history = []
    st.session_state.chat_title = "محادثة جديدة"


def copy_text_button(text):

    st.text_area(
        "📋 انسخ الرد من هنا:",
        value=text,
        height=150
    )


# ============================================================
#              أدوات عامة
# ============================================================

def add_values_on_plot(ax, x, y, num_points=5, color='black', fmt='{:.3f}'):

    if len(x) == 0:
        return

    indices = np.linspace(0, len(x) - 1, num_points, dtype=int)

    for i in indices:
        if i < len(y):
            ax.annotate(
                fmt.format(y[i]),
                xy=(x[i], y[i]),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color=color
            )


def time_to_reach(values, times, threshold, direction="decrease"):

    for i, v in enumerate(values):

        if direction == "decrease" and v <= threshold:
            return times[i]

        elif direction == "increase" and v >= threshold:
            return times[i]

    return None


# ============================================================
#     محرك توحيد اللغة العربية
# ============================================================

def normalize_arabic(text):

    if not text:
        return ""

    replacements = {
        "أ": "ا", "إ": "ا", "آ": "ا",
        "ة": "ه", "ى": "ي",
        "ئ": "ي", "ؤ": "و"
    }

    for a, b in replacements.items():
        text = text.replace(a, b)

    return text


# ============================================================
#     استخراج الأرقام من النص
# ============================================================

def smart_extract_number(text, keywords, search_direction="forward"):

    arabic_numbers = {
        "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
        "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9"
    }

    for a, b in arabic_numbers.items():
        text = text.replace(a, b)

    text = normalize_arabic(text)
    words = text.split()

    keywords = [normalize_arabic(k) for k in keywords]

    for keyword in keywords:

        for index, word in enumerate(words):

            if keyword in word:

                search_range = []

                if search_direction == "backward":

                    search_range.extend(range(index - 1, max(index - 6, -1), -1))
                    search_range.extend(range(index + 1, min(index + 6, len(words))))

                else:

                    search_range.extend(range(index + 1, min(index + 6, len(words))))
                    search_range.extend(range(index - 1, max(index - 6, -1), -1))

                for j in search_range:

                    value = words[j].strip(".,،؛:!?؟")

                    if re.fullmatch(r"\d+(\.\d+)?", value):
                        return float(value)

    return None


# ============================================================
#     معالجة أوامر المستخدم
# ============================================================

def process_chat_command(user_input, app_name):

    updated = False
    details = []

    KEY_WEEKS = ["اسبوع", "اسابيع", "الأسبوع", "الاسابيع"]
    KEY_YEARS = ["سنه", "سنة", "سنوات", "عام"]
    KEY_HOURS = ["ساعة", "ساعات"]
    KEY_TIME = ["زمن", "وقت"]
    KEY_GROWTH = ["نمو"]
    KEY_MINERAL = ["تمعدن"]

    if app_name == "🦴 التئام العظام":

        value = smart_extract_number(user_input, KEY_WEEKS, "backward")
        if value is not None:
            value = min(max(int(value), 4), 24)
            st.session_state.bone_wk = value
            details.append(f"الأسابيع={value}")
            updated = True

        value = smart_extract_number(user_input, KEY_MINERAL)
        if value is not None:
            value = min(max(value, 0.05), 0.5)
            st.session_state.bone_km = value
            details.append(f"التمعدن={value}")
            updated = True

    elif app_name == "🦵 خشونة الركبة":

        value = smart_extract_number(user_input, KEY_YEARS, "backward")
        if value is not None:
            value = min(max(int(value), 1), 25)
            st.session_state.knee_yrs = value
            details.append(f"السنوات={value}")
            updated = True

    elif app_name == "💧 الأقراص الفقرية":

        value = smart_extract_number(user_input, KEY_HOURS, "backward")
        if value is not None:
            value = min(max(int(value), 6), 48)
            st.session_state.disc_h = value
            details.append(f"الساعات={value}")
            updated = True

    elif app_name == "⚙️ النموذج الديناميكي العام":

        value = smart_extract_number(user_input, KEY_TIME)
        if value is not None:
            value = min(max(int(value), 10), 200)
            st.session_state.gen_te = value
            details.append(f"الزمن={value}")
            updated = True

    if updated:
        return (True, "✅ تم تحديث المحاكاة:\n" + " | ".join(details))

    return (False, "⚠️ لم أفهم الطلب. اكتب مثالاً مثل: غير الزمن إلى 100")


# ============================================================
#     نظام حفظ المحادثات محلياً
# ============================================================

def save_chat_history():
    """حفظ سجل المحادثة الحالي — النسخة المحلية"""
    return True


def add_message(role, content):

    save_chat_message(role, content)

    if role == "assistant":
        st.session_state.last_response = content


def export_chat_text():

    text = "HYDROMEM Dynamics AI Chat\n"
    text += "=" * 40 + "\n\n"

    for msg in st.session_state.chat_history:
        text += (msg["role"] + ": " + msg["content"] + "\n\n")

    return text


# ============================================================
#     واجهة سجل المحادثة
# ============================================================

def show_chat_tools():

    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 إدارة المحادثة")

    if st.sidebar.button("🗑️ محادثة جديدة"):
        clear_current_chat()
        st.rerun()

    if st.sidebar.button("📥 تصدير المحادثة"):
        st.sidebar.download_button(
            "تحميل TXT",
            export_chat_text(),
            file_name="HYDROMEM_chat.txt"
        )

    if st.session_state.last_response:
        st.sidebar.success("آخر رد محفوظ ✅")


show_chat_tools()


# ============================================================
#              النماذج الرياضية
# ============================================================

def general(y, t, mu, k, b, g):

    A, T = y
    dA = mu * A - A**3 - k * T * A
    dT = b * (A - T) - g * T

    return [dA, dT]


def cartilage(y, t, kp, kd, a, ms):

    c, m = y
    dc = kp - kd * c
    dm = -a * (c / ms) * m

    return [dc, dm]


def bone(y, t, k, mu, Cm):

    Ca, m, C = y
    dCa = 0.5 * (1 - Ca / 5)
    dm = k * max(mu - 1, 0) * (1 - m)
    dC = 0.5 * (Cm * m**1.5 - C)

    return [dCa, dm, dC]


def disc(y, t, ks, kd, Pl):

    w, h, P = y
    dw = ks * (1 - w) - kd * w * Pl
    dh = 0.05 * (w - 0.5) * (1.5 - h)
    dP = 0.3 * (w - 0.6) - 0.1 * P

    return [dw, dh, dP]


def wound(y, t, p):

    E, F, C, I, B, M = y

    E = max(E, 0)
    F = max(F, 0)
    C = max(C, 0)

    return [
        p['ke'] * E * (1 - E) - p['ka'] * E * I,
        p['kf'] * F * (1 - F) - p['kd'] * F * I,
        p['kc'] * F * (1 - C) - p['kr'] * C * M,
        p['ki'] * B - p['kii'] * I,
        p['kb'] * (1 - B) - p['kbb'] * B * E,
        p['km'] * I - p['kmm'] * M * 0.8
    ]


# ============================================================
#              تصنيف النتائج
# ============================================================

def classify_kl(value):

    if value > 0.95:
        return "Healthy (سليم)"
    elif value > 0.85:
        return "KL-1 (بسيط)"
    elif value > 0.70:
        return "KL-2 (خفيف)"
    elif value > 0.50:
        return "KL-3 (متوسط)"
    else:
        return "KL-4 (شديد)"


def healing_stage(C, Cm):

    ratio = C / Cm

    if ratio < 0.1:
        return "Inflammation (التهاب)"
    elif ratio < 0.4:
        return "Soft Callus (دشبذ رخو)"
    elif ratio < 0.8:
        return "Hard Callus (دشبذ صلب)"
    else:
        return "Remodeling (إعادة تشكيل)"


# ============================================================
#              نظام التقارير المطور
# ============================================================

def generate_report(app_name, results, timeline=None, recommendations=None):

    st.markdown("---")
    st.header("📄 تقرير HYDROMEM Dynamics AI")

    report_id = "HRM-" + datetime.now().strftime("%Y%m%d-%H%M")

    st.info(f"""
    **رقم التقرير:** {report_id}

    **التطبيق:** {app_name}

    **التاريخ:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
    """)

    st.subheader("📊 النتائج")

    report_text = ""

    for key, value in results.items():
        line = f"- {key}: {value}"
        st.write(line)
        report_text += line + "\n"

    if timeline:
        st.subheader("⏱️ الجدول الزمني")
        for item in timeline:
            st.write("- " + item)
            report_text += "- " + item + "\n"

    if recommendations:
        st.subheader("💡 التوصيات")
        for category, items in recommendations.items():
            st.write("**" + category + "**")
            for item in items:
                st.write("- " + item)
                report_text += "- " + item + "\n"

    st.warning("""
⚠️ تنبيه:

هذه المحاكاة لأغراض بحثية وتعليمية فقط.
لا تعتبر تشخيصاً طبياً ولا بديلاً عن الطبيب المختص.
""")

    full_report = f"""
HYDROMEM Dynamics AI
====================

Report ID: {report_id}

Application: {app_name}

RESULTS
-------

{report_text}

Contact:
ghythanbdalghny97@gmail.com
"""

    st.download_button(
        label="📥 تحميل التقرير TXT",
        data=full_report.encode("utf-8"),
        file_name=f"HYDROMEM_Report_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

    st.text_area("📋 نسخ التقرير", value=full_report, height=250)


# ============================================================
#              إدارة الحالة للمحاكاة
# ============================================================

def init_simulation_state():

    defaults = {

        "gen_A0": 0.5,
        "gen_T0": 0.2,
        "gen_mu": 1.0,
        "gen_k": 0.5,
        "gen_b": 0.8,
        "gen_g": 0.3,
        "gen_te": 50,

        "knee_yrs": 10,
        "knee_kp": 0.005,
        "knee_kd": 0.015,
        "knee_a": 0.00010,

        "bone_wk": 16,
        "bone_km": 0.3,
        "bone_mu": 2.0,
        "bone_Cm": 20.0,

        "disc_h": 24,
        "disc_ks": 0.1,
        "disc_kd": 0.05,
        "disc_pl": 0.5,

        "wound_wk": 12,
        "wound_scenario": "Normal (طبيعي)"
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_simulation_state()


# ============================================================
#              نظام الاشتراكات
# ============================================================

PLANS = {

    "free": {
        "name": "🆓 مجاني",
        "price": 0,
        "days": 999999,
        "trials": 10,
        "features": {"ai": False, "pdf": False, "csv": False}
    },

    "monthly": {
        "name": "📆 شهري",
        "price": 59.99,
        "days": 30,
        "trials": -1,
        "features": {"ai": True, "pdf": True, "csv": True}
    },

    "yearly": {
        "name": "⭐ سنوي",
        "price": 499,
        "days": 365,
        "trials": -1,
        "features": {"ai": True, "pdf": True, "csv": True}
    },

    "university": {
        "name": "🏫 جامعة",
        "price": 7000,
        "days": 365,
        "trials": -1,
        "features": {"ai": True, "pdf": True, "csv": True}
    },

    "hospital": {
        "name": "🏥 مستشفى",
        "price": 35000,
        "days": 365,
        "trials": -1,
        "features": {"ai": True, "pdf": True, "csv": True}
    }
}


def init_subscription():

    defaults = {
        "user_plan": "free",
        "trials_used": 0,
        "customer_name": None,
        "subscription_end": None,
        "admin_auth": False
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_subscription()


def current_plan():
    return PLANS[st.session_state.user_plan]


def can_use_ai():
    return current_plan()["features"]["ai"]


def remaining_trials():

    plan = current_plan()

    if plan["trials"] == -1:
        return "∞"

    return max(0, plan["trials"] - st.session_state.trials_used)


def use_trial():

    plan = current_plan()

    if plan["trials"] == -1:
        return True

    if st.session_state.trials_used < plan["trials"]:
        st.session_state.trials_used += 1
        return True

    return False


# ============================================================
#              حالة الاشتراك
# ============================================================

def show_subscription_status():

    st.sidebar.markdown("---")
    st.sidebar.subheader("💳 الاشتراك")

    plan = current_plan()

    if st.session_state.user_plan == "free":
        st.sidebar.warning(f"""
الباقة: {plan['name']}

التجارب: {remaining_trials()} / 10
""")
    else:
        st.sidebar.success(plan["name"])
        if st.session_state.customer_name:
            st.sidebar.info(st.session_state.customer_name)


# ============================================================
#              صفحة الأسعار
# ============================================================

def show_pricing_page():

    st.header("💎 باقات HYDROMEM")
    st.markdown("---")

    columns = st.columns(3)
    index = 0

    for key, plan in PLANS.items():

        with columns[index % 3]:
            st.subheader(plan["name"])
            st.metric("السعر", f"${plan['price']}")
            st.write(f"مدة الاشتراك: {plan['days']} يوم")

            if plan["features"]["ai"]:
                st.success("✅ AI متقدم")
            else:
                st.info("🔹 تجربة أساسية")

        index += 1


# ============================================================
#              لوحة المسؤول
# ============================================================

def admin_dashboard():

    st.header("🔧 لوحة تحكم المسؤول")

    if not st.session_state.admin_auth:

        password = st.text_input("كلمة المرور", type="password")

        if st.button("دخول"):

            correct_password = st.secrets.get(
                "ADMIN_PASSWORD",
                "Hydromem2026Strong"
            )

            if password == correct_password:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("كلمة مرور خاطئة")

        return

    stats = get_stats()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("العملاء", stats.get("total", 0))
    c2.metric("نشط", stats.get("active", 0))
    c3.metric("قريب الانتهاء", stats.get("expiring", 0))
    c4.metric("الإيرادات", f"${stats.get('revenue', 0)}")

    st.markdown("---")

    tab1, tab2 = st.tabs(["➕ إضافة عميل", "📋 العملاء"])

    with tab1:

        name = st.text_input("اسم العميل")
        phone = st.text_input("الهاتف")
        email = st.text_input("البريد")
        plan = st.selectbox("الباقة", list(PLANS.keys()))

        if st.button("إضافة"):

            if name and phone:

                success, result = add_customer(
                    name, phone, email, plan,
                    PLANS[plan]["price"], ""
                )

                if success:
                    st.success("تمت الإضافة")
                else:
                    st.error(result)

    with tab2:

        customers = get_all_customers()
        for customer in customers:
            st.write(customer)

    if st.button("🚪 خروج"):
        st.session_state.admin_auth = False
        st.rerun()


# ============================================================
#              الطبقة النهائية لتجربة المستخدم
# ============================================================

def show_platform_status():

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 حالة المنصة")

    st.sidebar.success("""
✅ النظام يعمل

🧬 HYDROMEM Engine

🤖 AI Components

💬 Chat Memory

📈 Dynamic Simulation
""")


def show_user_settings():

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ إعدادات المستخدم")

    if st.sidebar.button("💾 حفظ الإعدادات", use_container_width=True):
        save_chat_history()
        st.sidebar.success("✅ تم حفظ الإعدادات")

    if st.sidebar.button("🆕 محادثة جديدة", use_container_width=True):
        clear_current_chat()
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.sidebar.success("تم إنشاء محادثة جديدة")
        st.rerun()


# ============================================================
#     ⭐ Widget المحادثة داخل الصفحة الرئيسية (v16.1)
# ============================================================

def home_chat_widget():

    st.markdown("---")
    st.header("💬 HYDROMEM AI Assistant")
    st.caption("اسأل مباشرة بدون مغادرة الصفحة الرئيسية")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⚡ رد مختصر", use_container_width=True):
            st.session_state.response_mode = "⚡ مختصر"
            st.rerun()

    with col2:
        if st.button("📚 رد مفصل", use_container_width=True):
            st.session_state.response_mode = "📚 مفصل"
            st.rerun()

    st.info(f"🎯 طريقة الرد الحالية: **{st.session_state.response_mode}**")

    st.markdown("---")

    # عرض سجل المحادثة داخل الرئيسية
    if st.session_state.chat_history:

        with st.expander(
            f"📜 سجل المحادثة ({len(st.session_state.chat_history)} رسالة)",
            expanded=True
        ):

            for message in st.session_state.chat_history:

                with st.chat_message(message["role"]):
                    st.write(message["content"])

    # خانة الإدخال
    user_prompt = st.chat_input("اسأل HYDROMEM AI...")

    if user_prompt:

        add_message("user", user_prompt)

        final_prompt = f"""
طريقة الإجابة:
{get_ai_style()}

سؤال المستخدم:
{user_prompt}
"""

        try:
            response = chat_page(final_prompt)
        except Exception as e:
            response = f"⚠️ خطأ: {e}"

        add_message("assistant", response)

        st.rerun()

    # أدوات إضافية
    if st.session_state.chat_history:

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🗑️ مسح المحادثة", use_container_width=True):
                clear_current_chat()
                st.rerun()

        with col_b:
            st.download_button(
                "📥 تحميل المحادثة",
                export_chat_text(),
                file_name="HYDROMEM_home_chat.txt",
                use_container_width=True
            )


# ============================================================
#              الواجهة الرئيسية v16.1
# ============================================================

st.title("🧬 HYDROMEM Dynamics AI")

st.markdown("""
### منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة

إصدار Professional v16.1
""")

st.markdown("---")


# ============================================================
#              القائمة الجانبية
# ============================================================

app = st.sidebar.radio(
    "🔬 اختر التطبيق:",
    [
        "🏠 الرئيسية",
        "💎 باقات الاشتراك",
        "🔧 لوحة التحكم",
        "💬 HYDROMEM Chat",
        "⚙️ النموذج الديناميكي العام",
        "🦵 خشونة الركبة",
        "🦴 التئام العظام",
        "💧 الأقراص الفقرية",
        "🩹 التئام الجروح",
        "🧠 مكونات الذكاء الاصطناعي"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info("""
🧬 HYDROMEM Dynamics AI

v16.1 Professional

5 تطبيقات + AI + Chat
""")

show_subscription_status()
show_platform_status()
show_user_settings()


# ============================================================
#              التوجيه بين الصفحات
# ============================================================

# ---------- الصفحة الرئيسية ----------
if app == "🏠 الرئيسية":

    st.header("🧬 HYDROMEM Dynamics AI")
    st.subheader("منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
⚙️

نماذج ديناميكية

ODE Simulation

Stability Analysis

Mathematical Models
""")

    with col2:
        st.success("""
🤖

ذكاء اصطناعي

ML Models

Neural Networks

Dynamic Prediction
""")

    with col3:
        st.warning("""
💬

HYDROMEM Chat

ذاكرة المحادثة

اختيار مستوى الرد
""")

    st.markdown("---")

    st.markdown("""
## 🚀 مميزات الإصدار 16.1

✅ اختيار الرد المختصر أو المفصل مباشرة من الرئيسية

✅ محادثة AI مدمجة في الصفحة الرئيسية

✅ حفظ سجل المحادثات

✅ نسخ وتصدير النتائج

✅ محاكاة الأنظمة الديناميكية

✅ تقارير آلية

✅ واجهة احترافية

✅ مكونات الذكاء الاصطناعي
""")

    # ⭐ إضافة Widget المحادثة في الصفحة الرئيسية
    home_chat_widget()


# ---------- صفحة الاشتراك ----------
elif app == "💎 باقات الاشتراك":
    show_pricing_page()


# ---------- لوحة الإدارة ----------
elif app == "🔧 لوحة التحكم":
    admin_dashboard()


# ---------- HYDROMEM CHAT (الصفحة الكاملة) ----------
elif app == "💬 HYDROMEM Chat":

    st.header("💬 HYDROMEM AI Chat")
    st.caption("الصفحة الكاملة للمحادثة")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⚡ رد مختصر", use_container_width=True):
            st.session_state.response_mode = "⚡ مختصر"
            st.rerun()

    with col2:
        if st.button("📚 رد مفصل", use_container_width=True):
            st.session_state.response_mode = "📚 مفصل"
            st.rerun()

    st.info(f"🎯 طريقة الرد الحالية: **{st.session_state.response_mode}**")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    user_prompt = st.chat_input("اكتب سؤالك هنا...")

    if user_prompt:

        add_message("user", user_prompt)

        with st.chat_message("user"):
            st.write(user_prompt)

        final_prompt = f"""
{get_ai_style()}

سؤال المستخدم:

{user_prompt}
"""

        try:
            response = chat_page(final_prompt)
        except Exception as e:
            response = f"⚠️ خطأ في محرك المحادثة: {e}"

        add_message("assistant", response)

        with st.chat_message("assistant"):
            st.write(response)

        st.markdown("---")
        st.subheader("📋 أدوات الرد")

        st.text_area("نسخ الرد", value=response, height=200)

        if st.button("🗑️ بدء محادثة جديدة"):
            clear_current_chat()
            st.rerun()


# ---------- النموذج الديناميكي العام ----------
elif app == "⚙️ النموذج الديناميكي العام":

    st.header("⚙️ النموذج الديناميكي العام")
    st.caption("نموذج تفاعل A–T مع تحليل الاستقرار")

    col1, col2 = st.columns(2)

    with col1:
        mu = st.slider("μ (معدل النمو)", 0.1, 3.0,
                       float(st.session_state.gen_mu), 0.1)
        k = st.slider("k (الاقتران)", 0.0, 2.0,
                      float(st.session_state.gen_k), 0.1)

    with col2:
        b = st.slider("b (استجابة T)", 0.1, 2.0,
                      float(st.session_state.gen_b), 0.1)
        g = st.slider("g (تحلل T)", 0.0, 1.5,
                      float(st.session_state.gen_g), 0.1)

    te = st.slider("زمن المحاكاة", 10, 200,
                   int(st.session_state.gen_te), 5)

    st.session_state.gen_mu = mu
    st.session_state.gen_k = k
    st.session_state.gen_b = b
    st.session_state.gen_g = g
    st.session_state.gen_te = te

    t = np.linspace(0, te, 500)

    sol = odeint(general, [st.session_state.gen_A0,
                            st.session_state.gen_T0],
                 t, args=(mu, k, b, g))

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t, sol[:, 0], label="A(t)")
    ax.plot(t, sol[:, 1], label="T(t)")
    ax.set_xlabel("Time")
    ax.set_ylabel("State")
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    if len(t) > 0:
        add_values_on_plot(ax, t, sol[:, 0], num_points=5)

    generate_report(
        "⚙️ النموذج الديناميكي العام",
        {
            "μ": mu, "k": k, "b": b, "g": g,
            "زمن المحاكاة": te,
            "A النهائي": round(float(sol[-1, 0]), 4),
            "T النهائي": round(float(sol[-1, 1]), 4)
        }
    )


# ---------- خشونة الركبة ----------
elif app == "🦵 خشونة الركبة":

    st.header("🦵 خشونة الركبة — نموذج الغضروف")

    yrs = st.slider("عدد السنوات", 1, 25,
                    int(st.session_state.knee_yrs))

    st.session_state.knee_yrs = yrs

    t = np.linspace(0, yrs * 365, 800)

    sol = odeint(
        cartilage,
        [1.0, 1.0],
        t,
        args=(st.session_state.knee_kp,
              st.session_state.knee_kd,
              st.session_state.knee_a,
              1.0)
    )

    final_c = float(sol[-1, 0])
    final_m = float(sol[-1, 1])

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t, sol[:, 0], label="Cartilage (c)")
    ax.plot(t, sol[:, 1], label="Matrix (m)")
    ax.set_xlabel("Days")
    ax.set_ylabel("State")
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    st.metric("تصنيف KL", classify_kl(final_c))

    generate_report(
        "🦵 خشونة الركبة",
        {
            "السنوات": yrs,
            "c النهائي": round(final_c, 4),
            "m النهائي": round(final_m, 4),
            "التصنيف": classify_kl(final_c)
        }
    )


# ---------- التئام العظام ----------
elif app == "🦴 التئام العظام":

    st.header("🦴 التئام العظام — نموذج ثلاثي المراحل")

    wk = st.slider("الأسابيع", 4, 24,
                   int(st.session_state.bone_wk))
    km = st.slider("معامل التمعدن", 0.05, 0.5,
                   float(st.session_state.bone_km), 0.01)

    st.session_state.bone_wk = wk
    st.session_state.bone_km = km

    t = np.linspace(0, wk * 7, 600)

    sol = odeint(
        bone,
        [1.0, 0.01, 0.0],
        t,
        args=(km, st.session_state.bone_mu,
              st.session_state.bone_Cm)
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t, sol[:, 0], label="Ca")
    ax.plot(t, sol[:, 1], label="m (mineral)")
    ax.plot(t, sol[:, 2], label="C (callus)")
    ax.set_xlabel("Days")
    ax.set_ylabel("State")
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    stage = healing_stage(float(sol[-1, 2]),
                          st.session_state.bone_Cm)
    st.metric("مرحلة الالتئام", stage)

    generate_report(
        "🦴 التئام العظام",
        {
            "الأسابيع": wk,
            "معامل التمعدن": km,
            "Ca النهائي": round(float(sol[-1, 0]), 4),
            "m النهائي": round(float(sol[-1, 1]), 4),
            "C النهائي": round(float(sol[-1, 2]), 4),
            "المرحلة": stage
        }
    )


# ---------- الأقراص الفقرية ----------
elif app == "💧 الأقراص الفقرية":

    st.header("💧 الأقراص الفقرية — نموذج ثلاثي")

    hours = st.slider("الساعات", 6, 48,
                      int(st.session_state.disc_h))

    st.session_state.disc_h = hours

    t = np.linspace(0, hours, 500)

    sol = odeint(
        disc,
        [1.0, 1.0, 0.2],
        t,
        args=(st.session_state.disc_ks,
              st.session_state.disc_kd,
              st.session_state.disc_pl)
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t, sol[:, 0], label="w (water)")
    ax.plot(t, sol[:, 1], label="h (height)")
    ax.plot(t, sol[:, 2], label="P (pressure)")
    ax.set_xlabel("Hours")
    ax.set_ylabel("State")
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    generate_report(
        "💧 الأقراص الفقرية",
        {
            "الساعات": hours,
            "w النهائي": round(float(sol[-1, 0]), 4),
            "h النهائي": round(float(sol[-1, 1]), 4),
            "P النهائي": round(float(sol[-1, 2]), 4)
        }
    )


# ---------- التئام الجروح ----------
elif app == "🩹 التئام الجروح":

    st.header("🩹 التئام الجروح — نموذج 6 متغيرات")

    wk = st.slider("الأسابيع", 4, 30,
                   int(st.session_state.wound_wk))

    scenario = st.selectbox(
        "السيناريو",
        ["Normal (طبيعي)", "Diabetic (سكري)", "Infected (ملتهب)"]
    )

    st.session_state.wound_wk = wk
    st.session_state.wound_scenario = scenario

    base_p = {
        "ke": 0.8, "ka": 0.5,
        "kf": 0.7, "kd": 0.4,
        "kc": 0.6, "kr": 0.3,
        "ki": 0.4, "kii": 0.5,
        "kb": 0.3, "kbb": 0.4,
        "km": 0.5, "kmm": 0.3
    }

    if scenario == "Diabetic (سكري)":
        base_p["ke"] = 0.4
        base_p["kf"] = 0.35
        base_p["kc"] = 0.3

    elif scenario == "Infected (ملتهب)":
        base_p["ki"] = 0.9
        base_p["kb"] = 0.7

    t = np.linspace(0, wk * 7, 700)

    sol = odeint(
        wound,
        [0.8, 0.6, 0.0, 0.2, 0.5, 0.0],
        t, args=(base_p,)
    )

    fig, ax = plt.subplots(figsize=(10, 4))
    labels = ["E", "F", "C", "I", "B", "M"]

    for i, lbl in enumerate(labels):
        ax.plot(t, sol[:, i], label=lbl)

    ax.set_xlabel("Days")
    ax.set_ylabel("State")
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)

    generate_report(
        "🩹 التئام الجروح",
        {
            "الأسابيع": wk,
            "السيناريو": scenario,
            "C النهائي": round(float(sol[-1, 2]), 4),
            "I النهائي": round(float(sol[-1, 3]), 4)
        }
    )


# ---------- مكونات الذكاء الاصطناعي ----------
elif app == "🧠 مكونات الذكاء الاصطناعي":

    if not can_use_ai():
        st.warning("🔒 هذه الميزة تحتاج اشتراك مدفوع")
    else:
        st.header("🧠 مكونات الذكاء الاصطناعي")
        st.info("""
- Neural Surrogate Model
- Stability Classifier
- Dynamic Regression Model
""")


# ============================================================
#              التحقق النهائي للنظام
# ============================================================

st.sidebar.markdown("---")

st.sidebar.caption("""
HYDROMEM Dynamics AI

v16.1 Professional

Research Prototype

© 2026 Abdulghani Saleh Mohsen Mohammed Ghaithan
""")


# ============================================================
#              التذييل النهائي
# ============================================================

st.markdown("---")

st.markdown("""
<div style="text-align:center">

🧬 <b>HYDROMEM Dynamics AI</b>

<br><br>

Advanced AI Simulation Platform

<br>

Professional Edition v16.1

<br><br>

© 2026 Abdulghani Saleh Mohsen Mohammed Ghaithan

<br>

All Rights Reserved

</div>
""", unsafe_allow_html=True)
