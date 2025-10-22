# 🧠 DocuBrain - Web Arayüzü & Product Kılavuzu

**Turn your PDFs and Docs into an intelligent assistant.**

## 🚀 Canlı Demo

**🌐 Web Linki**: [DocuBrain on Streamlit Cloud](https://docubrain.streamlit.app/)

## 📋 Çalışma Akışı

### 1️⃣ **Başlangıç**
- **Web sitesine giriş** → [DocuBrain Demo](https://docubrain.streamlit.app/)
- **Sol sidebar** → Ayarlar ve konfigürasyon
- **Ana sekme** → Knowledge Base (dosya yükleme)

### 2️⃣ **Ayarlar Konfigürasyonu**
Sol sidebar'da şu seçenekleri yapılandırabilirsiniz:

#### 🎯 **Kullanım Modu**
- **RAG Chain**: Otomatik doküman arama ve cevap üretme
- **Agent (tools)**: Akıllı karar verme ile arama (OpenAI gerekli)

#### 📝 **Cevap Stili**
- **Kısa ve Öz**: 2-3 cümle, direkt bilgi
- **Detaylı ve Kapsamlı**: Kapsamlı açıklama ve analiz

#### 🤖 **LLM Seçimi**
- **OpenAI GPT-4o-mini**: Hızlı ve ekonomik (önerilen)
- **Ollama**: Yerel model (fallback)

### 3️⃣ **Knowledge Base - Dosya Yükleme**

#### 📁 **Dosya Yükleme**
- **Desteklenen Formatlar**: PDF, DOCX
- **Yükleme**: Drag & drop veya dosya seçici
- **Otomatik İşleme**: Dosyalar otomatik olarak işlenir

#### 🔍 **İndeksleme**
- **İndeksle Butonu**: Dosyaları ChromaDB'ye indeksler
- **İşlem Durumu**: Progress bar ile takip
- **Başarı Mesajı**: İndeksleme tamamlandığında bildirim

#### 📊 **Dosya Yönetimi**
- **İndekslenen Dosyalar**: Tablo halinde görüntüleme
- **Dosya Bilgileri**: İsim, tip, boyut
- **Silme**: Seçili dosyaları veritabanından kaldırma
- **Veritabanı Sıfırlama**: Tüm verileri temizleme

### 4️⃣ **Chat - Sohbet Etme**

#### 💬 **Sohbet Arayüzü**
- **Soru Sorma**: Metin kutusuna soru yazın
- **Cevap Alma**: AI'dan anında cevap
- **Sohbet Geçmişi**: Tüm konuşmalar korunur
- **Sayfa Yenileme**: Sohbet geçmişi kalıcı

#### 🎯 **Özellikler**
- **Bağlamsal Cevaplar**: Dokümanlara dayalı
- **Kaynak Gösterimi**: Hangi dosyadan bilgi alındığı
- **Cevap Stilleri**: Kısa/uzun cevap seçenekleri
- **Sohbet Temizleme**: İstediğiniz zaman sıfırlama

## 🛠️ **Proje Kabiliyetlerini Test Etme**

### ✅ **Temel Test Senaryoları**

#### 1️⃣ **Dosya Yükleme Testi**
```
1. Knowledge Base sekmesine tıklayın
2. PDF veya DOCX dosyası yükleyin
3. "İndeksle" butonuna tıklayın
4. Başarı mesajını kontrol edin
5. İndekslenen dosyaları görüntüleyin
```

#### 2️⃣ **Sohbet Testi**
```
1. Chat sekmesine geçin
2. Basit bir soru sorun: "Bu dokümanda ne hakkında?"
3. AI'dan cevap alın
4. Cevabın dokümana dayalı olduğunu kontrol edin
5. Kaynak gösterimini inceleyin
```

#### 3️⃣ **Mod Değiştirme Testi**
```
1. Sol sidebar'da "Kullanım Modu" seçin
2. RAG Chain ve Agent arasında geçiş yapın
3. Aynı soruyu farklı modlarda sorun
4. Cevap farklarını gözlemleyin
```

#### 4️⃣ **Cevap Stili Testi**
```
1. "Cevap uzunluğu" seçin
2. "Kısa ve Öz" ile soru sorun
3. "Detaylı ve Kapsamlı" ile aynı soruyu sorun
4. Cevap farklarını karşılaştırın
```

### 🔧 **Gelişmiş Test Senaryoları**

#### 1️⃣ **Çoklu Dosya Testi**
```
1. Birden fazla PDF yükleyin
2. Farklı konularda sorular sorun
3. AI'nın doğru dosyayı referans ettiğini kontrol edin
4. Dosya yönetimi ile silme işlemi yapın
```

#### 2️⃣ **Karmaşık Sorular**
```
1. "Bu dokümanda X konusu hakkında ne diyor?"
2. "Y ve Z arasındaki fark nedir?"
3. "Özetle bu dokümanın ana noktaları neler?"
4. AI'nın bağlamsal cevaplar verdiğini kontrol edin
```

#### 3️⃣ **Hata Durumları**
```
1. Geçersiz dosya formatı yükleyin
2. API anahtarı olmadan Agent modunu test edin
3. Boş soru gönderin
4. Sistemin hata yönetimini kontrol edin
```

## 📊 **Performans Özellikleri**

### ⚡ **Hız Optimizasyonları**
- **Lazy Loading**: Modüller gerektiğinde yüklenir
- **Hafif Model**: 90MB embedding modeli
- **Hızlı Başlangıç**: 5-10 saniye içinde hazır

### 💾 **Depolama**
- **Kalıcı Sohbet**: JSON tabanlı depolama
- **ChromaDB**: Vektör veritabanı
- **Dosya Yönetimi**: Yükleme, silme, durum takibi

### 🔒 **Güvenlik**
- **API Anahtarı**: Güvenli environment variables
- **Dosya Güvenliği**: Sadece PDF/DOCX kabul edilir
- **Veri Korunması**: Yerel depolama

## 🎯 **Kullanım İpuçları**

### 💡 **En İyi Sonuçlar İçin**
1. **Kaliteli Dosyalar**: Net, okunabilir PDF/DOCX
2. **Açık Sorular**: Spesifik ve net sorular sorun
3. **Cevap Stili**: İhtiyacınıza göre kısa/uzun seçin
4. **Mod Seçimi**: RAG Chain (hızlı) vs Agent (akıllı)

### ⚠️ **Dikkat Edilecekler**
1. **API Anahtarı**: Agent modu için OpenAI gerekli
2. **Dosya Boyutu**: Büyük dosyalar işlem süresini artırabilir
3. **İnternet Bağlantısı**: OpenAI API için gerekli
4. **Tarayıcı**: Modern tarayıcı kullanın

## 🆘 **Sorun Giderme**

### ❌ **Yaygın Sorunlar**
- **"Agent oluşturulamadı"**: OpenAI API anahtarı eksik
- **"Dosya yüklenemedi"**: Format kontrolü yapın
- **"Cevap alamıyorum"**: İnternet bağlantısını kontrol edin
- **"Sayfa yenileniyor"**: Sohbet geçmişi korunur

### 🔧 **Çözümler**
1. **API Anahtarı**: .env dosyasına ekleyin
2. **Dosya Formatı**: Sadece PDF/DOCX kullanın
3. **İnternet**: Bağlantıyı kontrol edin
4. **Tarayıcı**: Sayfayı yenileyin

## 📞 **Destek**

**🚀 DocuBrain ile dokümanlarınızı akıllı asistanınıza dönüştürün!**

**Web Linki**: [DocuBrain on Streamlit Cloud](https://docubrain.streamlit.app/)
