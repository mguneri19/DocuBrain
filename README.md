# 🧠 DocuBrain

**Turn your PDFs and Docs into an intelligent assistant.**

DocuBrain, **kullanıcının yüklediği PDF ve DOCX** dosyaları üzerinden **RAG tabanlı** akıllı asistan deneyimi sunar. 
Aşağıdaki bileşenleri içerir:
- **Hybrid Retrieval** (BM25 + Vector + RRF + Reranker) ile en isabetli arama
- **LangChain** ile `RecursiveCharacterTextSplitter` (chunking)
- **HuggingFaceEmbeddings** (varsayılan: `BAAI/bge-m3` — çok dilli & normalize)
- **Chroma** (kalıcı vektör veritabanı)
- **RAG Chains** ve **RAG Agents (tool)** modları
- **Token tracking** ve **kullanıcı aktivite logları**
- **Streamlit** ile modern, kullanışlı arayüz

> Varsayılan kurulum, **OpenAI** anahtarı varsa ajan modunu da etkinleştirir. Anahtar yoksa, **RAG Chain** modu tek başına çalışır.

## Kurulum

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Gerekirse düzenleyin
```

> Eğer **GPU** kullanacaksanız, `sentence-transformers` ve PyTorch için uygun sürümü kurmayı unutmayın.

## Çalıştırma

```bash
streamlit run src/app.py
```

## Dosya Yapısı

```
docubrain/
├── requirements.txt
├── .env.example
├── README.md
├── storage/
│   ├── uploads/           # Kullanıcının yüklediği dosyalar
│   ├── chroma_db/         # Chroma kalıcı veritabanı
│   └── logs/              # Kullanıcı aktivite logları
└── src/
    ├── app.py             # Streamlit arayüzü (DocuBrain UI)
    ├── config.py          # Ayarlar
    ├── ingest.py          # PDF/DOCX yükle, parçala ve vektörle
    ├── rag_chain.py       # RAG chain (retrieval + prompt + LLM)
    ├── agent.py           # RAG agent (retriever tool + agent executor)
    ├── hybrid_retriever.py # Hybrid retrieval (BM25 + Vector + RRF + Reranker)
    ├── logger.py          # Kullanıcı aktivite logları
    └── utils.py           # Yardımcılar (citations vs.)
```

## Özellikler

### 🧠 **Akıllı Arama**
- **Hybrid Retrieval**: BM25 (sözcüksel) + Vector (anlamsal) + RRF + Reranker
- **En İsabetli Sonuçlar**: Cross-encoder ile son aşamada reranking
- **Çok Dilli Destek**: Türkçe ve diğer dillerde mükemmel çalışır

### 💬 **İki Mod**
- **RAG Chain**: Her soru için otomatik arama
- **Agent Tools**: Akıllı karar verme ile arama (OpenAI gerekli)

### 📊 **Gelişmiş Özellikler**
- **Token Tracking**: Gerçek maliyet takibi
- **Kullanıcı Logları**: Aktivite analizi ve istatistikler
- **Dosya Yönetimi**: Yükleme, silme, durum takibi
- **Cevap Stilleri**: Kısa/uzun cevap seçenekleri

## Notlar
- **Sadece PDF ve DOCX** desteklidir (tasarım gereği).
- `agent` modu için **tool calling** yeteneği olan bir sohbet modeli gerekir (ör. OpenAI `gpt-4o-mini`). 
- **Embeddings** varsayılanı HF (`BAAI/bge-m3`) olduğundan API anahtarı gerekmeden yerel çalışır.
- Chroma veritabanı **kalıcıdır**; Sıfırlamak için uygulama içindeki "Veri Tabanını Sıfırla" butonunu kullanın.

**DocuBrain ile dokümanlarınızı akıllı asistanınıza dönüştürün!** 🚀