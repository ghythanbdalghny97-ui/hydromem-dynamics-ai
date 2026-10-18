import streamlit as st

def chat_page():
    st.title("💬 HYDROMEM Chat AI")
    
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        st.error("⚠️ مفتاح الذكاء الاصطناعي غير موجود في الإعدادات.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("اسألني عن النمذجة الرياضية أو الطب..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                
                # تجربة النموذج الأحدث
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                response = completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"حدث خطأ في الاتصال: {e}")
