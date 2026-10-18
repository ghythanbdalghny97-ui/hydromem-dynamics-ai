import streamlit as st

def chat_page():
    st.title("💬 HYDROMEM Chat AI")
    
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        st.error("⚠️ مفتاح الذكاء الاصطناعي (GROQ_API_KEY) غير موجود في إعدادات Streamlit Secrets.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # عرض الرسائل السابقة
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # استقبال رسالة جديدة
    if prompt := st.chat_input("اسألني عن النمذجة الرياضية أو الطب..."):
        # إضافة رسالة المستخدم وعرضها
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # تجهيز رد المساعد
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("جاري التفكير... ⏳")
            
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                
                models_to_try = [
                    "llama-3.3-70b-versatile",
                    "llama-3.1-8b-instant",
                    "mixtral-8x7b-32768"
                ]
                
                response = None
                last_error = ""
                
                for model_name in models_to_try:
                    try:
                        completion = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": "أنت مساعد علمي. أجب باللغة العربية."},
                                *st.session_state.messages
                            ]
                        )
                        response = completion.choices[0].message.content
                        break 
                    except Exception as e:
                        last_error = str(e)
                        
                if response:
                    message_placeholder.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    message_placeholder.error(f"عذراً، حدث خطأ في النماذج: {last_error}")
                    
            except Exception as e:
                message_placeholder.error(f"حدث خطأ غير متوقع: {e}")
