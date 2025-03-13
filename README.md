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
.\env\Scripts\activate   # Windows için
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

Geliştirme modunda çalıştırmak için:
```bash
flask run
```

Üretim modunda çalıştırmak için:
```bash
export FLASK_ENV=production  # Linux/Mac için
set FLASK_ENV=production    # Windows için
flask run
```

## API Endpointleri

- `POST /mac/tahmin`: Maç tahmini yapar
- `GET /erisilen-takimlar`: Erişilebilir takımları listeler
- `GET /gunun-maclari`: Günün maçlarını listeler
- `POST /model/veri-topla`: Model için veri toplar
- `POST /model/egit`: Modeli eğitir
- `GET /model/durum`: Model durumunu kontrol eder

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