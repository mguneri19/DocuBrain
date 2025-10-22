import streamlit as st
import os

st.set_page_config(page_title="DocuBrain Test", layout="wide")

st.title("🧠 DocuBrain - Minimal Test")
st.write("Bu en basit test uygulaması")

# Check API key
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    st.success("✅ API Key bulundu!")
else:
    st.error("❌ API Key bulunamadı")

st.info("🎯 Bu minimal test çalışırsa, sorun ana uygulamada")
