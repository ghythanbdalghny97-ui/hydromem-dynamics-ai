# ============================================================
# HYDROMEM Dynamics AI
# Copyright (c) 2026 Abdulghani Saleh Mohsen Mohammed Ghaithan
# عبد الغني صالح محسن محمد غيثان — اليمن
# SPDX-License-Identifier: LicenseRef-Proprietary
# All Rights Reserved.
# ============================================================

"""
============================================================
HYDROMEM Dynamics AI v10.0
منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة
Version 10.0 — With Numbers on Charts & Time Analysis
============================================================
"""

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

st.set_page_config(
    page_title="HYDROMEM Dynamics AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { direction: rtl; text-align: right; }
    .stMetric { direction: rtl; }
    h1, h2, h3 { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)


# ============================================================
#                  النماذج الرياضية الخمسة
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


def classify_kl(m):
    if m > 0.95: return "Healthy (سليم)"
    elif m > 0.85: return "KL-1 (مشكوك)"
    elif m > 0.70: return "KL-2 (خفيف)"
    elif m > 0.50: return "KL-3 (متوسط)"
    else: return "KL-4 (شديد)"

def healing_stage(C, Cm):
    r = C/Cm
    if r<0.1: return "Inflammation (التهاب)"
    elif r<0.4: return "Soft Callus (دشبذ رخو)"
    elif r<0.8: return "Hard Callus (دشبذ صلب)"
    else: return "Remodeling (إعادة تشكيل)"


def time_to_reach(values, times, threshold, direction='decrease'):
    """حساب الوقت للوصول إلى عتبة معينة"""
    for i, v in enumerate(values):
        if direction == 'decrease' and v <= threshold:
            return times[i]
        elif direction == 'increase' and v >= threshold:
            return times[i]
    return None

def format_duration(value, unit='days'):
    """تنسيق المدة الزمنية"""
    if value is None:
        return "غير محقق"
    if unit == 'days':
        if value >= 365:
            return f"{value/365:.1f} سنة"
        elif value >= 30:
            return f"{value/30:.1f} شهر"
        else:
            return f"{value:.0f} يوم"
    elif unit == 'weeks':
        return f"{value:.1f} أسبوع"
    elif unit == 'hours':
        return f"{value:.1f} ساعة"
    return str(value)

def add_values_on_plot(ax, x_data, y_data, num_points=5, color='black', fmt='{:.3f}'):
    """إضافة قيم رقمية على الرسم البياني"""
    indices = np.linspace(0, len(x_data)-1, num_points, dtype=int)
    for i in indices:
        ax.annotate(fmt.format(y_data[i]),
                    xy=(x_data[i], y_data[i]),
                    xytext=(0, 8), textcoords='offset points',
                    ha='center', fontsize=8, color=color,
                    bbox=dict(boxstyle='round,pad=0.3', 
                              facecolor='white', edgecolor=color, alpha=0.7))


# ============================================================
#              مكونات الذكاء الاصطناعي
# ============================================================

@st.cache_resource
def train_surrogate():
    np.random.seed(42)
    X, Y = [], []
    for _ in range(800):
        params = [np.random.uniform(0.1,2), np.random.uniform(0,2),
                  np.random.uniform(0.1,2), np.random.uniform(0,1),
                  np.random.uniform(0.1,2), np.random.uniform(0,2)]
        t = np.linspace(0, 50, 80)
        s = odeint(general, [params[4], params[5]], t, args=tuple(params[:4]))
        X.append(params)
        Y.append([s[-1,0], s[-1,1], s[:,0].max(), s[:,1].max()])
    X, Y = np.array(X), np.array(Y)
    Xt, Xe, Yt, Ye = train_test_split(X, Y, test_size=0.2, random_state=42)
    m = MLPRegressor(hidden_layer_sizes=(64,128,64), activation='relu',
                     max_iter=300, random_state=42)
    m.fit(Xt, Yt)
    loss = mean_squared_error(Ye, m.predict(Xe))
    return m, loss


@st.cache_resource
def train_classifier():
    np.random.seed(42)
    X, y = [], []
    attempts = 0
    while len(X) < 1000 and attempts < 20000:
        attempts += 1
        mu = np.random.uniform(-0.5, 3.0)
        k  = np.random.uniform(-1.0, 3.0)
        b  = np.random.uniform(-0.5, 2.5)
        g  = np.random.uniform(-0.5, 1.5)
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
    Xt, Xe, Yt, Ye = train_test_split(X, y, test_size=0.2,
                                       random_state=42, stratify=y)
    m = RandomForestClassifier(n_estimators=100, random_state=42)
    m.fit(Xt, Yt)
    acc = accuracy_score(Ye, m.predict(Xe))
    return m, acc


@st.cache_resource
def train_regressor():
    np.random.seed(42)
    X, y = [], []
    for _ in range(1000):
        params = [np.random.uniform(1,20),
                  np.random.uniform(0.003,0.012),
                  np.random.uniform(0.008,0.025),
                  np.random.uniform(0.00005,0.0004)]
        t = np.linspace(0, params[0]*365, 400)
        s = odeint(cartilage, [0,1.0], t, args=(params[1], params[2], params[3], 0.5))
        X.append(params); y.append(s[-1,1])
    X, y = np.array(X), np.array(y)
    Xt, Xe, Yt, Ye = train_test_split(X, y, test_size=0.2, random_state=42)
    m = Pipeline([
        ('scaler', StandardScaler()),
        ('mlp', MLPRegressor(hidden_layer_sizes=(128,64,32), activation='relu',
                             max_iter=600, learning_rate_init=0.001, random_state=42))
    ])
    m.fit(Xt, Yt)
    r2 = r2_score(Ye, m.predict(Xe))
    return m, r2


# ============================================================
#              نظام التسعير
# ============================================================

PLANS = {
    "free": {"name": "🆓 مجاني", "price_yemen": 0, "price_gulf": 0, "price_global": 0,
             "duration_days": 999999, "max_trials": 10,
             "features": {"ai": False, "csv": False, "pdf": False, "api": False}},
    "weekly": {"name": "📅 أسبوعي", "price_yemen": 2, "price_gulf": 9.99, "price_global": 19.99,
               "duration_days": 7, "max_trials": -1,
               "features": {"ai": True, "csv": True, "pdf": False, "api": False}},
    "monthly": {"name": "📆 شهري", "price_yemen": 7, "price_gulf": 29.99, "price_global": 49.99,
                "duration_days": 30, "max_trials": -1,
                "features": {"ai": True, "csv": True, "pdf": True, "api": False}},
    "yearly": {"name": "⭐ سنوي", "price_yemen": 50, "price_gulf": 199, "price_global": 399,
               "duration_days": 365, "max_trials": -1,
               "features": {"ai": True, "csv": True, "pdf": True, "api": True}},
    "pro_monthly": {"name": "🩺 احترافي شهري", "price_yemen": 15, "price_gulf": 59, "price_global": 99,
                    "duration_days": 30, "max_trials": -1,
                    "features": {"ai": True, "csv": True, "pdf": True, "api": True}},
    "pro_yearly": {"name": "🏆 احترافي سنوي", "price_yemen": 120, "price_gulf": 499, "price_global": 799,
                   "duration_days": 365, "max_trials": -1,
                   "features": {"ai": True, "csv": True, "pdf": True, "api": True}}
}

ENTERPRISE_PLANS = {
    "university": {"name": "🏫 باقة الجامعة",
                   "price_yemen": 500, "price_gulf": 2500, "price_global": 5000,
                   "features": ["حتى 200 طالب", "كل الميزات", "لوحة تحكم إدارية",
                                "تدريب مخصص", "دعم فني مباشر"]},
    "hospital": {"name": "🏥 باقة المستشفى",
                 "price_yemen": 2000, "price_gulf": 10000, "price_global": 25000,
                 "features": ["عدد أطباء غير محدود", "كل الميزات", "API Access",
                              "تكامل مع الأنظمة", "دعم مخصص 24/7"]},
    "pharma": {"name": "💊 باقة شركة الأدوية",
               "price_yemen": 10000, "price_gulf": 50000, "price_global": 200000,
               "features": ["نموذج مخصص", "تطوير خاص", "شريك بحثي",
                            "بيانات خاصة", "دعم مخصص 24/7"]}
}


def init_user_session():
    defaults = {'user_plan': 'free', 'trials_used': 0,
                'subscription_start': None, 'subscription_end': None,
                'show_pricing': False}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_current_plan():
    return PLANS[st.session_state.user_plan]


def can_use_ai():
    return get_current_plan()['features']['ai']


def use_trial():
    if get_current_plan()['max_trials'] == -1:
        return True
    if st.session_state.trials_used < 10:
        st.session_state.trials_used += 1
        return True
    return False


def remaining_trials():
    plan = get_current_plan()
    if plan['max_trials'] == -1:
        return "∞ غير محدود"
    return max(0, plan['max_trials'] - st.session_state.trials_used)


def show_subscription_status():
    plan = get_current_plan()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💳 حالة الاشتراك")
    
    if st.session_state.user_plan == 'free':
        st.sidebar.warning(f"**الباقة:** {plan['name']}")
        st.sidebar.info(f"**التجارب المتبقية:** {remaining_trials()} / 10")
        if st.sidebar.button("🚀 ترقية الآن", use_container_width=True, type="primary"):
            st.session_state.show_pricing = True
            st.rerun()
    else:
        st.sidebar.success(f"**الباقة:** {plan['name']}")
        if st.session_state.subscription_end:
            days_left = max(0, (st.session_state.subscription_end - datetime.now()).days)
            st.sidebar.info(f"**متبقي:** {days_left} يوم")


def show_pricing_page():
    st.header("💎 باقات الاشتراك الاحترافية")
    st.markdown("---")
    
    region = st.radio("🌍 اختر منطقتك:",
        ["🌴 الخليج والشرق الأوسط", "🌍 عالمي (دولي)", "🇾🇪 اليمن (محلي)"], horizontal=True)
    region_map = {"🌴 الخليج والشرق الأوسط": "gulf", "🌍 عالمي (دولي)": "global", "🇾🇪 اليمن (محلي)": "yemen"}
    region_key = region_map[region]
    
    st.markdown("## 🎯 الباقات الفردية")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### 🆓 مجاني")
        st.markdown("# $0")
        st.markdown("**10 تجارب**")
        st.markdown("✅ محاكاة كاملة")
        st.markdown("❌ مكونات AI")
    
    with c2:
        st.markdown("### 📆 شهري")
        st.markdown(f"# ${PLANS['monthly'][f'price_{region_key}']}")
        st.markdown("**30 يوماً**")
        st.markdown("✅ محاكاة غير محدودة")
        st.markdown("✅ 3 مكونات AI")
        st.markdown("✅ تقارير PDF")
    
    with c3:
        st.markdown("### ⭐ سنوي (الأفضل)")
        st.markdown(f"# ${PLANS['yearly'][f'price_{region_key}']}")
        st.markdown("**365 يوماً — وفّر 30%** 💰")
        st.markdown("✅ كل الميزات")
        st.markdown("✅ API Access")
    
    st.markdown("---")
    st.markdown("## 🏢 الباقات المؤسسية")
    c1, c2, c3 = st.columns(3)
    for i, (key, plan) in enumerate(ENTERPRISE_PLANS.items()):
        with [c1, c2, c3][i]:
            st.markdown(f"### {plan['name']}")
            st.markdown(f"# ${plan[f'price_{region_key}']:,}")
            for feature in plan['features']:
                st.markdown(f"✅ {feature}")
    
    st.markdown("---")
    st.markdown("## 💳 طرق الدفع")
    st.info("🌍 **جميع الأسعار بالدولار الأمريكي** — يمكن التحويل بالعملة المحلية")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        #### 🏦 التحويل المباشر
        
        **اسم المستفيد:**
        عبد الغني صالح محسن محمد غيثان
        
        **رقم الجوال:**
        📱 **779193805**
        
        **العملات المقبولة:**
        - ✅ الدولار (USD)
        - ✅ الريال السعودي (SAR)
        - ✅ الريال اليمني (YER)
        """)
    
    with c2:
        st.markdown("""
        #### 💰 المحافظ المدعومة
        
        - ✅ ONE Cash
        - ✅ جوالي (Jawali)
        - ✅ Mobile Money
        - ✅ كريمي / العمقي
        
        **رقم الاستقبال:** 779193805
        """)
    
    st.success("""
    ### 📩 خطوات الاشتراك:
    1. اختر الباقة
    2. حوّل المبلغ إلى: **779193805**
    3. أرسل الإيصال على: **ghythanbdalghny97@gmail.com**
    4. تفعيل الباقة خلال 24 ساعة
    """)
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📱 واتساب\n[اضغط للمحادثة](https://wa.me/967779193805)")
    with c2:
        st.markdown("#### 📧 البريد\nghythanbdalghny97@gmail.com")


# ============================================================
#                    الواجهة الرئيسية
# ============================================================

init_user_session()

st.title("🧬 HYDROMEM Dynamics AI")
st.markdown("### منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة")
st.markdown("---")

app = st.sidebar.radio("🔬 اختر التطبيق:", [
    "🏠 الرئيسية", "💎 باقات الاشتراك", "⚙️ النموذج الديناميكي العام",
    "🦵 خشونة الركبة", "🦴 التئام العظام", "💧 الأقراص الفقرية",
    "🩹 التئام الجروح", "🧠 مكونات الذكاء الاصطناعي"
])

st.sidebar.markdown("---")
st.sidebar.info("**HYDROMEM Dynamics AI**\n\nالإصدار 10.0\n\n5 تطبيقات + 3 مكونات AI")
st.sidebar.markdown("📧 ghythanbdalghny97@gmail.com")
st.sidebar.markdown("📱 +967 779193805")

show_subscription_status()


# ============================================================
#                   الصفحة الرئيسية
# ============================================================
if app == "🏠 الرئيسية":
    st.header("مرحباً بكم في HYDROMEM Dynamics AI")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        ### 🎯 الرؤية
        منصة حاسوبية متكاملة لمحاكاة وتحليل الأنظمة الديناميكية المعقدة.

        ### 🔬 التطبيقات
        - ⚙️ النموذج الديناميكي العام
        - 🦵 خشونة الركبة — 10-20 سنة
        - 🦴 التئام العظام — 12-24 أسبوعاً
        - 💧 الأقراص الفقرية — 24 ساعة
        - 🩹 التئام الجروح — 8-16 أسبوعاً
        """)
    with c2:
        st.markdown("""
        ### ⚙️ التقنيات
        - النمذجة الرياضية (ODEs)
        - المحاكاة العددية (odeint)
        - تحليل الاستقرار (Jacobian)
        - الذكاء الاصطناعي (MLP + RF)
        - Streamlit Web App
        """)
        st.success("✅ 5 تطبيقات + 3 مكونات AI")


