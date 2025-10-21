"""
Kullanıcı aktivitelerini loglama modülü
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import os

# Log dosyası
LOG_DIR = Path(os.getenv("LOG_DIRECTORY", "storage/logs"))
LOG_FILE = LOG_DIR / "activity_log.json"

def ensure_log_dir():
    """Log klasörünü oluştur"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_activity(
    activity_type: str,
    details: Optional[Dict] = None,
    user_id: str = "anonymous"
):
    """
    Aktivite logu kaydet
    
    Args:
        activity_type: Aktivite tipi (file_upload, indexing, chat_rag, chat_agent, etc.)
        details: Ek detaylar
        user_id: Kullanıcı ID (varsayılan: anonymous)
    """
    ensure_log_dir()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "activity_type": activity_type,
        "details": details or {}
    }
    
    # Mevcut logları oku
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            logs = []
    
    # Yeni logu ekle
    logs.append(log_entry)
    
    # Son 1000 logu tut (performans için)
    logs = logs[-1000:]
    
    # Dosyaya yaz
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Log yazma hatası: {e}")

def get_logs(limit: int = 100) -> List[Dict]:
    """
    Logları oku
    
    Args:
        limit: Maksimum log sayısı
    
    Returns:
        Log listesi
    """
    ensure_log_dir()
    
    if not LOG_FILE.exists():
        return []
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        return logs[-limit:]  # Son N logu döndür
    except Exception:
        return []

def get_stats() -> Dict:
    """
    İstatistikleri hesapla
    
    Returns:
        İstatistik dictionary
    """
    logs = get_logs(limit=1000)
    
    if not logs:
        return {
            "total_activities": 0,
            "unique_users": 0,
            "activity_counts": {},
            "last_activity": None
        }
    
    # Aktivite tiplerini say
    activity_counts = {}
    users = set()
    
    for log in logs:
        activity_type = log.get("activity_type", "unknown")
        activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
        users.add(log.get("user_id", "anonymous"))
    
    return {
        "total_activities": len(logs),
        "unique_users": len(users),
        "activity_counts": activity_counts,
        "last_activity": logs[-1].get("timestamp") if logs else None
    }

def clear_logs():
    """Tüm logları temizle"""
    if LOG_FILE.exists():
        LOG_FILE.unlink()

