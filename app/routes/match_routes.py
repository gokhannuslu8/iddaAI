from flask import Blueprint, request, jsonify
from app.services.football_service import FootballService
from app.utils.helpers import TEAM_ID_MAPPING, get_team_id, get_team_league
from datetime import datetime
from app.services.data_collection_service import DataCollectionService
from app.services.ml_service import MLService
from app.services.match_service import MatchService
from app.services.training_service import TrainingService
import os
import pandas as pd
import numpy as np

bp = Blueprint('match', __name__)

@bp.route('/mac/tahmin', methods=['POST'])
def mac_tahmin():
    try:
        football_service = FootballService()
        training_service = TrainingService()
        data = request.get_json()
        takim1_adi = data.get('takım1')
        takim2_adi = data.get('takım2')
        
        if not takim1_adi or not takim2_adi:
            return jsonify({'hata': 'Takım isimleri gerekli'}), 400
        
        print(f"\nTakım ID'si aranıyor: {takim1_adi}")
        takim1_id = get_team_id(takim1_adi)
        print(f"Takım eşleşti: {takim1_adi} -> {takim1_adi} (ID: {takim1_id})")
        
        print(f"\nTakım ID'si aranıyor: {takim2_adi}")
        takim2_id = get_team_id(takim2_adi)
        print(f"Takım eşleşti: {takim2_adi} -> {takim2_adi} (ID: {takim2_id})")
        
        if not takim1_id or not takim2_id:
            return jsonify({'hata': f'Takım bulunamadı: {takim1_adi if not takim1_id else takim2_adi}'}), 404
        
        takim1_stats = football_service.get_team_stats(takim1_id)
        if not takim1_stats:
            return jsonify({'hata': f'{takim1_adi} için istatistikler alınamadı. Lütfen biraz bekleyip tekrar deneyin.'}), 500
            
        takim2_stats = football_service.get_team_stats(takim2_id)
        if not takim2_stats:
            return jsonify({'hata': f'{takim2_adi} için istatistikler alınamadı. Lütfen biraz bekleyip tekrar deneyin.'}), 500
        
        # TrainingService ile tahmin yap
        prediction = training_service.predict_match(takim1_stats, takim2_stats)
        if prediction['durum'] == 'hata':
            return jsonify({'hata': prediction['mesaj']}), 500
            
        # İlk yarı gol olasılıklarını kontrol et ve düzelt
        if 'ilk_yari_detayli' in prediction['tahminler']:
            first_half = prediction['tahminler']['ilk_yari_detayli']
            expected_goals = first_half['beklenen_goller']
            
            # Poisson dağılımı ile olasılıkları yeniden hesapla
            def poisson_prob(k, lambda_param):
                return np.exp(-lambda_param) * (lambda_param**k) / np.math.factorial(k)
            
            # Her bir gol sayısı için olasılıkları hesapla (0'dan 5'e kadar)
            goal_probs = [poisson_prob(i, expected_goals) for i in range(6)]
            
            # Olasılıkları güncelle
            first_half['olasiliklar'] = {
                '0.5 Alt': round(goal_probs[0] * 100),  # Sadece 0 gol
                '0.5 Üst': round((1 - goal_probs[0]) * 100),  # 1 veya daha fazla gol
                '1.5 Alt': round(sum(goal_probs[:2]) * 100),  # 0 ve 1 gol
                '1.5 Üst': round((1 - sum(goal_probs[:2])) * 100),  # 2 veya daha fazla gol
                '2.5 Alt': round(sum(goal_probs[:3]) * 100),  # 0, 1 ve 2 gol
                '2.5 Üst': round((1 - sum(goal_probs[:3])) * 100)  # 3 veya daha fazla gol
            }
            
            prediction['tahminler']['ilk_yari_detayli'] = first_half
            
        response_data = {
            'durum': 'basarili',
            'takim1': {
                'id': takim1_id,
                'isim': takim1_adi,
                'istatistikler': takim1_stats
            },
            'takim2': {
                'id': takim2_id,
                'isim': takim2_adi,
                'istatistikler': takim2_stats
            },
            'tahminler': prediction['tahminler']
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        return jsonify({'hata': str(e)}), 500

@bp.route('/erisilen-takimlar', methods=['GET'])
def get_available_teams():
    """Erişilebilir takımları ve liglerini getirir"""
    try:
        football_service = FootballService()
        result = football_service.get_available_teams()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'durum': 'hata',
            'mesaj': str(e)
        }), 500

@bp.route('/gunun-maclari', methods=['GET'])
def get_daily_matches():
    football_service = FootballService()
    matches = football_service.get_daily_matches()
    return jsonify(matches)

