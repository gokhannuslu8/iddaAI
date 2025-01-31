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
                return []
                
            standings_data = []
            standings = data['response'][0]['league']['standings'][0]
            
            for team in standings:
                team_data = {
                    'takim_adi': team['team']['name'],
                    'oynadigi_mac': team['all']['played'],
                    'galibiyet': team['all']['win'],
                    'beraberlik': team['all']['draw'],
                    'maglubiyet': team['all']['lose'],
                    'attigi_gol': team['all']['goals']['for'],
                    'yedigi_gol': team['all']['goals']['against'],
                    'averaj': team['goalsDiff'],
                    'puan': team['points'],
                    'lig_sirasi': team['rank']
                }
                standings_data.append(team_data)
                print(f"Takım verisi eklendi: {team_data['takim_adi']}")
            
            return standings_data
            
        except Exception as e:
            print(f"Puan durumu çekme hatası: {str(e)}")
            return []
    
    @staticmethod
    def get_matches(season="2023"):
        """Sezon maçlarını çeker"""
        try:
            url = f"{TFFService.BASE_URL}/fixtures"
            params = {
                'league': TFFService.SUPER_LIG_ID,
                'season': season,
                'status': 'FT'  # Sadece tamamlanmış maçları al
            }
            
            response = requests.get(url, headers=TFFService.HEADERS, params=params)
            data = response.json()
            
            if not data or 'response' not in data:
                print("API'den veri alınamadı!")
                return []
                
            matches_data = []
            
            for match in data['response']:
                try:
                    match_data = {
                        'tarih': datetime.fromtimestamp(match['fixture']['timestamp']).strftime('%d.%m.%Y'),
                        'ev_sahibi': match['teams']['home']['name'],
                        'deplasman': match['teams']['away']['name'],
                        'skor': f"{match['goals']['home']}-{match['goals']['away']}",
                        'sezon': season
                    }
                    
                    # Sonucu belirle
                    if match['goals']['home'] > match['goals']['away']:
                        match_data['sonuc'] = '1'
                    elif match['goals']['home'] == match['goals']['away']:
                        match_data['sonuc'] = 'X'
                    else:
                        match_data['sonuc'] = '2'
                        
                    matches_data.append(match_data)
                    print(f"Maç verisi eklendi: {match_data['ev_sahibi']} vs {match_data['deplasman']}")
                except Exception as e:
                    print(f"Maç işleme hatası: {str(e)}")
                    continue
            
            return matches_data
            
        except Exception as e:
            print(f"Maç verisi çekme hatası: {str(e)}")
            return [] 