import os
from pathlib import Path
import streamlit as st
import pandas as pd

# Lazy imports - sadece gerektiğinde yükle
def get_imports():
    """Lazy imports to reduce startup time"""
    try:
        from langchain_openai import ChatOpenAI
        from langchain_community.chat_models import ChatOllama
        from langchain_core.messages import AIMessage, HumanMessage
        return True, None
    except Exception as e:
        return False, str(e)

def get_rag_imports():
    """Lazy imports for RAG functionality"""
    try:
        from ingest import index_files, get_vectorstore, reset_vectorstore
        from rag_chain import build_retriever, answer_with_chain
        from agent import build_agent, run_agent
        return True, None
    except Exception as e:
        return False, str(e)

def get_config():
    """Lazy config import"""
    try:
        from config import (
            UPLOAD_DIRECTORY, PERSIST_DIRECTORY,
            OPENAI_API_KEY, DEFAULT_OPENAI_MODEL,
            SEARCH_TYPE, TOP_K, MMR_LAMBDA
        )
        from rag_chain import ensure_dirs
        return True, None
    except Exception as e:
        return False, str(e)

st.set_page_config(page_title="DocuBrain - Intelligent Document Assistant", layout="wide")
st.title("🧠 DocuBrain")
st.markdown("*Turn your PDFs and Docs into an intelligent assistant.*", help="DocuBrain ile dokümanlarınızı akıllı asistanınıza dönüştürün")

# Check imports
import_success, import_error = get_imports()
if not import_success:
    st.error(f"❌ Import hatası: {import_error}")
    st.stop()

rag_success, rag_error = get_rag_imports()
if not rag_success:
    st.error(f"❌ RAG import hatası: {rag_error}")
    st.stop()

config_success, config_error = get_config()
if not config_success:
    st.error(f"❌ Config import hatası: {config_error}")
    st.stop()

# Import everything now that we know it works
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage
from ingest import index_files, get_vectorstore, reset_vectorstore
from rag_chain import build_retriever, answer_with_chain
from agent import build_agent, run_agent
# Logger removed for simplicity
from config import (
    UPLOAD_DIRECTORY, PERSIST_DIRECTORY,
    OPENAI_API_KEY, DEFAULT_OPENAI_MODEL,
    SEARCH_TYPE, TOP_K, MMR_LAMBDA
)
from rag_chain import ensure_dirs
from chat_storage import save_chat_history, load_chat_history, clear_chat_history, get_chat_stats

# State
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "retriever" not in st.session_state:
    st.session_state.retriever = None
# Chat history will be loaded from file storage
if "chat_history_chain" not in st.session_state:
    st.session_state.chat_history_chain = load_chat_history("rag_chain")
if "chat_history_agent" not in st.session_state:
    st.session_state.chat_history_agent = load_chat_history("agent")
if "agent_exec" not in st.session_state:
    st.session_state.agent_exec = None
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []

ensure_dirs(UPLOAD_DIRECTORY, PERSIST_DIRECTORY)

# Sidebar — settings
with st.sidebar:
    st.header("⚙️ Ayarlar")
    # Mod: OpenAI anahtarı varsa varsayılan olarak Agent; yoksa RAG Chain
    mode_default = "Agent (tools)" if OPENAI_API_KEY else "RAG Chain"
    mode = st.selectbox(
        "Kullanım Modu",
        ["RAG Chain", "Agent (tools)"],
        index=1 if mode_default == "Agent (tools)" else 0,
        help="RAG Chain: Basit ve hızlı. Agent: Her soruda bilgi tabanı aracını kullanır (OpenAI önerilir).",
    )

    # Optimized settings - kullanıcı ayarlamasına gerek yok
    top_k = TOP_K  # 8 - optimal chunk sayısı
    search_type = SEARCH_TYPE  # "mmr" - çeşitlilik için
    mmr_lambda = float(MMR_LAMBDA)  # 0.6 - optimal denge
    
    
    # Cevap uzunluğu seçimi
    st.divider()
    st.subheader("💬 Cevap Stili")
    answer_style = st.radio(
        "Cevap uzunluğu seçin:",
        ["Kısa ve Öz", "Detaylı ve Kapsamlı"],
        index=0,
        help="Kısa: 2-3 cümle, Detaylı: Kapsamlı açıklama"
    )

    st.divider()
    st.caption("LLM Seçimi")
    
    # Sadece OpenAI kullanılabilir
    use_openai = True
    if not OPENAI_API_KEY:
        st.info("OPENAI_API_KEY bulunamadı. .env dosyasıyla ekleyebilirsiniz.")
    # Sadece gpt-4o-mini kullanılabilir (maliyet optimizasyonu)
    openai_model = "gpt-4o-mini"
    st.info("🚀 **GPT-4o-mini** seçildi (hızlı + ekonomik)")
    st.caption("OpenAI GPT-4o-mini modeli kullanılıyor.")

    if st.button("🗑️ Veri Tabanını Sıfırla"):
        reset_vectorstore()
        st.session_state.vectorstore = None
        st.session_state.retriever = None
        st.session_state.agent_exec = None
        st.success("Chroma veritabanı sıfırlandı.")
    

