import joblib
import pandas as pd
import numpy as np
from tff_service import TFFService

def load_model_and_scaler():
    # Model ve scaler'ı yükle
    model = joblib.load('tff_model_20250131_201552.joblib')
    scaler = joblib.load('tff_scaler_20250131_201552.joblib')
    return model, scaler

def get_team_stats():
    # Güncel takım istatistiklerini al
    tff = TFFService()
    standings = tff.get_standings(2024)
    return standings

def calculate_team_power(stats):
    """Takımın gücünü hesapla"""
    # Temel güç (sıralamaya göre)
    base_power = (20 - stats['rank']) / 20
    
    # Form gücü
    win_rate = stats['won'] / stats['played']
    goal_ratio = stats['goals_for'] / (stats['goals_against'] + 1)  # +1 to avoid division by zero
    
    # Toplam güç
    total_power = (base_power * 0.4) + (win_rate * 0.4) + (goal_ratio * 0.2)
    return total_power

def calculate_goal_limits(home_goals_avg, away_goals_avg):
    """Gol sınırları için olasılıkları hesapla"""
    total_goals_avg = home_goals_avg + away_goals_avg
    
    # Poisson dağılımı kullanarak olasılıkları hesapla
    def poisson_prob(k, lambda_param):
        return np.exp(-lambda_param) * (lambda_param**k) / np.math.factorial(k)
    
    def calculate_under_prob(limit, lambda_param):
        prob = 0
        for i in range(int(limit) + 1):
            prob += poisson_prob(i, lambda_param)
        return prob
    
    # Her bir sınır için olasılıkları hesapla
    limits = {
        '1.5': calculate_under_prob(1.5, total_goals_avg),
        '2.5': calculate_under_prob(2.5, total_goals_avg),
        '3.5': calculate_under_prob(3.5, total_goals_avg)
    }
    
    # Alt/Üst formatında sonuçları hazırla
    goal_limits = {
        '1.5 Alt': round(limits['1.5'] * 100),
        '1.5 Üst': round((1 - limits['1.5']) * 100),
        '2.5 Alt': round(limits['2.5'] * 100),
        '2.5 Üst': round((1 - limits['2.5']) * 100),
        '3.5 Alt': round(limits['3.5'] * 100),
        '3.5 Üst': round((1 - limits['3.5']) * 100)
    }
    
    return goal_limits

