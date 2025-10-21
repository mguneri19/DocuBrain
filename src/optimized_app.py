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

# Streamlit config
st.set_page_config(
    page_title="DocuBrain - Intelligent Document Assistant",
    layout="wide"
)

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

# Main UI
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

st.success("✅ Tüm import'lar başarılı!")
st.write("Optimized app çalışıyor!")
