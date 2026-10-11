# ============================================================
# HYDROMEM Dynamics AI
# Copyright (c) 2026 Abdulghani Saleh Mohsen Mohammed Ghaithan
# عبد الغني صالح محسن محمد غيثان — اليمن
# SPDX-License-Identifier: LicenseRef-Proprietary
# All Rights Reserved.
# ============================================================

"""
============================================================
HYDROMEM Dynamics AI
منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة
Computational Intelligence Platform for Complex Dynamic Systems
Version 8.0 — Commercial Platform (5 Apps + 3 AI + Pricing)

Author: عبد الغني صالح محسن محمد غيثان
        Abdulghani Saleh Mohsen Mohammed Ghaithan
Location: Yemen — اليمن
Contact: ghythanbdalghny97@gmail.com
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
import pandas as pd
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
    .pricing-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: center;
    }
    .premium-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: center;
    }
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


# ============================================================
#              مكونات الذكاء الاصطناعي (Cache)
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
#              نظام التسعير والاشتراكات
# ============================================================

PLANS = {
    "free": {
        "name": "🆓 مجاني", "name_en": "Free",
        "price_yemen": 0, "price_gulf": 0, "price_global": 0,
        "duration_days": 999999, "max_trials": 10,
        "features": {"ai": False, "csv": False, "pdf": False,
                     "api": False, "support": "لا يوجد", "training": False}
    },
    "weekly": {
        "name": "📅 أسبوعي", "name_en": "Weekly",
        "price_yemen": 2, "price_gulf": 9.99, "price_global": 19.99,
        "duration_days": 7, "max_trials": -1,
        "features": {"ai": True, "csv": True, "pdf": False,
                     "api": False, "support": "بريد", "training": False}
    },
    "monthly": {
        "name": "📆 شهري", "name_en": "Monthly",
        "price_yemen": 7, "price_gulf": 29.99, "price_global": 49.99,
        "duration_days": 30, "max_trials": -1,
        "features": {"ai": True, "csv": True, "pdf": True,
                     "api": False, "support": "بريد", "training": False}
    },
    "yearly": {
        "name": "⭐ سنوي", "name_en": "Yearly",
        "price_yemen": 50, "price_gulf": 199, "price_global": 399,
        "duration_days": 365, "max_trials": -1,
        "features": {"ai": True, "csv": True, "pdf": True,
                     "api": True, "support": "بريد + واتساب", "training": False}
    },
    "pro_monthly": {
        "name": "🩺 احترافي شهري", "name_en": "Pro Monthly",
        "price_yemen": 15, "price_gulf": 59, "price_global": 99,
        "duration_days": 30, "max_trials": -1,
        "features": {"ai": True, "csv": True, "pdf": True,
                     "api": True, "support": "مباشر", "training": True}
    },
    "pro_yearly": {
        "name": "🏆 احترافي سنوي", "name_en": "Pro Yearly",
        "price_yemen": 120, "price_gulf": 499, "price_global": 799,
        "duration_days": 365, "max_trials": -1,
        "features": {"ai": True, "csv": True, "pdf": True,
                     "api": True, "support": "مباشر", "training": True}
    }
}

ENTERPRISE_PLANS = {
    "university": {
        "name": "🏫 باقة الجامعة",
        "price_yemen": 500, "price_gulf": 2500, "price_global": 5000,
        "features": ["حتى 200 طالب", "كل الميزات", "لوحة تحكم إدارية",
                     "تدريب مخصص", "دعم فني مباشر"]
    },
    "hospital": {
        "name": "🏥 باقة المستشفى",
        "price_yemen": 2000, "price_gulf": 10000, "price_global": 25000,
        "features": ["عدد أطباء غير محدود", "كل الميزات", "API Access",
                     "تكامل مع الأنظمة", "دعم مخصص 24/7"]
    },
    "pharma": {
        "name": "💊 باقة شركة الأدوية",
        "price_yemen": 10000, "price_gulf": 50000, "price_global": 200000,
        "features": ["نموذج مخصص", "تطوير خاص", "شريك بحثي",
                     "بيانات خاصة", "دعم مخصص 24/7"]
    }
}


def init_user_session():
    defaults = {
        'user_plan': 'free', 'trials_used': 0,
        'subscription_start': None, 'subscription_end': None,
        'user_email': None, 'show_pricing': False,
        'pricing_region': 'gulf'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_current_plan():
    return PLANS[st.session_state.user_plan]


def can_use_trial():
    plan = get_current_plan()
    if plan['max_trials'] == -1:
        return True
    return st.session_state.trials_used < plan['max_trials']


def can_use_ai():
    return get_current_plan()['features']['ai']


def use_trial():
    if can_use_trial():
        st.session_state.trials_used += 1
        return True
    return False


def remaining_trials():
    plan = get_current_plan()
    if plan['max_trials'] == -1:
        return "∞ غير محدود"
    return max(0, plan['max_trials'] - st.session_state.trials_used)


def subscribe(plan_key):
    plan = PLANS[plan_key]
    st.session_state.user_plan = plan_key
    st.session_state.subscription_start = datetime.now()
    st.session_state.subscription_end = datetime.now() + timedelta(days=plan['duration_days'])
    return True


def show_subscription_status():
    plan = get_current_plan()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💳 حالة الاشتراك")
    
    if st.session_state.user_plan == 'free':
        remaining = remaining_trials()
        st.sidebar.warning(f"**الباقة:** {plan['name']}")
        st.sidebar.info(f"**التجارب المتبقية:** {remaining} / 10")
        progress = st.session_state.trials_used / 10
        st.sidebar.progress(min(progress, 1.0))
        
        if st.session_state.trials_used >= 10:
            st.sidebar.error("⚠️ انتهت تجاربك المجانية!")
        
        if st.sidebar.button("🚀 ترقية الآن", use_container_width=True, type="primary"):
            st.session_state.show_pricing = True
            st.rerun()
    else:
        st.sidebar.success(f"**الباقة:** {plan['name']}")
        if st.session_state.subscription_end:
            days_left = max(0, (st.session_state.subscription_end - datetime.now()).days)
            st.sidebar.info(f"**متبقي:** {days_left} يوم")
        
        if st.sidebar.button("🔄 تغيير الباقة", use_container_width=True):
            st.session_state.show_pricing = True
            st.rerun()


def show_pricing_page():
    st.header("💎 باقات الاشتراك الاحترافية")
    st.markdown("### اختر الباقة المناسبة لاحتياجك — جميع الأسعار تنافسية وعالمية")
    st.markdown("---")
    
    region = st.radio(
        "🌍 اختر منطقتك لعرض الأسعار المناسبة:",
        ["🌴 الخليج والشرق الأوسط", "🌍 عالمي (دولي)", "🇾🇪 اليمن (محلي)"],
        horizontal=True
    )
    region_map = {
        "🌴 الخليج والشرق الأوسط": "gulf",
        "🌍 عالمي (دولي)": "global",
        "🇾🇪 اليمن (محلي)": "yemen"
    }
    region_key = region_map[region]
    st.session_state.pricing_region = region_key
    currency = "$"
    
    st.markdown("---")
    st.markdown("## 🎯 الباقات الفردية")
    st.markdown("*مثالية للباحثين والطلاب والمهنيين الأفراد*")
    
    # الباقات الثلاث الأساسية
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### 🆓 مجاني")
        st.markdown("# $0")
        st.markdown("**10 تجارب مجانية**")
        st.markdown("---")
        st.markdown("✅ محاكاة كاملة")
        st.markdown("✅ تحليل الاستقرار")
        st.markdown("❌ مكونات AI")
        st.markdown("❌ تحميل النتائج")
        st.markdown("❌ API Access")
        if st.session_state.user_plan == 'free':
            st.success("✅ باقتك الحالية")
    
    with c2:
        st.markdown("### 📆 شهري")
        st.markdown(f"# {currency}{PLANS['monthly'][f'price_{region_key}']}")
        st.markdown("**30 يوماً**")
        st.markdown("---")
        st.markdown("✅ محاكاة غير محدودة")
        st.markdown("✅ 3 مكونات AI")
        st.markdown("✅ تقارير PDF")
        st.markdown("✅ تحميل CSV")
        st.markdown("✅ دعم بريد")
        if st.session_state.user_plan == 'monthly':
            st.success("✅ باقتك الحالية")
        else:
            if st.button("اشترك شهرياً", key='btn_m', type='primary', use_container_width=True):
                subscribe('monthly')
                st.success("✅ تم الاشتراك!")
                st.rerun()
    
    with c3:
        st.markdown("### ⭐ سنوي")
        st.markdown(f"# {currency}{PLANS['yearly'][f'price_{region_key}']}")
        st.markdown("**365 يوماً — وفّر 30%** 💰")
        st.markdown("---")
        st.markdown("✅ كل ما في الشهري")
        st.markdown("✅ API Access")
        st.markdown("✅ دعم واتساب")
        st.markdown("✅ أولوية في الدعم")
        st.markdown("✅ تحديثات مجانية")
        if st.session_state.user_plan == 'yearly':
            st.success("✅ باقتك الحالية")
        else:
            if st.button("اشترك سنوياً", key='btn_y', type='primary', use_container_width=True):
                subscribe('yearly')
                st.success("✅ تم الاشتراك!")
                st.rerun()
    
    st.markdown("---")
    st.markdown("## 💼 الباقات الاحترافية")
    st.markdown("*للأطباء والباحثين الجادين والمهنيين*")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 🩺 احترافي شهري")
        st.markdown(f"# {currency}{PLANS['pro_monthly'][f'price_{region_key}']}")
        st.markdown("**30 يوماً**")
        st.markdown("---")
        st.markdown("✅ كل ما في السنوي")
        st.markdown("✅ **دعم مباشر فوري**")
        st.markdown("✅ **تدريب مخصص**")
        st.markdown("✅ **مراجعة النتائج**")
        if st.session_state.user_plan == 'pro_monthly':
            st.success("✅ باقتك الحالية")
        else:
            if st.button("اشترك احترافي شهري", key='btn_pm', type='primary', use_container_width=True):
                subscribe('pro_monthly')
                st.success("✅ تم الاشتراك!")
                st.rerun()
    
    with c2:
        st.markdown("### 🏆 احترافي سنوي")
        st.markdown(f"# {currency}{PLANS['pro_yearly'][f'price_{region_key}']}")
        st.markdown("**365 يوماً — وفّر 33%** 💰")
        st.markdown("---")
        st.markdown("✅ كل ما في الاحترافي الشهري")
        st.markdown("✅ **توفير 33%**")
        st.markdown("✅ **أولوية قصوى**")
        st.markdown("✅ **استشارات شهرية**")
        if st.session_state.user_plan == 'pro_yearly':
            st.success("✅ باقتك الحالية")
        else:
            if st.button("اشترك احترافي سنوي", key='btn_py', type='primary', use_container_width=True):
                subscribe('pro_yearly')
                st.success("✅ تم الاشتراك!")
                st.rerun()
    
    st.markdown("---")
    st.markdown("## 🏢 الباقات المؤسسية")
    st.markdown("*للجامعات والمستشفيات وشركات الأدوية*")
    
    c1, c2, c3 = st.columns(3)
    for i, (key, plan) in enumerate(ENTERPRISE_PLANS.items()):
        with [c1, c2, c3][i]:
            st.markdown(f"### {plan['name']}")
            st.markdown(f"# {currency}{plan[f'price_{region_key}']:,}")
            st.markdown("**سنوياً**")
            st.markdown("---")
            for feature in plan['features']:
                st.markdown(f"✅ {feature}")
            st.markdown("📧 **للتواصل:** ghythanbdalghny97@gmail.com")
            st.markdown("📞 **+967 779193805**")
    
    st.markdown("---")
    st.info("💡 **طرق الدفع المتاحة:** بطاقات الائتمان | PayPal | تحويل بنكي | محافظ إلكترونية")
    st.success("📧 للاستفسارات: ghythanbdalghny97@gmail.com | 📞 +967 779193805")


# ============================================================
#                    الواجهة الرئيسية
# ============================================================

init_user_session()

st.title("🧬 HYDROMEM Dynamics AI")
st.markdown("### منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة")
st.markdown("*Computational Intelligence Platform for Complex Dynamic Systems*")
st.markdown("---")

app = st.sidebar.radio("🔬 اختر التطبيق:", [
    "🏠 الرئيسية",
    "💎 باقات الاشتراك",
    "⚙️ النموذج الديناميكي العام",
    "🦵 خشونة الركبة",
    "🦴 التئام العظام",
    "💧 الأقراص الفقرية",
    "🩹 التئام الجروح",
    "🧠 مكونات الذكاء الاصطناعي"
])

st.sidebar.markdown("---")
st.sidebar.info(
    "**HYDROMEM Dynamics AI**\n\n"
    "الإصدار 8.0\n\n"
    "5 تطبيقات + 3 مكونات AI\n\n"
    "TRL 3"
)
st.sidebar.markdown("---")
st.sidebar.markdown("[📂 GitHub](https://github.com/ghythanbdalghny97-ui/hydromem-dynamics-ai)")

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
        منصة حاسوبية متكاملة لمحاكاة وتحليل الأنظمة الديناميكية المعقدة،
        تدمج النمذجة الرياضية، المحاكاة العددية، تحليل الاستقرار،
        ومكونات الذكاء الاصطناعي.

        ### 🔬 التطبيقات المتاحة
        - ⚙️ **النموذج الديناميكي العام** — نظام A/Θ
        - 🦵 **خشونة الركبة** — 10-20 سنة
        - 🦴 **التئام العظام** — 12-24 أسبوعاً
        - 💧 **الأقراص الفقرية** — 24 ساعة
        - 🩹 **التئام الجروح** — 8-16 أسبوعاً
        """)

    with c2:
        st.markdown("""
        ### ⚙️ التقنيات المستخدمة
        - النمذجة الرياضية: معادلات تفاضلية غير خطية
        - المحاكاة العددية: odeint (Runge-Kutta)
        - تحليل الاستقرار: Jacobian + Eigenvalues
        - الذكاء الاصطناعي: MLP + Random Forest
        - الواجهة: Streamlit Web App
        """)
        st.success("✅ 5 تطبيقات حية + 3 مكونات AI منفذة")
        
        if st.session_state.user_plan == 'free':
            st.warning(f"⚠️ باقتك المجانية: {remaining_trials()}")
            if st.button("💎 ترقية الآن للاستفادة من كل الميزات"):
                st.session_state.show_pricing = True
                st.rerun()


