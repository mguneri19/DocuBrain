"""
Utility fonksiyonları - Dizin yönetimi ve doküman formatlama

Bu modül şu görevleri yerine getirir:
- Dizinlerin otomatik oluşturulması
- Kaynak gösterimlerinin formatlanması
- Dokümanların prompt için hazırlanması
"""
from typing import List, Dict
from langchain_core.documents import Document
from pathlib import Path

def ensure_dirs(*paths: Path) -> None:
    """
    Belirtilen dizinlerin var olduğundan emin olur, yoksa oluşturur.
    
    """
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def format_citations(docs: List[Document]) -> str:
    """
    Dokümanlardan kaynak gösterimleri oluşturur (alıntı formatı).
    
    """
    if not docs:
        return ""
    items = []
    seen = set()
    for d in docs:
        meta = d.metadata or {}
        src = Path(meta.get("source", "unknown")).name
        page = meta.get("page", None)
        key = (src, page)
        if key in seen:
            continue
        seen.add(key)
        if page is not None:
            items.append(f"[kaynak: {src} p.{page + 1}]")
        else:
            items.append(f"[kaynak: {src}]")
    return " ".join(items)

def format_docs_for_prompt(docs: List[Document]) -> str:
    """
    Dokümanları LLM prompt'u için formatlar (bağlam oluşturma).
    
    """
    blocks = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "")
        page = d.metadata.get("page", None)
        header = f"--- DOC {i} | {src}" + (f" | page {page + 1}" if page is not None else "") + " ---"
        blocks.append(header + "\n" + d.page_content.strip())
    return "\n\n".join(blocks)
