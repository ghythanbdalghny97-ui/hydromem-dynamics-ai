import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import config

def hydromem_model(t, y, r, beta, gamma, eta, tau, mu):
    A, Theta = y
    dA = r*A - beta*A**3 - gamma*A*Theta
    dTheta = (1/tau) * (eta*A**2*(1+mu*Theta) - Theta)
    return [dA, dTheta]

def render():
    st.title("🔬 HYDROMEM Dynamic Simulation")
    st.info("نموذج ديناميكي تجريبي لدراسة التفاعل بين المتغير البنيوي A ومتغير الذاكرة Θ.")
    
    # جلب الباقة الحالية للتحقق من الصلاحيات
    user = st.session_state.user
    plan_info = config.PLANS.get(user.get("plan", "individual"), config.PLANS["individual"])

    st.sidebar.header("⚙️ معاملات النموذج")
    r = st.sidebar.slider("r", -2.0, 3.0, 1.0, 0.1)
    beta = st.sidebar.slider("β", 0.1, 3.0, 1.0, 0.1)
    gamma = st.sidebar.slider("γ", 0.0, 3.0, 0.5, 0.1)
    eta = st.sidebar.slider("η", 0.1, 3.0, 0.8, 0.1)
    tau = st.sidebar.slider("τ", 0.1, 10.0, 1.0, 0.1)
    mu = st.sidebar.slider("μ", -2.0, 3.0, 0.5, 0.1)

    t_end = st.slider("مدة المحاكاة", 10, 200, 100)
    A0 = st.number_input("القيمة الابتدائية A", value=0.5)
    Theta0 = st.number_input("القيمة الابتدائية Θ", value=0.2)

    if st.button("▶️ تشغيل المحاكاة", use_container_width=True):
        t = np.linspace(0, t_end, 1000)
        result = solve_ivp(hydromem_model, [0, t_end], [A0, Theta0], args=(r, beta, gamma, eta, tau, mu), t_eval=t)
        
        A, Theta = result.y[0], result.y[1]

        col1, col2 = st.columns(2)
        col1.metric("A النهائي", f"{A[-1]:.6f}")
        col2.metric("Θ النهائي", f"{Theta[-1]:.6f}")

        fig, ax = plt.subplots(1, 2, figsize=(12, 4))
        ax[0].plot(t, A, color='blue'); ax[0].set_title("A vs Time"); ax[0].grid(True)
        ax[1].plot(t, Theta, color='orange'); ax[1].set_title("Theta vs Time"); ax[1].grid(True)
        st.pyplot(fig)

        # التحقق من صلاحية تصدير الـ PDF
        if plan_info.get("allow_pdf"):
            st.success("✅ اكتملت المحاكاة. يمكنك تحميل التقرير.")
            st.download_button("📄 تحميل التقرير (PDF)", data="HYDROMEM Simulation Report", file_name="report.pdf")
        else:
            st.warning("🔒 تصدير التقارير (PDF) متاح في باقة الباحث وما فوق. يرجى ترقية اشتراكك.")
