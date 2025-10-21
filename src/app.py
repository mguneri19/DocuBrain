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
        from logger import log_activity, get_logs, get_stats, clear_logs
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
        from utils import ensure_dirs
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
from logger import log_activity, get_logs, get_stats, clear_logs
from config import (
    UPLOAD_DIRECTORY, PERSIST_DIRECTORY,
    OPENAI_API_KEY, DEFAULT_OPENAI_MODEL,
    SEARCH_TYPE, TOP_K, MMR_LAMBDA
)
from utils import ensure_dirs

# State
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
tab_kb, tab_chat, tab_logs = st.tabs(["📁 Knowledge Base", "💬 Chat", "📊 Logs"])

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
        
        # Log kaydı
        log_activity(
            activity_type="file_upload",
            details={"file_count": len(saved_paths), "files": [f.name for f in saved_paths]}
        )

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
                
                # Log kaydı
                log_activity(
                    activity_type="indexing",
                    details={
                        "file_count": len(path_list),
                        "raw_docs": raw_n,
                        "chunks": chunk_n,
                        "duration": f"{elapsed:.1f}s"
                    }
                )
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
            st.session_state.chat_history_chain = []
            st.session_state.chat_history_agent = []
            st.rerun()
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
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    if cites:
                        st.caption(cites)
            
            # Log kaydı
            tokens_info = result.get("tokens", {})
            log_activity(
                activity_type="chat_rag",
                details={
                    "mode": "RAG Chain",
                    "answer_style": answer_style,
                    "question_length": len(question),
                    "answer_length": len(answer),
                    "prompt_tokens": tokens_info.get("prompt_tokens", 0),
                    "completion_tokens": tokens_info.get("completion_tokens", 0),
                    "total_tokens": tokens_info.get("total_tokens", 0),
                    "cost_usd": round(tokens_info.get("total_cost", 0), 6)
                }
            )
        else:
            # Agent modu
            if st.session_state.agent_exec:
                st.session_state.chat_history_agent.append(HumanMessage(content=question))
                result = run_agent(st.session_state.agent_exec, question, st.session_state.chat_history_agent)
                answer = result["answer"]
                cites = result["citations"]
                st.session_state.chat_history_agent.append(AIMessage(content=answer + ("\n\n" + cites if cites else "")))
                with chat_container:
                    with st.chat_message("assistant"):
                        st.markdown(answer)
                        if cites:
                            st.caption(cites)
                
                # Log kaydı
                tokens_info = result.get("tokens", {})
                log_activity(
                    activity_type="chat_agent",
                    details={
                        "mode": "Agent (tools)",
                        "answer_style": answer_style,
                        "question_length": len(question),
                        "answer_length": len(answer),
                        "prompt_tokens": tokens_info.get("prompt_tokens", 0),
                        "completion_tokens": tokens_info.get("completion_tokens", 0),
                        "total_tokens": tokens_info.get("total_tokens", 0),
                        "cost_usd": round(tokens_info.get("total_cost", 0), 6)
                    }
                )
            else:
                st.error("Agent başlatılamadı. RAG Chain moduna geçin veya OpenAI anahtarı ekleyin.")
    elif question and not llm:
        st.error("LLM başlatılamadı. OpenAI anahtarı ekleyin veya Ollama kurun.")

with tab_logs:
    st.subheader("📊 Aktivite Logları")
    
    # İstatistikler
    stats = get_stats()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Toplam Aktivite", stats["total_activities"])
    with col2:
        st.metric("Benzersiz Kullanıcı", stats["unique_users"])
    with col3:
        total_chats = stats["activity_counts"].get("chat_rag", 0) + stats["activity_counts"].get("chat_agent", 0)
        st.metric("Toplam Sohbet", total_chats)
    with col4:
        st.metric("Dosya Yükleme", stats["activity_counts"].get("file_upload", 0))
    
    # Token istatistiklerini hesapla
    logs = get_logs(limit=1000)
    total_tokens = 0
    total_cost = 0.0
    for log in logs:
        details = log.get("details", {})
        total_tokens += details.get("total_tokens", 0)
        total_cost += details.get("cost_usd", 0)
    
    with col5:
        st.metric("Toplam Token", f"{total_tokens:,}")
    
    # Maliyet bilgisi
    if total_cost > 0:
        st.info(f"💰 **Toplam Maliyet:** ${total_cost:.6f} USD")
    
    st.divider()
    
    # Aktivite dağılımı
    if stats["activity_counts"]:
        st.subheader("📈 Aktivite Dağılımı")
        activity_df = pd.DataFrame([
            {"Aktivite": k, "Sayı": v} 
            for k, v in stats["activity_counts"].items()
        ])
        st.bar_chart(activity_df.set_index("Aktivite"))
    
    st.divider()
    
    # Son aktiviteler
    st.subheader("🕐 Son Aktiviteler")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        log_limit = st.slider("Gösterilecek log sayısı", 10, 100, 50)
    with col2:
        st.write("")
        if st.button("🗑️ Logları Temizle", type="secondary"):
            clear_logs()
            st.success("Loglar temizlendi!")
            st.rerun()
    
    logs = get_logs(limit=log_limit)
    
    if logs:
        # Logları ters sırada göster (en yeni üstte)
        for log in reversed(logs):
            timestamp = log.get("timestamp", "")
            activity_type = log.get("activity_type", "unknown")
            user_id = log.get("user_id", "anonymous")
            details = log.get("details", {})
            
            # Emoji seç
            emoji_map = {
                "file_upload": "📤",
                "indexing": "📥",
                "chat_rag": "💬",
                "chat_agent": "🤖",
            }
            emoji = emoji_map.get(activity_type, "📋")
            
            # Detayları göster
            with st.expander(f"{emoji} {activity_type} - {timestamp[:19]}", expanded=False):
                st.write(f"**Kullanıcı:** {user_id}")
                if details:
                    st.json(details)
    else:
        st.info("Henüz log kaydı yok.")
