# İddaAI

İddaAI, spor bahislerinde yapay zeka destekli bir tahmin platformudur. Makine öğrenimi algoritmalarıyla geçmiş maç verilerini analiz ederek sonuçları tahmin eder ve veri odaklı içgörüler sunar. Kullanıcıların yalnızca şansa değil, güvenilir verilere dayalı kararlar almasını sağlar.

## Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)

### Adım Adım Kurulum

1. Projeyi klonlayın:
```bash
git clone https://github.com/kullaniciadi/iddaAI.git
cd iddaAI
```

2. Sanal ortam oluşturun ve aktif edin:

Windows için:
```bash
python -m venv venv
venv\Scripts\activate
```

Linux/Mac için:
```bash
python -m venv venv
source venv/bin/activate
```

3. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

4. Çevre değişkenlerini ayarlayın:
- `.env` dosyası oluşturun ve aşağıdaki değişkenleri ekleyin:
```
FOOTBALL_API_KEY=your_api_key_here
FOOTBALL_API_BASE_URL=https://api.football-data.org/v4
```

5. Uygulamayı çalıştırın:
```bash
python run.py
```

Uygulama varsayılan olarak http://localhost:5000 adresinde çalışacaktır.

## API Endpointleri

- `GET /gunun-kuponu`: Günün maç tahminlerini getirir
- `GET /mac/tahmin`: Belirli bir maç için tahmin yapar
- `GET /model/durum`: Model durumunu kontrol eder
- `POST /model/egit`: Modeli yeniden eğitir

## Geliştirme

1. Geliştirme için sanal ortamı aktif edin:
```bash
venv\Scripts\activate  # Windows için
source venv/bin/activate  # Linux/Mac için
```

2. Debug modunda çalıştırın:
```bash
python run.py --debug
```

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## Katkıda Bulunma

1. Bu depoyu fork edin
2. Feature branch'i oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'e push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun