"""
HYDROMEM Dynamics AI
Simulation Engine

Dynamic Model:
dA/dt = rA - beta A^3 - gamma A Theta

dTheta/dt =
(1/tau)(eta A^2(1+mu Theta)-Theta)

"""

import numpy as np
import streamlit as st

from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt



# ============================================================
# النموذج الرياضي
# ============================================================

def hydromem_model(
        t,
        y,
        r,
        beta,
        gamma,
        eta,
        tau,
        mu
):

    A, Theta = y


    dA = (
        r*A
        -
        beta*A**3
        -
        gamma*A*Theta
    )


    dTheta = (
        1/tau
    ) * (
        eta*A**2*(1+mu*Theta)
        -
        Theta
    )


    return [
        dA,
        dTheta
    ]



# ============================================================
# صفحة المحاكاة
# ============================================================

def simulation_page():

    st.title(
        "🔬 HYDROMEM Dynamic Simulation"
    )


    st.info(
        """
        نموذج ديناميكي تجريبي لدراسة
        التفاعل بين المتغير البنيوي A
        ومتغير الذاكرة الحرارية/المادية Θ.
        
        النموذج مرحلة محاكاة حاسوبية.
        لا يمثل تحققاً تجريبياً.
        """
    )



    # --------------------------------------------------------
    # المعاملات
    # --------------------------------------------------------

    st.sidebar.header(
        "⚙️ معاملات النموذج"
    )


    r = st.sidebar.slider(
        "r",
        -2.0,
        3.0,
        1.0,
        0.1
    )


    beta = st.sidebar.slider(
        "β",
        0.1,
        3.0,
        1.0,
        0.1
    )


    gamma = st.sidebar.slider(
        "γ",
        0.0,
        3.0,
        0.5,
        0.1
    )


    eta = st.sidebar.slider(
        "η",
        0.1,
        3.0,
        0.8,
        0.1
    )


    tau = st.sidebar.slider(
        "τ",
        0.1,
        10.0,
        1.0,
        0.1
    )


    mu = st.sidebar.slider(
        "μ",
        -2.0,
        3.0,
        0.5,
        0.1
    )



    # --------------------------------------------------------
    # الزمن والبداية
    # --------------------------------------------------------

    t_end = st.slider(
        "مدة المحاكاة",
        10,
        200,
        100
    )


    A0 = st.number_input(
        "القيمة الابتدائية A",
        value=0.5
    )


    Theta0 = st.number_input(
        "القيمة الابتدائية Θ",
        value=0.2
    )



    if st.button(
        "▶️ تشغيل المحاكاة",
        use_container_width=True
    ):


        t = np.linspace(
            0,
            t_end,
            1000
        )


        result = solve_ivp(
            hydromem_model,
            [
                0,
                t_end
            ],
            [
                A0,
                Theta0
            ],
            args=(
                r,
                beta,
                gamma,
                eta,
                tau,
                mu
            ),
            t_eval=t
        )


        A = result.y[0]

        Theta = result.y[1]



        # ----------------------------------------------------
        # النتائج
        # ----------------------------------------------------

        col1,col2 = st.columns(2)


        with col1:

            st.metric(
                "A النهائي",
                f"{A[-1]:.6f}"
            )


        with col2:

            st.metric(
                "Θ النهائي",
                f"{Theta[-1]:.6f}"
            )



        # ----------------------------------------------------
        # الرسم A
        # ----------------------------------------------------

        st.subheader(
            "تطور A"
        )

        fig1, ax1 = plt.subplots()

        ax1.plot(
            t,
            A
        )

        ax1.set_xlabel(
            "Time"
        )

        ax1.set_ylabel(
            "A"
        )

        ax1.grid(
            True
        )

        st.pyplot(
            fig1
        )



        # ----------------------------------------------------
        # الرسم Theta
        # ----------------------------------------------------

        st.subheader(
            "تطور Θ"
        )

        fig2, ax2 = plt.subplots()

        ax2.plot(
            t,
            Theta
        )

        ax2.set_xlabel(
            "Time"
        )

        ax2.set_ylabel(
            "Theta"
        )

        ax2.grid(
            True
        )

        st.pyplot(
            fig2
        )



        # ----------------------------------------------------
        # مسار الطور
        # ----------------------------------------------------

        st.subheader(
            "Phase Space"
        )


        fig3, ax3 = plt.subplots()


        ax3.plot(
            A,
            Theta
        )


        ax3.set_xlabel(
            "A"
        )

        ax3.set_ylabel(
            "Theta"
        )


        ax3.grid(
            True
        )


        st.pyplot(
            fig3
        )



        st.success(
            "اكتملت المحاكاة بنجاح"
        )
