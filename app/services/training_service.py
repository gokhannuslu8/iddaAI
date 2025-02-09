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
                                n_estimators=500,
                                max_depth=6,
                                learning_rate=0.05,
                                subsample=0.8,
                                colsample_bytree=0.8,
                                min_child_weight=3,
                                gamma=0.1,
                                random_state=42
                            )),
                            ('xgb2', XGBClassifier(
                                n_estimators=500,
                                max_depth=4,
                                learning_rate=0.1,
                                subsample=0.9,
                                colsample_bytree=0.9,
                                min_child_weight=2,
                                gamma=0.2,
                                random_state=43
                            )),
                            ('xgb3', XGBClassifier(
                                n_estimators=500,
                                max_depth=5,
                                learning_rate=0.075,
                                subsample=0.85,
                                colsample_bytree=0.85,
                                min_child_weight=4,
                                gamma=0.15,
                                random_state=44
                            )),
                            ('lr', LogisticRegression(
                                C=0.1,
                                max_iter=2000,
                                class_weight='balanced',
                                random_state=42
                            ))
                        ],
                        voting='soft',
                        weights=[3, 2, 2, 1]  # XGBoost modellerine daha fazla ağırlık ver
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
            
            # Feature engineering geliştirmeleri
            df['recent_form_ratio'] = df['home_team_last_5_form'] / df['away_team_last_5_form']
            df['goal_efficiency'] = (df['home_team_goals_scored'] / df['home_team_played']) / (df['away_team_goals_scored'] / df['away_team_played'])
            df['defense_efficiency'] = (df['home_team_goals_conceded'] / df['home_team_played']) / (df['away_team_goals_conceded'] / df['away_team_played'])
            df['win_rate_ratio'] = df['home_win_rate'] / df['away_win_rate']
            
            # Sezon içi trend
            df['home_trend'] = df['home_team_last_5_form'] - df['home_team_form']
            df['away_trend'] = df['away_team_last_5_form'] - df['away_team_form']
            
            # Yeni özellikleri listeye ekle
            features.extend([
                'recent_form_ratio', 'goal_efficiency', 'defense_efficiency',
                'win_rate_ratio', 'home_trend', 'away_trend'
            ])
            
            # Model güven skorunu hesaplama fonksiyonunu güncelle
            def calculate_confidence_score(probabilities, power_diff, form_diff):
                max_prob = max(probabilities)
                base_confidence = max_prob * 100
                
                # Güç ve form farklarına göre güven artışı
                power_confidence = min(abs(power_diff) * 20, 15)  # Maksimum %15 artış
                form_confidence = min(abs(form_diff) * 15, 10)    # Maksimum %10 artış
                
                # Eğer en yüksek olasılık belirli bir eşiğin üzerindeyse ek bonus
                prob_bonus = 10 if max_prob > 0.6 else (5 if max_prob > 0.5 else 0)
                
                # Olasılıklar arasındaki fark ne kadar büyükse o kadar güvenilir
                prob_diff = max_prob - sorted(probabilities)[-2]  # En yüksek ile ikinci en yüksek arasındaki fark
                diff_bonus = min(prob_diff * 100 * 0.5, 10)  # Maksimum %10 bonus
                
                total_confidence = base_confidence + power_confidence + form_confidence + prob_bonus + diff_bonus
                
                # Maksimum %95 ile sınırla
                return min(round(total_confidence), 95)
                
            # Model tahmininde güven skorunu güncelle
            ml_guven = calculate_confidence_score(
                probabilities,
                power_diff,
                form_diff
            )
            
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
            
            # Güven skoru hesaplama
            max_prob = max(probabilities)
            base_confidence = max_prob * 100
            
            # Güç ve form farklarına göre güven artışı
            power_confidence = min(abs(power_diff) * 20, 15)  # Maksimum %15 artış
            form_confidence = min(abs(form_diff) * 15, 10)    # Maksimum %10 artış
            
            # Eğer en yüksek olasılık belirli bir eşiğin üzerindeyse ek bonus
            prob_bonus = 10 if max_prob > 0.6 else (5 if max_prob > 0.5 else 0)
            
            # Olasılıklar arasındaki fark ne kadar büyükse o kadar güvenilir
            prob_diff = max_prob - sorted(probabilities)[-2]  # En yüksek ile ikinci en yüksek arasındaki fark
            diff_bonus = min(prob_diff * 100 * 0.5, 10)  # Maksimum %10 bonus
            
            # Toplam güven skoru
            ml_guven = min(round(base_confidence + power_confidence + form_confidence + prob_bonus + diff_bonus), 95)
            
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
            
            # İlk yarı gol olasılıkları için Poisson dağılımı
            first_half_probs = {
                '0.5 Alt': 0,
                '0.5 Üst': 0,
                '1.5 Alt': 0,
                '1.5 Üst': 0,
                '2.5 Alt': 0,
                '2.5 Üst': 0
            }
            
            # Poisson dağılımı kullanarak olasılıkları hesapla
            def poisson_prob(k, lambda_param):
                return np.exp(-lambda_param) * (lambda_param**k) / np.math.factorial(k)
            
            # Her bir gol sayısı için olasılıkları hesapla (0'dan 5'e kadar)
            first_half_goal_probs = [poisson_prob(i, total_expected_goals) for i in range(6)]
            
            # Alt/Üst olasılıklarını hesapla
            first_half_probs['0.5 Alt'] = round(first_half_goal_probs[0] * 100)  # Sadece 0 gol
            first_half_probs['0.5 Üst'] = round((1 - first_half_goal_probs[0]) * 100)  # 1 veya daha fazla gol
            
            first_half_probs['1.5 Alt'] = round(sum(first_half_goal_probs[:2]) * 100)  # 0 ve 1 gol
            first_half_probs['1.5 Üst'] = round((1 - sum(first_half_goal_probs[:2])) * 100)  # 2 veya daha fazla gol
            
            first_half_probs['2.5 Alt'] = round(sum(first_half_goal_probs[:3]) * 100)  # 0, 1 ve 2 gol
            first_half_probs['2.5 Üst'] = round((1 - sum(first_half_goal_probs[:3])) * 100)  # 3 veya daha fazla gol
            
            # Form ve güç farkına göre minimal düzeltmeler
            power_adjustment = abs(power_diff) * 0.05  # Güç farkı etkisini azalttık
            form_adjustment = abs(form_diff) * 0.03   # Form farkı etkisini azalttık
            
            # Ev sahibi daha güçlü/formda ise gol olasılıkları artar
            if power_diff > 0 or form_diff > 0:
                total_adjustment = min((power_adjustment + form_adjustment), 0.1)  # Maksimum %10 etki
                
                for limit in ['0.5', '1.5', '2.5']:
                    alt_prob = first_half_probs[f'{limit} Alt']
                    ust_prob = first_half_probs[f'{limit} Üst']
                    
                    alt_reduction = round(alt_prob * total_adjustment)
                    first_half_probs[f'{limit} Alt'] = max(5, alt_prob - alt_reduction)
                    first_half_probs[f'{limit} Üst'] = min(95, ust_prob + alt_reduction)
            
            # İlk yarı gol olasılıkları için Poisson dağılımı
            first_half_probs = {
                '0.5 Alt': 0,
                '0.5 Üst': 0,
                '1.5 Alt': 0,
                '1.5 Üst': 0,
                '2.5 Alt': 0,
                '2.5 Üst': 0
            }
            
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
            
            # Gol aralıkları için olasılıklar
            under_15 = goal_probs['under_15']
            over_15 = goal_probs['over_15']
            under_25 = goal_probs['under_25']
            over_25 = goal_probs['over_25']
            under_35 = goal_probs['under_35']
            over_35 = goal_probs['over_35']
            
            # İlk yarı gol beklentisi hesaplama
            home_first_half_goals = home_team_stats.get('ilk_yari_gol_ortalama', home_expected_goals * 0.4)
            away_first_half_goals = away_team_stats.get('ilk_yari_gol_ortalama', away_expected_goals * 0.4)
            home_first_half_conceded = home_team_stats.get('ilk_yari_yenilen_ortalama', home_conceded_per_game * 0.4)
            away_first_half_conceded = away_team_stats.get('ilk_yari_yenilen_ortalama', away_conceded_per_game * 0.4)
            
            # Form etkisini hesapla
            home_form = home_team_stats.get('son_5_form', 50) / 100
            away_form = away_team_stats.get('son_5_form', 50) / 100
            
            # Ev sahibi avantajı
            HOME_ADVANTAGE = 1.2
            expected_home_first_half = home_first_half_goals * HOME_ADVANTAGE
            expected_away_first_half = away_first_half_goals
            
            # Form etkisini uygula
            expected_home_first_half *= (0.8 + home_form * 0.4)
            expected_away_first_half *= (0.8 + away_form * 0.4)
            
            # Savunma zafiyetlerini hesaba kat
            defense_factor_home = away_first_half_conceded / 0.75  # 0.75 ortalama ilk yarı gol sayısı
            defense_factor_away = home_first_half_conceded / 0.75
            
            # Ev sahibi ve deplasman beklentilerini güncelle
            expected_home_first_half = round(expected_home_first_half * defense_factor_away * 1.1, 2)  # Ev sahibine %10 bonus
            expected_away_first_half = round(expected_away_first_half * defense_factor_home * 0.9, 2)  # Deplasmana %10 handikap
            
            # Toplam ilk yarı gol beklentisi
            expected_first_half_goals = round(expected_home_first_half + expected_away_first_half, 2)
            
            # İlk yarı gol olasılıkları için Poisson dağılımı
            first_half_probs = {
                '0.5 Alt': 0,
                '0.5 Üst': 0,
                '1.5 Alt': 0,
                '1.5 Üst': 0,
                '2.5 Alt': 0,
                '2.5 Üst': 0
            }
            
            # Her bir sınır için olasılıkları hesapla
            # Düzeltilmiş beklenti hesabı
            duzeltilmis_beklenti = expected_first_half_goals * (
                ((0.8 + home_form * 0.4) + (0.8 + away_form * 0.4)) / 2 * 
                HOME_ADVANTAGE * 
                (defense_factor_away + defense_factor_home) / 2
            )
            
            # Mantıklı sınırlar için son kontroller
            # 0.5 için
            if duzeltilmis_beklenti > 1.0:
                first_half_probs['0.5 Alt'] = max(20, min(30, first_half_probs['0.5 Alt']))  # Üst sınırı 30'a düşürdük
                first_half_probs['0.5 Üst'] = 100 - first_half_probs['0.5 Alt']
            else:
                first_half_probs['0.5 Alt'] = max(25, min(40, first_half_probs['0.5 Alt']))
                first_half_probs['0.5 Üst'] = 100 - first_half_probs['0.5 Alt']
                
            # 1.5 için
            if duzeltilmis_beklenti > 1.0:
                first_half_probs['1.5 Alt'] = max(50, min(60, first_half_probs['1.5 Alt']))  # Sınırları düşürdük
                first_half_probs['1.5 Üst'] = 100 - first_half_probs['1.5 Alt']
            else:
                first_half_probs['1.5 Alt'] = max(60, min(70, first_half_probs['1.5 Alt']))
                first_half_probs['1.5 Üst'] = 100 - first_half_probs['1.5 Alt']
                
            # 2.5 için
            if duzeltilmis_beklenti > 1.0:
                first_half_probs['2.5 Alt'] = max(85, min(92, first_half_probs['2.5 Alt']))
            else:
                first_half_probs['2.5 Alt'] = max(90, min(95, first_half_probs['2.5 Alt']))
            first_half_probs['2.5 Üst'] = 100 - first_half_probs['2.5 Alt']
            
            # Düzeltilmiş beklenti 1.0'dan büyükse 0.5 Üst olasılığını artır
            if duzeltilmis_beklenti > 1.0:
                current_05_ust = first_half_probs['0.5 Üst']
                first_half_probs['0.5 Üst'] = min(80, current_05_ust + 10)  # 10 puan artır ama max 80
                first_half_probs['0.5 Alt'] = 100 - first_half_probs['0.5 Üst']
            
            # Form ve güç farkına göre düzeltmeler
            power_adjustment = abs(power_diff) * 0.1  # Güç farkı etkisi
            form_adjustment = abs(form_diff) * 0.05   # Form farkı etkisi
            
            # Eğer ev sahibi daha güçlü/formda ise gol olasılıkları artar
            if power_diff > 0 or form_diff > 0:
                for limit in ['0.5', '1.5', '2.5']:
                    alt_prob = first_half_probs[f'{limit} Alt']
                    ust_prob = first_half_probs[f'{limit} Üst']
                    
                    # Alt olasılığını azalt, üst olasılığını artır
                    adjustment = (power_adjustment + form_adjustment) * 100
                    first_half_probs[f'{limit} Alt'] = max(5, round(alt_prob * (1 - adjustment/200)))  # Düzeltme faktörünü yarıya indirdik
                    first_half_probs[f'{limit} Üst'] = min(95, round(100 - first_half_probs[f'{limit} Alt']))
            
            # Olasılıkları mantıklı sınırlara çek
            for limit in ['0.5', '1.5', '2.5']:
                alt_prob = first_half_probs[f'{limit} Alt']
                ust_prob = first_half_probs[f'{limit} Üst']
                
                # 0.5 için minimum/maksimum sınırlar
                if limit == '0.5':
                    first_half_probs[f'{limit} Alt'] = max(25, min(35, alt_prob))  # 0.5 Alt için daha dar aralık
                    first_half_probs[f'{limit} Üst'] = 100 - first_half_probs[f'{limit} Alt']
                # 1.5 için minimum/maksimum sınırlar
                elif limit == '1.5':
                    first_half_probs[f'{limit} Alt'] = max(65, min(80, alt_prob))  # 1.5 Alt için daha dar aralık
                    first_half_probs[f'{limit} Üst'] = 100 - first_half_probs[f'{limit} Alt']
                # 2.5 için minimum/maksimum sınırlar
                else:
                    first_half_probs[f'{limit} Alt'] = max(85, min(95, alt_prob))  # 2.5 Alt için aynı aralık
                    first_half_probs[f'{limit} Üst'] = 100 - first_half_probs[f'{limit} Alt']
            
            # Detaylı ilk yarı analizi
            first_half_analysis = {
                'beklenen_goller': expected_first_half_goals,
                'ev_sahibi_beklenen': round(expected_home_first_half, 2),
                'deplasman_beklenen': round(expected_away_first_half, 2),
                'olasiliklar': first_half_probs,
                'analiz': {
                    'ev_form_etkisi': round(home_form, 2),
                    'deplasman_form_etkisi': round(away_form, 2),
                    'ev_sahibi_avantaji': HOME_ADVANTAGE,
                    'ev_ilk_yari_gol_ort': round(home_first_half_goals, 2),
                    'dep_ilk_yari_gol_ort': round(away_first_half_goals, 2),
                    'ev_ilk_yari_yenilen_ort': round(home_first_half_conceded, 2),
                    'dep_ilk_yari_yenilen_ort': round(away_first_half_conceded, 2),
                    'savunma_etkisi': {
                        'ev_sahibi': round(defense_factor_away, 2),
                        'deplasman': round(defense_factor_home, 2)
                    }
                }
            }
            
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
                'X/X': round(iy_draw * probabilities[0] * 1.2, 2),  # Beraberlik devam eder
                'X/2': round(iy_draw * probabilities[2] * 1.1, 2),  # Beraberlikten deplasman açılır
                '2/1': round(iy_away * probabilities[1] * 0.5, 2),  # Deplasman üstünlüğünü tamamen kaybeder
                '2/X': round(iy_away * probabilities[0] * 0.8, 2),  # Deplasman üstünlüğünü koruyamaz
                '2/2': round(iy_draw * probabilities[2] * 1.2, 2)   # Deplasman üstünlüğünü devam ettirir
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
                    'ilk_yari_detayli': first_half_analysis,
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
                        'ml_guven': ml_guven,
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
        """İki olayın birlikte gerçekleşme olasılığını hesaplar"""
        try:
            # Olayların bağımsız olduğunu varsayarak çarpımsal olasılık
            combined_prob = (prob1 * prob2) / 100
            
            # Korelasyon faktörü (0.1 pozitif korelasyon)
            correlation_factor = 1.1
            
            # Korelasyonu hesaba katarak düzeltilmiş olasılık
            adjusted_prob = min(combined_prob * correlation_factor, 100)
            
            return round(adjusted_prob, 2)
            
        except Exception as e:
            print(f"Kombinasyon olasılığı hesaplama hatası: {str(e)}")
            return 0