import streamlit as st

def chat_page():
    st.title("💬 HYDROMEM Chat AI")
    
    # تنبيه بخصوص الترجمة
    st.caption("⚠️ للحصول على أفضل تجربة، يرجى إيقاف الترجمة التلقائية في المتصفح.")

    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        st.error("⚠️ مفتاح الذكاء الاصطناعي غير موجود في الإعدادات.")
        return

    # تهيئة سجل المحادثات
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # عرض الرسائل السابقة باستخدام واجهة الدردشة الجميلة
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # مربع الإدخال الجميل (مثل ChatGPT)
    if prompt := st.chat_input("اسألني عن النمذجة الرياضية أو الطب..."):
        # إضافة رسالة المستخدم
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # عرض رد المساعد
        with st.chat_message("assistant"):
            with st.spinner("جاري التفكير..."):
                try:
                    from groq import Groq
                    client = Groq(api_key=groq_key)
                    
                    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
                    response = None
                    last_error = ""
                    
                    for model_name in models_to_try:
                        try:
                            completion = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {"role": "system", "content": "أنت مساعد علمي. أجب باللغة العربية. استخدم $$ للمعادلات الرياضية المستقلة و $ للمعادلات المضمنة."},
                                    *st.session_state.messages
                                ]
                            )
                            response = completion.choices[0].message.content
                            break 
                        except Exception as e:
                            last_error = str(e)
                            
                    if response:
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        st.error(f"عذراً، فشلت جميع النماذج. الخطأ الأخير: {last_error}")
                        
                except Exception as e:
                    st.error(f"حدث خطأ غير متوقع: {e}")
