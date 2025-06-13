# İddaa Tahmin Uygulaması

Bu uygulama, futbol maçları için tahmin ve analiz yapan bir API servisidir.

## Kurulum

1. Projeyi klonlayın:
```bash
git clone https://github.com/yourusername/iddaAI.git
cd iddaAI
```

2. Python sanal ortamı oluşturun ve aktifleştirin:
```bash
python -m venv env
source env/bin/activate  # Linux/Mac için
venv/Scripts/activate   # Windows için
```

3. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

4. Konfigürasyon dosyalarını hazırlayın:
```bash
# Ana konfigürasyon dosyası
cp config.example.py config.py

# API konfigürasyon dosyası
cp app/config/config.example.py app/config/config.py
```

5. Konfigürasyon dosyalarını düzenleyin:
- `config.py`:
  - `SECRET_KEY`: Güvenli bir rastgele anahtar oluşturun
  - `FOOTBALL_API_KEY`: [football-data.org](https://www.football-data.org/) üzerinden bir API anahtarı alın
  - Veritabanı bağlantı bilgilerini güncelleyin

- `app/config/config.py`:
  - `API_KEY`: football-data.org API anahtarınızı ekleyin

## Çalıştırma

- Türk takımları için tahmin yapmak istiyorsanız:
  ```bash
  python app.py
  ```
  Uygulama http://localhost:5000/api/predict endpointiyle çalışır.

- Avrupa ve yabancı takımlar için tahmin yapmak istiyorsanız:
  ```bash
  python run.py
  ```
  Uygulama /mac/tahmin endpointiyle çalışır.

## API Endpointleri

- `POST /mac/tahmin`:
  Türk olmayan (Avrupa ligleri ve diğer yabancı takımlar) için iki takım adı gönderilerek skor ve istatistik tahmini yapılır.
  
  **Body:**
  ```json
  {
    "takım1": "Barcelona",
    "takım2": "Real Madrid"
  }
  ```
  **Dönüş:** Skor tahminleri, gol aralıkları, olasılıklar ve detaylı analiz.

- `POST /api/predict`:
  Türk takımları için maç tahmini yapılır. Yine iki takım adı gönderilir.
  
  **Body:**
  ```json
  {
    "takım1": "Galatasaray",
    "takım2": "Fenerbahçe"
  }
  ```
  **Dönüş:** Skor tahminleri, gol aralıkları, olasılıklar ve detaylı analiz.

- `GET /erisilen-takimlar`:
  API ile tahmin yapılabilen ve istatistikleri erişilebilen tüm takımları ve liglerini listeler.

- `GET /gunun-maclari`:
  Bugünün (veya istenirse belirli bir tarihin) oynanacak maçlarını ve temel bilgilerini listeler.

- `POST /model/veri-topla`:
  Modelin eğitimi için geçmiş maç verilerini toplar.
  
  **Body (opsiyonel):**
  ```json
  { "days": 30 }
  ```
  **Dönüş:** Toplanan veri sayısı ve özet.

- `POST /model/egit`:
  Toplanan verilerle makine öğrenmesi modelini eğitir.
  
  **Dönüş:** Eğitim başarısı, doğruluk oranları ve önemli özellikler.

- `GET /model/durum`:
  Modelin mevcut durumunu, son eğitim tarihini ve model dosyası bilgilerini döndürür.

## Güvenlik

Hassas bilgiler içeren dosyalar `.gitignore` dosyasına eklenmiştir:
- `config.py`
- `app/config/config.py`
- `.env` dosyaları
- API anahtarları
- Model ve veri dosyaları
- Log dosyaları

## Katkıda Bulunma

1. Bu repoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/yeniOzellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik: X'`)
4. Branch'inizi push edin (`git push origin feature/yeniOzellik`)
5. Pull Request oluşturun