# Tabs
tab_kb, tab_chat = st.tabs(["📁 Knowledge Base", "💬 Chat"])

with tab_kb:
    st.subheader("Dosya Yükle (PDF / DOCX)")
    
    # Sayfa yüklendiğinde mevcut dosyaları kontrol et
    if not st.session_state.indexed_files:
        existing_files = [p for p in UPLOAD_DIRECTORY.iterdir() if p.suffix.lower() in [".pdf", ".docx"]]
        if existing_files:
            st.session_state.indexed_files = existing_files
            # Eğer vectorstore varsa, dosyalar zaten indekslenmiş demektir
            if st.session_state.vectorstore is None:
                try:
                    st.session_state.vectorstore = get_vectorstore()
                    st.session_state.retriever = build_retriever(
                        st.session_state.vectorstore,
                        search_type=SEARCH_TYPE,
                        top_k=TOP_K,
                        mmr_lambda=MMR_LAMBDA,
                    )
                except Exception:
                    pass  # Vectorstore yoksa yeni indeksleme gerekir
    
    files = st.file_uploader("Dosyaları seçin", type=["pdf", "docx"], accept_multiple_files=True)
    if files:
        saved_paths = []
        for f in files:
            save_path = UPLOAD_DIRECTORY / f.name
            with open(save_path, "wb") as out:
                out.write(f.read())
            saved_paths.append(save_path)
        st.session_state.uploaded_files = saved_paths
        st.success(f"{len(saved_paths)} dosya yüklendi.")
        
        # Logging removed for simplicity

    if st.button("📥 İndeksle (Chroma'ya ekle)"):
        path_list = [p for p in UPLOAD_DIRECTORY.iterdir() if p.suffix.lower() in [".pdf", ".docx"]]
        if not path_list:
            st.warning("Önce en az bir PDF/DOCX yükleyin.")
        else:
            try:
                import time
                start_t = time.time()
                with st.spinner("Belgeler indeksleniyor, lütfen bekleyin…"):
                    raw_n, chunk_n = index_files(path_list)
                elapsed = time.time() - start_t
                st.success(f"Yüklendi: {raw_n} belge, {chunk_n} parça eklendi. ({elapsed:.1f}s)")
                st.session_state.vectorstore = get_vectorstore()
                st.session_state.retriever = build_retriever(
                    st.session_state.vectorstore,
                    search_type=search_type,
                    top_k=top_k,
                    mmr_lambda=mmr_lambda,
                )
                st.session_state.agent_exec = None  # rebuild agent next time
                st.session_state.indexed_files = path_list  # Store indexed files
                
                # Logging removed for simplicity
            except OSError as e:
                if getattr(e, 'errno', None) == 28:
                    st.error(
                        "Disk dolu: HuggingFace modeli indirilirken yer kalmadı. \n\n"
                        "Çözüm: Daha boş bir dizine cache yönlendirin (örn. D:):\n"
                        "- PowerShell (geçici): $env:HF_HOME=\"D:\\hf_cache\"\n"
                        "- Kalıcı: Sistem Değişkeni olarak HF_HOME veya HUGGINGFACE_HUB_CACHE ekleyin.\n"
                        "- Alternatif: .env içine EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2 yazın (daha küçük model).\n"
                        "- Veya disk alanı boşaltın."
                    )
                else:
                    st.error(f"İndeksleme sırasında hata: {e}")

    # Show uploaded files info
    st.divider()
    st.subheader("📊 Dosya Durumu")
    
    if st.session_state.indexed_files:
        st.success(f"✅ **İndekslenen dosyalar:** {len(st.session_state.indexed_files)} dosya")
        
        # Tablo formatında göster
        file_data = []
        for file_path in st.session_state.indexed_files:
            file_size = os.path.getsize(file_path) / 1024  # KB
            file_data.append({
                "Dosya Adı": file_path.name,
                "Tip": file_path.suffix.upper(),
                "Boyut (KB)": f"{file_size:.1f}"
            })
        
        if file_data:
            df = pd.DataFrame(file_data)
            st.dataframe(df, width="stretch", hide_index=True)
            
            # Dosya silme seçeneği
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_files = st.multiselect(
                    "Silmek istediğiniz dosyaları seçin:",
                    options=[f.name for f in st.session_state.indexed_files],
                    help="Birden fazla dosya seçebilirsiniz"
                )
            with col2:
                st.write("")  # Boşluk için
                if st.button("🗑️ Seçili Dosyaları Sil", type="secondary", disabled=not selected_files):
                    # Seçili dosyaları sil
                    for file_name in selected_files:
                        for file_path in st.session_state.indexed_files:
                            if file_path.name == file_name:
                                try:
                                    # Dosyayı fiziksel olarak sil
                                    file_path.unlink()
                                    st.success(f"✅ {file_name} silindi")
                                except Exception as e:
                                    st.error(f"❌ {file_name} silinemedi: {e}")
                    
                    # Session state'i güncelle
                    st.session_state.indexed_files = [
                        f for f in st.session_state.indexed_files 
                        if f.name not in selected_files
                    ]
                    
                    # Eğer tüm dosyalar silindiyse vectorstore'u temizle
                    if not st.session_state.indexed_files:
                        reset_vectorstore()
                        st.session_state.vectorstore = None
                        st.session_state.retriever = None
                        st.session_state.agent_exec = None
                        st.info("Tüm dosyalar silindi. Veri tabanı sıfırlandı.")
                    else:
                        # Kalan dosyalar varsa yeniden indeksle
                        st.warning("⚠️ Dosyalar silindi. Değişikliklerin etkili olması için 'İndeksle' butonuna tıklayın.")
                    
                    st.rerun()
    else:
        st.info("📁 Henüz indekslenmiş dosya yok. Dosya yükleyip 'İndeksle' butonuna tıklayın.")
    
    if st.session_state.uploaded_files:
        st.caption(f"Son yükleme: {len(st.session_state.uploaded_files)} dosya")
    
    st.caption(f"💾 Chroma klasörü: {PERSIST_DIRECTORY}")

