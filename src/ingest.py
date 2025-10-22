"""
Doküman yükleme ve indeksleme modülü

Bu modül şu görevleri yerine getirir:
- PDF ve DOCX dosyalarını yükler
- Dokümanları chunk'lara böler (RecursiveCharacterTextSplitter)
- Embeddings oluşturur (HuggingFace BAAI/bge-m3 modeli)
- ChromaDB'ye indeksler ve BM25 index'i oluşturur
"""
from __future__ import annotations
from typing import List, Tuple
from pathlib import Path
import hashlib

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import (
    PERSIST_DIRECTORY, UPLOAD_DIRECTORY,
    EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP
)
from rag_chain import ensure_dirs

ALLOWED_EXTS = {".pdf", ".docx"}

def _doc_id(doc: Document) -> str:
    """
    Doküman için benzersiz ID oluşturur (tekrar önleme).
    
    """
    meta = doc.metadata or {}
    base = f"{meta.get('source','')}-{meta.get('page','')}-{meta.get('start_index','')}-{len(doc.page_content)}"
    return hashlib.sha1(base.encode('utf-8')).hexdigest()

def _load_single_file(path: Path) -> List[Document]:
    """
    Tek bir dosyayı yükler (PDF veya DOCX).
    
    """
    ext = path.suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(str(path))
        docs = loader.load()
        # Ensure 'source' in metadata
        for d in docs:
            d.metadata.setdefault("source", str(path))
        return docs
    elif ext == ".docx":
        loader = Docx2txtLoader(str(path))
        docs = loader.load()
        for d in docs:
            d.metadata.setdefault("source", str(path))
        return docs
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def load_documents(paths: List[Path]) -> List[Document]:
    """
    Birden fazla dosyayı yükler.
    
    """
    docs: List[Document] = []
    for p in paths:
        if p.suffix.lower() not in ALLOWED_EXTS:
            continue
        docs.extend(_load_single_file(p))
    return docs

def split_documents(docs: List[Document]) -> List[Document]:
    """
    Dokümanları daha küçük chunk'lara böler (text splitting).
    
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    # propagate source/page metadata & start_index
    for c in chunks:
        c.metadata.setdefault("source", c.metadata.get("source", ""))
    return chunks

def get_embeddings():
    """
    Embedding modeli oluşturur (HuggingFace BAAI/bge-m3).
    
    """
    # Force CPU device to avoid GPU/meta-tensor issues on some Windows setups
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

def get_vectorstore(embedding=None) -> Chroma:
    """
    ChromaDB vector store'u oluşturur veya yükler.
    
    """
    emb = embedding or get_embeddings()
    ensure_dirs(PERSIST_DIRECTORY)
    return Chroma(
        collection_name="knowledge_base",
        embedding_function=emb,
        persist_directory=str(PERSIST_DIRECTORY),
    )

def index_files(file_paths: List[Path]) -> Tuple[int, int]:
    """
    Dosyaları yükler, chunk'lar ve hem ChromaDB hem BM25'e indeksler.
    
    """
    raw_docs = load_documents(file_paths)
    chunks = split_documents(raw_docs)

    vs = get_vectorstore()
    # Add with deterministic IDs to avoid duplicates
    ids = [_doc_id(c) for c in chunks]
    vs.add_documents(chunks, ids=ids)
    vs.persist()
    
    return len(raw_docs), len(chunks)

def reset_vectorstore():
    """
    Tüm indekslenmiş veriyi siler (ChromaDB).
    
    """
    # Danger: deletes all persisted data
    import shutil
    if PERSIST_DIRECTORY.exists():
        shutil.rmtree(PERSIST_DIRECTORY)
    ensure_dirs(PERSIST_DIRECTORY)