@bp.route('/model/veri-topla', methods=['POST'])
def collect_data():
    try:
        data = request.get_json()
        days = data.get('days', 7)  # Varsayılan olarak 7 gün
        
        football_service = FootballService()
        result = football_service.collect_data(days)

        if result.get('status') == 'error':
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/model/egit', methods=['POST'])
def train_model():
    """Modeli eğit"""
    try:
        training_service = TrainingService()
        result = training_service.train_model()
        
        if result['durum'] == 'basarili':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'durum': 'hata',
            'mesaj': str(e)
        }), 500

@bp.route('/model/durum', methods=['GET'])
def model_status():
    """Model durumunu kontrol eder"""
    try:
        training_service = TrainingService()
        
        # Model dosyalarını kontrol et
        model_files = [f for f in os.listdir(training_service.models_dir) if f.startswith('model_')]
        if not model_files:
            return jsonify({
                'durum': 'hata',
                'mesaj': 'Eğitilmiş model bulunamadı'
            })
        
        latest_model = sorted(model_files)[-1]
        latest_scaler = latest_model.replace('model_', 'scaler_')
        
        # Model ve scaler dosyalarının yolları
        model_path = os.path.join(training_service.models_dir, latest_model)
        scaler_path = os.path.join(training_service.models_dir, latest_scaler)
        
        # Model ve scaler'ın varlığını kontrol et
        model_exists = os.path.exists(model_path)
        scaler_exists = os.path.exists(scaler_path)
        
        if not model_exists or not scaler_exists:
            return jsonify({
                'durum': 'hata',
                'mesaj': 'Model dosyaları eksik'
            })
        
        # Model bilgilerini döndür
        return jsonify({
            'durum': 'basarili',
            'model_bilgisi': {
                'model_dosyasi': latest_model,
                'scaler_dosyasi': latest_scaler,
                'olusturulma_tarihi': datetime.fromtimestamp(os.path.getctime(model_path)).strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return jsonify({
            'durum': 'hata',
            'mesaj': str(e)
        }), 500

@bp.route('/mac/sonuc', methods=['POST'])
def mac_sonuc_bildir():
    try:
        data = request.get_json()
        match_id = data.get('mac_id')
        actual_result = data.get('sonuc')  # '1', 'X' veya '2'
        
        if not match_id or not actual_result:
            return jsonify({'hata': 'mac_id ve sonuc gerekli'}), 400
            
        success = FootballService.collect_match_result(match_id, actual_result)
        
        if success:
            return jsonify({
                'durum': 'başarılı',
                'mesaj': 'Sonuç kaydedildi ve model güncellendi'
            })
        else:
            return jsonify({'hata': 'Sonuç kaydedilemedi'}), 500
            
    except Exception as e:
        return jsonify({'hata': str(e)}), 500

@bp.route('/mac/tahmin', methods=['POST'])
def predict_match():
    match_service = MatchService()
    data = request.get_json()
    result = match_service.predict_match(data)
    return jsonify(result)

@bp.route('/tarih-maclari/<tarih>', methods=['GET'])
def get_matches_by_date(tarih):
    try:
        # Tarih formatını kontrol et (YYYY-MM-DD)
        datetime.strptime(tarih, '%Y-%m-%d')
        
        matches = FootballService.get_matches_by_date(tarih)
        return jsonify(matches)
        
    except ValueError:
        return jsonify({
            'hata': 'Geçersiz tarih formatı. Örnek: 2025-01-25'
        }), 400
    except Exception as e:
        return jsonify({
            'hata': str(e)
        }), 500

@bp.route('/gunun-kuponu', methods=['GET'])
@bp.route('/gunun-kuponu/<tarih>', methods=['GET'])
def get_daily_coupon(tarih=None):
    """Belirtilen tarihteki maçlar için en iyi kuponu getirir"""
    try:
        football_service = FootballService()
        training_service = TrainingService()
        
        # Tarih kontrolü
        if tarih:
            try:
                selected_date = datetime.strptime(tarih, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'durum': 'hata',
                    'mesaj': 'Geçersiz tarih formatı. Örnek: 2025-01-25'
                }), 400
        else:
            selected_date = datetime.now()
        
        # Günün maçlarını al
        matches = football_service.get_daily_matches(selected_date.strftime('%Y-%m-%d'))
        
        if not matches:
            return jsonify({
                'durum': 'hata',
                'mesaj': 'Belirtilen tarih için maç bulunamadı'
            }), 404
        
        analyzed_matches = []
        
        for match in matches:
            try:
                home_stats = football_service.get_team_stats(match['home_team_id'])
                away_stats = football_service.get_team_stats(match['away_team_id'])
                
                if not home_stats or not away_stats:
                    continue
                
                prediction = training_service.predict_match(home_stats, away_stats)
                
                if prediction['durum'] != 'basarili':
                    continue
                
                tahminler = prediction['tahminler']
                
                # Güven skorunu hesapla
                guven_skoru = 0
                en_yuksek_oran = 0
                en_guvenli_tahmin = None
                
                # Maç sonucu için güven kontrolü
                mac_sonucu_guven = max(tahminler['mac_sonucu'].values())
                if mac_sonucu_guven > 45:  # %45'ten yüksek güven
                    ms_tahmin = max(tahminler['mac_sonucu'].items(), key=lambda x: x[1])
                    guven_skoru = mac_sonucu_guven
                    en_yuksek_oran = mac_sonucu_guven
                    en_guvenli_tahmin = {
                        'tahmin_turu': 'Maç Sonucu',
                        'tahmin': ms_tahmin[0],
                        'oran': ms_tahmin[1],
                        'guven': mac_sonucu_guven
                    }
                
                # Gol sınırları için güven kontrolü
                for sinir, oran in tahminler['gol_sinirlari'].items():
                    if oran > en_yuksek_oran:
                        en_yuksek_oran = oran
                        en_guvenli_tahmin = {
                            'tahmin_turu': 'Gol Sınırı',
                            'tahmin': sinir,
                            'oran': oran,
                            'guven': oran
                        }
                
                # KG var/yok için güven kontrolü
                kg_var_oran = tahminler['gol_tahminleri']['KG Var']
                if kg_var_oran > en_yuksek_oran:
                    en_yuksek_oran = kg_var_oran
                    en_guvenli_tahmin = {
                        'tahmin_turu': 'Karşılıklı Gol',
                        'tahmin': 'VAR' if kg_var_oran > 50 else 'YOK',
                        'oran': max(kg_var_oran, 100 - kg_var_oran),
                        'guven': max(kg_var_oran, 100 - kg_var_oran)
                    }
                
                # İlk yarı/maç sonu için güven kontrolü
                for kombinasyon, oran in tahminler['iy_ms']['olasiliklar'].items():
                    if oran > en_yuksek_oran:
                        en_yuksek_oran = oran
                        en_guvenli_tahmin = {
                            'tahmin_turu': 'İY/MS',
                            'tahmin': kombinasyon,
                            'oran': oran,
                            'guven': oran
                        }
                
                if en_guvenli_tahmin and en_guvenli_tahmin['guven'] >= 55:  # En az %55 güven
                    analyzed_matches.append({
                        'mac_id': match['match_id'],
                        'ev_sahibi': match['home_team_name'],
                        'deplasman': match['away_team_name'],
                        'tarih': match['match_date'],
                        'lig': match['competition_name'],
                        'en_iyi_tahmin': en_guvenli_tahmin,
                        'tum_tahminler': tahminler,
                        'guven_skoru': en_guvenli_tahmin['guven']
                    })
            
            except Exception as e:
                print(f"Maç analiz hatası: {str(e)}")
                continue
        
        # En güvenilir tahminlere göre sırala
        analyzed_matches.sort(key=lambda x: x['guven_skoru'], reverse=True)
        
        # En iyi 5 maçı seç
        best_matches = analyzed_matches[:5]
        
        # Kupon güvenilirlik skoru
        toplam_guven = sum(mac['guven_skoru'] for mac in best_matches) / len(best_matches) if best_matches else 0
        
        return jsonify({
            'durum': 'basarili',
            'tarih': selected_date.strftime('%Y-%m-%d'),
            'kupon_guven_skoru': round(toplam_guven, 2),
            'mac_sayisi': len(best_matches),
            'maclar': best_matches,
            'oneriler': {
                'minimum_mac': 2,
                'maximum_mac': 4,
                'ideal_mac': 3,
                'guvenilirlik': 'Yüksek' if toplam_guven > 70 else 'Orta' if toplam_guven > 60 else 'Düşük'
            }
        })
        
    except Exception as e:
        print(f"Kupon oluşturma hatası: {str(e)}")
        return jsonify({
            'durum': 'hata',
            'mesaj': str(e)
        }), 500

@bp.route('/model/temizle', methods=['DELETE'])
def clean_model():
    try:
        ml_service = MLService()
        
        # Model dosyasını sil
        if os.path.exists(ml_service.model_path):
            os.remove(ml_service.model_path)
            
        # Scaler dosyasını sil
        if os.path.exists(ml_service.scaler_path):
            os.remove(ml_service.scaler_path)
            
        # Veri dosyasını sil
        if os.path.exists(ml_service.data_path):
            os.remove(ml_service.data_path)
            
        return jsonify({
            'status': 'success',
            'message': 'Model ve veri dosyaları başarıyla temizlendi',
            'detaylar': {
                'model_silindi': not os.path.exists(ml_service.model_path),
                'scaler_silindi': not os.path.exists(ml_service.scaler_path),
                'veri_silindi': not os.path.exists(ml_service.data_path)
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/tum-takimlar', methods=['GET'])
def get_all_teams():
    """Tüm liglerdeki takımları getirir"""
    try:
        football_service = FootballService()
        result = football_service.get_all_teams()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'durum': 'hata',
            'mesaj': str(e)
        }), 500