def predict_match(model, scaler, standings, home_team, away_team):
    # İki takım için istatistikleri bul
    home_stats = standings[standings['team'] == home_team].iloc[0]
    away_stats = standings[standings['team'] == away_team].iloc[0]
    
    # Tahmin için özellikleri hazırla
    features = pd.DataFrame({
        'home_rank': [home_stats['rank']],
        'away_rank': [away_stats['rank']],
        'home_points': [home_stats['points']],
        'away_points': [away_stats['points']],
        'home_played': [home_stats['played']],
        'away_played': [away_stats['played']],
        'home_won': [home_stats['won']],
        'away_won': [away_stats['won']],
        'home_drawn': [home_stats['drawn']],
        'away_drawn': [away_stats['drawn']],
        'home_lost': [home_stats['lost']],
        'away_lost': [away_stats['lost']],
        'home_goals_for': [home_stats['goals_for']],
        'away_goals_for': [away_stats['goals_for']],
        'home_goals_against': [home_stats['goals_against']],
        'away_goals_against': [away_stats['goals_against']]
    })
    
    # Özellikleri ölçeklendir
    features_scaled = scaler.transform(features)
    
    # Model tahminlerini al
    model_probabilities = model.predict_proba(features_scaled)[0]
    
    # Takım güçlerini hesapla
    home_power = calculate_team_power(home_stats)
    away_power = calculate_team_power(away_stats)
    
    # Ev sahibi avantajı
    HOME_ADVANTAGE = 1.3
    home_power *= HOME_ADVANTAGE
    
    # Güç farkına göre olasılıkları hesapla
    power_diff = home_power - away_power
    
    # İstatistiksel olasılıkları hesapla
    if power_diff > 0.3:  # Ev sahibi çok üstün
        stats_probs = [0.70, 0.20, 0.10]
    elif power_diff > 0.15:  # Ev sahibi üstün
        stats_probs = [0.55, 0.25, 0.20]
    elif power_diff > -0.15:  # Dengeli
        stats_probs = [0.40, 0.35, 0.25]
    elif power_diff > -0.3:  # Deplasman üstün
        stats_probs = [0.20, 0.25, 0.55]
    else:  # Deplasman çok üstün
        stats_probs = [0.10, 0.20, 0.70]
    
    # Model ve istatistik ağırlıkları
    MODEL_WEIGHT = 0.3  # %30 model
    STATS_WEIGHT = 0.7  # %70 istatistik
    
    # Son olasılıkları hesapla
    final_probs = []
    for model_prob, stats_prob in zip(model_probabilities, stats_probs):
        final_prob = (model_prob * MODEL_WEIGHT) + (stats_prob * STATS_WEIGHT)
        final_probs.append(final_prob)
    
    # Olasılıkları normalize et
    total_prob = sum(final_probs)
    final_probs = [p/total_prob for p in final_probs]
    
    # En yüksek olasılığa sahip sonucu bul
    max_prob_index = final_probs.index(max(final_probs))
    prediction = ['H', 'D', 'A'][max_prob_index]
    
    # Skor tahmini yap
    home_goals_avg = home_stats['goals_for'] / home_stats['played']
    away_goals_avg = away_stats['goals_for'] / away_stats['played']
    
    # Güç farkına göre gol tahminlerini ayarla
    if prediction == 'H':
        predicted_home_goals = round(home_goals_avg * (1 + power_diff))
        predicted_away_goals = max(0, round(away_goals_avg * (1 - power_diff)))
    elif prediction == 'A':
        predicted_home_goals = max(0, round(home_goals_avg * (1 - abs(power_diff))))
        predicted_away_goals = round(away_goals_avg * (1 + abs(power_diff)))
    else:  # Beraberlik
        avg_goals = (home_goals_avg + away_goals_avg) / 2
        predicted_home_goals = predicted_away_goals = round(avg_goals)
    
    # Sonuçları hazırla
    result_mapping = {
        'H': 'Ev Sahibi Kazanır',
        'D': 'Beraberlik',
        'A': 'Deplasman Kazanır'
    }
    
    prob_mapping = {
        'H': f'Ev Sahibi Kazanma Olasılığı: %{final_probs[0]*100:.1f}',
        'D': f'Beraberlik Olasılığı: %{final_probs[1]*100:.1f}',
        'A': f'Deplasman Kazanma Olasılığı: %{final_probs[2]*100:.1f}'
    }
    
    # Takım istatistiklerini hazırla
    home_team_stats = {
        'sıralama': int(home_stats['rank']),
        'puan': int(home_stats['points']),
        'gol_attığı': int(home_stats['goals_for']),
        'gol_yediği': int(home_stats['goals_against']),
        'maç_başı_gol_ortalaması': round(home_goals_avg, 2),
        'maç_başı_yenilen_gol_ortalaması': round(home_stats['goals_against'] / home_stats['played'], 2)
    }
    
    away_team_stats = {
        'sıralama': int(away_stats['rank']),
        'puan': int(away_stats['points']),
        'gol_attığı': int(away_stats['goals_for']),
        'gol_yediği': int(away_stats['goals_against']),
        'maç_başı_gol_ortalaması': round(away_goals_avg, 2),
        'maç_başı_yenilen_gol_ortalaması': round(away_stats['goals_against'] / away_stats['played'], 2)
    }
    
    # Gol sınırları olasılıklarını hesapla
    goal_limits = calculate_goal_limits(home_goals_avg, away_goals_avg)
    
    # İlk yarı gol beklentisi (toplam beklentinin %35'i)
    first_half_expected_goals = round((predicted_home_goals + predicted_away_goals) * 0.35, 2)
    
    # Ek istatistikleri hazırla
    additional_stats = {
        'ml_guven': round(max(model_probabilities) * 100),  # En yüksek olasılığı güven oranı olarak al
        'ml_kullanildi': True,  # Model kullanıldığını belirt
        'beklenen_ilk_yari_gol': first_half_expected_goals  # İlk yarı gol beklentisi
    }
    
    prediction_result = {
        'match': f"{home_team} vs {away_team}",
        'prediction': {
            'tahmin': result_mapping[prediction],
            'skor_tahmini': f'{predicted_home_goals}-{predicted_away_goals}',
            'olasiliklar': [prob_mapping['H'], prob_mapping['D'], prob_mapping['A']],
            'ev_sahibi_form': f"Son form - Galibiyet: {home_stats['won']}, Beraberlik: {home_stats['drawn']}, Mağlubiyet: {home_stats['lost']}",
            'deplasman_form': f"Son form - Galibiyet: {away_stats['won']}, Beraberlik: {away_stats['drawn']}, Mağlubiyet: {away_stats['lost']}",
            'ev_sahibi_detay': home_team_stats,
            'deplasman_detay': away_team_stats,
            'gol_sinirlari': goal_limits,
            'ek_istatistikler': additional_stats
        },
        'success': True
    }
    
    return prediction_result

if __name__ == "__main__":
    try:
        # Model ve scaler'ı yükle
        model, scaler = load_model_and_scaler()
        
        # Güncel takım istatistiklerini al
        standings = get_team_stats()
        
        # Kullanıcıdan takım isimlerini al
        print("\nMevcut takımlar:")
        for team in standings['team'].values:
            print(f"- {team}")
            
        print("\nTahmin yapmak istediğiniz maç için takım isimlerini girin:")
        home_team = input("Ev Sahibi Takım: ")
        away_team = input("Deplasman Takımı: ")
        
        # Tahmin yap
        result = predict_match(model, scaler, standings, home_team, away_team)
        
        # Sonuçları göster
        print(f"\n{home_team} vs {away_team} maç tahmini:")
        print(f"Tahmin: {result['prediction']['tahmin']}")
        print(f"Skor Tahmini: {result['prediction']['skor_tahmini']}")
        print("\nOlasılıklar:")
        for prob in result['prediction']['olasiliklar']:
            print(prob)
        print(f"\n{home_team} {result['prediction']['ev_sahibi_form']}")
        print(f"{away_team} {result['prediction']['deplasman_form']}")
        
    except Exception as e:
        print(f"Bir hata oluştu: {str(e)}") 