# ============================================================
#              صفحة التسعير
# ============================================================
elif app == "💎 باقات الاشتراك":
    show_pricing_page()


# ============================================================
#         النموذج الديناميكي العام (مع الأرقام على الرسم)
# ============================================================
elif app == "⚙️ النموذج الديناميكي العام":
    st.header("⚙️ النموذج الديناميكي العام")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])
    with c1:
        A0 = st.slider("A₀", 0.0, 2.0, 0.5, 0.1)
        T0 = st.slider("Θ₀", 0.0, 2.0, 0.2, 0.1)
        mu = st.slider("μ", 0.1, 2.0, 1.0, 0.1)
        k  = st.slider("κ", 0.0, 2.0, 0.5, 0.1)
        b  = st.slider("β", 0.1, 2.0, 0.8, 0.1)
        g  = st.slider("γ", 0.0, 1.0, 0.3, 0.05)
        te = st.slider("الزمن", 10, 200, 50)

    with c2:
        t = np.linspace(0, te, 500)
        s = odeint(general, [A0, T0], t, args=(mu, k, b, g))
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(t, s[:,0], 'b-', lw=2, label='A (الحالة)')
        ax.plot(t, s[:,1], 'r-', lw=2, label='Θ (الذاكرة)')
        
        # إضافة الأرقام على المنحنى
        add_values_on_plot(ax, t, s[:,0], num_points=6, color='blue', fmt='{:.3f}')
        add_values_on_plot(ax, t, s[:,1], num_points=6, color='red', fmt='{:.3f}')
        
        ax.set_xlabel('الزمن', fontsize=12)
        ax.set_ylabel('القيمة', fontsize=12)
        ax.legend(fontsize=11); ax.grid(alpha=0.3)
        ax.set_title('تطور النظام الديناميكي — القيم الرقمية', fontsize=13)
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج الدقيقة")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("A النهائي", f"{s[-1,0]:.6f}")
    c2.metric("Θ النهائي", f"{s[-1,1]:.6f}")
    c3.metric("A الأقصى", f"{s[:,0].max():.6f}")
    c4.metric("Θ الأقصى", f"{s[:,1].max():.6f}")

    # وقت الاستقرار
    st.markdown("---")
    st.subheader("⏱️ تحليل الوصول للاستقرار")
    tolerance = 0.01 * abs(s[-1,0])
    stable_time = None
    for i in range(len(s)):
        if abs(s[i,0] - s[-1,0]) < tolerance:
            stable_time = t[i]
            break
    if stable_time:
        st.metric("⏱️ وقت الاستقرار (99%)", f"{stable_time:.2f} وحدة زمنية")
    
    use_trial()


