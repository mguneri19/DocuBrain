import os
import streamlit as st

# Streamlit config
st.set_page_config(
    page_title="DocuBrain - Ultra Minimal",
    layout="wide"
)

# Basic UI
st.title("🧠 DocuBrain - Ultra Minimal")
st.markdown("*Turn your PDFs and Docs into an intelligent assistant.*")

# Check API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
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
        
        if st.button("📝 İndeksle"):
            st.info("🔄 İndeksleme işlemi başlatılıyor...")
            
            # Try basic indexing
            try:
                # Only import when needed
                from pathlib import Path
                from config import UPLOAD_DIRECTORY
                
                # Save files
                saved_paths = []
                for uploaded_file in uploaded_files:
                    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
                    file_path = os.path.join(UPLOAD_DIRECTORY, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    saved_paths.append(file_path)
                
                st.success(f"✅ {len(saved_paths)} dosya kaydedildi!")
                st.warning("⚠️ Tam indeksleme özelliği henüz aktif değil.")
                
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")

with tab2:
    st.write("**Sohbet**")
    
    question = st.text_input("Sorunuzu yazın:")
    
    if st.button("Gönder") and question:
        st.write(f"**Soru:** {question}")
        st.info("🔄 Cevap oluşturuluyor...")
        
        # Try basic chat
        try:
            from langchain_openai import ChatOpenAI
            from config import DEFAULT_OPENAI_MODEL
            
            # Initialize LLM
            llm = ChatOpenAI(
                model=DEFAULT_OPENAI_MODEL,
                api_key=openai_api_key,
                temperature=0.7
            )
            
            # Simple response
            response = llm.invoke(question)
            st.write("**Cevap:**", response.content)
            
        except Exception as e:
            st.error(f"❌ Chat hatası: {str(e)}")
            st.warning("⚠️ Basit chat özelliği test ediliyor...")

st.info("🎯 **Ultra Minimal DocuBrain** - Sadece temel özellikler")