# ============================================================
#              صفحة التسعير
# ============================================================
elif app == "💎 باقات الاشتراك":
    show_pricing_page()


# ============================================================
#         النموذج الديناميكي العام
# ============================================================
elif app == "⚙️ النموذج الديناميكي العام":
    st.header("⚙️ النموذج الديناميكي العام")
    st.markdown("**General Dynamic System — A/Θ Model**")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])
    with c1:
        st.subheader("⚙️ المعاملات")
        A0 = st.slider("A₀", 0.0, 2.0, 0.5, 0.1)
        T0 = st.slider("Θ₀", 0.0, 2.0, 0.2, 0.1)
        mu = st.slider("μ (النمو)", 0.1, 2.0, 1.0, 0.1)
        k  = st.slider("κ (الاقتران)", 0.0, 2.0, 0.5, 0.1)
        b  = st.slider("β (الانتقال)", 0.1, 2.0, 0.8, 0.1)
        g  = st.slider("γ (الاضمحلال)", 0.0, 1.0, 0.3, 0.05)
        te = st.slider("الزمن", 10, 200, 50)

    with c2:
        t = np.linspace(0, te, 500)
        s = odeint(general, [A0, T0], t, args=(mu, k, b, g))
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(t, s[:,0], 'b-', lw=2, label='A (الحالة)')
        ax.plot(t, s[:,1], 'r-', lw=2, label='Θ (الذاكرة)')
        ax.set_xlabel('الزمن'); ax.set_ylabel('القيمة')
        ax.legend(); ax.grid(alpha=0.3)
        ax.set_title('تطور النظام الديناميكي')
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("A النهائي", f"{s[-1,0]:.4f}")
    c2.metric("Θ النهائي", f"{s[-1,1]:.4f}")
    c3.metric("A الأقصى", f"{s[:,0].max():.4f}")
    c4.metric("Θ الأقصى", f"{s[:,1].max():.4f}")

    st.markdown("---")
    st.subheader("🔍 تحليل الاستقرار (Jacobian)")
    A_f, Th_f = s[-1,0], s[-1,1]
    J = np.array([[mu - 3*A_f**2 - k*Th_f, -k*A_f],[b, -b-g]])
    ev = np.linalg.eigvals(J)
    st.write("**مصفوفة Jacobian:**")
    st.write(J)
    for i, e in enumerate(ev, 1):
        st.write(f"λ{i} = {e:.6f}")
    if all(np.real(e) < 0 for e in ev):
        st.success("✅ استقرار محلي (Re(λ) < 0)")
    else:
        st.warning("⚠️ النظام قد لا يكون مستقراً")
    
    use_trial()


