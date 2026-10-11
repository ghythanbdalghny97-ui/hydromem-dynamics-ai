"""
HYDROMEM Dynamics AI
منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة
Computational Intelligence Platform for Complex Dynamic Systems

Version 6.0 — Five-Application Platform
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# ==================== إعدادات الصفحة ====================
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


# ====================================================
#                    النماذج الرياضية
# ====================================================

# ---------- 0. النموذج الديناميكي العام ----------
def general_model(y, t, mu, kappa, beta, gamma):
    A, Theta = y
    dA = mu * A - A**3 - kappa * Theta * A
    dTheta = beta * (A - Theta) - gamma * Theta
    return [dA, dTheta]

def simulate_general(A0, Theta0, mu, kappa, beta, gamma, t_end):
    t = np.linspace(0, t_end, 1000)
    sol = odeint(general_model, [A0, Theta0], t, args=(mu, kappa, beta, gamma))
    return t, sol[:, 0], sol[:, 1]

def stability_analysis(A, Theta, mu, kappa, beta, gamma):
    J11 = mu - 3*A**2 - kappa*Theta
    J12 = -kappa*A
    J21 = beta
    J22 = -beta - gamma
    J = np.array([[J11, J12], [J21, J22]])
    eigvals = np.linalg.eigvals(J)
    return J, eigvals


# ---------- 1. خشونة الركبة ----------
def cartilage_model(y, t, k_prod, k_deg, alpha, mmp_sat):
    c, m = y
    dc = k_prod - k_deg * c
    dm = -alpha * (c / mmp_sat) * m
    return [dc, dm]

def simulate_cartilage(years, k_prod, k_deg, alpha, mmp_sat):
    t = np.linspace(0, years * 365, 1000)
    sol = odeint(cartilage_model, [0.0, 1.0], t,
                 args=(k_prod, k_deg, alpha, mmp_sat))
    return t, sol[:, 0], sol[:, 1]

def classify_kl(m):
    if m > 0.95: return "Healthy (سليم)"
    elif m > 0.85: return "KL-1 (مشكوك)"
    elif m > 0.70: return "KL-2 (خفيف)"
    elif m > 0.50: return "KL-3 (متوسط)"
    else: return "KL-4 (شديد)"


# ---------- 2. التئام العظام ----------
def bone_model(y, t, k_min, mu_min, C_max):
    Ca, m, C = y
    dCa = 0.5 * (1 - Ca / 5.0)
    dm = k_min * max(mu_min - 1, 0) * (1 - m)
    dC = 0.5 * (C_max * (m ** 1.5) - C)
    return [dCa, dm, dC]

def simulate_bone(weeks, k_min, mu_min, C_max):
    t = np.linspace(0, weeks * 7, 500)
    sol = odeint(bone_model, [0.0, 0.0, 0.0], t,
                 args=(k_min, mu_min, C_max))
    return t, sol[:, 0], sol[:, 1], sol[:, 2]

def healing_stage(C, C_max):
    r = C / C_max
    if r < 0.1: return "Inflammation (التهاب)"
    elif r < 0.4: return "Soft Callus (دشبذ رخو)"
    elif r < 0.8: return "Hard Callus (دشبذ صلب)"
    else: return "Remodeling (إعادة تشكيل)"


# ---------- 3. الأقراص الفقرية ----------
def disc_model(y, t, k_swell, k_deg, P_load):
    w, h, P = y
    dw = k_swell * (1 - w) - k_deg * w * P_load
    dh = 0.05 * (w - 0.5) * (1.5 - h)
    dP = 0.3 * (w - 0.6) - 0.1 * P
    return [dw, dh, dP]

def simulate_disc(hours, k_swell, k_deg, P_load):
    t = np.linspace(0, hours, 500)
    sol = odeint(disc_model, [0.5, 1.0, 0.3], t,
                 args=(k_swell, k_deg, P_load))
    return t, sol[:, 0], sol[:, 1], sol[:, 2]


# ---------- 4. التئام الجروح ----------
def wound_model(y, t, p):
    E, F, C, I, B, MMP = y
    dE = p['k_e']*E*(1 - E/p['E_max']) - p['k_a']*E*I
    dF = p['k_f']*F*(1 - F/p['F_max']) - p['k_d']*F*I
    dC = p['k_c']*F*(1 - C/p['C_max']) - p['k_r']*C*MMP
    dI = p['k_i']*B - p['k_ii']*I
    dB = p['k_b']*(p['B_max'] - B) - p['k_bb']*B*E
    dMMP = p['k_m']*I - p['k_mm']*MMP*p['TIMP']
    return [dE, dF, dC, dI, dB, dMMP]

def simulate_wound(weeks):
    t = np.linspace(0, weeks * 7, 1000)
    y0 = [0.01, 0.01, 0.0, 0.95, 0.3, 0.1]
    p = {'k_e':0.8,'E_max':1.0,'k_a':0.5,'k_f':0.6,'F_max':1.0,
         'k_d':0.3,'k_c':0.7,'C_max':1.0,'k_r':0.4,'k_i':0.5,
         'k_ii':0.3,'k_b':0.2,'B_max':1.0,'k_bb':0.6,'k_m':0.4,
         'k_mm':0.5,'TIMP':0.8}
    sol = odeint(wound_model, y0, t, args=(p,))
    return t, sol[:,0], sol[:,1], sol[:,2], sol[:,3], sol[:,4], sol[:,5]


# ====================================================
#                    الواجهة
# ====================================================

st.title("🧬 HYDROMEM Dynamics AI")
st.markdown("### منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة")
st.markdown("*Computational Intelligence Platform for Complex Dynamic Systems*")
st.markdown("---")

app = st.sidebar.radio("🔬 اختر التطبيق:", [
    "🏠 الرئيسية",
    "⚙️ النموذج الديناميكي العام",
    "🦵 خشونة الركبة",
    "🦴 التئام العظام",
    "💧 الأقراص الفقرية",
    "🩹 التئام الجروح"
])

st.sidebar.markdown("---")
st.sidebar.info(
    "**HYDROMEM Dynamics AI**\n\n"
    "الإصدار 6.0\n\n"
    "Computational Prototype — TRL 3"
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "[📂 GitHub](https://github.com/ghythanbdalghny97-ui/hydromem-dynamics-ai)"
)


# ====================================================
#                   الصفحة الرئيسية
# ====================================================
if app == "🏠 الرئيسية":
    st.header("مرحباً بكم في HYDROMEM Dynamics AI")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        ### 🎯 الرؤية
        منصة حاسوبية متكاملة لمحاكاة وتحليل الأنظمة الديناميكية
        المعقدة، تدمج النمذجة الرياضية، المحاكاة العددية،
        تحليل الاستقرار، ومكونات الذكاء الاصطناعي.

        ### 🔬 التطبيقات المتاحة
        - ⚙️ **النموذج الديناميكي العام** — نظام A/Θ
        - 🦵 **خشونة الركبة** — محاكاة 10 سنوات
        - 🦴 **التئام العظام** — محاكاة 16 أسبوعاً
        - 💧 **الأقراص الفقرية** — محاكاة 24 ساعة
        - 🩹 **التئام الجروح** — محاكاة 12 أسبوعاً
        """)

    with c2:
        st.markdown("""
        ### ⚙️ التقنيات المستخدمة
        - **النمذجة الرياضية**: معادلات تفاضلية غير خطية
        - **المحاكاة العددية**: odeint (Runge-Kutta)
        - **تحليل الاستقرار**: Jacobian + Eigenvalues
        - **الذكاء الاصطناعي**: MLP + Random Forest
        - **الواجهة**: Streamlit Web App
        """)
        st.success("✅ 5 تطبيقات حية جاهزة للاستخدام")


