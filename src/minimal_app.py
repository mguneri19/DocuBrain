import streamlit as st
import os

st.set_page_config(page_title="DocuBrain Minimal", layout="wide")
st.title("🧠 DocuBrain Minimal")
st.write("Basit test uygulaması")

# Environment variables kontrolü
if 'OPENAI_API_KEY' in os.environ:
    st.success("✅ OPENAI_API_KEY bulundu")
else:
    st.warning("⚠️ OPENAI_API_KEY bulunamadı")

# Basit import testleri
try:
    import pandas as pd
    st.success("✅ Pandas import başarılı")
except Exception as e:
    st.error(f"❌ Pandas import hatası: {e}")

try:
    from langchain_openai import ChatOpenAI
    st.success("✅ ChatOpenAI import başarılı")
except Exception as e:
    st.error(f"❌ ChatOpenAI import hatası: {e}")

st.write("Minimal test tamamlandı!")