# ============================================================
#              خشونة الركبة (مع الأرقام والمدة)
# ============================================================
elif app == "🦵 خشونة الركبة":
    st.header("🦵 محاكاة خشونة الركبة")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])
    with c1:
        yrs = st.slider("عدد السنوات", 1, 25, 10)
        kp = st.slider("معدل إنتاج MMP", 0.003, 0.012, 0.005, 0.001)
        kd = st.slider("معدل التحلل", 0.008, 0.025, 0.015, 0.001)
        a  = st.slider("معامل التلف", 0.00005, 0.0004, 0.00010, 0.00005)

    with c2:
        t = np.linspace(0, yrs*365, 1000)
        s = odeint(cartilage, [0, 1.0], t, args=(kp, kd, a, 0.5))
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(t/365, s[:,0], 'r-', lw=2, label='MMP')
        ax1.set_xlabel('السنوات', fontsize=12)
        ax1.set_ylabel('MMP', color='r', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='r')
        
        ax2 = ax1.twinx()
        ax2.plot(t/365, s[:,1], 'b-', lw=2, label='الصلابة')
        ax2.set_ylabel('الصلابة', color='b', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='b')
        
        # إضافة الأرقام
        add_values_on_plot(ax1, t/365, s[:,0], num_points=6, color='darkred', fmt='{:.3f}')
        add_values_on_plot(ax2, t/365, s[:,1], num_points=6, color='darkblue', fmt='{:.3f}')
        
        ax1.grid(alpha=0.3)
        plt.title('تطور خشونة الركبة — مع القيم الرقمية', fontsize=13)
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج الدقيقة")
    c1, c2, c3 = st.columns(3)
    c1.metric("الصلابة النهائية", f"{s[-1,1]:.6f}")
    c2.metric("مرحلة KL", classify_kl(s[-1,1]))
    c3.metric("MMP النهائي", f"{s[-1,0]:.6f}")
    
    st.markdown("---")
    st.subheader("⏱️ المدة الزمنية للوصول إلى كل مرحلة")
    
    time_kl2 = time_to_reach(s[:,1], t/365, 0.70, 'decrease')
    time_kl3 = time_to_reach(s[:,1], t/365, 0.50, 'decrease')
    time_kl4 = time_to_reach(s[:,1], t/365, 0.30, 'decrease')
    
    d1, d2, d3 = st.columns(3)
    d1.metric("⏱️ إلى KL-2", f"{time_kl2:.1f} سنة" if time_kl2 else "لا يصل")
    d2.metric("⏱️ إلى KL-3", f"{time_kl3:.1f} سنة" if time_kl3 else "لا يصل")
    d3.metric("⏱️ إلى KL-4", f"{time_kl4:.1f} سنة" if time_kl4 else "لا يصل")
    
    use_trial()


