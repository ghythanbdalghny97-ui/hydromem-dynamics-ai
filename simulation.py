import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from fpdf import FPDF
import config

# ==========================================
# المعادلات الرياضية للنماذج الطبية
# ==========================================
def hydromem_model(t, y, r, beta, gamma, eta, tau, mu):
    A, Theta = y
    return [r*A - beta*A**3 - gamma*A*Theta, (1/tau)*(eta*A**2*(1+mu*Theta) - Theta)]

def bone_healing_model(t, y, k1, k2):
    B, C = y # Osteoblasts, Osteoclasts
    return [k1 * B - k2 * B * C, k2 * B * C - 0.1 * C]

def wound_healing_model(t, y, alpha, beta):
    W = y[0] # Wound size
    return [ -alpha * W + beta * np.exp(-t) ]

def knee_oa_model(t, y, wear_rate, repair_rate):
    Cartilage = y[0]
    return [ -wear_rate + repair_rate * (1 - Cartilage) ]

def disc_degeneration_model(t, y, load, hydration):
    Disc = y[0]
    return [ -load * Disc + hydration ]

def generate_pdf(user_name, model_name, params, final_result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="HYDROMEM Medical Simulation Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"User: {user_name}", ln=True)
    pdf.cell(200, 10, txt=f"Model: {model_name}", ln=True)
    pdf.cell(200, 10, txt="----------------------------------------", ln=True)
    pdf.cell(200, 10, txt="Parameters:", ln=True)
    for k, v in params.items(): pdf.cell(200, 10, txt=f"{k}: {v}", ln=True)
    pdf.cell(200, 10, txt="----------------------------------------", ln=True)
    pdf.cell(200, 10, txt=f"Final Result: {final_result:.4f}", ln=True)
    pdf.cell(200, 10, txt="----------------------------------------", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, txt="Disclaimer: This is a computational simulation. Results require experimental validation.")
    return bytes(pdf.output())

def render():
    st.title("🔬 HYDROMEM Medical Simulation Center")
    user = st.session_state.user
    plan_info = config.PLANS.get(user.get("plan", "individual"), config.PLANS["individual"])

    # تقسيم المحاكاة إلى تبويبات (Tabs)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧬 النموذج الديناميكي", 
        "🦴 التئام العظام", 
        "🩹 التئام الجروح", 
        "🦵 خشونة الركبة", 
        "🦴 أقراص العمود الفقري"
    ])

    with tab1:
        st.subheader("Dynamic System Model")
        st.latex(r"\frac{dA}{dt} = rA - \beta A^3 - \gamma A\Theta")
        st.latex(r"\frac{d\Theta}{dt} = \frac{1}{\tau}(\eta A^2(1+\mu\Theta) - \Theta)")
        
        c1, c2 = st.columns(2)
        r = c1.slider("r", 0.1, 3.0, 1.0)
        beta = c2.slider("beta", 0.1, 1.0, 0.5)
        
        if st.button("تشغيل النموذج", key="run1"):
            t = np.linspace(0, 50, 500)
            sol = solve_ivp(hydromem_model, [0, 50], [0.5, 0.2], args=(r, beta, 0.5, 1.0, 1.0, 0.1), t_eval=t)
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], label="A(t)")
            ax.plot(t, sol.y[1], label="Theta(t)")
            ax.legend(); st.pyplot(fig)

    with tab2:
        st.subheader("Bone Healing Model (Osteoblasts vs Osteoclasts)")
        st.write("يحاكي تفاعل الخلايا البانية للعظام (B) مع الخلايا الناقضة (C).")
        k1 = st.slider("معدل بناء العظم", 0.1, 2.0, 1.0)
        k2 = st.slider("معدل الارتشاف", 0.1, 2.0, 0.5)
        
        if st.button("تشغيل التئام العظام", key="run2"):
            t = np.linspace(0, 30, 300)
            sol = solve_ivp(bone_healing_model, [0, 30], [1.0, 0.5], args=(k1, k2), t_eval=t)
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], label="Osteoblasts (بناء)")
            ax.plot(t, sol.y[1], label="Osteoclasts (ارتشاف)")
            ax.legend(); st.pyplot(fig)

    with tab3:
        st.subheader("Wound Healing Kinetics")
        st.write("نموذج Fisher-KPP لسرعة التئام الجروح.")
        alpha = st.slider("معدل انكماش الجرح", 0.1, 2.0, 1.0)
        
        if st.button("تشغيل التئام الجروح", key="run3"):
            t = np.linspace(0, 20, 200)
            sol = solve_ivp(wound_healing_model, [0, 20], [5.0], args=(alpha, 1.0), t_eval=t)
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], color="red", label="Wound Size")
            ax.legend(); st.pyplot(fig)

    with tab4:
        st.subheader("Knee Osteoarthritis Model")
        st.write("محاكاة تآكل الغضروف مع الوقت بسبب الأحمال.")
        wear = st.slider("معدل التآكل", 0.01, 0.5, 0.1)
        
        if st.button("تشغيل خشونة الركبة", key="run4"):
            t = np.linspace(0, 50, 500)
            sol = solve_ivp(knee_oa_model, [0, 50], [1.0], args=(wear, 0.2), t_eval=t)
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], color="purple", label="Cartilage Thickness")
            ax.legend(); st.pyplot(fig)

    with tab5:
        st.subheader("Intervertebral Disc Degeneration")
        st.write("تأثير الحمل على نسبة الماء في الأقراص الفقرية.")
        load = st.slider("الحمل الميكانيكي", 0.01, 1.0, 0.2)
        
        if st.button("تشغيل أقراص العمود", key="run5"):
            t = np.linspace(0, 24, 100)
            sol = solve_ivp(disc_degeneration_model, [0, 24], [0.8], args=(load, 0.5), t_eval=t)
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], color="blue", label="Hydration Level")
            ax.legend(); st.pyplot(fig)

    # زر تحميل التقرير (موحد لكل النماذج)
    st.divider()
    if plan_info.get("allow_pdf"):
        st.success("✅ يمكنك الآن تصدير تقرير المحاكاة (PDF)")
        if st.button("📄 تحميل التقرير (PDF)"):
            pdf_bytes = generate_pdf(user.get('name', 'User'), "Medical Simulation", {"Info": "Check charts"}, 1.0)
            st.download_button("اضغط للتحميل", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")
    else:
        st.warning("🔒 تصدير التقارير (PDF) متاح في باقة الباحث وما فوق.")
