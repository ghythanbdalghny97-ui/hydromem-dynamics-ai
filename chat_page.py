import streamlit as st

def chat_page():
    st.title("💬 HYDROMEM Chat AI")
    
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        st.error("⚠️ مفتاح الذكاء الاصطناعي غير موجود في الإعدادات.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # عرض الرسائل السابقة بطريقة بسيطة
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**🧑‍🔬 أنت:** {msg['content']}")
        else:
            st.markdown(f"**🤖 HYDROMEM:** {msg['content']}")

    # استقبال رسالة جديدة
    prompt = st.text_input("اكتب سؤالك هنا واضغط Enter:")
    
    if prompt:
        # إضافة سؤال المستخدم
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f"**🧑‍🔬 أنت:** {prompt}")
        
        # جلب الرد
        with st.spinner("جاري التفكير..."):
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "أنت مساعد علمي. أجب باللغة العربية."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                response = completion.choices[0].message.content
                st.markdown(f"**🤖 HYDROMEM:** {response}")
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"حدث خطأ في الاتصال: {e}")
