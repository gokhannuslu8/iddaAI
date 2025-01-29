from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
import os
from flask import current_app
import pandas as pd
from datetime import datetime
import scipy.stats as stats
from scipy.stats import poisson
from collections import Counter
import glob
import traceback

class MLService:
    def __init__(self):
        self.models = {}
        self.models_dir = os.path.join('app', 'models')
        self.initialize_models()

    def initialize_models(self):
        """Tüm modelleri yükler"""
        try:
            model_types = ['mac_sonucu', 'kg_var', 'ust_2_5']
            
            for model_type in model_types:
                # En son eğitilmiş model dosyasını bul
                model_pattern = os.path.join(self.models_dir, f'{model_type}_model_*.joblib')
                scaler_pattern = os.path.join(self.models_dir, f'{model_type}_scaler_*.joblib')
                
                model_files = sorted(glob.glob(model_pattern))
                scaler_files = sorted(glob.glob(scaler_pattern))
                
                if model_files and scaler_files:
                    latest_model = model_files[-1]
                    latest_scaler = scaler_files[-1]
                    
                    self.models[model_type] = {
                        'model': joblib.load(latest_model),
                        'scaler': joblib.load(latest_scaler)
                    }
                    print(f"[INFO] {model_type} modeli yüklendi: {latest_model}")
                else:
                    print(f"[WARNING] {model_type} modeli bulunamadı")
                    
        except Exception as e:
            print(f"[ERROR] Model yükleme hatası: {str(e)}")

    def train_model(self, **kwargs):
        """Modeli eğitir"""
        try:
            # Football servisini başlat
            from app.services.football_service import FootballService
            football_service = FootballService()
            
            # Son 1800 maçı al
            matches = football_service.get_historical_matches(1800)
            
            if len(matches) < 1000:
                return {
                    'status': 'error',
                    'message': 'Yeterli eğitim verisi yok'
                }

            features = []
            labels = []
            
            print("[INFO] Eğitim verisi hazırlanıyor...")
            print(f"[INFO] Toplam {len(matches)} maç verisi bulundu")
            
            # Özellik isimlerini tanımla
            self.feature_names = [
                'home_goals_per_game', 'away_goals_per_game',
                'home_conceded_per_game', 'away_conceded_per_game',
                'home_form', 'away_form',
                'home_win_rate', 'away_win_rate',
                'home_draw_rate', 'away_draw_rate',
                'home_loss_rate', 'away_loss_rate',
                'home_home_goals_per_game', 'away_away_goals_per_game',
                'home_first_half_goals', 'away_first_half_goals',
                'home_last_5_form', 'away_last_5_form',
                'home_last_5_goals', 'away_last_5_goals',
                'home_both_scored_rate', 'away_both_scored_rate'
            ]
            
            for idx, match in enumerate(matches):
                try:
                    match_date = match['match_date']
                    home_team_id = match['home_team_id']
                    away_team_id = match['away_team_id']
                    
                    # Maç öncesi takım istatistiklerini al
                    home_stats = football_service.get_team_stats_before_match(home_team_id, match_date)
                    away_stats = football_service.get_team_stats_before_match(away_team_id, match_date)
                    
                    if not home_stats or not away_stats:
                        print(f"[WARNING] {home_team_id} veya {away_team_id} için istatistik bulunamadı")
                        continue

                    # Sıfıra bölme kontrolü
                    home_matches = max(home_stats.get('oynadigi_mac', 1), 1)
                    away_matches = max(away_stats.get('oynadigi_mac', 1), 1)
                    
                    # İstatistikleri kontrol et ve varsayılan değerler kullan
                    home_goals = float(home_stats.get('attigi_gol', 0))
                    away_goals = float(away_stats.get('attigi_gol', 0))
                    home_conceded = float(home_stats.get('yedigi_gol', 0))
                    away_conceded = float(away_stats.get('yedigi_gol', 0))
                    home_points = float(home_stats.get('puan', 0))
                    away_points = float(away_stats.get('puan', 0))
                    home_rank = float(home_stats.get('lig_sirasi', 10))
                    away_rank = float(away_stats.get('lig_sirasi', 10))
                    
                    # Form puanlarını hesapla
                    home_form = self._calculate_form(home_stats.get('son_maclar', []))
                    away_form = self._calculate_form(away_stats.get('son_maclar', []))
                    
                    # Özellik vektörünü oluştur
                    feature_vector = [
                        home_stats['mac_basi_gol'],
                        away_stats['mac_basi_gol'],
                        home_stats['yenilen_gol_ortalama'],
                        away_stats['yenilen_gol_ortalama'],
                        home_stats['form'] / 100,
                        away_stats['form'] / 100,
                        home_stats['galibiyetler'] / home_stats['toplam_mac'],
                        away_stats['galibiyetler'] / away_stats['toplam_mac'],
                        home_stats['beraberlikler'] / home_stats['toplam_mac'],
                        away_stats['beraberlikler'] / away_stats['toplam_mac'],
                        home_stats['maglubiyetler'] / home_stats['toplam_mac'],
                        away_stats['maglubiyetler'] / away_stats['toplam_mac'],
                        home_stats['ev_sahibi_mac_basi_gol'],
                        away_stats['deplasman_mac_basi_gol'],
                        home_stats['ilk_yari_gol_ortalama'],
                        away_stats['ilk_yari_gol_ortalama'],
                        home_stats['son_5_form'] / 100,
                        away_stats['son_5_form'] / 100,
                        home_stats['son_5_gol'] / 5,
                        away_stats['son_5_gol'] / 5,
                        home_stats['kg_var_yuzde'] / 100,
                        away_stats['kg_var_yuzde'] / 100
                    ]
                    
                    # NaN ve sonsuz değer kontrolü
                    if any(np.isnan(x) or np.isinf(x) for x in feature_vector):
                        print(f"[WARNING] Geçersiz değer bulundu: {feature_vector}")
                        continue
                    
                    # Sonucu belirle (1: Ev sahibi kazandı, 0: Berabere, 2: Deplasman kazandı)
                    if int(match['home_goals']) > int(match['away_goals']):
                        result = 1
                    elif int(match['home_goals']) < int(match['away_goals']):
                        result = 2
                    else:
                        result = 0
                    
                    features.append(feature_vector)
                    labels.append(result)
                    
                    # Her 100 maçta bir ilerleme bilgisi
                    if (idx + 1) % 100 == 0:
                        print(f"[INFO] {idx + 1} maç işlendi, {len(features)} geçerli veri hazırlandı")
                    
                except Exception as e:
                    print(f"[ERROR] Veri hazırlama hatası ({home_team_id} vs {away_team_id}): {str(e)}")
                    continue
            
            if len(features) < 1000:
                return {
                    'status': 'error',
                    'message': f'Yeterli eğitim verisi hazırlanamadı. Sadece {len(features)} geçerli veri bulundu.'
                }

            print(f"[INFO] {len(features)} adet eğitim verisi hazırlandı")
            
            # Verileri numpy dizisine çevir
            X = np.array(features, dtype=np.float32)
            y = np.array(labels, dtype=np.int32)
            
            # Son kontrol
            if np.any(np.isnan(X)) or np.any(np.isinf(X)):
                return {
                    'status': 'error',
                    'message': 'Eğitim verisinde geçersiz değerler var'
                }
            
            # Verileri ölçeklendir
            X_scaled = self.models['mac_sonucu']['scaler'].fit_transform(X)
            
            print("[INFO] Model eğitimi başlıyor...")

            # Zaman damgası oluştur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Her model tipi için eğitim yap
            for model_type in ['mac_sonucu', 'kg_var', 'ust_2_5']:
                print(f"[INFO] {model_type} modeli eğitiliyor...")
                
                # Model ve scaler'ı hazırla
                if model_type not in self.models:
                    self.models[model_type] = {
                        'model': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
                        'scaler': StandardScaler()
                    }
                
                # Verileri ölçeklendir
                X_scaled = self.models[model_type]['scaler'].fit_transform(X)
                
                # Modeli eğit
                self.models[model_type]['model'].fit(X_scaled, y)
                
                # Model ve scaler'ı kaydet
                model_path = os.path.join(self.models_dir, f'{model_type}_model_{timestamp}.joblib')
                scaler_path = os.path.join(self.models_dir, f'{model_type}_scaler_{timestamp}.joblib')
                
                joblib.dump(self.models[model_type]['model'], model_path)
                joblib.dump(self.models[model_type]['scaler'], scaler_path)
                
                print(f"[INFO] {model_type} modeli kaydedildi: {model_path}")

            # Eğitim sonuçlarını hesapla
            results = {}
            for model_type in self.models:
                accuracy = self.models[model_type]['model'].score(X_scaled, y)
                results[model_type] = {
                    'dogruluk': round(accuracy * 100, 2)
                }

            return {
                'status': 'basarili',
                'sonuclar': results,
                'veri_sayisi': len(X),
                'egitim_tarihi': timestamp
            }

        except Exception as e:
            print(f"[ERROR] Model eğitim hatası: {str(e)}")
            return {
                'status': 'hata',
                'mesaj': str(e)
            }

    def _calculate_form(self, matches, limit=5):
        """Son maçların form puanını hesaplar"""
        try:
            if not matches:
                return 0
                
            total_points = 0
            matches_analyzed = 0
            
            for match in matches[:limit]:
                try:
                    scores = match['skor'].split(' - ')
                    home_goals = int(scores[0])
                    away_goals = int(scores[1])
                    is_home = match['ev_sahibi_mi']
                    
                    if is_home:
                        if home_goals > away_goals:
                            total_points += 3
                        elif home_goals == away_goals:
                            total_points += 1
                    else:
                        if away_goals > home_goals:
                            total_points += 3
                        elif home_goals == away_goals:
                            total_points += 1
                            
                    matches_analyzed += 1
                    
                except:
                    continue
            
            if matches_analyzed == 0:
                return 0
                
            return total_points / (matches_analyzed * 3)  # 0-1 aralığında normalize et
            
        except Exception as e:
            print(f"[ERROR] Form hesaplama hatası: {str(e)}")
            return 0

    def predict_match_result(self, model_type, home_stats, away_stats):
        """Maç sonucunu tahmin eder"""
        try:
            if model_type not in self.models:
                print(f"[ERROR] Model tipi bulunamadı: {model_type}")
                return None

            model = self.models[model_type]['model']
            scaler = self.models[model_type]['scaler']

            # Özellik vektörünü DataFrame olarak hazırla
            features_dict = {
                'home_goals_per_game': home_stats['mac_basi_gol'],
                'away_goals_per_game': away_stats['mac_basi_gol'],
                'home_conceded_per_game': home_stats['yenilen_gol_ortalama'],
                'away_conceded_per_game': away_stats['yenilen_gol_ortalama'],
                'home_form': home_stats['form'] / 100,
                'away_form': away_stats['form'] / 100,
                'home_win_rate': home_stats['galibiyetler'] / home_stats['toplam_mac'],
                'away_win_rate': away_stats['galibiyetler'] / away_stats['toplam_mac'],
                'home_draw_rate': home_stats['beraberlikler'] / home_stats['toplam_mac'],
                'away_draw_rate': away_stats['beraberlikler'] / away_stats['toplam_mac'],
                'home_loss_rate': home_stats['maglubiyetler'] / home_stats['toplam_mac'],
                'away_loss_rate': away_stats['maglubiyetler'] / away_stats['toplam_mac'],
                'home_home_goals_per_game': home_stats['ev_sahibi_mac_basi_gol'],
                'away_away_goals_per_game': away_stats['deplasman_mac_basi_gol'],
                'home_first_half_goals': home_stats['ilk_yari_gol_ortalama'],
                'away_first_half_goals': away_stats['ilk_yari_gol_ortalama'],
                'home_last_5_form': home_stats['son_5_form'] / 100,
                'away_last_5_form': away_stats['son_5_form'] / 100,
                'home_last_5_goals': home_stats['son_5_gol'] / 5,
                'away_last_5_goals': away_stats['son_5_gol'] / 5,
                'home_both_scored_rate': home_stats['kg_var_yuzde'] / 100,
                'away_both_scored_rate': away_stats['kg_var_yuzde'] / 100
            }
            
            # DataFrame oluştur
            X = pd.DataFrame([features_dict])

            # Ölçeklendir
            X_scaled = scaler.transform(X)
            
            # Tahmin yap
            prediction = model.predict(X_scaled)[0]
            probabilities = model.predict_proba(X_scaled)[0]
            
            # Güven skorunu hesapla
            confidence = round(max(probabilities) * 100)
            
            # Model tipine göre sonuçları formatla
            if model_type == 'mac_sonucu':
                return {
                    'tahmin': 'MS1' if prediction == 1 else ('MSX' if prediction == 0 else 'MS2'),
                    'olasiliklar': {
                        'MS1': round(probabilities[1] * 100, 2),
                        'MSX': round(probabilities[0] * 100, 2),
                        'MS2': round(probabilities[2] * 100, 2)
                    },
                    'guven': confidence
                }
            elif model_type == 'kg_var':
                return {
                    'tahmin': 'VAR' if prediction == 1 else 'YOK',
                    'olasiliklar': {
                        'VAR': round(probabilities[1] * 100, 2),
                        'YOK': round(probabilities[0] * 100, 2)
                    },
                    'guven': confidence
                }
            else:  # ust_2_5
                return {
                    'tahmin': 'ÜST' if prediction == 1 else 'ALT',
                    'olasiliklar': {
                        'ÜST': round(probabilities[1] * 100, 2),
                        'ALT': round(probabilities[0] * 100, 2)
                    },
                    'guven': confidence
                }
            
        except Exception as e:
            print(f"[ERROR] Tahmin hatası ({model_type}): {str(e)}")
            print(f"[ERROR] Detay: {traceback.format_exc()}")
            return None
    
    def get_model_status(self):
        """Model durumunu kontrol eder"""
        try:
            model_files = {
                'mac_sonucu': {
                    'model': 'mac_sonucu_model_*.joblib',
                    'scaler': 'mac_sonucu_scaler_*.joblib'
                },
                'kg_var': {
                    'model': 'kg_var_model_*.joblib',
                    'scaler': 'kg_var_scaler_*.joblib'
                },
                'ust_2_5': {
                    'model': 'ust_2_5_model_*.joblib',
                    'scaler': 'ust_2_5_scaler_*.joblib'
                }
            }
            
            model_statuses = {}
            models_ready = True
            
            for model_type, files in model_files.items():
                # En son model dosyasını bul
                model_pattern = os.path.join(self.models_dir, files['model'].replace('*', '*'))
                model_files = sorted(glob.glob(model_pattern))
                
                if not model_files:
                    models_ready = False
                    model_statuses[model_type] = {
                        'durum': 'bulunamadı',
                        'son_guncelleme': None
                    }
                    continue
                    
                latest_model = model_files[-1]
                model_modified = datetime.fromtimestamp(os.path.getmtime(latest_model))
                
                model_statuses[model_type] = {
                    'durum': 'hazır',
                    'model_yolu': latest_model,
                    'son_guncelleme': model_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'boyut': f"{os.path.getsize(latest_model) / (1024*1024):.2f} MB"
                }
            
            return {
                'durum': 'hazir' if models_ready else 'hazir_degil',
                'model_durumlari': model_statuses,
                'son_guncelleme': max(
                    status['son_guncelleme'] 
                    for status in model_statuses.values() 
                    if status['son_guncelleme']
                ) if models_ready else None
            }
            
        except Exception as e:
            print(f"Model durum kontrolü hatası: {str(e)}")
            return {
                'durum': 'hata',
                'hata_mesaji': str(e)
            } 