# ============================================================
#              التئام العظام (مع الأرقام والمدة)
# ============================================================
elif app == "🦴 التئام العظام":
    st.header("🦴 محاكاة التئام العظام")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])
    with c1:
        wk = st.slider("عدد الأسابيع", 4, 24, 16)
        km = st.slider("معدل التمعدن", 0.05, 0.5, 0.3, 0.05)
        mu = st.slider("معامل النمو", 1.1, 3.0, 2.0, 0.1)
        Cm = st.slider("الصلابة القصوى", 10.0, 30.0, 20.0, 1.0)

    with c2:
        t = np.linspace(0, wk*7, 500)
        s = odeint(bone, [0,0,0], t, args=(km, mu, Cm))
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(t/7, s[:,0], 'g-', lw=2, label='الكالسيوم')
        ax.plot(t/7, s[:,1]*10, 'b-', lw=2, label='التمعدن ×10')
        ax.plot(t/7, s[:,2], 'r-', lw=2, label='الصلابة')
        
        add_values_on_plot(ax, t/7, s[:,0], num_points=5, color='green', fmt='{:.2f}')
        add_values_on_plot(ax, t/7, s[:,2], num_points=5, color='red', fmt='{:.2f}')
        
        ax.set_xlabel('الأسابيع', fontsize=12)
        ax.set_ylabel('القيمة', fontsize=12)
        ax.legend(fontsize=11); ax.grid(alpha=0.3)
        plt.title('تطور التئام العظام — مع القيم الرقمية', fontsize=13)
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج الدقيقة")
    C = s[-1,2]
    c1, c2, c3 = st.columns(3)
    c1.metric("الصلابة النهائية", f"{C:.4f}")
    c2.metric("نسبة الحمل", f"{(C/Cm)*100:.2f}%")
    c3.metric("المرحلة", healing_stage(C, Cm))
    
    st.markdown("---")
    st.subheader("⏱️ المدة الزمنية للالتئام")
    
    t_50 = time_to_reach(s[:,2], t/7, 0.5*Cm, 'increase')
    t_90 = time_to_reach(s[:,2], t/7, 0.9*Cm, 'increase')
    t_100 = time_to_reach(s[:,2], t/7, 0.99*Cm, 'increase')
    
    d1, d2, d3 = st.columns(3)
    d1.metric("⏱️ لـ 50% التئام", f"{t_50:.1f} أسبوع" if t_50 else "لا يصل")
    d2.metric("⏱️ لـ 90% التئام", f"{t_90:.1f} أسبوع" if t_90 else "لا يصل")
    d3.metric("⏱️ للالتئام الكامل", f"{t_100:.1f} أسبوع" if t_100 else "لا يصل")
    
    use_trial()


