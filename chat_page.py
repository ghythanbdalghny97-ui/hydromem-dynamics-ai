import streamlit as st

def chat_page():
    st.title("💬 HYDROMEM Chat AI")
    
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        st.error("⚠️ مفتاح الذكاء الاصطناعي غير موجود في الإعدادات.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # عرض الرسائل السابقة
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.info(f"🧑‍🔬 أنت: {msg['content']}")
        else:
            st.success(f"🤖 HYDROMEM: {msg['content']}")

    # مربع الإدخال
    prompt = st.text_input("اكتب سؤالك هنا واضغط Enter:")
    
    if prompt:
        # إضافة سؤال المستخدم
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.info(f"🧑‍🔬 أنت: {prompt}")
        
        # جلب الرد من الذكاء الاصطناعي مع تجربة النماذج المتاحة تلقائياً
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            
            # قائمة النماذج النشطة حالياً في Groq
            models_to_try = [
                "openai/gpt-oss-20b",
                "openai/gpt-oss-120b",
                "qwen/qwen3.6-27b"
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
                    break # إذا نجح النموذج، توقف عن التجربة
                except Exception as e:
                    last_error = str(e)
                    continue
                    
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.success(f"🤖 HYDROMEM: {response}")
            else:
                st.error(f"عذراً، فشلت جميع النماذج. آخر خطأ: {last_error}")
                
        except Exception as e:
            st.error(f"حدث خطأ غير متوقع: {e}")
