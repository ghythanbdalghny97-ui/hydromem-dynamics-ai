import streamlit as st
import time

def chat_page():
    st.title("💬 HYDROMEM Chat AI")
    
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        st.error("⚠️ مفتاح الذكاء الاصطناعي غير موجود في الإعدادات.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.info(f"🧑‍🔬 أنت: {msg['content']}")
        else:
            st.success(f"🤖 HYDROMEM: {msg['content']}")

    prompt = st.text_input("اكتب سؤالك هنا واضغط Enter:")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.info(f"🧑‍🔬 أنت: {prompt}")
        
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            
            models_to_try = [
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
                "qwen/qwen3.8-27b"
            ]
            
            response = None
            last_error = ""
            
            for model_name in models_to_try:
                try:
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response = completion.choices[0].message.content
                    break 
                except Exception as e:
                    last_error = str(e)
                    time.sleep(1) 
                    
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.success(f"🤖 HYDROMEM: {response}")
            else:
                st.error(f"عذراً، فشلت جميع النماذج. الخطأ الأخير: {last_error}")
                
        except Exception as e:
            st.error(f"حدث خطأ غير متوقع: {e}")
