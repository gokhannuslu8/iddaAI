from flask import Flask, request, jsonify
from predict_matches import load_model_and_scaler, get_team_stats, predict_match
from collect_tff_data import collect_data, train_model
from tff_service import TFFService
import pandas as pd

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
            # Sonuç başarılıysa ve prediction içinde ek_istatistikler varsa
            if result.get('success') and 'prediction' in result:
                prediction = result['prediction']
                
                if 'ek_istatistikler' in prediction and 'ilk_yari_gol_analizi' in prediction['ek_istatistikler']:
                    del prediction['ek_istatistikler']['ilk_yari_gol_analizi']
                
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
                    
                    prediction['toplam_gol_analizi'] = {
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
                    gol_araliklari = prediction['toplam_gol_analizi']['beklenen_gol_araligi']
                    en_olasi_aralik = max(gol_araliklari.items(), key=lambda x: x[1]['oran'])[0]
                    prediction['toplam_gol_analizi']['en_olasilik_gol_araligi'] = en_olasi_aralik
        
        except Exception as e:
            print(f"Toplam gol analizi hesaplama hatası: {str(e)}")
            # Hata durumunda mevcut result'ı değiştirmeden devam et
            pass
            
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
