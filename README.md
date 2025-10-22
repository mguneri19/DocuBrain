# 🧠 DocuBrain: Intelligent Document Assistant

**Turn your PDFs and Docs into an intelligent assistant.**

## Projenin Amacı

DocuBrain, **Retrieval-Augmented Generation (RAG)** teknolojisi kullanarak, kullanıcıların yüklediği PDF ve DOCX dokümanları üzerinden akıllı soru-cevap sistemi sunan bir web uygulamasıdır. Proje, dokümanların içeriğini anlayarak kullanıcı sorularına doğru ve bağlamsal cevaplar üretmeyi amaçlamaktadır.

## Veri Seti Hakkında Bilgi

- **Dosya Formatları**: PDF ve DOCX dokümanları
- **Doküman İşleme**: RecursiveCharacterTextSplitter ile chunk'lara bölme
- **Embedding Modeli**: sentence-transformers/all-MiniLM-L6-v2 (hafif ve hızlı)
- **Vektör Veritabanı**: ChromaDB ile kalıcı depolama
- **Dil Desteği**: Türkçe ve çok dilli doküman desteği

## Kullanılan Yöntemler

### 🔍 **Retrieval-Augmented Generation (RAG)**
- **Vector Search**: Semantic similarity ile doküman parçalarını bulma
- **MMR (Maximum Marginal Relevance)**: Çeşitlilik ve relevans dengesi
- **Context Assembly**: İlgili parçaları birleştirerek bağlam oluşturma

### 🤖 **İki Farklı Mod**
- **RAG Chain**: Her soru için otomatik doküman arama ve cevap üretme
- **Agent Tools**: Akıllı karar verme ile arama (OpenAI tool-calling)

### 🛠️ **Teknoloji Stack**
- **Frontend**: Streamlit (modern web arayüzü)
- **LLM**: OpenAI GPT-4o-mini (maliyet optimizasyonu)
- **Embeddings**: HuggingFace sentence-transformers
- **Vector DB**: ChromaDB (kalıcı depolama)
- **Framework**: LangChain (orchestration)

### 📊 **Gelişmiş Özellikler**
- **Kalıcı Sohbet Geçmişi**: JSON tabanlı depolama
- **Token Tracking**: API maliyet takibi
- **Dosya Yönetimi**: Yükleme, silme, durum takibi
- **Cevap Stilleri**: Kısa/uzun cevap seçenekleri

## Elde Edilen Sonuçlar

### ✅ **Başarılı Özellikler**
- **Hafif Model**: 90MB embedding modeli ile hızlı başlangıç
- **Kalıcı Depolama**: Sohbet geçmişi ve doküman indeksleri korunur
- **İki Mod Desteği**: RAG Chain ve Agent modları
- **Streamlit Cloud**: Başarılı deployment
- **Temiz Arayüz**: Kullanıcı dostu interface

### 📈 **Performans Optimizasyonları**
- **Memory Optimization**: Ağır modeller kaldırıldı
- **Import Optimization**: Gereksiz bağımlılıklar temizlendi
- **Code Cleanup**: Kullanılmayan fonksiyonlar kaldırıldı
- **Deployment Ready**: Streamlit Cloud uyumlu

### 🎯 **Kullanım Senaryoları**
- **Kurumsal Dokümanlar**: PDF raporları, dökümanlar
- **Eğitim Materyalleri**: Ders notları, kitaplar
- **Teknik Dokümantasyon**: API dökümanları, kılavuzlar
- **Araştırma Makaleleri**: Akademik yayınlar

## Kurulum ve Çalıştırma

### Gereksinimler
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Çalıştırma
```bash
streamlit run src/app.py
```

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Dosya Yapısı

```
docubrain/
├── requirements.txt
├── .env.example
├── README.md
├── storage/
│   ├── uploads/           # Kullanıcı dosyaları
│   ├── chroma_db/        # ChromaDB veritabanı
│   └── chat_history.json # Sohbet geçmişi
└── src/
    ├── app.py            # Ana Streamlit uygulaması
    ├── config.py         # Konfigürasyon
    ├── ingest.py         # Doküman işleme
    ├── rag_chain.py      # RAG chain + utils
    ├── agent.py          # Agent modu
    └── chat_storage.py   # Sohbet depolama
```

## Özellikler

### 🧠 **Akıllı Arama**
- **Vector Search**: Semantic similarity ile doküman bulma
- **MMR Search**: Çeşitlilik ve relevans dengesi
- **Context Assembly**: İlgili parçaları birleştirme

### 💬 **İki Mod**
- **RAG Chain**: Otomatik doküman arama
- **Agent Tools**: Akıllı karar verme (OpenAI gerekli)

### 📊 **Gelişmiş Özellikler**
- **Kalıcı Sohbet**: Sayfa yenileme sonrası korunur
- **Dosya Yönetimi**: Yükleme, silme, durum takibi
- **Cevap Stilleri**: Kısa/uzun cevap seçenekleri
- **Token Tracking**: API maliyet takibi

## Notlar

- **Sadece PDF ve DOCX** dosyaları desteklenir
- **Agent modu** için OpenAI API anahtarı gerekli
- **Embeddings** yerel olarak çalışır (API anahtarı gerektirmez)
- **ChromaDB** kalıcıdır; sıfırlamak için uygulama içindeki butonu kullanın

## Web Linki

**🚀 Canlı Demo**: [DocuBrain on Streamlit Cloud](https://docubrain.streamlit.app/)

**DocuBrain ile dokümanlarınızı akıllı asistanınıza dönüştürün!** 🚀