import streamlit as st
from main import main  # reuse your logic

st.set_page_config(page_title="Auto Email Responder", layout="centered")
st.title("📬 Auto Email Responder")

st.write("All secrets:", st.secrets)
st.write("Google section:", st.secrets.get("google", "Not found"))

if st.button("Send Replies to New Google Form Responses"):
    try:
        main()
        st.success("✅ Replies sent successfully!")
    except Exception as e:
        st.error(f"❌ Error: {e}")