# ====================================================
#         النموذج الديناميكي العام
# ====================================================
elif app == "⚙️ النموذج الديناميكي العام":
    st.header("⚙️ النموذج الديناميكي العام")
    st.markdown("**General Dynamic System — A/Θ Model**")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])

    with c1:
        st.subheader("⚙️ المعاملات")
        A0 = st.slider("A₀ (الحالة الابتدائية)", 0.0, 2.0, 0.5, 0.1)
        Theta0 = st.slider("Θ₀ (الذاكرة الابتدائية)", 0.0, 2.0, 0.2, 0.1)
        mu = st.slider("μ (معامل النمو)", 0.1, 2.0, 1.0, 0.1)
        kappa = st.slider("κ (الاقتران)", 0.0, 2.0, 0.5, 0.1)
        beta = st.slider("β (الانتقال للذاكرة)", 0.1, 2.0, 0.8, 0.1)
        gamma = st.slider("γ (الاضمحلال)", 0.0, 1.0, 0.3, 0.05)
        t_end = st.slider("زمن المحاكاة", 10, 200, 50)

    with c2:
        t, A, Theta = simulate_general(A0, Theta0, mu, kappa, beta, gamma, t_end)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(t, A, 'b-', linewidth=2, label='A (الحالة)')
        ax.plot(t, Theta, 'r-', linewidth=2, label='Θ (الذاكرة)')
        ax.set_xlabel('الزمن')
        ax.set_ylabel('القيمة')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.title('تطور النظام الديناميكي')
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("A النهائي", f"{A[-1]:.4f}")
    c2.metric("Θ النهائي", f"{Theta[-1]:.4f}")
    c3.metric("A الأقصى", f"{A.max():.4f}")
    c4.metric("Θ الأقصى", f"{Theta.max():.4f}")

    st.markdown("---")
    st.subheader("🔍 تحليل الاستقرار (Jacobian)")
    J, eigvals = stability_analysis(A[-1], Theta[-1], mu, kappa, beta, gamma)
    st.write("**مصفوفة Jacobian عند الحالة النهائية:**")
    st.write(J)
    st.write("**القيم الذاتية:**")
    for i, ev in enumerate(eigvals, 1):
        st.write(f"λ{i} = {ev:.6f}")
    if all(np.real(ev) < 0 for ev in eigvals):
        st.success("✅ استقرار محلي (Re(λ) < 0 لجميع القيم)")
    else:
        st.warning("⚠️ النظام قد لا يكون مستقراً")