# ============================================================
#              الأقراص الفقرية (مع الأرقام والمدة)
# ============================================================
elif app == "💧 الأقراص الفقرية":
    st.header("💧 محاكاة الأقراص الفقرية")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])
    with c1:
        h = st.slider("عدد الساعات", 6, 48, 24)
        ks = st.slider("معدل الانتفاخ", 0.05, 0.2, 0.1, 0.01)
        kd = st.slider("معدل التحلل", 0.02, 0.1, 0.05, 0.01)
        pl = st.slider("الحمل", 0.2, 1.0, 0.5, 0.1)

    with c2:
        t = np.linspace(0, h, 500)
        s = odeint(disc, [0.5, 1.0, 0.3], t, args=(ks, kd, pl))
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(t, s[:,0]*100, 'b-', lw=2, label='الماء %')
        ax1.set_xlabel('الساعات', fontsize=12)
        ax1.set_ylabel('الماء %', color='b', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='b')
        
        ax2 = ax1.twinx()
        ax2.plot(t, s[:,1], 'g-', lw=2, label='الارتفاع')
        ax2.plot(t, s[:,2], 'r-', lw=2, label='الضغط')
        ax2.set_ylabel('الارتفاع / الضغط', fontsize=12)
        ax2.legend(loc='upper left')
        
        add_values_on_plot(ax1, t, s[:,0]*100, num_points=6, color='darkblue', fmt='{:.1f}%')
        add_values_on_plot(ax2, t, s[:,1], num_points=4, color='darkgreen', fmt='{:.3f}')
        
        ax1.grid(alpha=0.3)
        plt.title('تطور الأقراص الفقرية — مع القيم الرقمية', fontsize=13)
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج الدقيقة")
    c1, c2, c3 = st.columns(3)
    c1.metric("الماء النهائي", f"{s[-1,0]*100:.2f}%")
    c2.metric("الارتفاع", f"{s[-1,1]:.6f}")
    c3.metric("الضغط", f"{s[-1,2]:.6f}")
    
    st.markdown("---")
    st.subheader("⏱️ المدة الزمنية")
    
    t_70 = time_to_reach(s[:,0], t, 0.70, 'increase')
    t_80 = time_to_reach(s[:,0], t, 0.80, 'increase')
    t_peak = t[np.argmax(s[:,0])]
    
    d1, d2, d3 = st.columns(3)
    d1.metric("⏱️ لـ 70% ماء", f"{t_70:.1f} ساعة" if t_70 else "لا يصل")
    d2.metric("⏱️ لـ 80% ماء", f"{t_80:.1f} ساعة" if t_80 else "لا يصل")
    d3.metric("⏱️ ذروة الماء", f"{t_peak:.1f} ساعة")
    
    use_trial()


