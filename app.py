from flask import Flask, request, jsonify
from predict_matches import load_model_and_scaler, get_team_stats, predict_match
from collect_tff_data import collect_data, train_model
from tff_service import TFFService
import pandas as pd

app = Flask(__name__)

# Model ve scaler'ı global olarak yükle
model, scaler = load_model_and_scaler()
standings = get_team_stats()

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

@app.route('/api/teams', methods=['GET'])
def get_teams():
    try:
        # Tüm takımları al ve lig bilgisiyle birlikte döndür
        teams_data = []
        for _, team in standings.iterrows():
            teams_data.append({
                'name': team['team'],
                'league': 'Süper Lig' if team['league_type'] == 'super' else 'TFF 1. Lig'
            })
        return jsonify({'success': True, 'teams': teams_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        if not data or 'home_team' not in data or 'away_team' not in data:
            return jsonify({
                'success': False,
                'error': 'Ev sahibi ve deplasman takımları gerekli'
            })
        
        home_team = data['home_team']
        away_team = data['away_team']
        
        if home_team not in standings['team'].values or away_team not in standings['team'].values:
            return jsonify({
                'success': False,
                'error': 'Geçersiz takım ismi'
            })
        
        result = predict_match(model, scaler, standings, home_team, away_team)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/model/train/tr', methods=['GET'])
def train_turkish_model():
    try:
        global model, scaler, standings
        print("\nTürk takımları için model eğitimi başlıyor...")
        
        # Veri toplama
        print("\nVeri toplama aşaması başladı...")
        matches = collect_data()
        
        if matches.empty:
            return jsonify({
                'success': False,
                'error': 'Veri toplanamadı'
            })
        
        # Model eğitimi
        print("\nModel eğitimi aşaması başladı...")
        model, scaler = train_model(matches)
        
        # Güncel takım istatistiklerini güncelle
        standings = get_team_stats()
        
        return jsonify({
            'success': True,
            'message': 'Model başarıyla eğitildi ve güncellendi',
            'total_matches': len(matches)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Model eğitimi sırasında hata oluştu: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
