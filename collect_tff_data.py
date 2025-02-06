from tff_service import TFFService
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
import joblib
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import confusion_matrix

def load_saved_data():
    # Önceden kaydedilmiş veriyi yükle
    try:
        matches = pd.read_csv('matches_data.csv')
        print(f"\nKaydedilmiş {len(matches)} maç verisi yüklendi")
        return matches
    except FileNotFoundError:
        print("\nKaydedilmiş veri bulunamadı, yeni veri toplanacak...")
        return collect_data()

def collect_data():
    tff = TFFService()
    all_matches = pd.DataFrame()
    
    # 2022-2023, 2023-2024 ve 2024-2025 sezonları için veri toplama
    seasons = [2022, 2023, 2024]
    leagues = ['super', 'tff1']  # Her iki lig için veri topla
    
    for season in seasons:
        for league in leagues:
            print(f"\n{season} sezonu {league} için veri toplama başladı...")
            
            # Puan durumu verilerini al
            standings = tff.get_standings(season, league)
            if standings.empty:
                print(f"{season} sezonu {league} için puan durumu verisi bulunamadı.")
                continue
                
            # Maç verilerini al
            matches = tff.get_matches(season, league)
            if matches.empty:
                print(f"{season} sezonu {league} için maç verisi bulunamadı.")
                continue
                
            # Her maç için ev sahibi ve deplasman takımının istatistiklerini ekle
            processed_matches = []
            for _, match in matches.iterrows():
                home_stats = standings[standings['team'] == match['home_team']].iloc[0]
                away_stats = standings[standings['team'] == match['away_team']].iloc[0]
                
                match_data = {
                    'date': match['date'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'home_rank': home_stats['rank'],
                    'away_rank': away_stats['rank'],
                    'home_points': home_stats['points'],
                    'away_points': away_stats['points'],
                    'home_played': home_stats['played'],
                    'away_played': away_stats['played'],
                    'home_won': home_stats['won'],
                    'away_won': away_stats['won'],
                    'home_drawn': home_stats['drawn'],
                    'away_drawn': away_stats['drawn'],
                    'home_lost': home_stats['lost'],
                    'away_lost': away_stats['lost'],
                    'home_goals_for': home_stats['goals_for'],
                    'away_goals_for': away_stats['goals_for'],
                    'home_goals_against': home_stats['goals_against'],
                    'away_goals_against': away_stats['goals_against'],
                    'result': match['result'],
                    'league_type': league  # Hangi ligden olduğunu belirt
                }
                processed_matches.append(match_data)
                
            season_matches = pd.DataFrame(processed_matches)
            print(f"\n{season} sezonu {league} için {len(season_matches)} maç verisi toplandı")
            
            all_matches = pd.concat([all_matches, season_matches], ignore_index=True)
    
    print(f"\nToplam {len(all_matches)} maç verisi toplandı")
    
    # Verileri kaydet
    all_matches.to_csv('matches_data.csv', index=False)
    print("Veriler matches_data.csv dosyasına kaydedildi")
    
    return all_matches

def train_model(matches):
    # Feature'ları ve target'ı ayır
    features = ['home_rank', 'away_rank', 'home_points', 'away_points',
                'home_played', 'away_played', 'home_won', 'away_won',
                'home_drawn', 'away_drawn', 'home_lost', 'away_lost',
                'home_goals_for', 'away_goals_for', 'home_goals_against', 'away_goals_against']
    
    X = matches[features]
    y = matches['result']
    
    # Veriyi eğitim ve test setlerine ayır
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Feature'ları ölçeklendir
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Sınıf ağırlıklarını hesapla
    class_weights = compute_class_weight('balanced', classes=['H', 'D', 'A'], y=y_train)
    class_weight_dict = dict(zip(['H', 'D', 'A'], class_weights))
    
    # Optimize edilmiş hiperparametreler ile modeli eğit
    model = RandomForestClassifier(
        n_estimators=500,          # Daha fazla ağaç
        max_depth=8,               # Daha sınırlı derinlik
        min_samples_split=15,      # Daha fazla örnek gerekli
        min_samples_leaf=5,        # Daha fazla yaprak örneği
        max_features='sqrt',       # Özellik seçimi
        bootstrap=True,
        random_state=42,
        class_weight=class_weight_dict,  # Sınıf ağırlıkları
        n_jobs=-1                  # Tüm CPU'ları kullan
    )
    model.fit(X_train_scaled, y_train)
    
    # Model performansını değerlendir
    train_accuracy = model.score(X_train_scaled, y_train)
    test_accuracy = model.score(X_test_scaled, y_test)
    
    print("\nModel performansı:")
    print(f"Eğitim seti doğruluğu: {train_accuracy:.4f}")
    print(f"Test seti doğruluğu: {test_accuracy:.4f}")
    
    # Feature importance analizi
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nÖzellik önem sıralaması:")
    print(feature_importance)
    
    # Confusion matrix
    y_pred = model.predict(X_test_scaled)
    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix:")
    print(cm)
    
    # Modeli ve scaler'ı kaydet
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_filename = f"tff_model_{timestamp}.joblib"
    scaler_filename = f"tff_scaler_{timestamp}.joblib"
    
    joblib.dump(model, model_filename)
    joblib.dump(scaler, scaler_filename)
    
    print(f"\nModel kaydedildi: {model_filename}")
    print(f"Scaler kaydedildi: {scaler_filename}")
    
    return model, scaler

if __name__ == "__main__":
    print("\nModel eğitimi başlıyor...")
    matches = load_saved_data()
    if not matches.empty:
        train_model(matches)
    else:
        print("Veri toplanamadığı için model eğitilemiyor.") 