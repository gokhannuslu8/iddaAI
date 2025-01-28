from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime
import os

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = "application/json;charset=utf-8"

API_KEY = "785e862acd6d40b19ae59b974d0958cd"

headers = {
    'X-Auth-Token': API_KEY,
    'Accept-Charset': 'utf-8',
    'Content-Type': 'application/json'
}

# Takım adından ID bulan yardımcı fonksiyon
def get_team_id(team_name):
    takim_id_listesi = {
        "Bayern Münih": 5,
        "Leverkusen": 3,
        "Dortmund": 4,
        "RB Leipzig": 721,
        "Hoffenheim": 722,
        "Freiburg": 723,
        "Bremen": 724,
        "Wolfsburg": 725,
        "Mönchengladbach": 726,
        "Werder Bremen": 727
        # Diğer takımları da ekleyebilirsiniz
    }
    return takim_id_listesi.get(team_name)

# Takım istatistiklerini çeken yardımcı fonksiyon
def get_team_stats(team_id):
    try:
        # Takım bilgilerini çek
        team_response = requests.get(
            f'https://api.football-data.org/v4/teams/{team_id}',
            headers=headers,
            timeout=10
        )
        
        # Bundesliga puan durumunu çek
        standings_response = requests.get(
            'https://api.football-data.org/v4/competitions/BL1/standings',
            headers=headers,
            timeout=10
        )
        
        # Takımın son maçlarını çek
        matches_response = requests.get(
            f'https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5',
            headers=headers,
            timeout=10
        )
        
        if all(response.status_code == 200 for response in [team_response, standings_response, matches_response]):
            team_data = team_response.json()
            standings_data = standings_response.json()
            matches_data = matches_response.json()
            
            # Puan durumu bilgilerini bul
            team_standings = None
            for standing in standings_data['standings'][0]['table']:
                if standing['team']['id'] == team_id:
                    team_standings = standing
                    break
            
            # Son 5 maç sonuçlarını düzenle
            last_matches = []
            for mac in matches_data['matches'][:5]:
                match_info = {
                    'tarih': datetime.strptime(mac['utcDate'], '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%Y'),
                    'ev_sahibi': mac['homeTeam']['name'],
                    'deplasman': mac['awayTeam']['name'],
                    'skor': f"{mac['score']['fullTime']['home']} - {mac['score']['fullTime']['away']}"
                }
                last_matches.append(match_info)
            
            return {
                'takim_adi': team_data['name'],
                'lig_sirasi': team_standings['position'],
                'oynadigi_mac': team_standings['playedGames'],
                'galibiyet': team_standings['won'],
                'beraberlik': team_standings['draw'],
                'maglubiyet': team_standings['lost'],
                'attigi_gol': team_standings['goalsFor'],
                'yedigi_gol': team_standings['goalsAgainst'],
                'averaj': team_standings['goalDifference'],
                'puan': team_standings['points'],
                'son_maclar': last_matches
            }
            
        return None
    except Exception as e:
        print(f"Hata: {str(e)}")
        return None

@app.route('/mac/tahmin', methods=['POST'])
def mac_tahmin():
    try:
        data = request.get_json()
        takim1_adi = data.get('takım1')
        takim2_adi = data.get('takım2')
        
        if not takim1_adi or not takim2_adi:
            return jsonify({'hata': 'Takım isimleri gerekli'}), 400
        
        takim1_id = get_team_id(takim1_adi)
        takim2_id = get_team_id(takim2_adi)
        
        if not takim1_id or not takim2_id:
            return jsonify({'hata': 'Takım bulunamadı'}), 404
        
        takim1_stats = get_team_stats(takim1_id)
        takim2_stats = get_team_stats(takim2_id)
        
        if not takim1_stats or not takim2_stats:
            return jsonify({'hata': 'Takım istatistikleri alınamadı'}), 500
        
        karsilastirma = {
            'takim1': takim1_stats,
            'takim2': takim2_stats
        }
        
        return jsonify(karsilastirma)
        
    except Exception as e:
        return jsonify({'hata': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
