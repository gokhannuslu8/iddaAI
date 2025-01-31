import pandas as pd

# 2022 sezonu maçları
matches_2022 = [
    # Önceki çıktıdan maç verilerini ekleyelim
    # Her satır: tarih, ev sahibi, deplasman, ev sahibi skor, deplasman skor, sonuç
]

# 2023 sezonu maçları
matches_2023 = [
    # Önceki çıktıdan maç verilerini ekleyelim
]

# 2024 sezonu maçları
matches_2024 = [
    # Önceki çıktıdan maç verilerini ekleyelim
]

# Tüm maçları birleştir
all_matches = pd.concat([
    pd.DataFrame(matches_2022),
    pd.DataFrame(matches_2023),
    pd.DataFrame(matches_2024)
], ignore_index=True)

# CSV dosyasına kaydet
all_matches.to_csv('matches_data.csv', index=False)
print(f"Toplam {len(all_matches)} maç verisi kaydedildi") 