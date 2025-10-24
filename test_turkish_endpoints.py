#!/usr/bin/env python3
"""
Türk takımları için endpointleri test etmek için script
"""

import requests
import json
import time

def test_turkish_endpoints():
    """Türk takımları için endpointleri test eder"""
    base_url = "http://localhost:5000"
    
    print("🚀 Türk Takımları Endpoint Testi Başlıyor...\n")
    
    # 1. Takımları listele
    print("1️⃣ Takımları listeleme testi...")
    try:
        response = requests.get(f"{base_url}/api/teams", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                teams = data.get('teams', [])
                print(f"✅ {len(teams)} takım bulundu")
                
                # İlk 5 takımı göster
                print("🏆 İlk 5 takım:")
                for i, team in enumerate(teams[:5]):
                    print(f"   {i+1}. {team['name']} ({team['league']})")
            else:
                print(f"❌ Hata: {data.get('error')}")
        else:
            print(f"❌ HTTP Hatası: {response.status_code}")
    except Exception as e:
        print(f"❌ Bağlantı hatası: {str(e)}")
        return False
    
    print()
    
    # 2. Tahmin testi
    print("2️⃣ Tahmin testi...")
    try:
        # Galatasaray vs Fenerbahçe tahmini
        prediction_data = {
            "home_team": "Galatasaray",
            "away_team": "Fenerbahçe"
        }
        
        response = requests.post(f"{base_url}/api/predict", 
                               json=prediction_data, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Tahmin başarılı!")
                print(f"   Ev sahibi: {data.get('home_team')}")
                print(f"   Deplasman: {data.get('away_team')}")
                print(f"   Tahmin: {data.get('prediction', 'N/A')}")
            else:
                print(f"❌ Tahmin hatası: {data.get('error')}")
        else:
            print(f"❌ HTTP Hatası: {response.status_code}")
            print(f"Yanıt: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Tahmin hatası: {str(e)}")
    
    print()
    
    # 3. Veri toplama testi
    print("3️⃣ Veri toplama testi...")
    try:
        collect_data = {"days": 7}  # Son 7 gün
        response = requests.post(f"{base_url}/model/veri-topla", 
                               json=collect_data, 
                               timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Veri toplama: {data.get('status', 'N/A')}")
            if 'message' in data:
                print(f"   Mesaj: {data['message']}")
        else:
            print(f"❌ HTTP Hatası: {response.status_code}")
    except Exception as e:
        print(f"❌ Veri toplama hatası: {str(e)}")
    
    print()
    
    # 4. Model eğitimi testi
    print("4️⃣ Model eğitimi testi...")
    try:
        response = requests.get(f"{base_url}/model/train/tr", timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Model eğitimi başarılı!")
                print(f"   Toplam maç: {data.get('total_matches', 'N/A')}")
            else:
                print(f"❌ Model eğitimi hatası: {data.get('error')}")
        else:
            print(f"❌ HTTP Hatası: {response.status_code}")
    except Exception as e:
        print(f"❌ Model eğitimi hatası: {str(e)}")
    
    print("\n" + "="*50)
    print("🎯 Test tamamlandı!")

if __name__ == "__main__":
    print("⏳ Uygulamanın başlamasını bekliyor...")
    time.sleep(3)  # Uygulamanın başlaması için bekle
    
    test_turkish_endpoints()
