from flask import current_app
import requests
import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
from datetime import datetime
import scipy.stats as stats
from scipy.stats import poisson
from collections import Counter
import traceback

class MLService:
    def __init__(self):
        self.model = None
        self.scaler = None
        # Mevcut dosyaları kullan
        self.data_path = os.path.join('app', 'data', 'training_data_20250128_152624.csv')
        self.model_path = os.path.join('app', 'models', 'match_prediction_model.joblib')
        self.scaler_path = os.path.join('app', 'models', 'match_prediction_scaler.joblib')
        self.initialize_model()

    def initialize_model(self):
        """Model ve scaler'ı yükler veya yeni oluşturur"""
        try:
            print(f"[INFO] Model yükleniyor: {self.model_path}")
            if not os.path.exists(self.model_path) or not os.path.exists(self.scaler_path):
                print("[WARNING] Model veya scaler dosyası bulunamadı")
                self._create_new_model()
                return

            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            print("[INFO] Model ve scaler başarıyla yüklendi")
            
        except Exception as e:
            print(f"[ERROR] Model yükleme hatası: {str(e)}")
            print("[INFO] Yeni model oluşturuluyor...")
            self._create_new_model()
    
    def _create_new_model(self):
        """Yeni bir model oluşturur"""
        try:
            print("[INFO] Yeni model oluşturuluyor...")
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.scaler = StandardScaler()
            
            # Model dizinini oluştur
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Modeli kaydet
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            print("[INFO] Yeni model oluşturuldu ve kaydedildi")
            
        except Exception as e:
            print(f"[ERROR] Model oluşturma hatası: {str(e)}")
            raise Exception("Model oluşturulamadı")

    def update_model(self, new_data):
        """Mevcut modeli yeni verilerle günceller"""
        try:
            print("[INFO] Model güncelleniyor...")
            
            # Mevcut verileri yükle
            if os.path.exists(self.data_path):
                print(f"[INFO] Mevcut veri dosyası kullanılıyor: {self.data_path}")
                existing_data = pd.read_csv(self.data_path)
            else:
                print("[WARNING] Mevcut veri dosyası bulunamadı, yeni dosya oluşturulacak")
                existing_data = pd.DataFrame()
            
            # Yeni verileri ekle
            new_df = pd.DataFrame(new_data)
            combined_data = pd.concat([existing_data, new_df], ignore_index=True)
            
            # Tekrarlanan verileri temizle
            combined_data = combined_data.drop_duplicates()
            
            # Güncellenmiş verileri aynı dosyaya kaydet
            combined_data.to_csv(self.data_path, index=False)
            print(f"[INFO] Toplam {len(combined_data)} veri noktası kaydedildi: {self.data_path}")
            
            # Modeli yeni verilerle güncelle
            X = combined_data.drop(['result', 'both_scored', 'over_25', 'total_goals', 'first_half_goals'], axis=1)
            y = combined_data['result']
            
            # Verileri ölçeklendir
            X_scaled = self.scaler.fit_transform(X)
            
            # Modeli güncelle
            self.model.fit(X_scaled, y)
            
            # Güncellenmiş modeli aynı dosyalara kaydet
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            print(f"[INFO] Model başarıyla güncellendi: {self.model_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Model güncelleme hatası: {str(e)}")
            print(traceback.format_exc())
            return False

    def predict(self, features):
        """Tahmin yapar"""
        try:
            if not self.model or not self.scaler:
                raise Exception("Model henüz hazır değil")
                
            # Özellikleri ölçeklendir
            scaled_features = self.scaler.transform([features])
            
            # Tahmin yap
            prediction = self.model.predict(scaled_features)
            probabilities = self.model.predict_proba(scaled_features)
            
            return {
                'tahmin': prediction[0],
                'olasiliklar': probabilities[0].tolist()
            }
            
        except Exception as e:
            print(f"[ERROR] Tahmin hatası: {str(e)}")
            raise e

class MatchService:
    def __init__(self, model_path=None, data_path=None):
        self.model_path = model_path or current_app.config['MODEL_PATH']
        self.data_path = data_path or current_app.config['DATA_PATH']
        self.football_service = FootballService()
        self.ml_service = MLService()
        
    def train_model(self):
        try:
            return {
                'status': 'success',
                'message': 'Model başarıyla eğitildi'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def get_model_status(self):
        try:
            model_exists = os.path.exists(self.model_path)
            data_exists = os.path.exists(self.data_path)
            
            return {
                'model_trained': model_exists,
                'data_available': data_exists,
                'status': 'ready' if model_exists and data_exists else 'not_ready'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def predict_match(self, data):
        """Maç tahminlerini yapar"""
        try:
            # Gerekli verileri kontrol et
            if not data or 'ev_sahibi' not in data or 'deplasman' not in data:
                return {
                    'status': 'error',
                    'message': 'Ev sahibi ve deplasman takımları gerekli'
                }
                
            # Takım isimlerini al
            ev_sahibi = data['ev_sahibi'].strip()
            deplasman = data['deplasman'].strip()
            
            if not ev_sahibi or not deplasman:
                return {
                    'status': 'error',
                    'message': 'Takım isimleri boş olamaz'
                }
                
            # Takım istatistiklerini al
            ev_sahibi_stats = self.football_service.get_team_stats(ev_sahibi)
            deplasman_stats = self.football_service.get_team_stats(deplasman)
            
            if not ev_sahibi_stats or not deplasman_stats:
                return {
                    'status': 'error',
                    'message': 'Takım istatistikleri alınamadı'
                }
            
            # ML modeli ile tahmin yap
            predictions = self.football_service.calculate_match_predictions(ev_sahibi_stats, deplasman_stats)
            
            # Sonuçları hazırla
            return {
                'status': 'success',
                'tahminler': predictions['mac_sonucu'],
                'detaylar': {
                    'ev_sahibi': {
                        'isim': ev_sahibi,
                        'guc': predictions['ek_istatistikler']['takim1_guc'],
                        'form': ev_sahibi_stats.get('form', 0)
                    },
                    'deplasman': {
                        'isim': deplasman,
                        'guc': predictions['ek_istatistikler']['takim2_guc'],
                        'form': deplasman_stats.get('form', 0)
                    },
                    'analiz': {
                        'guc_farki': predictions['ek_istatistikler']['guc_farki'],
                        'yakin_guc': predictions['ek_istatistikler']['yakin_guc'],
                        'ml_guven': predictions['ek_istatistikler']['ml_guven']
                    }
                }
            }
            
        except Exception as e:
            print(f"Tahmin hatası: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            } 