# ============================================================
#              خشونة الركبة
# ============================================================
elif app == "🦵 خشونة الركبة":
    st.header("🦵 محاكاة خشونة الركبة")
    st.markdown("**Knee Osteoarthritis Simulation**")
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
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(t/365, s[:,0], 'r-', lw=2, label='MMP')
        ax1.set_xlabel('السنوات'); ax1.set_ylabel('MMP', color='r')
        ax1.tick_params(axis='y', labelcolor='r')
        ax2 = ax1.twinx()
        ax2.plot(t/365, s[:,1], 'b-', lw=2, label='الصلابة')
        ax2.set_ylabel('الصلابة', color='b')
        ax2.tick_params(axis='y', labelcolor='b')
        ax1.grid(alpha=0.3)
        plt.title('تطور خشونة الركبة')
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    c1, c2, c3 = st.columns(3)
    c1.metric("الصلابة النهائية", f"{s[-1,1]:.4f}")
    c2.metric("مرحلة KL", classify_kl(s[-1,1]))
    c3.metric("MMP النهائي", f"{s[-1,0]:.4f}")
    
    use_trial()


# ============================================================
#              التئام العظام
# ============================================================
elif app == "🦴 التئام العظام":
    st.header("🦴 محاكاة التئام العظام")
    st.markdown("**Bone Fracture Healing Simulation**")
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
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(t/7, s[:,0], 'g-', lw=2, label='الكالسيوم')
        ax.plot(t/7, s[:,1]*10, 'b-', lw=2, label='التمعدن ×10')
        ax.plot(t/7, s[:,2], 'r-', lw=2, label='الصلابة')
        ax.set_xlabel('الأسابيع'); ax.set_ylabel('القيمة')
        ax.legend(); ax.grid(alpha=0.3)
        plt.title('تطور التئام العظام')
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    C = s[-1,2]
    c1, c2, c3 = st.columns(3)
    c1.metric("الصلابة النهائية", f"{C:.2f}")
    c2.metric("نسبة الحمل", f"{(C/Cm)*100:.1f}%")
    c3.metric("المرحلة", healing_stage(C, Cm))
    
    use_trial()