# ====================================================
#              خشونة الركبة
# ====================================================
elif app == "🦵 خشونة الركبة":
    st.header("🦵 محاكاة خشونة الركبة")
    st.markdown("**Knee Osteoarthritis Simulation**")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])

    with c1:
        st.subheader("⚙️ المعاملات")
        years = st.slider("عدد السنوات", 1, 20, 10)
        k_prod = st.slider("معدل إنتاج MMP", 0.005, 0.05, 0.02, 0.001)
        k_deg = st.slider("معدل التحلل", 0.005, 0.03, 0.01, 0.001)
        alpha = st.slider("معامل التلف", 0.01, 0.15, 0.05, 0.01)

    with c2:
        t, c, m = simulate_cartilage(years, k_prod, k_deg, alpha, 0.5)

        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(t/365, c, 'r-', linewidth=2, label='MMP (إنزيم التلف)')
        ax1.set_xlabel('السنوات')
        ax1.set_ylabel('تركيز MMP', color='r')
        ax1.tick_params(axis='y', labelcolor='r')

        ax2 = ax1.twinx()
        ax2.plot(t/365, m, 'b-', linewidth=2, label='الصلابة')
        ax2.set_ylabel('نسبة الصلابة', color='b')
        ax2.tick_params(axis='y', labelcolor='b')

        plt.title('تطور خشونة الركبة على مدى السنوات')
        plt.grid(True, alpha=0.3)
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    c1, c2, c3 = st.columns(3)
    c1.metric("الصلابة النهائية", f"{m[-1]:.4f}")
    c2.metric("مرحلة KL", classify_kl(m[-1]))
    c3.metric("MMP النهائي", f"{c[-1]:.4f}")


# ====================================================
#              التئام العظام
# ====================================================
elif app == "🦴 التئام العظام":
    st.header("🦴 محاكاة التئام العظام")
    st.markdown("**Bone Fracture Healing Simulation**")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])

    with c1:
        st.subheader("⚙️ المعاملات")
        weeks = st.slider("عدد الأسابيع", 4, 24, 16)
        k_min = st.slider("معدل التمعدن", 0.1, 0.5, 0.3, 0.05)
        mu_min = st.slider("معامل النمو", 1.5, 3.0, 2.0, 0.1)
        C_max = st.slider("الصلابة القصوى", 10.0, 30.0, 20.0, 1.0)

    with c2:
        t, Ca, m, C = simulate_bone(weeks, k_min, mu_min, C_max)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(t/7, Ca, 'g-', linewidth=2, label='الكالسيوم')
        ax.plot(t/7, m, 'b-', linewidth=2, label='التمعدن')
        ax.plot(t/7, C, 'r-', linewidth=2, label='الصلابة')
        ax.set_xlabel('الأسابيع')
        ax.set_ylabel('القيمة')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.title('تطور التئام العظام')
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    c1, c2, c3 = st.columns(3)
    c1.metric("الصلابة النهائية", f"{C[-1]:.2f}")
    c2.metric("نسبة الحمل", f"{(C[-1]/C_max)*100:.1f}%")
    c3.metric("المرحلة", healing_stage(C[-1], C_max))


