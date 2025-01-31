import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class TFFService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
        }
        self.base_url = 'https://api-football-v1.p.rapidapi.com/v3'
        self.league_id = 203  # Süper Lig ID'si
        
        # Retry stratejisi oluştur
        retry_strategy = Retry(
            total=3,  # toplam deneme sayısı
            backoff_factor=1,  # her denemede beklenecek süre
            status_forcelist=[429, 500, 502, 503, 504]  # yeniden denenecek HTTP kodları
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_standings(self, season):
        url = f"{self.base_url}/standings"
        params = {
            'league': self.league_id,
            'season': season
        }
        
        try:
            response = self.session.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data['response']:
                print(f"{season} sezonu için puan durumu verisi bulunamadı")
                return pd.DataFrame()
                
            standings = data['response'][0]['league']['standings'][0]
            
            teams_data = []
            for team in standings:
                team_data = {
                    'team': team['team']['name'],
                    'rank': team['rank'],
                    'points': team['points'],
                    'played': team['all']['played'],
                    'won': team['all']['win'],
                    'drawn': team['all']['draw'],
                    'lost': team['all']['lose'],
                    'goals_for': team['all']['goals']['for'],
                    'goals_against': team['all']['goals']['against']
                }
                teams_data.append(team_data)
                print(f"Takım verisi eklendi: {team_data['team']}")
                
            time.sleep(2)  # API rate limit için bekle
            return pd.DataFrame(teams_data)
            
        except requests.exceptions.RequestException as e:
            print(f"Puan durumu verisi alınırken hata oluştu: {e}")
            return pd.DataFrame()

    def get_matches(self, season):
        url = f"{self.base_url}/fixtures"
        params = {
            'league': self.league_id,
            'season': season
        }
        
        try:
            response = self.session.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data['response']:
                print(f"{season} sezonu için maç verisi bulunamadı")
                return pd.DataFrame()
                
            matches_data = []
            for match in data['response']:
                if match['fixture']['status']['short'] == 'FT':  # Sadece tamamlanmış maçları al
                    match_data = {
                        'date': datetime.strptime(match['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z').strftime('%d.%m.%Y'),
                        'home_team': match['teams']['home']['name'],
                        'away_team': match['teams']['away']['name'],
                        'home_score': match['goals']['home'],
                        'away_score': match['goals']['away'],
                        'result': 'H' if match['goals']['home'] > match['goals']['away'] else 'A' if match['goals']['home'] < match['goals']['away'] else 'D'
                    }
                    matches_data.append(match_data)
                    print(f"Maç verisi eklendi: {match_data['home_team']} vs {match_data['away_team']}")
                    
            time.sleep(2)  # API rate limit için bekle
            return pd.DataFrame(matches_data)
            
        except requests.exceptions.RequestException as e:
            print(f"Maç verisi alınırken hata oluştu: {e}")
            return pd.DataFrame() 