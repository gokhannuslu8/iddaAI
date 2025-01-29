import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
import joblib
import os
from datetime import datetime
from scipy.stats import poisson
import time

class TrainingService:
    def __init__(self):
        self.models_dir = os.path.join('app', 'models')
        self.data_dir = os.path.join('app', 'data')
        
        # Dizinleri oluştur
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def prepare_training_data(self, csv_file):
        """CSV dosyasından eğitim verilerini hazırlar"""
        try:
            print("[INFO] Eğitim verileri hazırlanıyor...")
            
            # CSV dosyasını oku
            df = pd.read_csv(csv_file)
            
            # Boş verileri temizle
            df = df.dropna()
            
            # Özellikler ve hedef değişkeni ayır
            features = [
                'home_team_form', 'home_team_goals_scored', 'home_team_goals_conceded',
                'home_team_wins', 'home_team_draws', 'home_team_losses',
                'away_team_form', 'away_team_goals_scored', 'away_team_goals_conceded',
                'away_team_wins', 'away_team_draws', 'away_team_losses'
            ]
            
            X = df[features].values
            y = df['result'].values
            
            return {
                'durum': 'basarili',
                'X': X,
                'y': y,
                'veri_sayisi': len(df)
            }
            
        except Exception as e:
            print(f"[ERROR] Veri hazırlama hatası: {str(e)}")
            return {
                'durum': 'hata',
                'mesaj': str(e)
            }
    
    def train_model(self, csv_file=None):
        """Modelleri eğitir"""
        try:
            # CSV dosyasını bul ve oku
            if csv_file is None:
                csv_files = [f for f in os.listdir(self.data_dir) if f.startswith('training_data_')]
                if not csv_files:
                    return {'durum': 'hata', 'mesaj': 'Eğitim verisi bulunamadı'}
                csv_file = os.path.join(self.data_dir, sorted(csv_files)[-1])
            
            df = pd.read_csv(csv_file)
            print(f"[INFO] Toplam {len(df)} veri noktası yüklendi")
            
            # Temel özellikler
            features = [
                'home_team_form', 'home_team_goals_scored', 'home_team_goals_conceded',
                'home_team_wins', 'home_team_draws', 'home_team_losses',
                'away_team_form', 'away_team_goals_scored', 'away_team_goals_conceded',
                'away_team_wins', 'away_team_draws', 'away_team_losses',
                'home_team_last_5_form', 'home_team_last_5_goals',
                'away_team_last_5_form', 'away_team_last_5_goals'
            ]
            
            # Basit ve etkili özellikler ekle
            df['home_win_rate'] = df['home_team_wins'] / (df['home_team_wins'] + df['home_team_draws'] + df['home_team_losses']).clip(lower=1)
            df['away_win_rate'] = df['away_team_wins'] / (df['away_team_wins'] + df['away_team_draws'] + df['away_team_losses']).clip(lower=1)
            df['home_goals_per_game'] = df['home_team_goals_scored'] / (df['home_team_wins'] + df['home_team_draws'] + df['home_team_losses']).clip(lower=1)
            df['away_goals_per_game'] = df['away_team_goals_scored'] / (df['away_team_wins'] + df['away_team_draws'] + df['away_team_losses']).clip(lower=1)
            df['form_diff'] = df['home_team_form'] - df['away_team_form']
            df['goals_diff'] = df['home_team_goals_scored'] - df['away_team_goals_scored']
            
            # Yeni özellikleri listeye ekle
            features.extend([
                'home_win_rate', 'away_win_rate',
                'home_goals_per_game', 'away_goals_per_game',
                'form_diff', 'goals_diff'
            ])
            
            # Sınıf dengesizliğini kontrol et
            print("\n[INFO] Sınıf dağılımı:")
            print(df['result'].value_counts(normalize=True))
            
            # Ensemble modeller
            models = {
                'mac_sonucu': {
                    'features': features,
                    'target': 'result',
                    'model': VotingClassifier(
                        estimators=[
                            ('xgb1', XGBClassifier(
                                n_estimators=300,
                                max_depth=4,
                                learning_rate=0.1,
                                subsample=0.8,
                                colsample_bytree=0.8,
                                random_state=42
                            )),
                            ('xgb2', XGBClassifier(
                                n_estimators=300,
                                max_depth=6,
                                learning_rate=0.05,
                                subsample=0.9,
                                colsample_bytree=0.9,
                                random_state=43
                            )),
                            ('lr', LogisticRegression(
                                C=0.1,
                                max_iter=1000,
                                random_state=42
                            ))
                        ],
                        voting='soft'
                    )
                },
                'kg_var': {
                    'features': features,
                    'target': 'both_scored',
                    'model': VotingClassifier(
                        estimators=[
                            ('xgb1', XGBClassifier(
                                n_estimators=200,
                                max_depth=3,
                                learning_rate=0.1,
                                random_state=42
                            )),
                            ('xgb2', XGBClassifier(
                                n_estimators=200,
                                max_depth=5,
                                learning_rate=0.05,
                                random_state=43
                            )),
                            ('lr', LogisticRegression(
                                C=0.1,
                                max_iter=1000,
                                random_state=42
                            ))
                        ],
                        voting='soft'
                    )
                },
                'ust_2_5': {
                    'features': features,
                    'target': 'over_25',
                    'model': VotingClassifier(
                        estimators=[
                            ('xgb1', XGBClassifier(
                                n_estimators=200,
                                max_depth=3,
                                learning_rate=0.1,
                                random_state=42
                            )),
                            ('xgb2', XGBClassifier(
                                n_estimators=200,
                                max_depth=5,
                                learning_rate=0.05,
                                random_state=43
                            )),
                            ('lr', LogisticRegression(
                                C=0.1,
                                max_iter=1000,
                                random_state=42
                            ))
                        ],
                        voting='soft'
                    )
                }
            }
            
            # Her model için eğitim yap
            results = {}
            for model_name, model_info in models.items():
                print(f"\n[INFO] {model_name} modeli eğitiliyor...")
                
                # Veriyi hazırla
                X = df[model_info['features']]
                y = df[model_info['target']]
                
                # Veriyi ölçeklendir
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                # Cross-validation ile model performansını değerlendir
                cv_scores = cross_val_score(model_info['model'], X_scaled, y, cv=5)
                print(f"[INFO] Cross-validation skorları: {cv_scores}")
                print(f"[INFO] Ortalama CV skoru: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
                
                # Tüm veri setiyle modeli eğit
                model = model_info['model']
                model.fit(X_scaled, y)
                
                # Özellik önemliliklerini hesapla (sadece XGBoost modellerinden)
                feature_importance = None
                if model_name == 'mac_sonucu':
                    # İlk XGBoost modelinden özellik önemliliklerini al
                    xgb_model = model.named_estimators_['xgb1']
                    feature_importance = pd.DataFrame({
                        'feature': model_info['features'],
                        'importance': xgb_model.feature_importances_
                    }).sort_values('importance', ascending=False)
                    
                    print("\n[INFO] En önemli 10 özellik (XGBoost-1):")
                    print(feature_importance.head(10))
                
                # Modeli kaydet
                model_path = os.path.join(self.models_dir, f'{model_name}_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.joblib')
                scaler_path = os.path.join(self.models_dir, f'{model_name}_scaler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.joblib')
                
                joblib.dump(model, model_path)
                joblib.dump(scaler, scaler_path)
                
                results[model_name] = {
                    'dogruluk': cv_scores.mean(),
                    'model_yolu': model_path,
                    'scaler_yolu': scaler_path,
                    'cv_skorlari': cv_scores.tolist(),
                    'en_onemli_ozellikler': feature_importance.head(10).to_dict('records') if feature_importance is not None else None
                }
            
            return {
                'durum': 'basarili',
                'sonuclar': results,
                'veri_sayisi': len(df),
                'egitim_tarihi': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'dogruluk': results['mac_sonucu']['dogruluk']
            }
            
        except Exception as e:
            print(f"[ERROR] Model eğitim hatası: {str(e)}")
            return {
                'durum': 'hata',
                'mesaj': str(e)
            }
    
    def predict_match(self, home_team_stats, away_team_stats):
        """Maç sonucunu tahmin eder ve detaylı istatistikler üretir"""
        try:
            # En son eğitilmiş modeli bul
            model_files = [f for f in os.listdir(self.models_dir) if f.startswith('model_')]
            if not model_files:
                return {
                    'durum': 'hata',
                    'mesaj': 'Eğitilmiş model bulunamadı'
                }
            
            latest_model = sorted(model_files)[-1]
            latest_scaler = latest_model.replace('model_', 'scaler_')
            
            # Model ve scaler'ı yükle
            model = joblib.load(os.path.join(self.models_dir, latest_model))
            scaler = joblib.load(os.path.join(self.models_dir, latest_scaler))
            
            # Özellik vektörü oluştur
            features = [
                home_team_stats.get('form', 0),
                home_team_stats.get('atilan_goller', 0),
                home_team_stats.get('yenilen_goller', 0),
                home_team_stats.get('galibiyetler', 0),
                home_team_stats.get('beraberlikler', 0),
                home_team_stats.get('maglubiyetler', 0),
                away_team_stats.get('form', 0),
                away_team_stats.get('atilan_goller', 0),
                away_team_stats.get('yenilen_goller', 0),
                away_team_stats.get('galibiyetler', 0),
                away_team_stats.get('beraberlikler', 0),
                away_team_stats.get('maglubiyetler', 0)
            ]
            
            # Veriyi ölçeklendir ve tahmin yap
            X = scaler.transform([features])
            prediction = int(model.predict(X)[0])  # numpy.int64'ü normal int'e çevir
            probabilities = model.predict_proba(X)[0].tolist()  # numpy array'i listeye çevir
            
            # Güç ve form hesaplamaları
            total_matches_home = max(home_team_stats.get('galibiyetler', 0) + home_team_stats.get('beraberlikler', 0) + home_team_stats.get('maglubiyetler', 0), 1)
            total_matches_away = max(away_team_stats.get('galibiyetler', 0) + away_team_stats.get('beraberlikler', 0) + away_team_stats.get('maglubiyetler', 0), 1)
            
            # Takım güçlerini hesapla (3 puan sistemi + gol katkısı)
            home_power = ((home_team_stats.get('galibiyetler', 0) * 3 + home_team_stats.get('beraberlikler', 0)) / (total_matches_home * 3) * 0.7 + 
                        (home_team_stats.get('atilan_goller', 0) / total_matches_home) / 3 * 0.3)
            away_power = ((away_team_stats.get('galibiyetler', 0) * 3 + away_team_stats.get('beraberlikler', 0)) / (total_matches_away * 3) * 0.7 + 
                        (away_team_stats.get('atilan_goller', 0) / total_matches_away) / 3 * 0.3)
            
            power_diff = round(home_power - away_power, 2)
            form_diff = round((home_team_stats.get('form', 0) - away_team_stats.get('form', 0)) / 100, 2)
            
            # Gol beklentileri hesaplama
            home_goals_per_game = home_team_stats.get('mac_basi_gol', 0)
            away_goals_per_game = away_team_stats.get('mac_basi_gol', 0)
            home_conceded_per_game = home_team_stats.get('yenilen_gol_ortalama', 0)
            away_conceded_per_game = away_team_stats.get('yenilen_gol_ortalama', 0)
            
            # Ev sahibi gol beklentisi
            home_expected_goals = round((
                home_goals_per_game * 1.1 +  # Ev sahibi avantajı
                away_conceded_per_game
            ) / 2, 2)
            
            # Deplasman gol beklentisi
            away_expected_goals = round((
                away_goals_per_game +
                home_conceded_per_game
            ) / 2, 2)
            
            # Toplam gol beklentisi
            total_expected_goals = round(home_expected_goals + away_expected_goals, 2)
            
            # İlk yarı gol beklentisi
            home_first_half = home_team_stats.get('first_half_goals_per_game', home_expected_goals * 0.35)
            away_first_half = away_team_stats.get('first_half_goals_per_game', away_expected_goals * 0.35)
            expected_first_half_goals = round(home_first_half + away_first_half, 2)
            
            print(f"[DEBUG] Ev sahibi beklenen gol: {home_expected_goals}, Deplasman beklenen gol: {away_expected_goals}")
            print(f"[DEBUG] Toplam beklenen gol: {total_expected_goals}, İlk yarı beklenen: {expected_first_half_goals}")
            
            # Gol aralıkları için olasılıklar hesaplama
            def calculate_goal_probabilities(expected_goals):
                # Poisson dağılımı kullanarak her gol sayısı için olasılıkları hesapla
                probs = [poisson.pmf(i, expected_goals) for i in range(10)]
                
                # Alt/Üst olasılıkları
                under_15_prob = sum(probs[:2])  # 0 ve 1 gol olasılıkları
                under_25_prob = sum(probs[:3])  # 0, 1 ve 2 gol olasılıkları
                under_35_prob = sum(probs[:4])  # 0, 1, 2 ve 3 gol olasılıkları
                
                # Güç farkına göre düzeltme
                adjustment = 0.1 * abs(power_diff)
                if power_diff > 0:  # Ev sahibi daha güçlüyse daha fazla gol beklenir
                    under_15_prob *= (1 - adjustment)
                    under_25_prob *= (1 - adjustment)
                    under_35_prob *= (1 - adjustment)
                elif power_diff < 0:  # Deplasman daha güçlüyse daha fazla gol beklenir
                    under_15_prob *= (1 - adjustment)
                    under_25_prob *= (1 - adjustment)
                    under_35_prob *= (1 - adjustment)
                
                # Form farkına göre düzeltme
                form_adjustment = 0.05 * abs(form_diff)
                if form_diff > 0:  # Ev sahibi formda
                    under_15_prob *= (1 - form_adjustment)
                    under_25_prob *= (1 - form_adjustment)
                    under_35_prob *= (1 - form_adjustment)
                elif form_diff < 0:  # Deplasman formda
                    under_15_prob *= (1 - form_adjustment)
                    under_25_prob *= (1 - form_adjustment)
                    under_35_prob *= (1 - form_adjustment)
                
                # Olasılıkları 0-1 aralığına sınırla
                under_15_prob = min(0.95, max(0.05, under_15_prob))
                under_25_prob = min(0.95, max(0.05, under_25_prob))
                under_35_prob = min(0.95, max(0.05, under_35_prob))
                
                return {
                    'under_15': under_15_prob,
                    'over_15': 1 - under_15_prob,
                    'under_25': under_25_prob,
                    'over_25': 1 - under_25_prob,
                    'under_35': under_35_prob,
                    'over_35': 1 - under_35_prob
                }
            
            # Gol olasılıklarını hesapla
            goal_probs = calculate_goal_probabilities(total_expected_goals)
            
            # İlk yarı gol olasılıkları
            first_half_probs = calculate_goal_probabilities(expected_first_half_goals)
            
            print(f"[DEBUG] Gol olasılıkları: {goal_probs}")
            print(f"[DEBUG] İlk yarı gol olasılıkları: {first_half_probs}")
            
            # Gol aralıkları için olasılıklar
            under_15 = goal_probs['under_15']
            over_15 = goal_probs['over_15']
            under_25 = goal_probs['under_25']
            over_25 = goal_probs['over_25']
            under_35 = goal_probs['under_35']
            over_35 = goal_probs['over_35']
            
            # İlk yarı tahminleri
            iy_home = probabilities[1] * 0.6  # Ev sahibi kazanma olasılığının %60'ı
            iy_draw = max(0.3, (1 - (iy_home + (probabilities[2] * 0.6))))  # En az %30 beraberlik
            iy_away = 1 - (iy_home + iy_draw)
            
            # Çifte şans hesaplamaları
            home_draw = probabilities[1] + probabilities[0]
            home_away = probabilities[1] + probabilities[2]
            draw_away = probabilities[0] + probabilities[2]
            
            # KG (Karşılıklı Gol) olasılığı hesapla
            kg_var_olasilik = round(min(0.95, max(0.05, 
                # Her iki takımın da gol atma olasılığı
                (1 - poisson.pmf(0, home_expected_goals)) *  # Ev sahibinin en az 1 gol atma olasılığı
                (1 - poisson.pmf(0, away_expected_goals))    # Deplasmanın en az 1 gol atma olasılığı
            )), 2)
            
            # En olası skorları hesapla
            muhtemel_skorlar = []
            
            # 0-0 ile 4-4 arası tüm olası skorlar
            for home_goals in range(5):
                for away_goals in range(5):
                    # Poisson dağılımı ile skor olasılığını hesapla
                    prob_home = poisson.pmf(home_goals, home_expected_goals)
                    prob_away = poisson.pmf(away_goals, away_expected_goals)
                    
                    # Toplam olasılığı hesapla
                    total_prob = prob_home * prob_away * 100
                    
                    # Takımların güç farkına göre düzeltme
                    if power_diff > 0 and home_goals > away_goals:  # Ev sahibi daha güçlüyse
                        total_prob *= (1 + abs(power_diff))
                    elif power_diff < 0 and away_goals > home_goals:  # Deplasman daha güçlüyse
                        total_prob *= (1 + abs(power_diff))
                    
                    muhtemel_skorlar.append({
                        'skor': f'{home_goals}-{away_goals}',
                        'oran': total_prob
                    })
            
            # Skorları olasılığa göre sırala
            muhtemel_skorlar.sort(key=lambda x: x['oran'], reverse=True)
            
            # İlk 5 skoru al ve oranları normalize et
            muhtemel_skorlar = muhtemel_skorlar[:5]
            toplam_oran = sum(skor['oran'] for skor in muhtemel_skorlar)
            
            # Oranları %100 üzerinden yeniden hesapla
            for skor in muhtemel_skorlar:
                skor['oran'] = round((skor['oran'] / toplam_oran) * 100, 2)
            
            # İlk yarı/maç sonu kombinasyonları için olasılıklar
            iy_ms_olasiliklar = {
                '1/1': round(iy_home * probabilities[1] * 1.2, 2),  # Ev sahibi üstünlüğünü devam ettirir
                '1/X': round(iy_home * probabilities[0] * 0.8, 2),  # Ev sahibi üstünlüğünü koruyamaz
                '1/2': round(iy_home * probabilities[2] * 0.5, 2),  # Ev sahibi üstünlüğünü tamamen kaybeder
                'X/1': round(iy_draw * probabilities[1] * 1.1, 2),  # Beraberlikten ev sahibi açılır
                'X/X': round(iy_draw * probabilities[0] * 1.3, 2),  # Beraberlik devam eder
                'X/2': round(iy_draw * probabilities[2] * 1.1, 2),  # Beraberlikten deplasman açılır
                '2/1': round(iy_away * probabilities[1] * 0.5, 2),  # Deplasman üstünlüğünü tamamen kaybeder
                '2/X': round(iy_away * probabilities[0] * 0.8, 2),  # Deplasman üstünlüğünü koruyamaz
                '2/2': round(iy_away * probabilities[2] * 1.2, 2)   # Deplasman üstünlüğünü devam ettirir
            }
            
            # Toplam olasılığı 100'e normalize et
            toplam_iy_ms = sum(iy_ms_olasiliklar.values())
            iy_ms_olasiliklar = {k: round((v / toplam_iy_ms) * 100, 2) for k, v in iy_ms_olasiliklar.items()}
            
            # İlk yarı/maç sonu için ek analizler
            iy_ms_analizler = {
                'en_olasilik': max(iy_ms_olasiliklar.items(), key=lambda x: x[1])[0],
                'ev_sahibi_one_gecer': round(iy_ms_olasiliklar['X/1'] + iy_ms_olasiliklar['2/1'], 2),
                'deplasman_one_gecer': round(iy_ms_olasiliklar['X/2'] + iy_ms_olasiliklar['1/2'], 2),
                'skor_degisir': round(sum([
                    iy_ms_olasiliklar['1/X'], iy_ms_olasiliklar['1/2'],
                    iy_ms_olasiliklar['2/X'], iy_ms_olasiliklar['2/1'],
                    iy_ms_olasiliklar['X/1'], iy_ms_olasiliklar['X/2']
                ]), 2),
                'skor_degismez': round(
                    iy_ms_olasiliklar['1/1'] + 
                    iy_ms_olasiliklar['X/X'] + 
                    iy_ms_olasiliklar['2/2'], 2
                )
            }

            # Kombinasyon tahminleri
            kg_var_prob = kg_var_olasilik * 100
            ust_25_prob = over_25 * 100
            
            kombinasyonlar = {
                # Gol sınırları ve maç sonucu kombinasyonları
                'ms1_15u': self._calculate_combined_probability(
                    probabilities[1] * 100,
                    goal_probs['over_15'] * 100
                ),
                'ms1_15a': self._calculate_combined_probability(
                    probabilities[1] * 100,
                    goal_probs['under_15'] * 100
                ),
                'msx_15u': self._calculate_combined_probability(
                    probabilities[0] * 100,
                    goal_probs['over_15'] * 100
                ),
                'msx_15a': self._calculate_combined_probability(
                    probabilities[0] * 100,
                    goal_probs['under_15'] * 100
                ),
                'ms2_15u': self._calculate_combined_probability(
                    probabilities[2] * 100,
                    goal_probs['over_15'] * 100
                ),
                'ms2_15a': self._calculate_combined_probability(
                    probabilities[2] * 100,
                    goal_probs['under_15'] * 100
                ),
                
                # 2.5 gol ve KG kombinasyonları
                'kg_var_25u': self._calculate_combined_probability(
                    kg_var_prob,
                    goal_probs['over_25'] * 100
                ),
                'kg_var_25a': self._calculate_combined_probability(
                    kg_var_prob,
                    goal_probs['under_25'] * 100
                ),
                'kg_yok_25u': self._calculate_combined_probability(
                    (1 - kg_var_olasilik) * 100,
                    goal_probs['over_25'] * 100
                ),
                'kg_yok_25a': self._calculate_combined_probability(
                    (1 - kg_var_olasilik) * 100,
                    goal_probs['under_25'] * 100
                )
            }
            
            # Tahminleri kategorilere ayır
            tahmin_kategorileri = {
                'mac_sonucu': {
                    'MS1': probabilities[1] * 100,
                    'MSX': probabilities[0] * 100,
                    'MS2': probabilities[2] * 100
                },
                'kg': {
                    'KG Var': kg_var_olasilik * 100,
                    'KG Yok': (1 - kg_var_olasilik) * 100
                },
                'gol_sinirlari': {
                    '2.5 Üst': goal_probs['over_25'] * 100,
                    '2.5 Alt': goal_probs['under_25'] * 100,
                    '1.5 Üst': goal_probs['over_15'] * 100,
                    '1.5 Alt': goal_probs['under_15'] * 100,
                    '3.5 Üst': goal_probs['over_35'] * 100,
                    '3.5 Alt': goal_probs['under_35'] * 100
                }
            }
            
            # Her kategoriden en yüksek olasılıklı tahmini bul
            en_yuksek_tahminler = {}
            for kategori, tahminler in tahmin_kategorileri.items():
                en_yuksek = max(tahminler.items(), key=lambda x: x[1])
                en_yuksek_tahminler[kategori] = {
                    'secim': en_yuksek[0],
                    'oran': en_yuksek[1]
                }
            
            # En mantıklı kombinasyonu bul
            kombinasyon_secenekleri = []
            
            # Gol sınırları ile KG kombinasyonları
            gol_siniri = en_yuksek_tahminler['gol_sinirlari']
            kg = en_yuksek_tahminler['kg']
            kombinasyon_secenekleri.append({
                'tahmin1': gol_siniri,
                'tahmin2': kg,
                'olasilik': self._calculate_combined_probability(gol_siniri['oran'], kg['oran'])
            })
            
            # Gol sınırları ile maç sonucu kombinasyonları
            ms = en_yuksek_tahminler['mac_sonucu']
            kombinasyon_secenekleri.append({
                'tahmin1': gol_siniri,
                'tahmin2': ms,
                'olasilik': self._calculate_combined_probability(gol_siniri['oran'], ms['oran'])
            })
            
            # KG ile maç sonucu kombinasyonları
            kombinasyon_secenekleri.append({
                'tahmin1': kg,
                'tahmin2': ms,
                'olasilik': self._calculate_combined_probability(kg['oran'], ms['oran'])
            })
            
            # En yüksek olasılıklı kombinasyonu seç
            en_iyi_kombinasyon = max(kombinasyon_secenekleri, key=lambda x: x['olasilik'])
            
            # 2.5Ü ve KG Var kombinasyonunu hesapla
            ust_25_kg_var = {
                'tahmin1': {
                    'secim': '2.5 Üst',
                    'oran': goal_probs['over_25'] * 100
                },
                'tahmin2': {
                    'secim': 'KG Var',
                    'oran': kg_var_olasilik * 100
                },
                'olasilik': self._calculate_combined_probability(
                    goal_probs['over_25'] * 100,
                    kg_var_olasilik * 100
                )
            }
            
            return {
                'durum': 'basarili',
                'tahminler': {
                    'mac_sonucu': {
                        'MS1': int(round(probabilities[1] * 100)),
                        'MSX': int(round(probabilities[0] * 100)),
                        'MS2': int(round(probabilities[2] * 100))
                    },
                    'cifte_sans': {
                        '1-X': int(round(home_draw * 100)),
                        '1-2': int(round(home_away * 100)),
                        'X-2': int(round(draw_away * 100))
                    },
                    'ilk_yari': {
                        'iy1': int(round(iy_home * 100)),
                        'iyX': int(round(iy_draw * 100)),
                        'iy2': int(round(iy_away * 100))
                    },
                    'iy_ms': {
                        'olasiliklar': {k: int(round(v)) for k, v in iy_ms_olasiliklar.items()},
                        'analizler': {
                            'en_olasilik': iy_ms_analizler['en_olasilik'],
                            'ev_sahibi_one_gecer': int(round(iy_ms_analizler['ev_sahibi_one_gecer'])),
                            'deplasman_one_gecer': int(round(iy_ms_analizler['deplasman_one_gecer'])),
                            'skor_degisir': int(round(iy_ms_analizler['skor_degisir'])),
                            'skor_degismez': int(round(iy_ms_analizler['skor_degismez']))
                        }
                    },
                    'beklenen_toplam_gol': int(round(total_expected_goals)),
                    'beklenen_ilk_yari_gol': int(round(expected_first_half_goals)),
                    'gol_beklentisi': {
                        'ev_sahibi': int(round(home_expected_goals)),
                        'deplasman': int(round(away_expected_goals)),
                        'toplam': int(round(total_expected_goals))
                    },
                    'gol_sinirlari': {
                        '1.5 Alt': int(round(under_15 * 100)),
                        '1.5 Üst': int(round(over_15 * 100)),
                        '2.5 Alt': int(round(under_25 * 100)),
                        '2.5 Üst': int(round(over_25 * 100)),
                        '3.5 Alt': int(round(under_35 * 100)),
                        '3.5 Üst': int(round(over_35 * 100))
                    },
                    'gol_tahminleri': {
                        '0-1 Gol': int(round(under_15 * 100)),
                        '2-3 Gol': int(round((over_15 - over_35) * 100)),
                        '4-5 Gol': int(round((over_35 - 0.1) * 100)),
                        '6+ Gol': int(round(0.1 * 100)),
                        'KG Var': int(round(kg_var_olasilik * 100)),
                        'KG Yok': int(round((1 - kg_var_olasilik) * 100))
                    },
                    'skor_tahminleri': [
                        {'skor': skor['skor'], 'oran': int(round(skor['oran']))}
                        for skor in muhtemel_skorlar
                    ],
                    'ek_istatistikler': {
                        'form_farki': int(round(form_diff * 100)),
                        'guc_farki': int(round(power_diff * 100)),
                        'takim1_guc': int(round(home_power * 100)),
                        'takim2_guc': int(round(away_power * 100)),
                        'takim1_mac_basi_gol': round(home_goals_per_game, 2),
                        'takim2_mac_basi_gol': round(away_goals_per_game, 2),
                        'beklenen_toplam_gol': round(total_expected_goals, 2),
                        'beklenen_ilk_yari_gol': round(expected_first_half_goals, 2),
                        'ml_guven': int(round(max(probabilities) * 100)),
                        'ml_kullanildi': True,
                        'yakin_guc': abs(power_diff) < 0.3,
                        'ev_sahibi_guclu': power_diff > 0.3
                    },
                    'kombinasyonlar': {
                        'en_yuksek_olasilikli': {
                            'tahmin1': {
                                'secim': en_iyi_kombinasyon['tahmin1']['secim'],
                                'oran': en_iyi_kombinasyon['tahmin1']['oran']
                            },
                            'tahmin2': {
                                'secim': en_iyi_kombinasyon['tahmin2']['secim'],
                                'oran': en_iyi_kombinasyon['tahmin2']['oran']
                            },
                            'kombinasyon_olasiligi': en_iyi_kombinasyon['olasilik'],
                            'aciklama': f"{en_iyi_kombinasyon['tahmin1']['secim']} (%{en_iyi_kombinasyon['tahmin1']['oran']:.1f}) ve {en_iyi_kombinasyon['tahmin2']['secim']} (%{en_iyi_kombinasyon['tahmin2']['oran']:.1f}) birlikte gerçekleşme olasılığı: %{en_iyi_kombinasyon['olasilik']:.1f}"
                        },
                        'ust_kg_var': {
                            'tahmin1': {
                                'secim': ust_25_kg_var['tahmin1']['secim'],
                                'oran': ust_25_kg_var['tahmin1']['oran']
                            },
                            'tahmin2': {
                                'secim': ust_25_kg_var['tahmin2']['secim'],
                                'oran': ust_25_kg_var['tahmin2']['oran']
                            },
                            'kombinasyon_olasiligi': ust_25_kg_var['olasilik'],
                            'aciklama': f"2.5 Üst (%{ust_25_kg_var['tahmin1']['oran']:.1f}) ve KG Var (%{ust_25_kg_var['tahmin2']['oran']:.1f}) birlikte gerçekleşme olasılığı: %{ust_25_kg_var['olasilik']:.1f}"
                        }
                    }
                }
            }
            
        except Exception as e:
            print(f"[ERROR] Tahmin hatası: {str(e)}")
            return {
                'durum': 'hata',
                'mesaj': str(e)
            }

    def _calculate_combined_probability(self, prob1, prob2):
        """İki olasılığın birlikte gerçekleşme olasılığını hesaplar"""
        # Olasılıkları 0-1 aralığına çevir
        p1 = prob1 / 100
        p2 = prob2 / 100
        
        # Birlikte gerçekleşme olasılığı
        combined_prob = p1 * p2
        
        # Yüzdeye çevir ve yuvarla
        return round(combined_prob * 100, 1)