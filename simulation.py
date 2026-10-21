import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from fpdf import FPDF
import config

# دوال النماذج الرياضية
def hydromem_model(t, y, r, beta, gamma, eta, tau, mu):
    A, Theta = y
    return [r*A - beta*A**3 - gamma*A*Theta, (1/tau)*(eta*A**2*(1+mu*Theta) - Theta)]

def bone_healing_model(t, y, k1, k2):
    B, C = y
    return [k1 * B - k2 * B * C, k2 * B * C - 0.1 * C]

def generate_pdf(user_name, model_name, params, final_result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"HYDROMEM Report - {model_name}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"User: {user_name}", ln=True)
    pdf.cell(200, 10, txt="----------------------------------------", ln=True)
    for k, v in params.items(): pdf.cell(200, 10, txt=f"{k}: {v}", ln=True)
    pdf.cell(200, 10, txt=f"Final Result: {final_result:.4f}", ln=True)
    return bytes(pdf.output())

def render():
    st.title("🔬 HYDROMEM Medical Simulation Center")
    user = st.session_state.user
    plan_info = config.PLANS.get(user.get("plan", "individual"), config.PLANS["individual"])

    tab1, tab2, tab3 = st.tabs([
        "🧬 النموذج الديناميكي", 
        "🦴 التئام العظام", 
        "🌊 الغوص والارتفاع (قانون التوازن)"
    ])

    with tab1:
        st.subheader("Dynamic System Model")
        c1, c2 = st.columns(2)
        r = c1.slider("r", 0.1, 3.0, 1.0)
        if st.button("تشغيل النموذج", key="run1"):
            t = np.linspace(0, 50, 500)
            sol = solve_ivp(hydromem_model, [0, 50], [0.5, 0.2], args=(r, 0.5, 0.5, 1.0, 1.0, 0.1), t_eval=t)
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], label="A(t)")
            ax.plot(t, sol.y[1], label="Theta(t)")
            ax.legend(); st.pyplot(fig)

    with tab2:
        st.subheader("Bone Healing Model")
        k1 = st.slider("معدل بناء العظم", 0.1, 2.0, 1.0)
        if st.button("تشغيل التئام العظام", key="run2"):
            t = np.linspace(0, 30, 300)
            sol = solve_ivp(bone_healing_model, [0, 30], [1.0, 0.5], args=(k1, 0.5), t_eval=t)
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], label="Osteoblasts")
            ax.plot(t, sol.y[1], label="Osteoclasts")
            ax.legend(); st.pyplot(fig)

    with tab3:
        st.subheader("🌊 محاكي الغوص والصعود (Transmural Pressure)")
        st.info("هذا النموذج يثبت فرضية 'قانون التوازن' ويفسر انفجار الأوعية في الغوص.")
        
        depth = st.slider("عمق الغوص (متر)", 0, 100, 20)
        altitude = st.slider("الارتفاع (متر)", 0, 5000, 2000)
        
        if st.button("تشغيل المحاكاة ورسم النتائج"):
            P_atm = 101325.0
            rho_water = 1025.0
            g = 9.81
            P_blood = 120 * 133.32
            
            p_underwater = P_atm + (rho_water * g * depth)
            p_at_altitude = P_atm * np.exp(-altitude / 8000)
            
            transmural_water = (p_underwater - P_blood) / 1000 # kPa
            transmural_air = (p_at_altitude - P_blood) / 1000
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # رسم الغوص
            depths = np.linspace(0, 100, 100)
            tw_water = (P_atm + (rho_water * g * depths) - P_blood) / 1000
            ax1.plot(depths, tw_water, color='blue', linewidth=3)
            ax1.axhline(0, color='black', linestyle='--')
            ax1.set_title('الغوص في البحر')
            ax1.set_xlabel('العمق (متر)')
            ax1.set_ylabel('فرق الضغط (kPa)')
            ax1.grid(True)
            
            # رسم الجبال
            altitudes = np.linspace(0, 5000, 100)
            tw_air = (P_atm * np.exp(-altitudes / 8000) - P_blood) / 1000
            ax2.plot(altitudes, tw_air, color='red', linewidth=3)
            ax2.axhline(0, color='black', linestyle='--')
            ax2.set_title('الصعود للجبال')
            ax2.set_xlabel('الارتفاع (متر)')
            ax2.set_ylabel('فرق الضغط (kPa)')
            ax2.grid(True)
            
            st.pyplot(fig)
