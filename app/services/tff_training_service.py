import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import joblib
from datetime import datetime
import os

class TFFTrainingService:
    def __init__(self):
        self.data_path = 'app/data'
        self.models_path = 'app/models'
        self.matches_file = f'{self.data_path}/tff_matches_data.csv'
        os.makedirs(self.models_path, exist_ok=True)
        
    def train_model(self):
        """TFF maç verilerini kullanarak model eğitir"""
        try:
            # Veri setini yükle
            if not os.path.exists(self.matches_file):
                print("Eğitim verisi bulunamadı!")
                return False
                
            df = pd.read_csv(self.matches_file)
            
            # Özellikleri ve hedef değişkeni ayır
            features = [
                'ev_puan_ort', 'ev_gol_ort', 'ev_yenilen_gol_ort', 'ev_galibiyet_orani', 'ev_lig_sirasi',
                'dep_puan_ort', 'dep_gol_ort', 'dep_yenilen_gol_ort', 'dep_galibiyet_orani', 'dep_lig_sirasi'
            ]
            
            X = df[features]
            y = df['sonuc']
            
            # Veriyi eğitim ve test setlerine ayır
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Verileri ölçeklendir
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Modeli eğit
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Model performansını değerlendir
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)
            
            print(f"\nModel performansı:")
            print(f"Eğitim seti doğruluğu: {train_score:.4f}")
            print(f"Test seti doğruluğu: {test_score:.4f}")
            
            # Modeli ve scaler'ı kaydet
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_filename = f'tff_model_{timestamp}.joblib'
            scaler_filename = f'tff_scaler_{timestamp}.joblib'
            
            joblib.dump(model, f'{self.models_path}/{model_filename}')
            joblib.dump(scaler, f'{self.models_path}/{scaler_filename}')
            
            print(f"\nModel kaydedildi: {model_filename}")
            print(f"Scaler kaydedildi: {scaler_filename}")
            
            return True
            
        except Exception as e:
            print(f"Model eğitimi hatası: {str(e)}")
            return False
            
    def predict_match(self, home_team_stats, away_team_stats):
        """Verilen takım istatistiklerine göre maç tahmini yapar"""
        try:
            # En son eğitilen modeli ve scaler'ı bul
            model_files = [f for f in os.listdir(self.models_path) if f.startswith('tff_model_')]
            scaler_files = [f for f in os.listdir(self.models_path) if f.startswith('tff_scaler_')]
            
            if not model_files or not scaler_files:
                print("Model veya scaler bulunamadı!")
                return None
                
            latest_model = sorted(model_files)[-1]
            latest_scaler = sorted(scaler_files)[-1]
            
            # Model ve scaler'ı yükle
            model = joblib.load(f'{self.models_path}/{latest_model}')
            scaler = joblib.load(f'{self.models_path}/{latest_scaler}')
            
            # Tahmin için özellikleri hazırla
            features = [
                home_team_stats['puan'] / home_team_stats['oynadigi_mac'],
                home_team_stats['attigi_gol'] / home_team_stats['oynadigi_mac'],
                home_team_stats['yedigi_gol'] / home_team_stats['oynadigi_mac'],
                home_team_stats['galibiyet'] / home_team_stats['oynadigi_mac'],
                home_team_stats['lig_sirasi'],
                away_team_stats['puan'] / away_team_stats['oynadigi_mac'],
                away_team_stats['attigi_gol'] / away_team_stats['oynadigi_mac'],
                away_team_stats['yedigi_gol'] / away_team_stats['oynadigi_mac'],
                away_team_stats['galibiyet'] / away_team_stats['oynadigi_mac'],
                away_team_stats['lig_sirasi']
            ]
            
            # Özellikleri ölçeklendir ve tahmin yap
            X = scaler.transform([features])
            prediction = model.predict(X)[0]
            probabilities = model.predict_proba(X)[0]
            
            return {
                'tahmin': prediction,
                'olasiliklar': {
                    '1': probabilities[list(model.classes_).index('1')],
                    'X': probabilities[list(model.classes_).index('X')],
                    '2': probabilities[list(model.classes_).index('2')]
                }
            }
            
        except Exception as e:
            print(f"Tahmin hatası: {str(e)}")
            return None 