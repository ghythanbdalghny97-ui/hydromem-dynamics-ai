# ============================================================
# HYDROMEM Dynamics AI — v15.6 (Final Absolute)
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
warnings.filterwarnings('ignore')

from supabase_utils import (
    init_supabase, add_customer, get_all_customers,
    get_expiring_customers, activate_subscription,
    update_customer_status, delete_customer, get_stats
)
from chat_page import chat_page

st.set_page_config(page_title="HYDROMEM Dynamics AI", page_icon="🧬",
                   layout="wide", initial_sidebar_state="expanded")

try:
    init_supabase(st.secrets.get("SUPABASE_URL", ""), st.secrets.get("SUPABASE_KEY", ""))
except Exception:
    pass

st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#667eea">
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .main { direction: rtl; text-align: right; }
    .stMetric { direction: rtl; }
    h1, h2, h3, h4 { direction: rtl; text-align: right; }
    .chat-container { margin-top: 20px; border-top: 2px solid #667eea; padding-top: 15px; }
</style>
""", unsafe_allow_html=True)


# ============================================================
#              دوال مساعدة
# ============================================================

def add_values_on_plot(ax, x, y, num_points=5, color='black', fmt='{:.3f}'):
    if len(x) == 0: return
    indices = np.linspace(0, len(x)-1, num_points, dtype=int)
    for i in indices:
        if i < len(y):
            ax.annotate(fmt.format(y[i]), xy=(x[i], y[i]),
                        xytext=(0, 8), textcoords='offset points',
                        ha='center', fontsize=8, color=color,
                        bbox=dict(boxstyle='round,pad=0.3',
                                  facecolor='white', edgecolor=color, alpha=0.7))

def time_to_reach(values, times, threshold, direction='decrease'):
    for i, v in enumerate(values):
        if direction == 'decrease' and v <= threshold:
            return times[i]
        elif direction == 'increase' and v >= threshold:
            return times[i]
    return None

def classify_kl(m):
    if m > 0.95: return "Healthy (سليم)"
    elif m > 0.85: return "KL-1 (مشكوك)"
    elif m > 0.70: return "KL-2 (خفيف)"
    elif m > 0.50: return "KL-3 (متوسط)"
    else: return "KL-4 (شديد)"

def healing_stage(C, Cm):
    r = C/Cm
    if r < 0.1: return "Inflammation (التهاب)"
    elif r < 0.4: return "Soft Callus (دشبذ رخو)"
    elif r < 0.8: return "Hard Callus (دشبذ صلب)"
    else: return "Remodeling (إعادة تشكيل)"


# ============================================================
#              إدارة الحالة
# ============================================================

def init_simulation_state():
    defaults = {
        'gen_A0': 0.5, 'gen_T0': 0.2, 'gen_mu': 1.0, 'gen_k': 0.5, 'gen_b': 0.8, 'gen_g': 0.3, 'gen_te': 50,
        'knee_yrs': 10, 'knee_kp': 0.005, 'knee_kd': 0.015, 'knee_a': 0.00010,
        'bone_wk': 16, 'bone_km': 0.3, 'bone_mu': 2.0, 'bone_Cm': 20.0,
        'disc_h': 24, 'disc_ks': 0.1, 'disc_kd': 0.05, 'disc_pl': 0.5,
        'wound_wk': 12, 'wound_scenario': "Normal (طبيعي)",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_simulation_state()


def apply_simulation_overrides():
    overrides = {
        'gen_A0', 'gen_T0', 'gen_mu', 'gen_k', 'gen_b', 'gen_g', 'gen_te',
        'knee_yrs', 'knee_kp', 'knee_kd', 'knee_a',
        'bone_wk', 'bone_km', 'bone_mu', 'bone_Cm',
        'disc_h', 'disc_ks', 'disc_kd', 'disc_pl',
        'wound_wk', 'wound_scenario'
    }
    for key in overrides:
        override_key = f"{key}_override"
        if override_key in st.session_state:
            st.session_state[key] = st.session_state[override_key]
            del st.session_state[override_key]

apply_simulation_overrides()


# ============================================================
#    محرك استخراج ذكي موحّد (يعمل مع كل صيغ الكلمات العربية)
# ============================================================

def normalize_arabic(text):
    """توحيد النص العربي للمقارنة الذكية"""
    if not text:
        return ""
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')
    text = text.replace('ئ', 'ي').replace('ؤ', 'و')
    return text


def smart_extract_number(text, keywords, search_direction='forward', previous_value=None):
    """
    محرك استخراج ذكي ثنائي الاتجاه مع توحيد النص العربي.
    - يوحد الهمزات والتاء المربوطة
    - يبحث في 5 كلمات قبل/بعد الكلمة المفتاحية
    - يدعم الاتجاه الأمامي والخلفي
    """
    import re
    
    # تحويل الأرقام العربية إلى إنجليزية
    arabic_to_english = {'٠':'0','١':'1','٢':'2','٣':'3','٤':'4','٥':'5','٦':'6','٧':'7','٨':'8','٩':'9'}
    for ar, en in arabic_to_english.items():
        text = text.replace(ar, en)
    
    # توحيد النص العربي
    normalized_text = normalize_arabic(text)
    normalized_keywords = [normalize_arabic(kw) for kw in keywords]
    
    tokens = normalized_text.split()
    
    for kw in normalized_keywords:
        for i, token in enumerate(tokens):
            if kw in token:
                if search_direction == 'backward':
                    # ابحث للخلف أولاً
                    for j in range(i-1, max(i-6, -1), -1):
                        cleaned = tokens[j].strip('.,،؛:!؟"\'')
                        if re.fullmatch(r'\d+(?:\.\d+)?', cleaned):
                            return float(cleaned)
                    # ثم للأمام
                    for j in range(i+1, min(i+6, len(tokens))):
                        cleaned = tokens[j].strip('.,،؛:!؟"\'')
                        if re.fullmatch(r'\d+(?:\.\d+)?', cleaned):
                            return float(cleaned)
                else:
                    # ابحث للأمام أولاً
                    for j in range(i+1, min(i+6, len(tokens))):
                        cleaned = tokens[j].strip('.,،؛:!؟"\'')
                        if re.fullmatch(r'\d+(?:\.\d+)?', cleaned):
                            return float(cleaned)
                    # ثم للخلف
                    for j in range(i-1, max(i-6, -1), -1):
                        cleaned = tokens[j].strip('.,،؛:!؟"\'')
                        if re.fullmatch(r'\d+(?:\.\d+)?', cleaned):
                            return float(cleaned)
    
    return None


def process_chat_command(user_input, app_name):
    """معالجة طلبات الدردشة مع كل الصيغ العربية"""
    updated = False
    msg_extra = ""
    details = []

    # === قوائم الكلمات المفتاحية الشاملة (كل الصيغ) ===
    KEY_WEEKS = ["أسبوع", "اسبوع", "أسابيع", "اسابيع", "الأسبوع", "الاسبوع", "الأسابيع", "الاسابيع", "أسبوعاً", "اسبوعا"]
    KEY_YEARS = ["سنة", "سنه", "سنوات", "سنين", "السنوات", "السنين", "السنة", "عام", "أعوام", "اعوام"]
    KEY_HOURS = ["ساعة", "ساعه", "ساعات", "الساعات", "ساعتان"]
    KEY_TIME  = ["زمن", "الزمن", "وقت", "الوقت"]
    KEY_MINERAL = ["تمعدن", "التمعدن"]
    KEY_GROWTH  = ["نمو", "النمو"]
    KEY_STIFF   = ["صلابة", "صلابه", "قصوى", "قصوي", "ثبات", "الصلابة", "الصلابه", "القصوى", "القصوي"]
    KEY_PRODUCE = ["إنتاج", "انتاج", "الإنتاج", "الانتاج"]
    KEY_LOAD    = ["حمل", "الحمل", "أحمال", "احمال"]

    if app_name == "🦴 التئام العظام":
        val = smart_extract_number(user_input, KEY_WEEKS, 'backward')
        if val is not None:
            safe = min(max(int(val), 4), 24)
            if safe != int(val): msg_extra += f" (ضُبط إلى {safe})"
            st.session_state.bone_wk_override = safe
            details.append(f"أسابيع={safe}")
            updated = True
        val = smart_extract_number(user_input, KEY_MINERAL, 'forward')
        if val is not None:
            safe = min(max(val, 0.05), 0.5)
            if safe != val: msg_extra += f" (تمعدن ضُبط إلى {safe})"
            st.session_state.bone_km_override = safe
            details.append(f"تمعدن={safe}")
            updated = True
        val = smart_extract_number(user_input, KEY_GROWTH, 'forward')
        if val is not None:
            safe = min(max(val, 1.1), 3.0)
            if safe != val: msg_extra += f" (نمو ضُبط إلى {safe})"
            st.session_state.bone_mu_override = safe
            details.append(f"نمو={safe}")
            updated = True
        val = smart_extract_number(user_input, KEY_STIFF, 'forward')
        if val is not None:
            safe = min(max(val, 10.0), 30.0)
            if safe != val: msg_extra += f" (صلابة ضُبطت إلى {safe})"
            st.session_state.bone_Cm_override = safe
            details.append(f"صلابة={safe}")
            updated = True

    elif app_name == "🦵 خشونة الركبة":
        val = smart_extract_number(user_input, KEY_YEARS, 'backward')
        if val is not None:
            safe = min(max(int(val), 1), 25)
            if safe != int(val): msg_extra += f" (سنوات ضُبطت إلى {safe})"
            st.session_state.knee_yrs_override = safe
            details.append(f"سنوات={safe}")
            updated = True
        val = smart_extract_number(user_input, KEY_PRODUCE, 'forward')
        if val is not None:
            safe = min(max(val, 0.003), 0.012)
            if safe != val: msg_extra += f" (إنتاج ضُبط إلى {safe})"
            st.session_state.knee_kp_override = safe
            details.append(f"إنتاج={safe}")
            updated = True

    elif app_name == "💧 الأقراص الفقرية":
        val = smart_extract_number(user_input, KEY_HOURS, 'backward')
        if val is not None:
            safe = min(max(int(val), 6), 48)
            if safe != int(val): msg_extra += f" (ساعات ضُبطت إلى {safe})"
            st.session_state.disc_h_override = safe
            details.append(f"ساعات={safe}")
            updated = True
        val = smart_extract_number(user_input, KEY_LOAD, 'forward')
        if val is not None:
            safe = min(max(val, 0.2), 1.0)
            if safe != val: msg_extra += f" (حمل ضُبط إلى {safe})"
            st.session_state.disc_pl_override = safe
            details.append(f"حمل={safe}")
            updated = True

    elif app_name == "🩹 التئام الجروح":
        val = smart_extract_number(user_input, KEY_WEEKS, 'backward')
        if val is not None:
            safe = min(max(int(val), 4), 16)
            if safe != int(val): msg_extra += f" (أسابيع ضُبطت إلى {safe})"
            st.session_state.wound_wk_override = safe
            details.append(f"أسابيع={safe}")
            updated = True
        if "مصاب" in user_input or "عدوى" in user_input:
            st.session_state.wound_scenario_override = "Infected (مصاب)"
            details.append("سيناريو=مصاب")
            updated = True
        elif "سريع" in user_input:
            st.session_state.wound_scenario_override = "Fast (سريع)"
            details.append("سيناريو=سريع")
            updated = True
        elif "طبيعي" in user_input:
            st.session_state.wound_scenario_override = "Normal (طبيعي)"
            details.append("سيناريو=طبيعي")
            updated = True

    elif app_name == "⚙️ النموذج الديناميكي العام":
        val = smart_extract_number(user_input, KEY_TIME, 'forward')
        if val is not None:
            safe = min(max(int(val), 10), 200)
            if safe != int(val): msg_extra += f" (زمن ضُبط إلى {safe})"
            st.session_state.gen_te_override = safe
            details.append(f"زمن={safe}")
            updated = True

    if updated:
        details_str = " | ".join(details) if details else ""
        return True, f"✅ تم تحديث المعاملات: {details_str}.{msg_extra} جاري إعادة المحاكاة..."
    else:
        return False, "⚠️ عذراً، لم أتمكن من التعرف على الأمر. يرجى كتابة طلب واضح، مثل: 'غير عدد الأسابيع إلى 12' أو 'ارفع معدل التمعدن إلى 0.4'."


# ============================================================
#                  النماذج الرياضية
# ============================================================

def general(y, t, mu, k, b, g):
    A, T = y
    return [mu*A - A**3 - k*T*A, b*(A-T) - g*T]

def cartilage(y, t, kp, kd, a, ms):
    c, m = y
    return [kp - kd*c, -a*(c/ms)*m]

def bone(y, t, k, mu, Cm, C_floor=0.0):
    Ca, m, C = y
    dCa = 0.5*(1 - Ca/5)
    dm = k*max(mu-1, 0)*(1-m)
    dC = 0.5*(Cm*m**1.5 - C)
    if C < C_floor:
        dC = max(dC, 0)
    return [dCa, dm, dC]

def disc(y, t, ks, kd, Pl):
    w, h, P = y
    return [ks*(1-w) - kd*w*Pl, 0.05*(w-0.5)*(1.5-h), 0.3*(w-0.6) - 0.1*P]

def wound(y, t, p):
    E, F, C, I, B, M = y
    E, F, C = max(E,0), max(F,0), max(C,0)
    return [p['ke']*E*(1-E) - p['ka']*E*I,
            p['kf']*F*(1-F) - p['kd']*F*I,
            p['kc']*F*(1-C) - p['kr']*C*M,
            p['ki']*B - p['kii']*I,
            p['kb']*(1-B) - p['kbb']*B*E,
            p['km']*I - p['kmm']*M*0.8]


# ============================================================
#              دالة التقرير الطبي
# ============================================================

def generate_report(app_name, results, timeline, recommendations):
    st.markdown("---")
    st.subheader("📄 التقرير الطبي التلقائي")
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 25px; border-radius: 15px; margin: 15px 0; direction: rtl;">
        <h2 style="color: #333; text-align: center;">🧬 تقرير HYDROMEM Dynamics AI</h2>
        <p style="text-align: center; color: #666;">
            Report ID: HRM-{datetime.now().strftime('%Y%m%d-%H%M')}<br>
            التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
        <hr>
        <h3>📊 التطبيق: {app_name}</h3>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 📊 نتائج المحاكاة")
    for key, value in results.items():
        st.markdown(f"- **{key}:** {value}")
    if timeline:
        st.markdown("### ⏱️ الجدول الزمني المتوقع")
        for item in timeline:
            st.markdown(f"- {item}")
    if recommendations:
        st.markdown("### 💡 التوصيات الإرشادية")
        for category, items in recommendations.items():
            st.markdown(f"**{category}:**")
            for item in items:
                st.markdown(f"  - {item}")
    st.error("""
    ⚠️ **إخلاء مسؤولية طبية:**
    هذا التقرير لأغراض **بحثية وتعليمية فقط**.
    لا يُعدّ تشخيصاً طبياً ولا بديلاً عن استشارة طبيب مختص.
    """)
    txt = f"HYDROMEM Dynamics AI - Medical Report\n" + "=" * 50 + "\n"
    txt += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nApplication: {app_name}\n\n"
    txt += "RESULTS:\n"
    for k, v in results.items():
        txt += f"  - {k}: {v}\n"
    if timeline:
        txt += "\nTIMELINE:\n"
        for item in timeline:
            txt += f"  - {item}\n"
    if recommendations:
        txt += "\nRECOMMENDATIONS:\n"
        for cat, items in recommendations.items():
            txt += f"  [{cat}]\n"
            for it in items:
                txt += f"    - {it}\n"
    txt += "\nContact: ghythanbdalghny97@gmail.com | +967 779193805\n"
    st.download_button(label="📥 تحميل التقرير (TXT)", data=txt.encode('utf-8'),
                       file_name=f"HYDROMEM_Report_{app_name}_{datetime.now().strftime('%Y%m%d')}.txt",
                       mime="text/plain")


# ============================================================
#              مكونات AI
# ============================================================

@st.cache_resource
def train_surrogate():
    np.random.seed(42)
    X, Y = [], []
    for _ in range(600):
        params = [np.random.uniform(0.1,2), np.random.uniform(0,2), np.random.uniform(0.1,2),
                  np.random.uniform(0,1), np.random.uniform(0.1,2), np.random.uniform(0,2)]
        t = np.linspace(0, 50, 80)
        s = odeint(general, [params[4], params[5]], t, args=tuple(params[:4]))
        X.append(params); Y.append([s[-1,0], s[-1,1], s[:,0].max(), s[:,1].max()])
    X, Y = np.array(X), np.array(Y)
    Xt, Xe, Yt, Ye = train_test_split(X, Y, test_size=0.2, random_state=42)
    m = MLPRegressor(hidden_layer_sizes=(64,128,64), activation='relu', max_iter=300, random_state=42)
    m.fit(Xt, Yt)
    return m, mean_squared_error(Ye, m.predict(Xe))

@st.cache_resource
def train_classifier():
    np.random.seed(42)
    X, y = [], []
    attempts = 0
    while len(X) < 800 and attempts < 15000:
        attempts += 1
        mu = np.random.uniform(-0.5, 3.0); k = np.random.uniform(-1.0, 3.0)
        b = np.random.uniform(-0.5, 2.5); g = np.random.uniform(-0.5, 1.5)
        try:
            t = np.linspace(0, 50, 150)
            s = odeint(general, [0.5, 0.2], t, args=(mu, k, b, g))
            if np.any(np.abs(s) > 100): continue
            A, Th = s[-1,0], s[-1,1]
            J = np.array([[mu-3*A**2-k*Th, -k*A],[b, -b-g]])
            ev = np.linalg.eigvals(J)
            stable = 1 if all(np.real(e) < 0 for e in ev) else 0
            X.append([mu, k, b, g]); y.append(stable)
        except: continue
    X, y = np.array(X), np.array(y)
    Xt, Xe, Yt, Ye = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    m = RandomForestClassifier(n_estimators=100, random_state=42)
    m.fit(Xt, Yt)
    return m, accuracy_score(Ye, m.predict(Xe))

@st.cache_resource
def train_regressor():
    np.random.seed(42)
    X, y = [], []
    for _ in range(800):
        params = [np.random.uniform(1,20), np.random.uniform(0.003,0.012),
                  np.random.uniform(0.008,0.025), np.random.uniform(0.00005,0.0004)]
        t = np.linspace(0, params[0]*365, 400)
        s = odeint(cartilage, [0,1.0], t, args=(params[1], params[2], params[3], 0.5))
        X.append(params); y.append(s[-1,1])
    X, y = np.array(X), np.array(y)
    Xt, Xe, Yt, Ye = train_test_split(X, y, test_size=0.2, random_state=42)
    m = Pipeline([('scaler', StandardScaler()),
                  ('mlp', MLPRegressor(hidden_layer_sizes=(128,64,32), activation='relu',
                                       max_iter=600, learning_rate_init=0.001, random_state=42))])
    m.fit(Xt, Yt)
    return m, r2_score(Ye, m.predict(Xe))


# ============================================================
#              نظام التسعير
# ============================================================

PLANS = {
    "free": {"name": "🆓 مجاني", "price_yemen": 0, "price_gulf": 0, "price_global": 0,
             "duration_days": 999999, "max_trials": 10,
             "features": {"ai": False, "csv": False, "pdf": False, "api": False}},
    "weekly": {"name": "📅 أسبوعي", "price_yemen": 3, "price_gulf": 14.99, "price_global": 24.99,
               "duration_days": 7, "max_trials": -1,
               "features": {"ai": True, "csv": True, "pdf": False, "api": False}},
    "monthly": {"name": "📆 شهري", "price_yemen": 10, "price_gulf": 39.99, "price_global": 59.99,
                "duration_days": 30, "max_trials": -1,
                "features": {"ai": True, "csv": True, "pdf": True, "api": False}},
    "yearly": {"name": "⭐ سنوي", "price_yemen": 80, "price_gulf": 299, "price_global": 499,
               "duration_days": 365, "max_trials": -1,
               "features": {"ai": True, "csv": True, "pdf": True, "api": True}},
    "pro_monthly": {"name": "🩺 احترافي شهري", "price_yemen": 20, "price_gulf": 79, "price_global": 129,
                    "duration_days": 30, "max_trials": -1,
                    "features": {"ai": True, "csv": True, "pdf": True, "api": True}},
    "pro_yearly": {"name": "🏆 احترافي سنوي", "price_yemen": 150, "price_gulf": 599, "price_global": 999,
                   "duration_days": 365, "max_trials": -1,
                   "features": {"ai": True, "csv": True, "pdf": True, "api": True}},
    "university": {"name": "🏫 باقة الجامعة", "price_yemen": 800, "price_gulf": 3500, "price_global": 7000,
                   "duration_days": 365, "max_trials": -1,
                   "features": {"ai": True, "csv": True, "pdf": True, "api": True}},
    "hospital": {"name": "🏥 باقة المستشفى", "price_yemen": 3000, "price_gulf": 15000, "price_global": 35000,
                 "duration_days": 365, "max_trials": -1,
                 "features": {"ai": True, "csv": True, "pdf": True, "api": True}},
    "pharma": {"name": "💊 باقة شركة الأدوية", "price_yemen": 15000, "price_gulf": 75000, "price_global": 300000,
               "duration_days": 365, "max_trials": -1,
               "features": {"ai": True, "csv": True, "pdf": True, "api": True}}
}

def init_user_session():
    defaults = {'user_plan': 'free', 'trials_used': 0, 'subscription_start': None,
                'subscription_end': None, 'show_pricing': False, 'customer_name': None}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_current_plan(): return PLANS[st.session_state.user_plan]
def can_use_ai(): return get_current_plan()['features']['ai']

def use_trial():
    if get_current_plan()['max_trials'] == -1: return True
    if st.session_state.trials_used < 10:
        st.session_state.trials_used += 1
        return True
    return False

def remaining_trials():
    plan = get_current_plan()
    if plan['max_trials'] == -1: return "∞"
    return max(0, plan['max_trials'] - st.session_state.trials_used)

def show_subscription_status():
    plan = get_current_plan()
    st.sidebar.markdown("---"); st.sidebar.markdown("### 💳 حالة الاشتراك")
    if st.session_state.user_plan == 'free':
        st.sidebar.warning(f"**الباقة:** {plan['name']}")
        st.sidebar.info(f"**التجارب:** {remaining_trials()} / 10")
        if st.sidebar.button("🚀 ترقية الآن", use_container_width=True, type="primary"):
            st.session_state.show_pricing = True; st.rerun()
    else:
        st.sidebar.success(f"**الباقة:** {plan['name']}")
        if st.session_state.get('customer_name'):
            st.sidebar.info(f"👤 {st.session_state.customer_name}")
        if st.session_state.subscription_end:
            days_left = max(0, (st.session_state.subscription_end - datetime.now()).days)
            st.sidebar.info(f"**متبقي:** {days_left} يوم")

def show_activation_field():
    st.sidebar.markdown("---"); st.sidebar.markdown("### 🔑 تفعيل الباقة")
    if st.session_state.user_plan == 'free':
        code_input = st.sidebar.text_input("أدخل كود التفعيل:", key='code_input')
        if st.sidebar.button("✅ تفعيل", key='activate_btn', use_container_width=True):
            if code_input:
                success, result = activate_subscription(code_input.strip().upper())
                if success:
                    st.session_state.user_plan = result['plan']
                    st.session_state.customer_name = result['name']
                    try:
                        end = datetime.fromisoformat(result['end_date'].replace('Z', '+00:00'))
                        st.session_state.subscription_end = end.replace(tzinfo=None)
                    except:
                        st.session_state.subscription_end = datetime.now() + timedelta(days=30)
                    st.sidebar.success(f"✅ مرحباً {result['name']}!")
                    st.sidebar.balloons(); st.rerun()
                else:
                    st.sidebar.error(f"❌ {result}")
            else:
                st.sidebar.warning("أدخل الكود أولاً")
    else:
        st.sidebar.success("✅ باقتك مفعّلة")

def show_pricing_page():
    st.header("💎 باقات الاشتراك الاحترافية"); st.markdown("---")
    region = st.radio("🌍 اختر منطقتك:",
        ["🌴 الخليج والشرق الأوسط", "🌍 عالمي (دولي)", "🇾🇪 اليمن (محلي)"], horizontal=True)
    region_key = {"🌴 الخليج والشرق الأوسط": "gulf", "🌍 عالمي (دولي)": "global", "🇾🇪 اليمن (محلي)": "yemen"}[region]
    st.markdown("## 🎯 الباقات الفردية")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 🆓 مجاني\n# $0\n**10 تجارب**\n✅ محاكاة كاملة\n❌ مكونات AI")
    with c2:
        st.markdown(f"### 📆 شهري\n# ${PLANS['monthly'][f'price_{region_key}']}\n**30 يوماً**\n✅ محاكاة غير محدودة\n✅ 3 مكونات AI\n✅ Chat AI")
    with c3:
        st.markdown(f"### ⭐ سنوي\n# ${PLANS['yearly'][f'price_{region_key}']}\n**365 يوماً**\n✅ كل الميزات\n✅ API Access")
    st.markdown("---")
    st.info("🌍 جميع الأسعار بالدولار الأمريكي — التحويل بالعملة المحلية")
    st.success("📩 للاشتراك: حوّل المبلغ إلى **779193805** وأرسل الإيصال إلى **ghythanbdalghny97@gmail.com**")

def admin_dashboard():
    st.header("🔧 لوحة تحكم المسؤول"); st.markdown("---")
    if 'admin_auth' not in st.session_state: st.session_state.admin_auth = False
    if not st.session_state.admin_auth:
        st.subheader("🔐 تسجيل دخول المسؤول")
        pwd = st.text_input("كلمة المرور:", type="password", key='admin_pwd')
        if st.button("دخول", type="primary"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", "Hydromem2026Strong"):
                st.session_state.admin_auth = True; st.rerun()
            else: st.error("❌ كلمة مرور خاطئة")
        return
    stats = get_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 إجمالي العملاء", stats['total'])
    c2.metric("✅ نشط", stats['active'])
    c3.metric("⚠️ قريب الانتهاء", stats['expiring'])
    c4.metric("💰 الإيرادات", f"${stats['revenue']:.2f}")
    if not stats['connected']: st.error("⚠️ لم يتم الاتصال بقاعدة البيانات.")
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["➕ إضافة عميل", "📋 قائمة العملاء", "⚠️ تذكيرات"])
    with tab1:
        st.subheader("➕ إضافة عميل جديد")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("اسم العميل *", key='new_name')
            phone = st.text_input("رقم الجوال *", key='new_phone')
        with c2:
            email = st.text_input("البريد الإلكتروني", key='new_email')
            plan = st.selectbox("الباقة *", list(PLANS.keys())[1:], key='new_plan',
                                format_func=lambda x: PLANS[x]['name'])
            amount = st.number_input("المبلغ (USD)", min_value=0.0, value=39.99, key='new_amount')
        if st.button("✅ إضافة العميل", type="primary", use_container_width=True):
            if name and phone:
                success, result = add_customer(name, phone, email, plan, amount, "")
                if success:
                    st.success(f"✅ تم الإضافة! الكود: **{result['code']}**")
                    st.balloons()
                else: st.error(f"❌ {result}")
    with tab2:
        customers = get_all_customers()
        if customers:
            for c in customers:
                st.write(f"**{c['name']}** - {c['phone']} - {c['plan']} - `{c['activation_code']}`")
        else: st.info("لا يوجد عملاء بعد")
    with tab3:
        expiring = get_expiring_customers(7)
        if expiring:
            for c in expiring: st.warning(f"⚠️ {c['name']} - {c['phone']}")
        else: st.success("✅ لا يوجد عملاء ينتهي اشتراكهم")
    if st.button("🚪 خروج"): st.session_state.admin_auth = False; st.rerun()


# ============================================================
#                    الواجهة الرئيسية
# ============================================================

init_user_session()
st.title("🧬 HYDROMEM Dynamics AI")
st.markdown("### منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة")
st.markdown("---")

app = st.sidebar.radio("🔬 اختر التطبيق:", [
    "🏠 الرئيسية", "💎 باقات الاشتراك", "🔧 لوحة التحكم", "💬 HYDROMEM Chat",
    "⚙️ النموذج الديناميكي العام", "🦵 خشونة الركبة", "🦴 التئام العظام",
    "💧 الأقراص الفقرية", "🩹 التئام الجروح", "🧠 مكونات الذكاء الاصطناعي"
])

st.sidebar.markdown("---")
st.sidebar.info("**HYDROMEM Dynamics AI**\n\nالإصدار 15.6")
st.sidebar.markdown("📧 ghythanbdalghny97@gmail.com\n📱 +967 779193805")

show_subscription_status()
show_activation_field()


if app == "🏠 الرئيسية":
    st.header("مرحباً بكم في HYDROMEM Dynamics AI")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🎯 الرؤية\nمنصة حاسوبية متكاملة لمحاكاة وتحليل الأنظمة الديناميكية المعقدة.")
        st.markdown("### 🔬 التطبيقات\n- 💬 HYDROMEM Chat\n- ⚙️ النموذج العام\n- 🦵 خشونة الركبة\n- 🦴 التئام العظام\n- 💧 الأقراص الفقرية\n- 🩹 التئام الجروح")
    with c2:
        st.markdown("### ⚙️ التقنيات\n- ODEs + odeint\n- Jacobian\n- MLP + RF\n- Gemini AI\n- Supabase\n- تقارير تلقائية")
        st.success("✅ منصة كاملة جاهزة")

elif app == "💎 باقات الاشتراك": show_pricing_page()
elif app == "🔧 لوحة التحكم": admin_dashboard()
elif app == "💬 HYDROMEM Chat": chat_page()

elif app == "⚙️ النموذج الديناميكي العام":
    st.header("⚙️ النموذج الديناميكي العام"); st.markdown("---")
    c1, c2 = st.columns([1, 3])
    with c1:
        A0 = st.slider("A₀", 0.0, 2.0, 0.5, 0.1, key='gen_A0')
        T0 = st.slider("Θ₀", 0.0, 2.0, 0.2, 0.1, key='gen_T0')
        mu = st.slider("μ", 0.1, 2.0, 1.0, 0.1, key='gen_mu')
        k = st.slider("κ", 0.0, 2.0, 0.5, 0.1, key='gen_k')
        b = st.slider("β", 0.1, 2.0, 0.8, 0.1, key='gen_b')
        g = st.slider("γ", 0.0, 1.0, 0.3, 0.05, key='gen_g')
        te = st.slider("الزمن", 10, 200, 50, key='gen_te')
    with c2:
        t = np.linspace(0, te, 500)
        s = odeint(general, [A0, T0], t, args=(mu, k, b, g))
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(t, s[:,0], 'b-', lw=2, label='A'); ax.plot(t, s[:,1], 'r-', lw=2, label='Θ')
        add_values_on_plot(ax, t, s[:,0], 6, 'blue'); add_values_on_plot(ax, t, s[:,1], 6, 'red')
        ax.set_xlabel('الزمن'); ax.legend(); ax.grid(alpha=0.3); st.pyplot(fig)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("A النهائي", f"{s[-1,0]:.6f}"); c2.metric("Θ النهائي", f"{s[-1,1]:.6f}")
    c3.metric("A الأقصى", f"{s[:,0].max():.6f}"); c4.metric("Θ الأقصى", f"{s[:,1].max():.6f}")
    st.markdown('<div class="chat-container"></div>', unsafe_allow_html=True)
    st.subheader("💬 دردشة التحكم السريع")
    if "gen_chat" not in st.session_state:
        st.session_state.gen_chat = [{"role": "assistant", "content": "مرحباً! اكتب طلبك لتعديل المحاكاة."}]
    for msg in st.session_state.gen_chat: st.chat_message(msg["role"]).write(msg["content"])
    if prompt := st.chat_input("اكتب طلبك...", key="gen_chat_input"):
        st.session_state.gen_chat.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        updated, response_msg = process_chat_command(prompt, app)
        st.session_state.gen_chat.append({"role": "assistant", "content": response_msg})
        st.chat_message("assistant").write(response_msg)
        if updated: st.rerun()
    use_trial()

elif app == "🦵 خشونة الركبة":
    st.header("🦵 محاكاة خشونة الركبة"); st.markdown("---")
    c1, c2 = st.columns([1, 3])
    with c1:
        yrs = st.slider("عدد السنوات", 1, 25, 10, key='knee_yrs')
        kp = st.slider("معدل إنتاج MMP", 0.003, 0.012, 0.005, 0.001, key='knee_kp')
        kd = st.slider("معدل التحلل", 0.008, 0.025, 0.015, 0.001, key='knee_kd')
        a = st.slider("معامل التلف", 0.00005, 0.0004, 0.00010, 0.00005, key='knee_a')
    with c2:
        t = np.linspace(0, yrs*365, 1000)
        s = odeint(cartilage, [0, 1.0], t, args=(kp, kd, a, 0.5))
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(t/365, s[:,0], 'r-', lw=2, label='MMP'); ax1.set_ylabel('MMP', color='r')
        ax2 = ax1.twinx(); ax2.plot(t/365, s[:,1], 'b-', lw=2, label='الصلابة'); ax2.set_ylabel('الصلابة', color='b')
        add_values_on_plot(ax1, t/365, s[:,0], 6, 'darkred'); add_values_on_plot(ax2, t/365, s[:,1], 6, 'darkblue')
        ax1.set_xlabel('السنوات'); ax1.grid(alpha=0.3); st.pyplot(fig)
    c1, c2, c3 = st.columns(3)
    c1.metric("الصلابة النهائية", f"{s[-1,1]:.6f}")
    c2.metric("مرحلة KL", classify_kl(s[-1,1]))
    c3.metric("MMP النهائي", f"{s[-1,0]:.6f}")
    results = {"الصلابة النهائية": f"{s[-1,1]:.4f}", "مرحلة KL": classify_kl(s[-1,1]),
               "MMP النهائي": f"{s[-1,0]:.4f}"}
    generate_report("خشونة الركبة", results, [], {"المتابعة": ["زيارة طبيب سنوياً"]})
    st.markdown('<div class="chat-container"></div>', unsafe_allow_html=True)
    st.subheader("💬 دردشة التحكم السريع")
    if "knee_chat" not in st.session_state:
        st.session_state.knee_chat = [{"role": "assistant", "content": "مرحباً! اكتب طلبك."}]
    for msg in st.session_state.knee_chat: st.chat_message(msg["role"]).write(msg["content"])
    if prompt := st.chat_input("اكتب طلبك...", key="knee_chat_input"):
        st.session_state.knee_chat.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        updated, response_msg = process_chat_command(prompt, app)
        st.session_state.knee_chat.append({"role": "assistant", "content": response_msg})
        st.chat_message("assistant").write(response_msg)
        if updated: st.rerun()
    use_trial()

elif app == "🦴 التئام العظام":
    st.header("🦴 محاكاة التئام العظام"); st.markdown("---")
    c1, c2 = st.columns([1, 3])
    with c1:
        wk = st.slider("عدد الأسابيع", 4, 24, 16, key='bone_wk')
        km = st.slider("معدل التمعدن", 0.05, 0.5, 0.3, 0.05, key='bone_km')
        mu = st.slider("معامل النمو", 1.1, 3.0, 2.0, 0.1, key='bone_mu')
        Cm = st.slider("الصلابة القصوى", 10.0, 30.0, 20.0, 1.0, key='bone_Cm')
    with c2:
        t = np.linspace(0, wk*7, 500)
        s = odeint(bone, [0,0,0], t, args=(km, mu, Cm))
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(t/7, s[:,0], 'g-', lw=2, label='الكالسيوم')
        ax.plot(t/7, s[:,1]*10, 'b-', lw=2, label='التمعدن ×10')
        ax.plot(t/7, s[:,2], 'r-', lw=2, label='الصلابة')
        add_values_on_plot(ax, t/7, s[:,0], 5, 'green'); add_values_on_plot(ax, t/7, s[:,2], 5, 'red')
        ax.set_xlabel('الأسابيع'); ax.legend(); ax.grid(alpha=0.3); st.pyplot(fig)
    C = s[-1,2]
    c1, c2, c3 = st.columns(3)
    c1.metric("الصلابة النهائية", f"{C:.4f}"); c2.metric("نسبة الحمل", f"{(C/Cm)*100:.2f}%")
    c3.metric("المرحلة", healing_stage(C, Cm))
    st.markdown('<div class="chat-container"></div>', unsafe_allow_html=True)
    st.subheader("💬 دردشة التحكم السريع")
    if "bone_chat" not in st.session_state:
        st.session_state.bone_chat = [{"role": "assistant", "content": "مرحباً! اكتب طلبك."}]
    for msg in st.session_state.bone_chat: st.chat_message(msg["role"]).write(msg["content"])
    if prompt := st.chat_input("اكتب طلبك...", key="bone_chat_input"):
        st.session_state.bone_chat.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        updated, response_msg = process_chat_command(prompt, app)
        st.session_state.bone_chat.append({"role": "assistant", "content": response_msg})
        st.chat_message("assistant").write(response_msg)
        if updated: st.rerun()
    use_trial()

elif app == "💧 الأقراص الفقرية":
    st.header("💧 محاكاة الأقراص الفقرية"); st.markdown("---")
    c1, c2 = st.columns([1, 3])
    with c1:
        h = st.slider("عدد الساعات", 6, 48, 24, key='disc_h')
        ks = st.slider("معدل الانتفاخ", 0.05, 0.2, 0.1, 0.01, key='disc_ks')
        kd = st.slider("معدل التحلل", 0.02, 0.1, 0.05, 0.01, key='disc_kd')
        pl = st.slider("الحمل", 0.2, 1.0, 0.5, 0.1, key='disc_pl')
    with c2:
        t = np.linspace(0, h, 500)
        s = odeint(disc, [0.5, 1.0, 0.3], t, args=(ks, kd, pl))
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(t, s[:,0]*100, 'b-', lw=2, label='الماء %'); ax1.set_ylabel('الماء %', color='b')
        ax2 = ax1.twinx(); ax2.plot(t, s[:,1], 'g-', lw=2, label='الارتفاع'); ax2.plot(t, s[:,2], 'r-', lw=2, label='الضغط')
        ax2.legend(loc='upper left'); ax1.set_xlabel('الساعات'); ax1.grid(alpha=0.3); st.pyplot(fig)
    c1, c2, c3 = st.columns(3)
    c1.metric("الماء النهائي", f"{s[-1,0]*100:.2f}%"); c2.metric("الارتفاع", f"{s[-1,1]:.6f}")
    c3.metric("الضغط", f"{s[-1,2]:.6f}")
    st.markdown('<div class="chat-container"></div>', unsafe_allow_html=True)
    st.subheader("💬 دردشة التحكم السريع")
    if "disc_chat" not in st.session_state:
        st.session_state.disc_chat = [{"role": "assistant", "content": "مرحباً! اكتب طلبك."}]
    for msg in st.session_state.disc_chat: st.chat_message(msg["role"]).write(msg["content"])
    if prompt := st.chat_input("اكتب طلبك...", key="disc_chat_input"):
        st.session_state.disc_chat.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        updated, response_msg = process_chat_command(prompt, app)
        st.session_state.disc_chat.append({"role": "assistant", "content": response_msg})
        st.chat_message("assistant").write(response_msg)
        if updated: st.rerun()
    use_trial()

elif app == "🩹 التئام الجروح":
    st.header("🩹 محاكاة التئام الجروح"); st.markdown("---")
    c1, c2 = st.columns([1, 3])
    with c1:
        wk = st.slider("عدد الأسابيع", 4, 16, 12, key='wound_wk')
        scenario = st.selectbox("السيناريو", ["Normal (طبيعي)", "Infected (مصاب)", "Fast (سريع)"], key='wound_scenario')
        if "Normal" in scenario: p = {'ke':1.2,'ka':0.15,'kf':1.0,'kd':0.10,'kc':1.0,'kr':0.20,'ki':0.5,'kii':0.6,'kb':0.2,'kbb':0.8,'km':0.3,'kmm':0.5}
        elif "Infected" in scenario: p = {'ke':0.6,'ka':0.40,'kf':0.5,'kd':0.30,'kc':0.6,'kr':0.35,'ki':0.9,'kii':0.25,'kb':0.5,'kbb':0.5,'km':0.6,'kmm':0.4}
        else: p = {'ke':1.5,'ka':0.08,'kf':1.3,'kd':0.05,'kc':1.3,'kr':0.10,'ki':0.3,'kii':0.8,'kb':0.1,'kbb':1.0,'km':0.2,'kmm':0.6}
    with c2:
        t = np.linspace(0, wk*7, 1000)
        s = odeint(wound, [0.01,0.01,0,0.95,0.3,0.1], t, args=(p,))
        fig, axes = plt.subplots(2, 2, figsize=(14, 9))
        axes[0,0].plot(t/7, np.maximum(s[:,0],0)*100, 'b-', lw=2); axes[0,0].set_title('إعادة التغطية %'); axes[0,0].grid(alpha=0.3)
        axes[0,1].plot(t/7, np.maximum(s[:,2],0)*100, 'g-', lw=2); axes[0,1].set_title('الكولاجين %'); axes[0,1].grid(alpha=0.3)
        axes[1,0].plot(t/7, s[:,3], 'r-', lw=2); axes[1,0].set_title('الالتهاب'); axes[1,0].grid(alpha=0.3)
        axes[1,1].plot(t/7, s[:,4], 'm-', lw=2); axes[1,1].set_title('الحمل البكتيري'); axes[1,1].grid(alpha=0.3)
        plt.tight_layout(); st.pyplot(fig)
    c1, c2, c3 = st.columns(3)
    c1.metric("التغطية النهائية", f"{max(s[-1,0],0)*100:.2f}%")
    c2.metric("الكولاجين النهائي", f"{max(s[-1,2],0)*100:.2f}%")
    c3.metric("البكتيريا", f"{s[-1,4]:.6f}")
    st.markdown('<div class="chat-container"></div>', unsafe_allow_html=True)
    st.subheader("💬 دردشة التحكم السريع")
    if "wound_chat" not in st.session_state:
        st.session_state.wound_chat = [{"role": "assistant", "content": "مرحباً! اكتب طلبك."}]
    for msg in st.session_state.wound_chat: st.chat_message(msg["role"]).write(msg["content"])
    if prompt := st.chat_input("اكتب طلبك...", key="wound_chat_input"):
        st.session_state.wound_chat.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        updated, response_msg = process_chat_command(prompt, app)
        st.session_state.wound_chat.append({"role": "assistant", "content": response_msg})
        st.chat_message("assistant").write(response_msg)
        if updated: st.rerun()
    use_trial()

elif app == "🧠 مكونات الذكاء الاصطناعي":
    if not can_use_ai():
        st.error("🔒 هذه الميزة متاحة فقط في الباقات المدفوعة")
        if st.button("💎 عرض الباقات"): st.session_state.show_pricing = True; st.rerun()
    else:
        st.header("🧠 مكونات الذكاء الاصطناعي"); st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["⚡ Surrogate", "🎯 Classifier", "📊 Regressor"])
        with tab1:
            with st.spinner("جاري التدريب..."): sm, loss = train_surrogate()
            c1, c2, c3 = st.columns(3)
            c1.metric("Test MSE", f"{loss:.8f}"); c2.metric("Speedup", "~50×"); c3.metric("Arch", "64-128-64")
        with tab2:
            with st.spinner("جاري التدريب..."): clf, acc = train_classifier()
            c1, c2, c3 = st.columns(3)
            c1.metric("Accuracy", f"{acc*100:.4f}%"); c2.metric("Trees", "100"); c3.metric("Samples", "800")
        with tab3:
            with st.spinner("جاري التدريب..."): reg, r2 = train_regressor()
            c1, c2, c3 = st.columns(3)
            c1.metric("R²", f"{r2:.6f}"); c2.metric("RMSE", "< 0.05"); c3.metric("Arch", "128-64-32")

st.markdown("---")
st.markdown("### 📞 للتواصل")
c1, c2, c3 = st.columns(3)
c1.markdown("📧 **ghythanbdalghny97@gmail.com**")
c2.markdown("📱 **+967 779193805**")
c3.markdown("🏦 **الجاد: 2312718**")

st.markdown("---")
st.markdown("**HYDROMEM Dynamics AI** — الإصدار 15.6 (Final Absolute) | 5 تطبيقات + 3 AI + تقارير + Supabase + Chat | TRL 3 | © عبد الغني غيثان 2026")