# ====================================================
#              الأقراص الفقرية
# ====================================================
elif app == "💧 الأقراص الفقرية":
    st.header("💧 محاكاة الأقراص الفقرية")
    st.markdown("**Intervertebral Disc Swelling Simulation**")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])

    with c1:
        st.subheader("⚙️ المعاملات")
        hours = st.slider("عدد الساعات", 6, 48, 24)
        k_swell = st.slider("معدل الانتفاخ", 0.05, 0.2, 0.1, 0.01)
        k_deg = st.slider("معدل التحلل", 0.02, 0.1, 0.05, 0.01)
        P_load = st.slider("الحمل", 0.2, 1.0, 0.5, 0.1)

    with c2:
        t, w, h, P = simulate_disc(hours, k_swell, k_deg, P_load)

        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(t, w*100, 'b-', linewidth=2, label='الماء %')
        ax1.set_xlabel('الساعات')
        ax1.set_ylabel('الماء %', color='b')
        ax1.tick_params(axis='y', labelcolor='b')

        ax2 = ax1.twinx()
        ax2.plot(t, h, 'g-', linewidth=2, label='الارتفاع')
        ax2.plot(t, P, 'r-', linewidth=2, label='الضغط')
        ax2.set_ylabel('الارتفاع / الضغط')
        ax2.legend(loc='upper left')

        plt.title('تطور الأقراص الفقرية')
        plt.grid(True, alpha=0.3)
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    c1, c2, c3 = st.columns(3)
    c1.metric("الماء النهائي", f"{w[-1]*100:.1f}%")
    c2.metric("الارتفاع النهائي", f"{h[-1]:.4f}")
    c3.metric("الضغط النهائي", f"{P[-1]:.4f}")


# ====================================================
#              التئام الجروح
# ====================================================
elif app == "🩹 التئام الجروح":
    st.header("🩹 محاكاة التئام الجروح")
    st.markdown("**Wound Healing Simulation**")
    st.markdown("---")

    c1, c2 = st.columns([1, 3])

    with c1:
        st.subheader("⚙️ المعاملات")
        weeks = st.slider("عدد الأسابيع", 4, 16, 12)
        st.markdown("""
        **المتغيرات:**
        - **E**: الخلايا الظهارية
        - **F**: الخلايا الليفية
        - **C**: الكولاجين
        - **I**: الالتهاب
        - **B**: الحمل البكتيري
        - **MMP**: الإنزيمات المحللة
        """)

    with c2:
        t, E, F, C, I, B, MMP = simulate_wound(weeks)

        fig, axes = plt.subplots(2, 2, figsize=(12, 8))

        axes[0, 0].plot(t/7, E*100, 'b-', linewidth=2)
        axes[0, 0].set_title('إعادة التغطية %')
        axes[0, 0].set_xlabel('الأسابيع')
        axes[0, 0].grid(True, alpha=0.3)

        axes[0, 1].plot(t/7, C*100, 'g-', linewidth=2)
        axes[0, 1].set_title('الكولاجين %')
        axes[0, 1].set_xlabel('الأسابيع')
        axes[0, 1].grid(True, alpha=0.3)

        axes[1, 0].plot(t/7, I, 'r-', linewidth=2)
        axes[1, 0].set_title('الالتهاب')
        axes[1, 0].set_xlabel('الأسابيع')
        axes[1, 0].grid(True, alpha=0.3)

        axes[1, 1].plot(t/7, B, 'm-', linewidth=2)
        axes[1, 1].set_title('الحمل البكتيري')
        axes[1, 1].set_xlabel('الأسابيع')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("---")
    st.subheader("📊 النتائج")
    c1, c2, c3 = st.columns(3)
    c1.metric("التغطية النهائية", f"{E[-1]*100:.1f}%")
    c2.metric("الكولاجين النهائي", f"{C[-1]*100:.1f}%")
    c3.metric("الحمل البكتيري", f"{B[-1]:.4f}")


# ====================================================
#                    التذييل
# ====================================================
st.markdown("---")
st.markdown(
    "**HYDROMEM Dynamics AI** — "
    "منصة ذكاء حاسوبي متعددة التطبيقات | "
    "الإصدار 6.0 | "
    "TRL 3 | "
    "© عبد الغني غيثان 2026"
)
