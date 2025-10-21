import os
import streamlit as st
import pandas as pd

# Streamlit config
st.set_page_config(
    page_title="DocuBrain - Intelligent Document Assistant",
    layout="wide"
)

# Basic UI
st.title("🧠 DocuBrain")
st.markdown("*Turn your PDFs and Docs into an intelligent assistant.*", help="DocuBrain ile dokümanlarınızı akıllı asistanınıza dönüştürün")

# Check basic imports
try:
    from langchain_openai import ChatOpenAI
    st.success("✅ LangChain OpenAI import başarılı")
except Exception as e:
    st.error(f"❌ LangChain OpenAI import hatası: {e}")
    st.stop()

# Check config
try:
    from config import OPENAI_API_KEY, DEFAULT_OPENAI_MODEL
    st.success("✅ Config import başarılı")
except Exception as e:
    st.error(f"❌ Config import hatası: {e}")
    st.stop()

# Check API key
if OPENAI_API_KEY:
    st.success("✅ OPENAI_API_KEY bulundu")
else:
    st.error("❌ OPENAI_API_KEY bulunamadı")
    st.stop()

# Simple tabs
tab1, tab2 = st.tabs(["📚 Knowledge Base", "💬 Chat"])

with tab1:
    st.write("**Dosya Yükleme**")
    uploaded_files = st.file_uploader(
        "PDF veya DOCX dosyalarınızı yükleyin",
        type=['pdf', 'docx'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} dosya yüklendi")
        for file in uploaded_files:
            st.write(f"- {file.name}")

with tab2:
    st.write("**Sohbet**")
    question = st.text_input("Sorunuzu yazın:")
    
    if st.button("Gönder") and question:
        st.write(f"**Soru:** {question}")
        st.info("Basit uygulama çalışıyor! Ana özellikler henüz eklenmedi.")

st.info("🎯 **Basit DocuBrain** - Tüm özellikler yavaş yavaş eklenecek")
