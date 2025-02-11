import requests
import pandas as pd
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

class TFFService:
    BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
    HEADERS = {
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
        'x-rapidapi-key': os.getenv('RAPIDAPI_KEY', '')
    }
    SUPER_LIG_ID = 203  # Türkiye Süper Lig ID'si
    
    @staticmethod
    def get_standings(season="2023"):
        """Süper Lig puan durumunu çeker"""
        try:
            url = f"{TFFService.BASE_URL}/standings"
            params = {
                'league': TFFService.SUPER_LIG_ID,
                'season': season
            }
            
            response = requests.get(url, headers=TFFService.HEADERS, params=params)
            data = response.json()
            
            if not data or 'response' not in data:
                print("API'den veri alınamadı!")
                return pd.DataFrame()
                
            standings_data = []
            standings = data['response'][0]['league']['standings'][0]
            
            for team in standings:
                team_data = {
                    'team': team['team']['name'],
                    'rank': team['rank'],
                    'played': team['all']['played'],
                    'won': team['all']['win'],
                    'drawn': team['all']['draw'],
                    'lost': team['all']['lose'],
                    'goals_for': team['all']['goals']['for'],
                    'goals_against': team['all']['goals']['against'],
                    'points': team['points']
                }
                standings_data.append(team_data)
                print(f"Takım verisi eklendi: {team_data['team']}")
            
            return pd.DataFrame(standings_data)
            
        except Exception as e:
            print(f"Puan durumu çekme hatası: {str(e)}")
            return pd.DataFrame()
    
    @staticmethod
    def get_matches(season="2023", league='super'):
        """Sezon maçlarını çeker"""
        try:
            url = f"{TFFService.BASE_URL}/fixtures"
            league_id = TFFService.SUPER_LIG_ID if league == 'super' else TFFService.TFF1_LIG_ID
            
            params = {
                'league': league_id,
                'season': season,
                'status': 'FT'  # Sadece tamamlanmış maçları al
            }
            
            print(f"\nAPI isteği yapılıyor: {url}")
            print(f"Parametreler: {params}")
            print(f"Headers: {TFFService.HEADERS}")
            
            response = requests.get(url, headers=TFFService.HEADERS, params=params)
            print(f"API yanıt kodu: {response.status_code}")
            
            data = response.json()
            
            if not data or 'response' not in data:
                print("API'den veri alınamadı!")
                return pd.DataFrame()
                
            matches_data = []
            
            for match in data['response']:
                try:
                    match_data = {
                        'date': datetime.fromtimestamp(match['fixture']['timestamp']).strftime('%Y-%m-%d'),
                        'home_team': match['teams']['home']['name'],
                        'away_team': match['teams']['away']['name'],
                        'score': f"{match['goals']['home']}-{match['goals']['away']}",
                        'season': season,
                        'league': league
                    }
                    
                    # Sonucu belirle
                    if match['goals']['home'] > match['goals']['away']:
                        match_data['result'] = 'H'  # Home win
                    elif match['goals']['home'] == match['goals']['away']:
                        match_data['result'] = 'D'  # Draw
                    else:
                        match_data['result'] = 'A'  # Away win
                        
                    matches_data.append(match_data)
                    print(f"Maç verisi eklendi: {match_data['home_team']} vs {match_data['away_team']}")
                except Exception as e:
                    print(f"Maç işleme hatası: {str(e)}")
                    continue
            
            return pd.DataFrame(matches_data)
            
        except Exception as e:
            print(f"Maç verisi çekme hatası: {str(e)}")
            return pd.DataFrame() 