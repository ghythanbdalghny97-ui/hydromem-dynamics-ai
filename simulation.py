import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import config
import chat_page # لدمج الدردشة مع المحاكاة

# ==========================================
# دوال النماذج الرياضية
# ==========================================
def dynamic_model(t, y, r, beta):
    A, Theta = y
    dA = r*A - beta*A**3 - 0.5*A*Theta
    dTheta = (1/1.0)*(0.8*A**2*(1+0.1*Theta) - Theta)
    return [dA, dTheta]

def bone_model(t, y, k1, k2):
    O, C = y
    dO = k1 * O - k2 * O * C
    dC = k2 * O * C - 0.1 * C
    return [dO, dC]

def wound_model(t, W, alpha, beta):
    dW = -alpha * W + beta * np.exp(-t)
    return [dW]

def knee_model(t, K, wear, repair):
    dK = -wear + repair * (1 - K)
    return [dK]

def disc_model(t, D, load, hydration):
    dD = -load * D + hydration
    return [dD]

# ==========================================
# دالة طلب التحليل من الذكاء الاصطناعي
# ==========================================
def get_ai_analysis(model_name, results_text):
    prompt = f"لقد قمت بتشغيل محاكاة ({model_name}) وكانت النتائج النهائية كالتالي:\n{results_text}\n\nبصفتك مساعداً علمياً، اشرح لي ماذا تعني هذه النتائج؟ وما هي التوصيات أو الاستنتاجات العلمية التي يمكن استخلاصها؟"
    system_prompt = "أنت مساعد علمي وطبي خبير. اشرح النتائج بدقة واحترافية باللغة العربية."
    # نستخدم دالة الاتصال الموجودة في chat_page
    return chat_page.call_ai(prompt, system_prompt, "Groq (سريع)", max_tokens=1024)

