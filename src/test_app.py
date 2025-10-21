import streamlit as st

st.set_page_config(page_title="DocuBrain Test", layout="wide")
st.title("🧠 DocuBrain Test")
st.write("Uygulama çalışıyor!")

# Test imports
try:
    from config import OPENAI_API_KEY
    st.success("✅ Config import başarılı")
except Exception as e:
    st.error(f"❌ Config import hatası: {e}")

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    st.success("✅ HuggingFaceEmbeddings import başarılı")
except Exception as e:
    st.error(f"❌ HuggingFaceEmbeddings import hatası: {e}")

try:
    from langchain_chroma import Chroma
    st.success("✅ Chroma import başarılı")
except Exception as e:
    st.error(f"❌ Chroma import hatası: {e}")

st.write("Test tamamlandı!")
