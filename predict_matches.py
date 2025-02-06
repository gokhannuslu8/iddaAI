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
    """Güncel takım istatistiklerini al"""
    tff = TFFService()
    all_standings = pd.DataFrame()
    
    # Her iki lig için de takımları al
    for league_type in ['super', 'tff1']:
        standings = tff.get_standings(2024, league_type)
        if not standings.empty:
            all_standings = pd.concat([all_standings, standings], ignore_index=True)
    
    return all_standings

def calculate_team_power(stats, opponent_league_type=None):
    """Takımın gücünü hesapla"""
    # Temel güç (sıralamaya göre)
    base_power = (20 - stats['rank']) / 20
    
    # Form gücü
    win_rate = stats['won'] / stats['played']
    goal_ratio = stats['goals_for'] / (stats['goals_against'] + 1)  # +1 to avoid division by zero
    
    # Toplam güç
    total_power = (base_power * 0.4) + (win_rate * 0.4) + (goal_ratio * 0.2)
    
    # Lig seviyesi farkını hesaba kat
    if opponent_league_type and stats['league_type'] != opponent_league_type:
        if stats['league_type'] == 'super' and opponent_league_type == 'tff1':
            # Süper Lig takımı, TFF 1. Lig takımına karşı güçlü
            total_power *= 1.3
        elif stats['league_type'] == 'tff1' and opponent_league_type == 'super':
            # TFF 1. Lig takımı, Süper Lig takımına karşı zayıf
            total_power *= 0.7
    
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

def calculate_btts_probability(home_stats, away_stats, is_different_leagues=False):
    """Karşılıklı gol olasılığını hesapla"""
    
    # Her takımın gol atma ve yeme oranlarını hesapla
    home_scoring_rate = home_stats['goals_for'] / home_stats['played']
    away_scoring_rate = away_stats['goals_for'] / away_stats['played']
    home_conceding_rate = home_stats['goals_against'] / home_stats['played']
    away_conceding_rate = away_stats['goals_against'] / away_stats['played']
    
    # Form faktörlerini hesapla
    home_form = home_stats['won'] / home_stats['played']  # Galibiyet oranı
    away_form = away_stats['won'] / away_stats['played']
    
    # Her takımın gol atma olasılığını hesapla
    home_scoring_prob = (home_scoring_rate / 3.0) * (1 + away_conceding_rate / 3.0)
    away_scoring_prob = (away_scoring_rate / 3.0) * (1 + home_conceding_rate / 3.0)
    
    # Form faktörünü uygula
    home_scoring_prob *= (0.8 + home_form * 0.4)  # Form maksimum %40 etki etsin
    away_scoring_prob *= (0.8 + away_form * 0.4)
    
    # Farklı ligler için düzeltme
    if is_different_leagues:
        if home_stats['league_type'] == 'super':
            home_scoring_prob *= 1.2  # Süper Lig ev sahibi daha kolay gol atar
            away_scoring_prob *= 0.8  # Alt lig takımı daha zor gol atar
        else:
            home_scoring_prob *= 0.8  # Alt lig ev sahibi daha zor gol atar
            away_scoring_prob *= 1.2  # Süper Lig takımı daha kolay gol atar
    
    # Her iki takımın da gol atma olasılığı
    btts_prob = home_scoring_prob * away_scoring_prob * 100
    
    # Olasılığı 0-100 arasına normalize et ve mantıklı bir aralığa çek
    btts_prob = min(max(round(btts_prob * 2), 15), 75)  # En az %15, en fazla %75
    
    # Eğer bir takımın gol ortalaması çok düşükse KG olasılığını düşür
    if home_scoring_rate < 0.5 or away_scoring_rate < 0.5:
        btts_prob = round(btts_prob * 0.6)  # %40 düşür
    elif home_scoring_rate < 1.0 or away_scoring_rate < 1.0:
        btts_prob = round(btts_prob * 0.8)  # %20 düşür
    
    # Eğer bir takımın savunması çok kötüyse KG olasılığını artır
    if home_conceding_rate > 2.0 or away_conceding_rate > 2.0:
        btts_prob = min(round(btts_prob * 1.2), 75)  # %20 artır ama max %75
    
    # Detaylı analiz
    analysis = {
        'ev_hucum_gucu': round(home_scoring_rate, 2),
        'deplasman_hucum_gucu': round(away_scoring_rate, 2),
        'ev_savunma_zaafiyeti': round(home_conceding_rate, 2),
        'deplasman_savunma_zaafiyeti': round(away_conceding_rate, 2),
        'ev_form_faktoru': round(home_form, 2),
        'deplasman_form_faktoru': round(away_form, 2)
    }
    
    return {
        'KG Var': btts_prob,
        'KG Yok': 100 - btts_prob,
        'analiz': analysis
    }

def predict_match(model, scaler, standings, home_team, away_team):
    # İki takım için istatistikleri bul
    home_stats = standings[standings['team'] == home_team].iloc[0]
    away_stats = standings[standings['team'] == away_team].iloc[0]
    
    # Farklı liglerden olup olmadığını kontrol et
    is_different_leagues = home_stats['league_type'] != away_stats['league_type']
    
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
    
    # Takım güçlerini hesapla (lig seviyesi farkını hesaba katarak)
    home_power = calculate_team_power(home_stats, away_stats['league_type'])
    away_power = calculate_team_power(away_stats, home_stats['league_type'])
    
    # Ev sahibi avantajı
    HOME_ADVANTAGE = 1.3
    home_power *= HOME_ADVANTAGE
    
    # Güç farkına göre olasılıkları hesapla
    power_diff = home_power - away_power
    
    # İstatistiksel olasılıkları hesapla
    if is_different_leagues:
        if home_stats['league_type'] == 'super':
            # Ev sahibi Süper Lig takımı
            stats_probs = [0.65, 0.20, 0.15]  # Süper Lig takımı lehine
        else:
            # Ev sahibi TFF 1. Lig takımı
            stats_probs = [0.30, 0.25, 0.45]  # Süper Lig takımı lehine
    else:
        # Normal güç farkı hesaplaması
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
    
    # Model ve istatistik ağırlıkları (farklı ligler için istatistiklere daha fazla ağırlık ver)
    if is_different_leagues:
        MODEL_WEIGHT = 0.2  # %20 model
        STATS_WEIGHT = 0.8  # %80 istatistik
    else:
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
    
    # Farklı ligler için gol tahminlerini ayarla
    if is_different_leagues:
        if home_stats['league_type'] == 'super':
            home_goals_avg *= 1.2  # Süper Lig ev sahibi daha fazla gol atar
            away_goals_avg *= 0.8  # TFF 1. Lig deplasmanı daha az gol atar
        else:
            home_goals_avg *= 0.8  # TFF 1. Lig ev sahibi daha az gol atar
            away_goals_avg *= 1.2  # Süper Lig deplasmanı daha fazla gol atar
    
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
    
    # Karşılıklı gol olasılıklarını hesapla
    btts_probs = calculate_btts_probability(home_stats, away_stats, is_different_leagues)
    
    # Ek istatistikleri hazırla
    additional_stats = {
        'ml_guven': round(max(model_probabilities) * 100),
        'ml_kullanildi': True,
        'beklenen_ilk_yari_gol': first_half_expected_goals,
        'farkli_lig_karsilasmasi': is_different_leagues,
        'karsilikli_gol': btts_probs
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
        for _, team in standings.iterrows():
            league_name = "Süper Lig" if team['league_type'] == 'super' else "TFF 1. Lig"
            print(f"- {team['team']} ({league_name})")
            
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