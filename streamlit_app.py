"""
HYDROMEM Dynamics AI
Interactive Simulation Platform
============================================================
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

st.set_page_config(
    page_title="HYDROMEM Dynamics AI",
    page_icon="🧬",
    layout="wide",
)

st.title("🧬 HYDROMEM Dynamics AI")
st.markdown("### منصة ذكاء حاسوبي للمحاكاة وتحليل الأنظمة الديناميكية المعقدة")
st.markdown("**Computational Prototype — TRL 3**")
st.markdown("---")

def model(y, t, mu, kappa, beta, gamma):
    A, Theta = y
    dA = mu * A - A**3 - kappa * Theta * A
    dTheta = beta * (A - Theta) - gamma * Theta
    return [dA, dTheta]

st.sidebar.header("⚙️ معاملات النموذج")

mu = st.sidebar.slider("μ (النمو)", 0.1, 1.5, 0.5, 0.05)
kappa = st.sidebar.slider("κ (الاقتران)", 0.1, 1.5, 0.8, 0.05)
beta = st.sidebar.slider("β (الانتقال)", 0.1, 1.0, 0.4, 0.05)
gamma = st.sidebar.slider("γ (الاضمحلال)", 0.1, 1.0, 0.6, 0.05)

st.sidebar.markdown("---")
st.sidebar.header("🔧 إعدادات المحاكاة")

T_end = st.sidebar.slider("زمن المحاكاة", 5, 100, 20, 5)
A0 = st.sidebar.slider("A₀", 0.0, 2.0, 0.5, 0.1)
Theta0 = st.sidebar.slider("Θ₀", 0.0, 2.0, 0.3, 0.1)

time = np.linspace(0, T_end, 2000)
solution = odeint(model, [A0, Theta0], time, args=(mu, kappa, beta, gamma))
A_values = solution[:, 0]
Theta_values = solution[:, 1]

st.markdown("### 📊 النتائج")
col1, col2, col3, col4 = st.columns(4)
col1.metric("A النهائي", f"{A_values[-1]:.4f}")
col2.metric("Θ النهائي", f"{Theta_values[-1]:.4f}")
col3.metric("A الأقصى", f"{np.max(A_values):.4f}")
col4.metric("Θ الأقصى", f"{np.max(Theta_values):.4f}")

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(time, A_values, label="A(t) — الحالة", linewidth=2)
ax.plot(time, Theta_values, label="Θ(t) — الذاكرة", linewidth=2)
ax.set_xlabel("الزمن")
ax.set_ylabel("القيم")
ax.set_title("تطور النظام مع الزمن", fontweight="bold")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

st.markdown("### 🔍 تحليل الاستقرار")
if st.button("تشغيل تحليل Jacobian", type="primary"):
    A_eq = A_values[-1]
    Theta_eq = Theta_values[-1]
    J11 = mu - 3 * A_eq**2 - kappa * Theta_eq
    J12 = -kappa * A_eq
    J21 = beta
    J22 = -beta - gamma
    J = np.array([[J11, J12], [J21, J22]])
    eigenvalues = np.linalg.eigvals(J)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**مصفوفة Jacobian:**")
        st.write(J)
    with col_b:
        st.markdown("**القيم الذاتية:**")
        for i, e in enumerate(eigenvalues):
            st.write(f"λ{i+1} = {e:.6f}")
    
    if np.all(np.real(eigenvalues) < 0):
        st.success("✅ استقرار محلي (Re(λ) < 0)")
    else:
        st.warning("⚠️ منطقة عدم استقرار محتملة")

st.markdown("---")
st.markdown("*HYDROMEM Dynamics AI — Computational Prototype — عبد الغني صالح محسن محمد غيثان — 2026*")