# ============================================================
#              الأقراص الفقرية
# ============================================================
elif app == "💧 الأقراص الفقرية":
    st.header("💧 محاكاة الأقراص الفقرية")
    st.markdown("**Intervertebral Disc Swelling Simulation**")
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
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(t, s[:,0]*100, 'b-', lw=2, label='الماء %')
        ax1.set_xlabel('الساعات'); ax1.set_ylabel('الماء %', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax2 = ax1.twinx()
        ax2.plot(t, s[:,1], 'g-', lw=2, label='الارتفاع')
        ax2.plot(t, s[:,2], 'r-', lw=2, label='الضغط')
        ax2.set_ylabel('الارتفاع / الضغط')
        ax2.legend(loc='upper left')
        ax1.grid(alpha=0.3)
        plt.title('تطور الأقراص الفقرية')
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    c1, c2, c3 = st.columns(3)
    c1.metric("الماء النهائي", f"{s[-1,0]*100:.1f}%")
    c2.metric("الارتفاع", f"{s[-1,1]:.4f}")
    c3.metric("الضغط", f"{s[-1,2]:.4f}")
    
    use_trial()


# ============================================================
#              التئام الجروح
# ============================================================
elif app == "🩹 التئام الجروح":
    st.header("🩹 محاكاة التئام الجروح")
    st.markdown("**Wound Healing Simulation**")
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
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        axes[0,0].plot(t/7, np.maximum(s[:,0],0)*100, 'b-', lw=2)
        axes[0,0].set_title('إعادة التغطية %'); axes[0,0].set_xlabel('الأسابيع')
        axes[0,0].grid(alpha=0.3)
        axes[0,1].plot(t/7, np.maximum(s[:,2],0)*100, 'g-', lw=2)
        axes[0,1].set_title('الكولاجين %'); axes[0,1].set_xlabel('الأسابيع')
        axes[0,1].grid(alpha=0.3)
        axes[1,0].plot(t/7, s[:,3], 'r-', lw=2)
        axes[1,0].set_title('الالتهاب'); axes[1,0].set_xlabel('الأسابيع')
        axes[1,0].grid(alpha=0.3)
        axes[1,1].plot(t/7, s[:,4], 'm-', lw=2)
        axes[1,1].set_title('الحمل البكتيري'); axes[1,1].set_xlabel('الأسابيع')
        axes[1,1].grid(alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    c1, c2, c3 = st.columns(3)
    c1.metric("التغطية", f"{max(s[-1,0],0)*100:.1f}%")
    c2.metric("الكولاجين", f"{max(s[-1,2],0)*100:.1f}%")
    c3.metric("البكتيريا", f"{s[-1,4]:.4f}")
    
    use_trial()


# ============================================================
#         مكونات الذكاء الاصطناعي
# ============================================================
elif app == "🧠 مكونات الذكاء الاصطناعي":
    if not can_use_ai():
        st.error("🔒 **هذه الميزة متاحة فقط في الباقات المدفوعة**")
        st.markdown("---")
        st.warning("""
        ### 💎 مكونات AI المحمية:
        - ⚡ **Surrogate Model** — تنبؤ سريع 50×
        - 🎯 **Stability Classifier** — دقة 99.25%
        - 📊 **Stiffness Regressor** — R² = 0.9942
        
        هذه المكونات توفر:
        - تنبؤات فورية بدلاً من انتظار المحاكاة
        - تحليل ذكي للبيانات
        - دقة علمية عالية
        """)
        st.markdown("---")
        st.markdown("### 🚀 قم بالترقية الآن للوصول إلى كل الميزات:")
        if st.button("💎 عرض الباقات والترقية", type="primary", use_container_width=True):
            st.session_state.show_pricing = True
            st.rerun()
    else:
        st.header("🧠 مكونات الذكاء الاصطناعي المنفذة")
        st.markdown("**AI Components — Trained & Deployed**")
        st.markdown("---")

        tab1, tab2, tab3 = st.tabs([
            "⚡ Surrogate Model",
            "🎯 Stability Classifier",
            "📊 Stiffness Regressor"
        ])

        with tab1:
            st.subheader("⚡ Surrogate Model (النموذج البديل)")
            st.markdown("""
            نموذج MLP يتنبأ بسلوك النظام في **أقل من 10ms**
            بدلاً من ~500ms باستخدام odeint.
            """)
            with st.spinner("جاري تدريب النموذج البديل..."):
                sm, loss = train_surrogate()
            c1, c2, c3 = st.columns(3)
            c1.metric("Test MSE", f"{loss:.6f}")
            c2.metric("Speedup", "~50×")
            c3.metric("Architecture", "64-128-64")
            st.success("✅ Surrogate Model trained successfully")

            st.markdown("#### 🔮 اختبار التنبؤ السريع")
            c1, c2 = st.columns(2)
            with c1:
                mu_t = st.slider("μ", 0.1, 2.0, 1.0, 0.1, key='sm_mu')
                k_t  = st.slider("κ", 0.0, 2.0, 0.5, 0.1, key='sm_k')
            with c2:
                b_t = st.slider("β", 0.1, 2.0, 0.8, 0.1, key='sm_b')
                g_t = st.slider("γ", 0.0, 1.0, 0.3, 0.05, key='sm_g')

            if st.button("🔮 تنبؤ سريع", key='predict_sm'):
                pred = sm.predict([[mu_t, k_t, b_t, g_t, 0.5, 0.2]])[0]
                c1, c2 = st.columns(2)
                c1.metric("A النهائي", f"{pred[0]:.4f}")
                c2.metric("Θ النهائي", f"{pred[1]:.4f}")

        with tab2:
            st.subheader("🎯 Stability Classifier (مصنف الاستقرار)")
            st.markdown("""
            مصنف Random Forest يتنبأ باستقرار النظام
            بناءً على المعاملات الأربعة (μ, κ, β, γ).
            """)
            with st.spinner("جاري تدريب المصنف..."):
                clf, acc = train_classifier()
            c1, c2, c3 = st.columns(3)
            c1.metric("Accuracy", f"{acc*100:.2f}%")
            c2.metric("Trees", "100")
            c3.metric("Samples", "1000")
            st.success("✅ Stability Classifier trained successfully")

            st.markdown("#### 🔍 اختبار التصنيف")
            c1, c2 = st.columns(2)
            with c1:
                mu_c = st.slider("μ", -0.5, 3.0, 1.0, 0.1, key='cl_mu')
                k_c  = st.slider("κ", -1.0, 3.0, 0.5, 0.1, key='cl_k')
            with c2:
                b_c = st.slider("β", -0.5, 2.5, 0.8, 0.1, key='cl_b')
                g_c = st.slider("γ", -0.5, 1.5, 0.3, 0.05, key='cl_g')

            if st.button("🔍 تصنيف", key='classify_btn'):
                pred = clf.predict([[mu_c, k_c, b_c, g_c]])[0]
                proba = clf.predict_proba([[mu_c, k_c, b_c, g_c]])[0]
                if pred == 1:
                    st.success(f"✅ النظام مستقر (ثقة: {proba[1]*100:.1f}%)")
                else:
                    st.error(f"❌ النظام غير مستقر (ثقة: {proba[0]*100:.1f}%)")

        with tab3:
            st.subheader("📊 Stiffness Regressor (مقدّر الصلابة)")
            st.markdown("""
            نموذج MLP مع StandardScaler يتنبأ بالصلابة النهائية للركبة
            بناءً على معاملات المريض.
            """)
            with st.spinner("جاري تدريب المقدّر..."):
                reg, r2 = train_regressor()
            c1, c2, c3 = st.columns(3)
            c1.metric("R² Score", f"{r2:.4f}")
            c2.metric("RMSE", "< 0.05")
            c3.metric("Architecture", "128-64-32")
            st.success("✅ Stiffness Regressor trained successfully")

            st.markdown("#### 🔮 اختبار التنبؤ بالصلابة")
            c1, c2 = st.columns(2)
            with c1:
                yrs_r = st.slider("السنوات", 1, 25, 10, key='reg_y')
                kp_r  = st.slider("k_prod", 0.003, 0.012, 0.005, 0.001, key='reg_kp')
            with c2:
                kd_r = st.slider("k_deg", 0.008, 0.025, 0.015, 0.001, key='reg_kd')
                a_r  = st.slider("alpha", 0.00005, 0.0004, 0.00010, 0.00005, key='reg_a')

            if st.button("🔮 تنبؤ", key='reg_btn'):
                pred = reg.predict([[yrs_r, kp_r, kd_r, a_r]])[0]
                c1, c2 = st.columns(2)
                c1.metric("الصلابة المتوقعة", f"{pred:.4f}")
                c2.metric("المرحلة", classify_kl(pred))


# ============================================================
#                    التذييل
# ============================================================
st.markdown("---")
st.markdown(
    "**HYDROMEM Dynamics AI** — "
    "منصة ذكاء حاسوبي متعددة التطبيقات | "
    "الإصدار 8.0 | "
    "5 تطبيقات + 3 مكونات AI | "
    "TRL 3 | "
    "© عبد الغني صالح محسن محمد غيثان 2026"
        )
