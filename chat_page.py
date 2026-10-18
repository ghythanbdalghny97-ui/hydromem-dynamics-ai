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
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("جاري التفكير..."):
                try:
                    from groq import Groq
                    client = Groq(api_key=groq_key)
                    
                    # 🌟 قائمة النماذج (سيجربها بالترتيب حتى ينجح أحدها)
                    models_to_try = [
                        "openai/gpt-oss-20b",
                        "llama-3.3-70b-versatile",
                        "mixtral-8x7b-32768",
                        "gemma2-9b-it",
                        "llama3-8b-8192"
                    ]
                    
                    response = None
                    last_error = ""
                    
                    for model_name in models_to_try:
                        try:
                            completion = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {"role": "system", "content": "أنت مساعد علمي من منصة HYDROMEM. أجب باللغة العربية بدقة وعلمية."},
                                    *st.session_state.messages
                                ]
                            )
                            response = completion.choices[0].message.content
                            break # إذا نجح النموذج، اخرج من الحلقة وتوقف عن التجربة
                        except Exception as e:
                            last_error = str(e)
                            continue # إذا فشل، انتقل تلقائياً لتجربة النموذج التالي
                            
                    if response:
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        st.error(f"عذراً، واجهت مشكلة في الاتصال بجميع النماذج. آخر خطأ: {last_error}")
                        
                except Exception as e:
                    st.error(f"حدث خطأ غير متوقع: {e}")
