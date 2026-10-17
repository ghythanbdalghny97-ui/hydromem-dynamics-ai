import streamlit as st
import numpy as np
import pandas as pd
from scipy.integrate import odeint
from fpdf import FPDF
import auth_db

def generate_pdf(user_name, params, results_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="HYDROMEM Dynamics AI - Simulation Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"User: {user_name}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(200, 10, txt="Parameters:", ln=True)
    for k, v in params.items():
        pdf.cell(200, 10, txt=f"{k}: {v}", ln=True)
    
    pdf.cell(200, 10, txt="Final Results:", ln=True)
    last_row = results_df.iloc[-1]
    pdf.cell(200, 10, txt=f"A(t) = {last_row['A(t)']:.4f}", ln=True)
    pdf.cell(200, 10, txt=f"Theta(t) = {last_row['Theta(t)']:.4f}", ln=True)
    
    return bytes(pdf.output())

def simulation_page():
    st.title("🔬 محرك المحاكاة")
    
    user = st.session_state.user
    
    with st.sidebar:
        st.header("المعاملات")
        r = st.slider("r (معدل النمو)", 0.1, 5.0, 1.0)
        beta = st.slider("beta (التخميد)", 0.01, 1.0, 0.1)
        gamma = st.slider("gamma (الاقتران)", 0.0, 2.0, 0.5)
        eta = st.slider("eta", 0.1, 2.0, 1.0)
        mu = st.slider("mu", 0.0, 1.0, 0.1)
        tau = st.slider("tau (الاسترخاء)", 0.1, 5.0, 1.0)
        
        run = st.button("🚀 تشغيل المحاكاة", use_container_width=True)

    if run:
        def model(y, t):
            A, Th = y
            dA = r * A - beta * (A**3) - gamma * A * Th
            dTh = (1/tau) * (eta * (A**2) * (1 + mu * Th) - Th)
            return [dA, dTh]

        t = np.linspace(0, 50, 500)
        sol = odeint(model, [0.1, 0.0], t)
        
        df = pd.DataFrame({"Time": t, "A(t)": sol[:,0], "Theta(t)": sol[:,1]})
        
        st.success("✅ تمت المحاكاة بنجاح")
        st.line_chart(df.set_index("Time"))
        
        auth_db.increment_simulation(user['email'])
        
        if user['plan'] != 'individual':
            pdf_bytes = generate_pdf(user['name'], {"r":r, "beta":beta}, df)
            st.download_button("📄 تحميل التقرير (PDF)", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")
        else:
            st.info("🔒 تصدير PDF متاح في باقة الباحث وما فوق.")
