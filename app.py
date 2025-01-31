from flask import Flask, request, jsonify
from predict_matches import load_model_and_scaler, get_team_stats, predict_match

app = Flask(__name__)

# Model ve scaler'ı global olarak yükle
model, scaler = load_model_and_scaler()
standings = get_team_stats()

@app.route('/api/teams', methods=['GET'])
def get_teams():
    try:
        teams = standings['team'].tolist()
        return jsonify({'success': True, 'teams': teams})
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