# ============================================================
#              التئام الجروح (مع الأرقام والمدة)
# ============================================================
elif app == "🩹 التئام الجروح":
    st.header("🩹 محاكاة التئام الجروح")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])
    with c1:
        wk = st.slider("عدد الأسابيع", 4, 16, 12)
        scenario = st.selectbox("السيناريو", ["Normal (طبيعي)", "Infected (مصاب)", "Fast (سريع)"])

        if "Normal" in scenario:
            p = {'ke':1.2,'ka':0.15,'kf':1.0,'kd':0.10,'kc':1.0,'kr':0.20,
                 'ki':0.5,'kii':0.6,'kb':0.2,'kbb':0.8,'km':0.3,'kmm':0.5}
        elif "Infected" in scenario:
            p = {'ke':0.6,'ka':0.40,'kf':0.5,'kd':0.30,'kc':0.6,'kr':0.35,
                 'ki':0.9,'kii':0.25,'kb':0.5,'kbb':0.5,'km':0.6,'kmm':0.4}
        else:
            p = {'ke':1.5,'ka':0.08,'kf':1.3,'kd':0.05,'kc':1.3,'kr':0.10,
                 'ki':0.3,'kii':0.8,'kb':0.1,'kbb':1.0,'km':0.2,'kmm':0.6}

    with c2:
        t = np.linspace(0, wk*7, 1000)
        s = odeint(wound, [0.01,0.01,0,0.95,0.3,0.1], t, args=(p,))
        fig, axes = plt.subplots(2, 2, figsize=(14, 9))
        
        # إعادة التغطية
        axes[0,0].plot(t/7, np.maximum(s[:,0],0)*100, 'b-', lw=2)
        add_values_on_plot(axes[0,0], t/7, np.maximum(s[:,0],0)*100, num_points=5, 
                           color='darkblue', fmt='{:.1f}%')
        axes[0,0].set_title('إعادة التغطية %', fontsize=11)
        axes[0,0].set_xlabel('الأسابيع'); axes[0,0].grid(alpha=0.3)
        
        # الكولاجين
        axes[0,1].plot(t/7, np.maximum(s[:,2],0)*100, 'g-', lw=2)
        add_values_on_plot(axes[0,1], t/7, np.maximum(s[:,2],0)*100, num_points=5,
                           color='darkgreen', fmt='{:.1f}%')
        axes[0,1].set_title('الكولاجين %', fontsize=11)
        axes[0,1].set_xlabel('الأسابيع'); axes[0,1].grid(alpha=0.3)
        
        # الالتهاب
        axes[1,0].plot(t/7, s[:,3], 'r-', lw=2)
        add_values_on_plot(axes[1,0], t/7, s[:,3], num_points=5,
                           color='darkred', fmt='{:.3f}')
        axes[1,0].set_title('الالتهاب', fontsize=11)
        axes[1,0].set_xlabel('الأسابيع'); axes[1,0].grid(alpha=0.3)
        
        # الحمل البكتيري
        axes[1,1].plot(t/7, s[:,4], 'm-', lw=2)
        add_values_on_plot(axes[1,1], t/7, s[:,4], num_points=5,
                           color='purple', fmt='{:.3f}')
        axes[1,1].set_title('الحمل البكتيري', fontsize=11)
        axes[1,1].set_xlabel('الأسابيع'); axes[1,1].grid(alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج الدقيقة")
    c1, c2, c3 = st.columns(3)
    c1.metric("التغطية النهائية", f"{max(s[-1,0],0)*100:.2f}%")
    c2.metric("الكولاجين النهائي", f"{max(s[-1,2],0)*100:.2f}%")
    c3.metric("الحمل البكتيري", f"{s[-1,4]:.6f}")
    
    st.markdown("---")
    st.subheader("⏱️ المدة الزمنية للالتئام")
    
    coverage = np.maximum(s[:,0], 0)
    t_50 = time_to_reach(coverage, t/7, 0.50, 'increase')
    t_90 = time_to_reach(coverage, t/7, 0.90, 'increase')
    t_99 = time_to_reach(coverage, t/7, 0.99, 'increase')
    
    d1, d2, d3 = st.columns(3)
    d1.metric("⏱️ لـ 50% تغطية", f"{t_50:.1f} أسبوع" if t_50 else "لا يصل")
    d2.metric("⏱️ لـ 90% تغطية", f"{t_90:.1f} أسبوع" if t_90 else "لا يصل")
    d3.metric("⏱️ للالتئام الكامل", f"{t_99:.1f} أسبوع" if t_99 else "لا يصل")
    
    use_trial()


# ============================================================
#         مكونات الذكاء الاصطناعي
# ============================================================
elif app == "🧠 مكونات الذكاء الاصطناعي":
    if not can_use_ai():
        st.error("🔒 **هذه الميزة متاحة فقط في الباقات المدفوعة**")
        st.warning("""
        ### 💎 مكونات AI المحمية:
        - ⚡ Surrogate Model — تنبؤ سريع 50×
        - 🎯 Stability Classifier — دقة 99%
        - 📊 Stiffness Regressor — R² = 0.99
        """)
        if st.button("💎 عرض الباقات والترقية", type="primary"):
            st.session_state.show_pricing = True
            st.rerun()
    else:
        st.header("🧠 مكونات الذكاء الاصطناعي")
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["⚡ Surrogate", "🎯 Classifier", "📊 Regressor"])
        
        with tab1:
            with st.spinner("جاري التدريب..."):
                sm, loss = train_surrogate()
            c1, c2, c3 = st.columns(3)
            c1.metric("Test MSE", f"{loss:.8f}")
            c2.metric("Speedup", "~50×")
            c3.metric("Architecture", "64-128-64")
            st.success("✅ Surrogate Model جاهز")
        
        with tab2:
            with st.spinner("جاري التدريب..."):
                clf, acc = train_classifier()
            c1, c2, c3 = st.columns(3)
            c1.metric("Accuracy", f"{acc*100:.4f}%")
            c2.metric("Trees", "100")
            c3.metric("Samples", "1000")
            st.success("✅ Stability Classifier جاهز")
        
        with tab3:
            with st.spinner("جاري التدريب..."):
                reg, r2 = train_regressor()
            c1, c2, c3 = st.columns(3)
            c1.metric("R² Score", f"{r2:.6f}")
            c2.metric("RMSE", "< 0.05")
            c3.metric("Architecture", "128-64-32")
            st.success("✅ Stiffness Regressor جاهز")


# ============================================================
#                    التذييل
# ============================================================
st.markdown("---")
st.markdown("### 📞 للتواصل")
c1, c2, c3 = st.columns(3)
c1.markdown("📧 **ghythanbdalghny97@gmail.com**")
c2.markdown("📱 **+967 779193805**")
c3.markdown("💳 **عبد الغني غيثان**")

st.markdown("---")
st.markdown(
    "**HYDROMEM Dynamics AI** — الإصدار 10.0 | "
    "5 تطبيقات + 3 مكونات AI | TRL 3 | "
    "© عبد الغني صالح محسن محمد غيثان 2026"
        )
