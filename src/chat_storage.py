"""
Sohbet geçmişi depolama modülü - Kalıcı sohbet geçmişi

Bu modül şu görevleri yerine getirir:
- Sohbet geçmişini JSON dosyasında saklama
- Sohbet geçmişini yükleme
- Sohbet geçmişini temizleme
- Sohbet geçmişini yedekleme
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Sohbet geçmişi dosya yolu
CHAT_HISTORY_FILE = Path("storage/chat_history.json")

def ensure_chat_storage():
    """Sohbet depolama dizinini oluşturur."""
    CHAT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

def save_chat_history(chat_history: List[BaseMessage], mode: str = "rag_chain"):
    """
    Sohbet geçmişini dosyaya kaydeder.
    
    Args:
        chat_history: Sohbet geçmişi mesajları
        mode: Sohbet modu ("rag_chain" veya "agent")
    """
    ensure_chat_storage()
    
    # Mesajları serialize et
    messages = []
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            messages.append({"type": "human", "content": msg.content, "timestamp": datetime.now().isoformat()})
        elif isinstance(msg, AIMessage):
            messages.append({"type": "ai", "content": msg.content, "timestamp": datetime.now().isoformat()})
    
    # Mevcut geçmişi yükle
    existing_data = load_all_chat_history()
    
    # Yeni geçmişi ekle
    existing_data[mode] = messages
    
    # Dosyaya kaydet
    with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

def load_chat_history(mode: str = "rag_chain") -> List[BaseMessage]:
    """
    Sohbet geçmişini dosyadan yükler.
    
    Args:
        mode: Sohbet modu ("rag_chain" veya "agent")
    
    Returns:
        Sohbet geçmişi mesajları
    """
    if not CHAT_HISTORY_FILE.exists():
        return []
    
    try:
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = data.get(mode, [])
        chat_history = []
        
        for msg_data in messages:
            if msg_data["type"] == "human":
                chat_history.append(HumanMessage(content=msg_data["content"]))
            elif msg_data["type"] == "ai":
                chat_history.append(AIMessage(content=msg_data["content"]))
        
        return chat_history
    except Exception:
        return []

def load_all_chat_history() -> Dict[str, List[Dict]]:
    """Tüm sohbet geçmişini yükler."""
    if not CHAT_HISTORY_FILE.exists():
        return {"rag_chain": [], "agent": []}
    
    try:
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"rag_chain": [], "agent": []}

def clear_chat_history(mode: str = None):
    """
    Sohbet geçmişini temizler.
    
    Args:
        mode: Temizlenecek mod (None = hepsi)
    """
    if mode is None:
        # Tüm geçmişi temizle
        if CHAT_HISTORY_FILE.exists():
            CHAT_HISTORY_FILE.unlink()
    else:
        # Belirli modu temizle
        existing_data = load_all_chat_history()
        existing_data[mode] = []
        
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

def get_chat_stats() -> Dict[str, Any]:
    """Sohbet istatistiklerini döndürür."""
    all_history = load_all_chat_history()
    
    stats = {
        "total_messages": 0,
        "rag_chain_messages": len(all_history.get("rag_chain", [])),
        "agent_messages": len(all_history.get("agent", [])),
        "last_updated": None
    }
    
    stats["total_messages"] = stats["rag_chain_messages"] + stats["agent_messages"]
    
    # Son güncelleme zamanını bul
    for mode in ["rag_chain", "agent"]:
        messages = all_history.get(mode, [])
        for msg in messages:
            if msg.get("timestamp"):
                if stats["last_updated"] is None or msg["timestamp"] > stats["last_updated"]:
                    stats["last_updated"] = msg["timestamp"]
    
    return stats
