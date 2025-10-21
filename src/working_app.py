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

# Initialize session state
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "retriever" not in st.session_state:
    st.session_state.retriever = None
if "chat_history_chain" not in st.session_state:
    st.session_state.chat_history_chain = []
if "chat_history_agent" not in st.session_state:
    st.session_state.chat_history_agent = []
if "agent_exec" not in st.session_state:
    st.session_state.agent_exec = None
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []

# Sidebar
with st.sidebar:
    st.header("⚙️ Ayarlar")
    
    # Mode selection
    mode = st.selectbox(
        "Kullanım Modu",
        ["RAG Chain", "Agent (tools)"],
        help="RAG Chain: Basit soru-cevap, Agent: Gelişmiş araçlar"
    )
    
    # Answer style
    answer_style = st.radio(
        "Cevap Stili",
        ["Kısa ve Öz", "Detaylı ve Kapsamlı"],
        help="Cevap uzunluğunu kontrol eder"
    )
    
    # LLM selection
    llm_provider = st.radio(
        "LLM Sağlayıcısı",
        ["OpenAI", "Ollama (Fallback)"],
        help="Hangi LLM sağlayıcısını kullanacağınızı seçin"
    )
    
    # Reset database
    if st.button("🗑️ Veri Tabanını Sıfırla", help="Tüm indekslenmiş dosyaları siler"):
        st.session_state.vectorstore = None
        st.session_state.retriever = None
        st.session_state.chat_history_chain = []
        st.session_state.chat_history_agent = []
        st.session_state.agent_exec = None
        st.session_state.uploaded_files = []
        st.session_state.indexed_files = []
        st.success("✅ Veri tabanı sıfırlandı!")
        st.rerun()

# Main tabs
tab1, tab2 = st.tabs(["📚 Knowledge Base", "💬 Chat"])

with tab1:
    st.write("**Dosya Yükleme**")
    
    # Show indexed files if any
    if st.session_state.indexed_files:
        st.success(f"📚 **İndekslenen Dosyalar:** {len(st.session_state.indexed_files)}")
        
        # File deletion
        files_to_delete = st.multiselect(
            "Silinecek dosyaları seçin:",
            st.session_state.indexed_files,
            help="Seçili dosyaları silmek için kullanın"
        )
        
        if st.button("🗑️ Seçili Dosyaları Sil", disabled=not files_to_delete):
            try:
                from config import UPLOAD_DIRECTORY
                import os
                
                # Delete selected files
                for file_name in files_to_delete:
                    file_path = os.path.join(UPLOAD_DIRECTORY, file_name)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # Update session state
                st.session_state.indexed_files = [f for f in st.session_state.indexed_files if f not in files_to_delete]
                
                # Reset vectorstore if no files left
                if not st.session_state.indexed_files:
                    st.session_state.vectorstore = None
                    st.session_state.retriever = None
                
                st.success(f"✅ {len(files_to_delete)} dosya silindi!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Silme hatası: {str(e)}")
        
        st.divider()
    
    uploaded_files = st.file_uploader(
        "PDF veya DOCX dosyalarınızı yükleyin",
        type=['pdf', 'docx'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} dosya yüklendi")
        for file in uploaded_files:
            st.write(f"- {file.name}")
        
        if st.button("📝 İndeksle", help="Dosyaları vektör veritabanına ekler"):
            st.info("🔄 İndeksleme işlemi başlatılıyor...")
            
            # Try to import indexing modules
            try:
                from ingest import index_files, get_vectorstore
                from config import UPLOAD_DIRECTORY
                from utils import ensure_dirs
                
                # Ensure directories exist
                ensure_dirs()
                
                # Save uploaded files
                saved_paths = []
                for uploaded_file in uploaded_files:
                    # Create upload directory if it doesn't exist
                    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
                    
                    # Save file
                    file_path = os.path.join(UPLOAD_DIRECTORY, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    saved_paths.append(file_path)
                
                # Update session state
                st.session_state.uploaded_files = saved_paths
                
                # Index files
                with st.spinner("📚 Dosyalar indeksleniyor..."):
                    try:
                        result = index_files(saved_paths)
                        if result:
                            st.session_state.vectorstore = get_vectorstore()
                            st.session_state.indexed_files = [os.path.basename(path) for path in saved_paths]
                            st.success(f"✅ {len(saved_paths)} dosya başarıyla indekslendi!")
                        else:
                            st.error("❌ İndeksleme başarısız!")
                    except Exception as e:
                        st.error(f"❌ İndeksleme hatası: {str(e)}")
                        
            except ImportError as e:
                st.error(f"❌ Import hatası: {str(e)}")
                st.warning("⚠️ İndeksleme modülleri yüklenemedi. Ana uygulamayı kullanın.")
            except Exception as e:
                st.error(f"❌ Genel hata: {str(e)}")

with tab2:
    st.write("**Sohbet**")
    
    # Chat input
    question = st.text_input("Sorunuzu yazın:", placeholder="Dokümanlarınız hakkında soru sorun...")
    
    if st.button("Gönder") and question:
        st.write(f"**Soru:** {question}")
        st.info("🔄 Cevap oluşturuluyor...")
        st.warning("⚠️ Bu özellik henüz aktif değil. Simple app sürümünde sadece temel arayüz mevcut.")
        
        # Simulate response
        st.write("**Cevap:** Bu basit sürümde henüz AI cevapları aktif değil. Ana uygulamayı yavaş yavaş düzelteceğiz.")

st.info("🎯 **Working DocuBrain** - Ana özellikler yavaş yavaş eklenecek")
