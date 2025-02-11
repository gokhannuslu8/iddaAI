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
        self.leagues = {
            'super': 203,  # Süper Lig ID'si
            'tff1': 204    # TFF 1. Lig ID'si
        }
        
        # Retry stratejisi oluştur
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_standings(self, season, league_type='super'):
        """Puan durumunu çeker
        
        Args:
            season: Sezon yılı (örn: 2024)
            league_type: 'super' veya 'tff1'
        """
        url = f"{self.base_url}/standings"
        league_id = self.leagues.get(league_type)
        
        if not league_id:
            print(f"Geçersiz lig tipi: {league_type}")
            return pd.DataFrame()
            
        params = {
            'league': league_id,
            'season': season
        }
        
        try:
            response = self.session.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data['response']:
                print(f"{season} sezonu için {league_type} puan durumu verisi bulunamadı")
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
                    'goals_against': team['all']['goals']['against'],
                    'league_type': league_type  # Hangi ligden olduğunu belirt
                }
                teams_data.append(team_data)
                print(f"Takım verisi eklendi: {team_data['team']} ({league_type})")
                
            time.sleep(2)  # API rate limit için bekle
            return pd.DataFrame(teams_data)
            
        except requests.exceptions.RequestException as e:
            print(f"Puan durumu verisi alınırken hata oluştu: {e}")
            return pd.DataFrame()

    def get_matches(self, season, league_type='super'):
        """Maç verilerini çeker
        
        Args:
            season: Sezon yılı (örn: 2024)
            league_type: 'super' veya 'tff1'
        """
        url = f"{self.base_url}/fixtures"
        league_id = self.leagues.get(league_type)
        
        if not league_id:
            print(f"Geçersiz lig tipi: {league_type}")
            return pd.DataFrame()
            
        params = {
            'league': league_id,
            'season': season,
            'status': 'FT'  # Sadece tamamlanmış maçları al
        }
        
        try:
            response = self.session.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data['response']:
                print(f"{season} sezonu için {league_type} maç verisi bulunamadı")
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
                        'result': 'H' if match['goals']['home'] > match['goals']['away'] else 'A' if match['goals']['home'] < match['goals']['away'] else 'D',
                        'league_type': league_type  # Hangi ligden olduğunu belirt
                    }
                    matches_data.append(match_data)
                    print(f"Maç verisi eklendi: {match_data['home_team']} vs {match_data['away_team']} ({league_type})")
                    
            time.sleep(2)  # API rate limit için bekle
            return pd.DataFrame(matches_data)
            
        except requests.exceptions.RequestException as e:
            print(f"Maç verisi alınırken hata oluştu: {e}")
            return pd.DataFrame() 