with tab_chat:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Sohbet")
    with col2:
        if st.button("🗑️ Sohbeti Temizle", help="Tüm sohbet geçmişini sil"):
            clear_chat_history()  # Tüm sohbet geçmişini temizle
            st.session_state.chat_history_chain = []
            st.session_state.chat_history_agent = []
            st.success("✅ Sohbet geçmişi temizlendi!")
            st.rerun()
    
    # Sohbet yönetimi
    if st.session_state.chat_history_chain or st.session_state.chat_history_agent:
        st.divider()
        st.subheader("📊 Sohbet Yönetimi")
        
        # Sohbet geçmişini göster
        all_chats = []
        for i, msg in enumerate(st.session_state.chat_history_chain):
            if isinstance(msg, HumanMessage):
                all_chats.append({
                    "Mod": "RAG Chain",
                    "Soru": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                    "Tip": "Soru",
                    "Index": f"chain_{i}"
                })
            elif isinstance(msg, AIMessage):
                all_chats.append({
                    "Mod": "RAG Chain", 
                    "Soru": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                    "Tip": "Cevap",
                    "Index": f"chain_{i}"
                })
        
        for i, msg in enumerate(st.session_state.chat_history_agent):
            if isinstance(msg, HumanMessage):
                all_chats.append({
                    "Mod": "Agent",
                    "Soru": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                    "Tip": "Soru",
                    "Index": f"agent_{i}"
                })
            elif isinstance(msg, AIMessage):
                all_chats.append({
                    "Mod": "Agent",
                    "Soru": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                    "Tip": "Cevap", 
                    "Index": f"agent_{i}"
                })
        
        if all_chats:
            # Sohbet listesi
            df = pd.DataFrame(all_chats)
            st.dataframe(df, width="stretch", hide_index=True)
            
            # Sohbet silme seçeneği
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_chats = st.multiselect(
                    "Silmek istediğiniz sohbetleri seçin:",
                    options=[f"{chat['Mod']} - {chat['Tip']} ({chat['Index']})" for chat in all_chats],
                    help="Birden fazla sohbet seçebilirsiniz"
                )
            with col2:
                st.write("")  # Boşluk için
                if st.button("🗑️ Seçili Sohbetleri Sil", type="secondary", disabled=not selected_chats):
                    # Seçili sohbetleri sil
                    for selected in selected_chats:
                        # Index'i parse et
                        if "chain_" in selected:
                            index = int(selected.split("chain_")[1].split(")")[0])
                            if index < len(st.session_state.chat_history_chain):
                                st.session_state.chat_history_chain.pop(index)
                        elif "agent_" in selected:
                            index = int(selected.split("agent_")[1].split(")")[0])
                            if index < len(st.session_state.chat_history_agent):
                                st.session_state.chat_history_agent.pop(index)
                    
                    # Dosyaya kaydet
                    save_chat_history(st.session_state.chat_history_chain, "rag_chain")
                    save_chat_history(st.session_state.chat_history_agent, "agent")
                    
                    st.success("✅ Seçili sohbetler silindi!")
                    st.rerun()
    else:
        st.info("📁 Henüz sohbet geçmişi yok. Sohbet başlatın!")
    # Ensure vectorstore
    if st.session_state.vectorstore is None:
        try:
            st.session_state.vectorstore = get_vectorstore()
            st.session_state.retriever = build_retriever(
                st.session_state.vectorstore,
                search_type=search_type,
                top_k=top_k,
                mmr_lambda=mmr_lambda,
            )
        except Exception as e:
            st.info("Önce dosya yükleyip indeksleyin.")
    # LLM init - Sadece OpenAI
    llm = None
    if OPENAI_API_KEY:
        llm = ChatOpenAI(
            model=openai_model, 
            temperature=0.1,
            max_tokens=1000
        )  # tool-calling destekli + maliyet optimizasyonu
    else:
        # Fallback (chain modunda çalışır). Ollama kurulu değilse hata verir.
        try:
            llm = ChatOllama(model="llama3", temperature=0)
            if mode == "Agent (tools)":
                st.warning("Ajan modu için OpenAI önerilir; yerel modeller her zaman tool-calling desteklemez.")
        except Exception:
            llm = None

    # Init agent if needed - cevap stiline göre yeniden oluştur
    if mode == "Agent (tools)" and st.session_state.retriever and llm:
        # Cevap stili değiştiyse agent'i yeniden oluştur
        is_short = (answer_style == "Kısa ve Öz")
        current_style = getattr(st.session_state, 'agent_answer_style', None)
        
        if st.session_state.agent_exec is None or current_style != is_short:
            try:
                st.session_state.agent_exec = build_agent(llm, st.session_state.retriever, is_short)
                st.session_state.agent_answer_style = is_short
            except Exception as e:
                st.error(f"Agent oluşturulamadı: {e}")
                st.session_state.agent_exec = None

    # Chat history
    chat_container = st.container()
    with chat_container:
        history = st.session_state.chat_history_agent if mode == "Agent (tools)" else st.session_state.chat_history_chain
        for m in history:
            role = "assistant" if isinstance(m, AIMessage) else "user"
            with st.chat_message(role):
                st.markdown(m.content)

    question = st.chat_input("Sorunuzu yazın…")
    if question and st.session_state.retriever and llm:
        if mode == "RAG Chain":
            # RAG Chain modu
            st.session_state.chat_history_chain.append(HumanMessage(content=question))
            
            # Cevap stiline göre is_short parametresini belirle
            is_short = (answer_style == "Kısa ve Öz")
            result = answer_with_chain(llm, st.session_state.retriever, question, is_short)
            
            answer = result["answer"]
            cites = result["citations"]
            st.session_state.chat_history_chain.append(AIMessage(content=answer + ("\n\n" + cites if cites else "")))
            
            # Sohbet geçmişini dosyaya kaydet
            save_chat_history(st.session_state.chat_history_chain, "rag_chain")
            
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    if cites:
                        st.caption(cites)
            
            # Logging removed for simplicity
        else:
            # Agent modu
            if st.session_state.agent_exec:
                st.session_state.chat_history_agent.append(HumanMessage(content=question))
                result = run_agent(st.session_state.agent_exec, question, st.session_state.chat_history_agent)
                answer = result["answer"]
                cites = result["citations"]
                st.session_state.chat_history_agent.append(AIMessage(content=answer + ("\n\n" + cites if cites else "")))
                
                # Sohbet geçmişini dosyaya kaydet
                save_chat_history(st.session_state.chat_history_agent, "agent")
                
                with chat_container:
                    with st.chat_message("assistant"):
                        st.markdown(answer)
                        if cites:
                            st.caption(cites)
                
                # Logging removed for simplicity
            else:
                st.error("Agent başlatılamadı. RAG Chain moduna geçin veya OpenAI anahtarı ekleyin.")
    elif question and not llm:
        st.error("LLM başlatılamadı. OpenAI anahtarı ekleyin veya Ollama kurun.")

# Logs tab removed for simplicity
