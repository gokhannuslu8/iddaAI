from flask import Flask, request, jsonify
from predict_matches import load_model_and_scaler, get_team_stats, predict_match
from collect_tff_data import collect_data, train_model
from tff_service import TFFService
import pandas as pd
import numpy as np

app = Flask(__name__)

# Model ve scaler'ı global olarak yükle
model, scaler = load_model_and_scaler()
standings = get_team_stats()

def get_team_stats():
    """Güncel takım istatistiklerini al"""
    tff = TFFService()
    all_standings = pd.DataFrame()
    
    # Her iki lig için de takımları al
    for league_type in ['super', 'tff1']:
        standings = tff.get_standings(2024, league_type)
        if not standings.empty:
            all_standings = pd.concat([all_standings, standings], ignore_index=True)
    
    return all_standings

@app.route('/api/teams', methods=['GET'])
def get_teams():
    try:
        # Tüm takımları al ve lig bilgisiyle birlikte döndür
        teams_data = []
        for _, team in standings.iterrows():
            teams_data.append({
                'name': team['team'],
                'league': 'Süper Lig' if team['league_type'] == 'super' else 'TFF 1. Lig'
            })
        return jsonify({'success': True, 'teams': teams_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        if not data or 'home_team' not in data or 'away_team' not in data:
            return jsonify({
                'success': False,
                'error': 'Ev sahibi ve deplasman takımları gerekli'
            })
        
        home_team = data['home_team']
        away_team = data['away_team']
        
        if home_team not in standings['team'].values or away_team not in standings['team'].values:
            return jsonify({
                'success': False,
                'error': 'Geçersiz takım ismi'
            })
        
        result = predict_match(model, scaler, standings, home_team, away_team)
        
        try:
            # Sonuç başarılıysa ve prediction içinde skor_tahminleri varsa
            if result.get('success') and 'prediction' in result:
                prediction = result['prediction']
                
                # Olası skorları hesapla
                home_goals_avg = prediction['ev_sahibi_detay']['maç_başı_gol_ortalaması']
                away_goals_avg = prediction['deplasman_detay']['maç_başı_gol_ortalaması']
                home_conceded_avg = prediction['ev_sahibi_detay']['maç_başı_yenilen_gol_ortalaması']
                away_conceded_avg = prediction['deplasman_detay']['maç_başı_yenilen_gol_ortalaması']
                
                # Ev sahibi avantajı
                HOME_ADVANTAGE = 1.3
                home_goals_avg *= HOME_ADVANTAGE
                
                # Form etkisi (son maçlardaki galibiyet oranı)
                home_wins = int(prediction['ev_sahibi_form'].split(': ')[1].split(',')[0])
                away_wins = int(prediction['deplasman_form'].split(': ')[1].split(',')[0])
                home_form = home_wins / 5  # Son 5 maçtaki galibiyet oranı
                away_form = away_wins / 5
                
                # Form etkisini uygula
                home_goals_avg *= (0.8 + home_form * 0.4)  # Maksimum %40 etki
                away_goals_avg *= (0.8 + away_form * 0.4)
                
                # Savunma faktörünü hesaba kat
                defense_factor_home = away_conceded_avg / 1.5  # 1.5 ortalama lig gol sayısı
                defense_factor_away = home_conceded_avg / 1.5
                
                # Gol beklentilerini güncelle
                home_expected = home_goals_avg * defense_factor_away
                away_expected = away_goals_avg * defense_factor_home
                
                # Poisson dağılımı kullanarak skor olasılıklarını hesapla
                muhtemel_skorlar = []
                for home_goals in range(5):  # 0-4 gol arası
                    for away_goals in range(5):  # 0-4 gol arası
                        # Her bir takımın gol atma olasılığını hesapla
                        home_prob = np.exp(-home_expected) * (home_expected ** home_goals) / np.math.factorial(home_goals)
                        away_prob = np.exp(-away_expected) * (away_expected ** away_goals) / np.math.factorial(away_goals)
                        
                        # Toplam olasılığı hesapla
                        total_prob = home_prob * away_prob * 100
                        
                        # Mantıksız skorları filtrele
                        if abs(home_goals - away_goals) <= 3:  # 3'ten fazla fark olan skorları azalt
                            skor_mantikli = True
                        else:
                            skor_mantikli = False
                            total_prob *= 0.3  # Olasılığı %70 azalt
                        
                        # Beraberlik düzeltmesi
                        if home_goals == away_goals:
                            if abs(home_expected - away_expected) < 0.5:  # Takımlar dengeli ise
                                total_prob *= 1.2  # Beraberlik olasılığını %20 artır
                            else:
                                total_prob *= 0.8  # Beraberlik olasılığını %20 azalt
                        
                        muhtemel_skorlar.append({
                            'skor': f"{home_goals}-{away_goals}",
                            'oran': round(total_prob, 1),
                            'mantikli': skor_mantikli
                        })
                
                # Skorları olasılıklarına göre sırala
                muhtemel_skorlar.sort(key=lambda x: (x['mantikli'], x['oran']), reverse=True)
                
                # En olası 5 skoru al
                en_olasi_skorlar = muhtemel_skorlar[:5]
                
                # Oranları normalize et (toplam 100 olacak şekilde)
                toplam_oran = sum(skor['oran'] for skor in en_olasi_skorlar)
                for skor in en_olasi_skorlar:
                    skor['oran'] = round((skor['oran'] / toplam_oran) * 100)
                    del skor['mantikli']  # mantikli anahtarını kaldır
                
                # Son kontrol - toplamın tam 100 olmasını sağla
                toplam = sum(skor['oran'] for skor in en_olasi_skorlar)
                if toplam != 100:
                    # Farkı en yüksek olasılığa ekle
                    fark = 100 - toplam
                    en_olasi_skorlar[0]['oran'] += fark
                
                # Yanıt formatını düzenle
                response = {
                    'success': True,
                    'match': f"{home_team} vs {away_team}",
                    'prediction': {
                        'ev_sahibi_detay': prediction['ev_sahibi_detay'],
                        'deplasman_detay': prediction['deplasman_detay'],
                        'ev_sahibi_form': prediction['ev_sahibi_form'],
                        'deplasman_form': prediction['deplasman_form'],
                        'skor_tahminleri': en_olasi_skorlar,
                        'tahmin': prediction['tahmin'],
                        'olasiliklar': prediction['olasiliklar'],
                        'gol_sinirlari': prediction['gol_sinirlari'],
                        'ilk_yari_gol_analizi': prediction['ilk_yari_gol_analizi'],
                        'toplam_gol_analizi': prediction.get('toplam_gol_analizi', {}),
                        'ek_istatistikler': prediction['ek_istatistikler']
                    }
                }
                
                # Toplam gol analizi ekle
                if all(key in prediction for key in ['gol_sinirlari', 'ev_sahibi_detay', 'deplasman_detay']):
                    gol_sinirlari = prediction['gol_sinirlari']
                    ev_detay = prediction['ev_sahibi_detay']
                    dep_detay = prediction['deplasman_detay']
                    
                    # Gol aralıkları hesaplama
                    alt_15 = gol_sinirlari.get('1.5 Alt', 0)
                    alt_25 = gol_sinirlari.get('2.5 Alt', 0)
                    alt_35 = gol_sinirlari.get('3.5 Alt', 0)
                    
                    # Doğru gol aralığı olasılıklarını hesapla
                    gol_araliklari_ham = {
                        '0-1 Gol': alt_15,  # 0-1 gol olasılığı direkt 1.5 Alt
                        '2-3 Gol': alt_35 - alt_15,  # 2-3 gol olasılığı 3.5 Alt - 1.5 Alt
                        '4-5 Gol': 90 - alt_35,  # 4-5 gol olasılığı 3.5 Üst'ün çoğu
                        '6+ Gol': 10  # 6+ gol için sabit düşük bir olasılık
                    }
                    
                    # Toplam oranı hesapla
                    toplam_oran = sum(gol_araliklari_ham.values())
                    
                    # Oranları normalize et (%100'e tamamla)
                    gol_araliklari_normalize = {
                        aralik: round((oran / toplam_oran) * 100) 
                        for aralik, oran in gol_araliklari_ham.items()
                    }
                    
                    # Son kontrol - toplamın tam 100 olmasını sağla
                    toplam = sum(gol_araliklari_normalize.values())
                    if toplam != 100:
                        # Farkı en yüksek olasılığa ekle veya çıkar
                        en_yuksek_aralik = max(gol_araliklari_normalize.items(), key=lambda x: x[1])[0]
                        gol_araliklari_normalize[en_yuksek_aralik] += (100 - toplam)
                    
                    # Takım detayları
                    ev_gol_ort = ev_detay.get('maç_başı_gol_ortalaması', 0)
                    ev_yenilen_ort = ev_detay.get('maç_başı_yenilen_gol_ortalaması', 0)
                    dep_gol_ort = dep_detay.get('maç_başı_gol_ortalaması', 0)
                    dep_yenilen_ort = dep_detay.get('maç_başı_yenilen_gol_ortalaması', 0)
                    
                    response['prediction']['toplam_gol_analizi'] = {
                        'beklenen_gol_araligi': {
                            aralik: {
                                'oran': oran,
                                'analiz': {
                                    '0-1 Gol': 'Düşük skorlu maç beklentisi',
                                    '2-3 Gol': 'Orta skorlu maç beklentisi',
                                    '4-5 Gol': 'Yüksek skorlu maç beklentisi',
                                    '6+ Gol': 'Çok yüksek skorlu maç beklentisi'
                                }[aralik]
                            }
                            for aralik, oran in gol_araliklari_normalize.items()
                        },
                        'takim_analizi': {
                            'ev_sahibi': {
                                'mac_basi_gol': ev_gol_ort,
                                'mac_basi_yenilen': ev_yenilen_ort,
                                'toplam_gol_etkisi': round((ev_gol_ort + ev_yenilen_ort) / 2, 2)
                            },
                            'deplasman': {
                                'mac_basi_gol': dep_gol_ort,
                                'mac_basi_yenilen': dep_yenilen_ort,
                                'toplam_gol_etkisi': round((dep_gol_ort + dep_yenilen_ort) / 2, 2)
                            }
                        },
                        'genel_analiz': {
                            'toplam_gol_egilimi': round((ev_gol_ort + ev_yenilen_ort + dep_gol_ort + dep_yenilen_ort) / 4, 2),
                            'yuksek_skor_olasiligi': gol_sinirlari.get('2.5 Üst', 0),
                            'dusuk_skor_olasiligi': gol_sinirlari.get('2.5 Alt', 0)
                        }
                    }
                    
                    # En olası gol aralığını hesapla
                    gol_araliklari = response['prediction']['toplam_gol_analizi']['beklenen_gol_araligi']
                    en_olasi_aralik = max(gol_araliklari.items(), key=lambda x: x[1]['oran'])[0]
                    response['prediction']['toplam_gol_analizi']['en_olasilik_gol_araligi'] = en_olasi_aralik
                
                return jsonify(response)
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Yanıt formatı düzenleme hatası: {str(e)}")
            return jsonify(result)
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/model/train/tr', methods=['GET'])
def train_turkish_model():
    try:
        global model, scaler, standings
        print("\nTürk takımları için model eğitimi başlıyor...")
        
        # Veri toplama
        print("\nVeri toplama aşaması başladı...")
        matches = collect_data()
        
        if matches.empty:
            return jsonify({
                'success': False,
                'error': 'Veri toplanamadı'
            })
        
        # Model eğitimi
        print("\nModel eğitimi aşaması başladı...")
        model, scaler = train_model(matches)
        
        # Güncel takım istatistiklerini güncelle
        standings = get_team_stats()
        
        return jsonify({
            'success': True,
            'message': 'Model başarıyla eğitildi ve güncellendi',
            'total_matches': len(matches)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Model eğitimi sırasında hata oluştu: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
