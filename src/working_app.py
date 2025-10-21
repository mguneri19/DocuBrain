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
tab1, tab2, tab3 = st.tabs(["📚 Knowledge Base", "💬 Chat", "📊 Logs"])

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
                        # Convert string paths to Path objects
                        from pathlib import Path
                        path_objects = [Path(p) for p in saved_paths]
                        result = index_files(path_objects)
                        if result and len(result) == 2:
                            docs_count, chunks_count = result
                            st.session_state.vectorstore = get_vectorstore()
                            st.session_state.indexed_files = [os.path.basename(path) for path in saved_paths]
                            st.success(f"✅ {docs_count} dosya, {chunks_count} chunk başarıyla indekslendi!")
                            
                            # Logging removed for simplicity
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
    
    # Check if files are indexed
    if not st.session_state.indexed_files:
        st.warning("⚠️ Önce dosyaları indekslemeniz gerekiyor. Knowledge Base sekmesine gidin.")
    else:
        st.success(f"📚 **{len(st.session_state.indexed_files)} dosya indekslendi**")
    
    # Chat input
    question = st.text_input("Sorunuzu yazın:", placeholder="Dokümanlarınız hakkında soru sorun...")
    
    if st.button("Gönder") and question:
        st.write(f"**Soru:** {question}")
        
        if not st.session_state.indexed_files:
            st.error("❌ Önce dosyaları indekslemeniz gerekiyor!")
        else:
            try:
                # Import RAG modules
                from rag_chain import build_retriever, answer_with_chain
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import AIMessage, HumanMessage
                
                # Initialize LLM
                llm = ChatOpenAI(
                    model=DEFAULT_OPENAI_MODEL,
                    api_key=OPENAI_API_KEY,
                    temperature=0.7
                )
                
                # Build retriever if not exists
                if not st.session_state.retriever:
                    st.session_state.retriever = build_retriever(st.session_state.vectorstore)
                
                # Determine answer style
                is_short = (answer_style == "Kısa ve Öz")
                
                # Get answer
                with st.spinner("🤔 Cevap oluşturuluyor..."):
                    if mode == "RAG Chain":
                        result = answer_with_chain(
                            st.session_state.retriever,
                            llm,
                            question,
                            st.session_state.chat_history_chain,
                            is_short
                        )
                        
                        if result and "answer" in result:
                            answer = result["answer"]
                            st.write("**Cevap:**", answer)
                            
                            # Update chat history
                            st.session_state.chat_history_chain.append(HumanMessage(content=question))
                            st.session_state.chat_history_chain.append(AIMessage(content=answer))
                            
                            # Show token usage if available
                            if "tokens" in result:
                                tokens = result["tokens"]
                                st.caption(f"Token kullanımı: {tokens.get('total_tokens', 'N/A')} | Maliyet: ${tokens.get('total_cost', 'N/A')}")
                            
                            # Logging removed for simplicity
                        else:
                            st.error("❌ Cevap oluşturulamadı!")
                    
                    elif mode == "Agent (tools)":
                        # Import agent modules
                        from agent import build_agent, run_agent
                        
                        # Build agent if not exists
                        if not st.session_state.agent_exec:
                            st.session_state.agent_exec = build_agent(
                                st.session_state.retriever,
                                llm,
                                is_short
                            )
                        
                        result = run_agent(
                            st.session_state.agent_exec,
                            question,
                            st.session_state.chat_history_agent
                        )
                        
                        if result and "answer" in result:
                            answer = result["answer"]
                            st.write("**Cevap:**", answer)
                            
                            # Update chat history
                            st.session_state.chat_history_agent.append(HumanMessage(content=question))
                            st.session_state.chat_history_agent.append(AIMessage(content=answer))
                            
                            # Show token usage if available
                            if "tokens" in result:
                                tokens = result["tokens"]
                                st.caption(f"Token kullanımı: {tokens.get('total_tokens', 'N/A')} | Maliyet: ${tokens.get('total_cost', 'N/A')}")
                            
                            # Logging removed for simplicity
                        else:
                            st.error("❌ Agent cevap oluşturamadı!")
                
            except ImportError as e:
                st.error(f"❌ Import hatası: {str(e)}")
                st.warning("⚠️ RAG modülleri yüklenemedi. Ana uygulamayı kullanın.")
            except Exception as e:
                st.error(f"❌ Chat hatası: {str(e)}")
    
    # Show chat history
    if st.session_state.chat_history_chain or st.session_state.chat_history_agent:
        st.divider()
        st.write("**Sohbet Geçmişi:**")
        
        # Show appropriate chat history based on mode
        chat_history = st.session_state.chat_history_chain if mode == "RAG Chain" else st.session_state.chat_history_agent
        
        for i, message in enumerate(chat_history):
            if isinstance(message, HumanMessage):
                st.write(f"**👤 Soru {i//2 + 1}:** {message.content}")
            elif isinstance(message, AIMessage):
                st.write(f"**🤖 Cevap {i//2 + 1}:** {message.content}")
                st.divider()
        
        # Clear chat button
        if st.button("🗑️ Sohbeti Temizle"):
            if mode == "RAG Chain":
                st.session_state.chat_history_chain = []
            else:
                st.session_state.chat_history_agent = []
            st.rerun()

with tab3:
    st.write("**Kullanıcı Aktivite Logları**")
    
    st.info("📊 **Logs sekmesi kaldırıldı** - Uygulama daha hafif hale getirildi")

st.info("🎯 **Working DocuBrain** - Ana özellikler yavaş yavaş eklenecek")
