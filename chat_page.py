"""
HYDROMEM Dynamics AI
Chat Interface Module

AI Chat:
- Groq
- Gemini
- File analysis
- Chat history
"""

import re
import pandas as pd
import streamlit as st

from PIL import Image
from pypdf import PdfReader
import docx

from groq import Groq
from google import genai

import config
import supabase_utils



# ============================================================
# إصلاح المعادلات
# ============================================================

def fix_latex(text):

    replacements = {
        r"\[": "$$",
        r"\]": "$$",
        r"\begin{cases}": "",
        r"\end{cases}": "",
        r"\bigr]": "",
        r"\bigl[": ""
    }

    for a,b in replacements.items():
        text = text.replace(a,b)


    symbols = [
        r"\Theta",
        r"\alpha",
        r"\beta",
        r"\gamma",
        r"\mu",
        r"\tau",
        r"\eta"
    ]


    for symbol in symbols:

        text = re.sub(
            r"(?<!\$)"
            + re.escape(symbol)
            +
            r"(?!\$)",
            lambda m: f"${symbol}$",
            text
        )


    return text



# ============================================================
# قراءة الملفات
# ============================================================

def extract_file(uploaded_file):

    text = ""

    try:

        if uploaded_file.name.endswith(".pdf"):

            reader = PdfReader(uploaded_file)

            for page in reader.pages:
                text += page.extract_text() or ""


        elif uploaded_file.name.endswith(".docx"):

            document = docx.Document(
                uploaded_file
            )

            for p in document.paragraphs:
                text += p.text + "\n"


        elif uploaded_file.name.endswith(".xlsx"):

            df = pd.read_excel(
                uploaded_file
            )

            text = df.to_string()


        elif uploaded_file.name.endswith(
            (".csv",".txt")
        ):

            text = uploaded_file.read().decode(
                "utf-8"
            )


    except Exception as e:

        text = f"خطأ قراءة الملف: {e}"


    return text[:5000]



# ============================================================
# الصفحة الرئيسية
# ============================================================

def chat_page():

    st.title(
        "💬 HYDROMEM Chat AI"
    )


    if "messages" not in st.session_state:
        st.session_state.messages=[]


    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id=None



    # --------------------------------------------------------
    # الشريط الجانبي
    # --------------------------------------------------------

    with st.sidebar:


        st.subheader(
            "⚙️ الإعدادات"
        )


        model = st.selectbox(
            "المحرك",
            [
                "Groq",
                "Gemini"
            ]
        )


        persona = st.selectbox(
            "نوع المساعد",
            list(
                config.PERSONAS.keys()
            )
        )


        st.divider()


        uploaded_file = st.file_uploader(
            "📎 رفع ملف",
            type=config.SUPPORTED_FILES
        )


        st.divider()


        st.subheader(
            "📚 المحادثات السابقة"
        )


        user_email = (
            st.session_state
            .user
            .get("email")
        )


        sessions = (
            supabase_utils
            .get_chat_sessions(
                user_email
            )
        )


        for s in sessions:

            if st.button(
                s["title"],
                key=s["id"]
            ):

                old = (
                    supabase_utils
                    .get_chat_session_by_id(
                        s["id"]
                    )
                )

                if old:

                    st.session_state.messages = old["messages"]

                    st.session_state.current_session_id = old["id"]

                    st.rerun()



        if st.button(
            "➕ محادثة جديدة"
        ):

            st.session_state.messages=[]

            st.session_state.current_session_id=None

            st.rerun()



    # --------------------------------------------------------
    # عرض المحادثة
    # --------------------------------------------------------

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )



    # --------------------------------------------------------
    # سؤال المستخدم
    # --------------------------------------------------------

    if prompt := st.chat_input(
        "اكتب سؤالك..."
    ):


        file_text=""

        if uploaded_file:

            if not uploaded_file.type.startswith(
                "image/"
            ):

                file_text = extract_file(
                    uploaded_file
                )



        full_prompt = prompt


        if file_text:

            full_prompt += (
                "\n\nمحتوى الملف:\n"
                +
                file_text
            )



        st.session_state.messages.append(
            {
                "role":"user",
                "content":prompt
            }
        )


        with st.chat_message(
            "user"
        ):

            st.markdown(prompt)



        # ----------------------------------------------------
        # الذكاء الاصطناعي
        # ----------------------------------------------------

        with st.chat_message(
            "assistant"
        ):


            with st.spinner(
                "🧠 جاري التحليل..."
            ):


                answer=""


                system = f"""
                {config.PERSONAS[persona]}

                أجب باللغة العربية.

                استخدم:
                $$ للمعادلات المستقلة

                $ للرموز الرياضية.

                اختم الإجابة بالخلاصة.
                """



                try:


                    if model=="Groq":


                        client = Groq(
                            api_key=config.GROQ_API_KEY
                        )


                        result = (
                            client.chat.completions.create(
                                model=config.GROQ_MODELS[0],
                                messages=[
                                    {
                                    "role":"system",
                                    "content":system
                                    },
                                    {
                                    "role":"user",
                                    "content":full_prompt
                                    }
                                ],
                                max_tokens=4096
                            )
                        )


                        answer = (
                            result
                            .choices[0]
                            .message
                            .content
                        )



                    else:


                        client = genai.Client(
                            api_key=config.GEMINI_API_KEY
                        )


                        content=[
                            full_prompt
                        ]


                        if uploaded_file and uploaded_file.type.startswith("image/"):

                            content.append(
                                Image.open(
                                    uploaded_file
                                )
                            )


                        result = (
                            client
                            .models
                            .generate_content(
                                model=config.GEMINI_MODEL,
                                contents=content
                            )
                        )


                        answer=result.text



                except Exception as e:

                    answer=f"خطأ: {e}"



                answer=fix_latex(
                    answer
                )


                st.markdown(
                    answer
                )


        st.session_state.messages.append(
            {
                "role":"assistant",
                "content":answer
            }
        )



        title = (
            st.session_state
            .messages[0]
            ["content"][:40]
        )


        sid = (
            supabase_utils
            .save_chat_session(
                user_email,
                title,
                st.session_state.messages,
                st.session_state.current_session_id
            )
        )


        if sid:

            st.session_state.current_session_id=sid