# ==========================================
# الواجهة الرئيسية للمحاكاة
# ==========================================
def render():
    st.title("🔬 HYDROMEM Medical Simulation Center")
    st.info("اختر النموذج الطبي، قم بتعديل المعاملات، ثم شغّل المحاكاة لرؤية النتائج والرسوم البيانية.")
    
    # إنشاء 5 تبويبات
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧬 النموذج الديناميكي", 
        "🦴 التئام العظام", 
        "🩹 التئام الجروح",
        "🦵 خشونة الركبة", 
        "🦴 أقراص العمود الفقري"
    ])

    # --------------------------------------------------------
    # 1. النموذج الديناميكي
    # --------------------------------------------------------
    with tab1:
        st.subheader("نموذج A / Θ الديناميكي")
        c1, c2 = st.columns(2)
        r = c1.slider("r (معدل النمو)", 0.1, 3.0, 1.0, key="r_dyn")
        beta = c2.slider("beta (التخميد)", 0.1, 2.0, 0.5, key="b_dyn")
        
        if st.button("تشغيل المحاكاة", key="run_dyn", type="primary"):
            t = np.linspace(0, 50, 500)
            sol = solve_ivp(dynamic_model, [0, 50], [0.5, 0.2], args=(r, beta), t_eval=t)
            
            # الرسم
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], label="A(t) (المتغير البنيوي)")
            ax.plot(t, sol.y[1], label="Θ(t) (متغير الذاكرة)")
            ax.set_xlabel("الزمن"); ax.set_ylabel("القيمة"); ax.legend(); ax.grid(True)
            st.pyplot(fig)
            
            # النتائج العددية
            st.write("### 📊 النتائج النهائية:")
            col1, col2 = st.columns(2)
            col1.metric("القيمة النهائية A", f"{sol.y[0][-1]:.4f}")
            col2.metric("القيمة النهائية Θ", f"{sol.y[1][-1]:.4f}")
            
            # دمج الدردشة
            if st.button("🤖 اطلب تحليل هذه النتائج من AI", key="ai_dyn"):
                with st.spinner("جاري التحليل..."):
                    res_text = f"القيمة النهائية A = {sol.y[0][-1]:.4f} و Θ = {sol.y[1][-1]:.4f}"
                    st.success(get_ai_analysis("النموذج الديناميكي", res_text))

    # --------------------------------------------------------
    # 2. التئام العظام
    # --------------------------------------------------------
    with tab2:
        st.subheader("نموذج التئام العظام (Osteoblasts vs Osteoclasts)")
        c1, c2 = st.columns(2)
        k1 = c1.slider("معدل بناء العظم (k1)", 0.1, 2.0, 1.2, key="k1_bone")
        k2 = c2.slider("معدل ارتشاف العظم (k2)", 0.1, 2.0, 0.4, key="k2_bone")
        
        if st.button("تشغيل المحاكاة", key="run_bone", type="primary"):
            t = np.linspace(0, 30, 300)
            sol = solve_ivp(bone_model, [0, 30], [1.0, 0.5], args=(k1, k2), t_eval=t)
            
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], label="Osteoblasts (بناء)", color='tab:blue')
            ax.plot(t, sol.y[1], label="Osteoclasts (ارتشاف)", color='tab:red')
            ax.set_xlabel("الزمن (يوم)"); ax.set_ylabel("الكثافة النسبية"); ax.legend(); ax.grid(True)
            st.pyplot(fig)
            
            st.write("### 📊 النتائج النهائية (بعد 30 يوم):")
            col1, col2 = st.columns(2)
            col1.metric("الخلايا البانية النهائية", f"{sol.y[0][-1]:.4f}")
            col2.metric("الخلايا الناقضة النهائية", f"{sol.y[1][-1]:.4f}")
            
            if st.button("🤖 اطلب تحليل هذه النتائج من AI", key="ai_bone"):
                with st.spinner("جاري التحليل..."):
                    res_text = f"الخلايا البانية = {sol.y[0][-1]:.4f}، الخلايا الناقضة = {sol.y[1][-1]:.4f}"
                    st.success(get_ai_analysis("التئام العظام", res_text))

    # --------------------------------------------------------
    # 3. التئام الجروح
    # --------------------------------------------------------
    with tab3:
        st.subheader("نموذج التئام الجروح (Wound Healing)")
        c1, c2 = st.columns(2)
        alpha = c1.slider("معدل انكماش الجرح (alpha)", 0.1, 2.0, 0.5, key="alpha_wnd")
        beta = c2.slider("معدل التغذية (beta)", 0.1, 2.0, 1.0, key="beta_wnd")
        
        if st.button("تشغيل المحاكاة", key="run_wnd", type="primary"):
            t = np.linspace(0, 20, 200)
            sol = solve_ivp(wound_model, [0, 20], [5.0], args=(alpha, beta), t_eval=t)
            
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], label="حجم الجرح W(t)", color='tab:red')
            ax.set_xlabel("الزمن (يوم)"); ax.set_ylabel("حجم الجرح"); ax.legend(); ax.grid(True)
            st.pyplot(fig)
            
            st.write("### 📊 النتائج النهائية (بعد 20 يوم):")
            st.metric("حجم الجرح المتبقي", f"{sol.y[0][-1]:.4f}")
            
            if st.button("🤖 اطلب تحليل هذه النتائج من AI", key="ai_wnd"):
                with st.spinner("جاري التحليل..."):
                    res_text = f"حجم الجرح المتبقي بعد 20 يوم = {sol.y[0][-1]:.4f}"
                    st.success(get_ai_analysis("التئام الجروح", res_text))

    # --------------------------------------------------------
    # 4. خشونة الركبة
    # --------------------------------------------------------
    with tab4:
        st.subheader("نموذج خشونة الركبة (Knee Osteoarthritis)")
        c1, c2 = st.columns(2)
        wear = c1.slider("معدل التآكل (wear)", 0.01, 0.5, 0.1, key="wear_oa")
        repair = c2.slider("معدل الإصلاح (repair)", 0.01, 0.5, 0.05, key="repair_oa")
        
        if st.button("تشغيل المحاكاة", key="run_oa", type="primary"):
            t = np.linspace(0, 50, 300)
            sol = solve_ivp(knee_model, [0, 50], [1.0], args=(wear, repair), t_eval=t)
            
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], label="سماكة الغضروف K(t)", color='tab:purple')
            ax.set_xlabel("الزمن (سنة)"); ax.set_ylabel("السماكة النسبية"); ax.legend(); ax.grid(True)
            st.pyplot(fig)
            
            st.write("### 📊 النتائج النهائية (بعد 50 سنة):")
            st.metric("السماكة المتبقية للغضروف", f"{sol.y[0][-1]:.4f}")
            
            if st.button("🤖 اطلب تحليل هذه النتائج من AI", key="ai_oa"):
                with st.spinner("جاري التحليل..."):
                    res_text = f"السماكة المتبقية للغضروف بعد 50 سنة = {sol.y[0][-1]:.4f}"
                    st.success(get_ai_analysis("خشونة الركبة", res_text))

    # --------------------------------------------------------
    # 5. أقراص العمود الفقري
    # --------------------------------------------------------
    with tab5:
        st.subheader("نموذج أقراص العمود الفقري (Disc Degeneration)")
        c1, c2 = st.columns(2)
        load = c1.slider("الحمل الميكانيكي (load)", 0.01, 1.0, 0.2, key="load_disc")
        hydration = c2.slider("معدل الترطيب (hydration)", 0.01, 1.0, 0.5, key="hyd_disc")
        
        if st.button("تشغيل المحاكاة", key="run_disc", type="primary"):
            t = np.linspace(0, 24, 100)
            sol = solve_ivp(disc_model, [0, 24], [0.8], args=(load, hydration), t_eval=t)
            
            fig, ax = plt.subplots()
            ax.plot(t, sol.y[0], label="نسبة الماء في القرص D(t)", color='tab:blue')
            ax.set_xlabel("الزمن (ساعة)"); ax.set_ylabel("نسبة الماء"); ax.legend(); ax.grid(True)
            st.pyplot(fig)
            
            st.write("### 📊 النتائج النهائية (بعد 24 ساعة):")
            st.metric("نسبة الماء المتبقية", f"{sol.y[0][-1]:.4f}")
            
            if st.button("🤖 اطلب تحليل هذه النتائج من AI", key="ai_disc"):
                with st.spinner("جاري التحليل..."):
                    res_text = f"نسبة الماء المتبقية في القرص بعد 24 ساعة = {sol.y[0][-1]:.4f}"
                    st.success(get_ai_analysis("أقراص العمود الفقري", res_text))
