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

class MLService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_path = os.path.join('app', 'models', 'match_prediction_model.joblib')
        self.scaler_path = os.path.join('app', 'models', 'match_prediction_scaler.joblib')
        self.data_path = os.path.join('app', 'data', 'training_data.csv')
        self.initialize_model()

    def initialize_model(self):
        """Model ve scaler'ı yükler veya yeni oluşturur"""
        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            print("[INFO] Model ve scaler başarıyla yüklendi")
        except:
            print("[INFO] Model ve scaler bulunamadı, yeni model oluşturulacak")
            self._create_new_model()
    
    def _create_new_model(self):
        """Yeni bir model oluşturur"""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()

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
                        home_goals / home_matches,
                        away_goals / away_matches,
                        home_conceded / home_matches,
                        away_conceded / away_matches,
                        home_points / home_matches,
                        away_points / away_matches,
                        home_form,
                        away_form,
                        home_rank,
                        away_rank
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
            X_scaled = self.scaler.fit_transform(X)
            
            print("[INFO] Model eğitimi başlıyor...")

            # Modeli eğit
            self.model.fit(X_scaled, y)
            
            print("[INFO] Model eğitimi tamamlandı")

            # Modeli kaydet
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            print("[INFO] Model kaydedildi")

            # Eğitim sonuçlarını hesapla
            train_accuracy = self.model.score(X_scaled, y)
            y_pred = self.model.predict(X_scaled)
            class_distribution = Counter(y)

            return {
                'status': 'success',
                'message': 'Model başarıyla eğitildi',
                'accuracy': round(train_accuracy * 100, 2),
                'data_points': len(X),
                'class_distribution': dict(class_distribution)
            }

        except Exception as e:
            print(f"[ERROR] Model eğitim hatası: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
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

    def predict_match_result(self, home_stats, away_stats):
        """Maç sonucunu tahmin eder"""
        try:
            if not self.model or not self.scaler:
                return None

            # Özellik vektörünü hazırla
            features = [
                home_stats['attigi_gol'] / max(home_stats['oynadigi_mac'], 1),
                away_stats['attigi_gol'] / max(away_stats['oynadigi_mac'], 1),
                home_stats['yedigi_gol'] / max(home_stats['oynadigi_mac'], 1),
                away_stats['yedigi_gol'] / max(away_stats['oynadigi_mac'], 1),
                home_stats['puan'] / max(home_stats['oynadigi_mac'], 1),
                away_stats['puan'] / max(away_stats['oynadigi_mac'], 1),
                self._calculate_form(home_stats.get('son_maclar', [])),
                self._calculate_form(away_stats.get('son_maclar', [])),
                home_stats.get('lig_sirasi', 10),
                away_stats.get('lig_sirasi', 10)
            ]
            
            # Ölçeklendir
            X_scaled = self.scaler.transform([features])
            
            # Tahmin yap
            prediction = self.model.predict([features])[0]
            probabilities = self.model.predict_proba([features])[0]
            
            # Güven skorunu hesapla
            confidence = round(max(probabilities) * 100)
            
            return {
                'tahmin': prediction,
                'olasiliklar': {
                    'MS1': round(probabilities[1] * 100, 2),
                    'MSX': round(probabilities[0] * 100, 2),
                    'MS2': round(probabilities[2] * 100, 2)
                },
                'guven': confidence
            }
            
        except Exception as e:
            print(f"[ERROR] Tahmin hatası: {str(e)}")
            return None
    
    def get_model_status(self):
        """Model durumunu kontrol eder"""
        try:
            model_file = self.model_path
            scaler_file = self.scaler_path
            
            # Model dosyası kontrolü
            model_exists = os.path.exists(model_file)
            model_size = os.path.getsize(model_file) if model_exists else 0
            model_created = datetime.fromtimestamp(os.path.getctime(model_file)).strftime('%Y-%m-%d %H:%M:%S') if model_exists else None
            model_modified = datetime.fromtimestamp(os.path.getmtime(model_file)).strftime('%Y-%m-%d %H:%M:%S') if model_exists else None
            
            model_statuses = {
                'model_dosyasi': {
                    'boyut': f"{model_size / (1024*1024):.2f} MB" if model_exists else None,
                    'olusturulma_tarihi': model_created,
                    'son_guncelleme': model_modified
                },
                'model_durumu': {
                    'model_var_mi': model_exists,
                    'model_yuklu_mu': self.model is not None,
                    'son_durum': 'Aktif ve Çalışıyor' if self.model else 'Yüklü Değil'
                },
                'model_ozellikleri': {
                    'agac_sayisi': 100,
                    'max_derinlik': 10,
                    'ozellik_sayisi': 12
                } if self.model else None
            }
            
            # Veri durumu kontrolü
            from app.services.football_service import FootballService
            football_service = FootballService()
            matches = football_service.get_historical_matches(1800)
            has_data = len(matches) > 0
            
            # Önerileri oluştur
            recommendations = []
            for model_type, status in model_statuses.items():
                if not status['model_durumu']['model_var_mi']:
                    recommendations.append(f"{model_type} modeli eğitimi gerekli")
                elif status['model_durumu']['model_var_mi'] and status['model_dosyasi']['son_guncelleme']:
                    days_since_update = (datetime.now() - datetime.strptime(status['model_dosyasi']['son_guncelleme'], '%Y-%m-%d %H:%M:%S')).days
                    if days_since_update > 7:
                        recommendations.append(f"{model_type} modeli güncelleme önerilir")
            
            if not has_data:
                recommendations.append("Veri toplama gerekli")
            
            # Genel durum kontrolü
            all_models_ready = all(status['model_durumu']['model_yuklu_mu'] for status in model_statuses.values())
            
            return {
                'durum': 'hazir' if all_models_ready and has_data else 'hazir_degil',
                'model_durumlari': model_statuses,
                'veri_durumu': {
                    'veri_var_mi': has_data,
                    'son_durum': f"Veri Mevcut ({len(matches)} maç)" if has_data else "Veri Yok",
                    'son_guncelleme': datetime.fromtimestamp(os.path.getmtime(self.model_path)).strftime('%Y-%m-%d %H:%M:%S') if os.path.exists(self.model_path) else None
                },
                'oneriler': recommendations if recommendations else None
            }
            
        except Exception as e:
            print(f"Model durum kontrolü hatası: {str(e)}")
            return {
                'durum': 'hata',
                'hata_mesaji': str(e)
            } 