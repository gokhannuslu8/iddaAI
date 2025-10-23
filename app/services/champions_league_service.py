import requests
import pandas as pd
from datetime import datetime, timedelta
from flask import current_app
import time
from app.utils.constants import LEAGUE_IDS
from app.utils.helpers import get_team_id, get_team_league

class ChampionsLeagueService:
    def __init__(self):
        self.api_key = current_app.config['FOOTBALL_API_KEY']
        self.base_url = 'https://api.football-data.org/v4'
        self.champions_league_id = 2001  # UEFA Champions League ID
        
    def get_headers(self):
        return {
            'X-Auth-Token': self.api_key
        }
    
    def get_champions_league_teams(self):
        """Şampiyonlar Ligi takımlarını getirir"""
        try:
            url = f"{self.base_url}/competitions/{self.champions_league_id}/teams"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code != 200:
                print(f"[ERROR] Şampiyonlar Ligi takımları alınamadı: {response.status_code}")
                return []
            
            teams_data = response.json()
            teams = teams_data.get('teams', [])
            
            print(f"[INFO] {len(teams)} Şampiyonlar Ligi takımı bulundu")
            return teams
            
        except Exception as e:
            print(f"[ERROR] Şampiyonlar Ligi takımları alma hatası: {str(e)}")
            return []
    
    def get_champions_league_matches(self, season=None):
        """Şampiyonlar Ligi maçlarını getirir"""
        try:
            if season is None:
                # Mevcut sezonu al
                current_year = datetime.now().year
                season = f"{current_year}-{current_year + 1}"
            
            url = f"{self.base_url}/competitions/{self.champions_league_id}/matches"
            params = {
                'season': season,
                'status': 'FINISHED'
            }
            
            response = requests.get(url, headers=self.get_headers(), params=params)
            
            if response.status_code != 200:
                print(f"[ERROR] Şampiyonlar Ligi maçları alınamadı: {response.status_code}")
                return pd.DataFrame()
            
            matches_data = response.json()
            matches = matches_data.get('matches', [])
            
            print(f"[INFO] {len(matches)} Şampiyonlar Ligi maçı bulundu")
            
            # DataFrame'e çevir
            matches_list = []
            for match in matches:
                match_info = {
                    'date': match['utcDate'],
                    'home_team': match['homeTeam']['name'],
                    'away_team': match['awayTeam']['name'],
                    'home_score': match['score']['fullTime']['home'],
                    'away_score': match['score']['fullTime']['away'],
                    'competition': 'UEFA Champions League',
                    'season': season,
                    'stage': match.get('stage', 'UNKNOWN'),
                    'group': match.get('group', 'UNKNOWN')
                }
                matches_list.append(match_info)
            
            return pd.DataFrame(matches_list)
            
        except Exception as e:
            print(f"[ERROR] Şampiyonlar Ligi maçları alma hatası: {str(e)}")
            return pd.DataFrame()
    
    def get_current_season_matches(self):
        """Mevcut sezonun Şampiyonlar Ligi maçlarını getirir"""
        try:
            current_year = datetime.now().year
            season = f"{current_year}-{current_year + 1}"
            
            print(f"[INFO] {season} sezonu Şampiyonlar Ligi maçları alınıyor...")
            return self.get_champions_league_matches(season)
            
        except Exception as e:
            print(f"[ERROR] Mevcut sezon maçları alma hatası: {str(e)}")
            return pd.DataFrame()
    
    def collect_champions_league_data(self, days=365):
        """Şampiyonlar Ligi verilerini toplar"""
        try:
            print(f"\n[INFO] Şampiyonlar Ligi veri toplama başladı...")
            
            # Son N günün maçlarını al
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = f"{self.base_url}/competitions/{self.champions_league_id}/matches"
            params = {
                'dateFrom': start_date.strftime('%Y-%m-%d'),
                'dateTo': end_date.strftime('%Y-%m-%d'),
                'status': 'FINISHED'
            }
            
            response = requests.get(url, headers=self.get_headers(), params=params)
            
            if response.status_code != 200:
                print(f"[ERROR] Şampiyonlar Ligi veri toplama hatası: {response.status_code}")
                return pd.DataFrame()
            
            matches_data = response.json()
            matches = matches_data.get('matches', [])
            
            print(f"[INFO] {len(matches)} Şampiyonlar Ligi maçı bulundu")
            
            # Verileri işle
            processed_matches = []
            for match in matches:
                try:
                    home_team = match['homeTeam']['name']
                    away_team = match['awayTeam']['name']
                    home_score = match['score']['fullTime']['home']
                    away_score = match['score']['fullTime']['away']
                    
                    # Sonuç belirleme
                    if home_score > away_score:
                        result = 'H'  # Ev sahibi kazandı
                    elif away_score > home_score:
                        result = 'A'  # Deplasman kazandı
                    else:
                        result = 'D'  # Beraberlik
                    
                    match_data = {
                        'date': match['utcDate'],
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_score': home_score,
                        'away_score': away_score,
                        'result': result,
                        'competition': 'UEFA Champions League',
                        'stage': match.get('stage', 'UNKNOWN'),
                        'group': match.get('group', 'UNKNOWN'),
                        'season': match.get('season', {}).get('startDate', 'UNKNOWN')
                    }
                    
                    processed_matches.append(match_data)
                    print(f"[INFO] {home_team} vs {away_team} ({home_score}-{away_score}) verisi eklendi")
                    
                except Exception as e:
                    print(f"[ERROR] Maç verisi işleme hatası: {str(e)}")
                    continue
                
                time.sleep(0.5)  # API rate limit için bekleme
            
            return pd.DataFrame(processed_matches)
            
        except Exception as e:
            print(f"[ERROR] Şampiyonlar Ligi veri toplama hatası: {str(e)}")
            return pd.DataFrame()
    
    def save_champions_league_data(self, matches_df, filename=None):
        """Şampiyonlar Ligi verilerini CSV dosyasına kaydeder"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'app/data/champions_league_matches_{timestamp}.csv'
            
            matches_df.to_csv(filename, index=False)
            print(f"[INFO] {len(matches_df)} Şampiyonlar Ligi maçı {filename} dosyasına kaydedildi")
            return filename
            
        except Exception as e:
            print(f"[ERROR] Şampiyonlar Ligi veri kaydetme hatası: {str(e)}")
            return None
    
    def get_team_champions_league_stats(self, team_name):
        """Belirli bir takımın Şampiyonlar Ligi istatistiklerini getirir"""
        try:
            # Takım ID'sini bul
            team_id = get_team_id(team_name)
            if not team_id:
                print(f"[ERROR] {team_name} takımı bulunamadı")
                return None
            
            # Takımın Şampiyonlar Ligi maçlarını al
            url = f"{self.base_url}/teams/{team_id}/matches"
            params = {
                'competitions': self.champions_league_id,
                'status': 'FINISHED',
                'limit': 50
            }
            
            response = requests.get(url, headers=self.get_headers(), params=params)
            
            if response.status_code != 200:
                print(f"[ERROR] {team_name} takım istatistikleri alınamadı: {response.status_code}")
                return None
            
            matches_data = response.json()
            matches = matches_data.get('matches', [])
            
            print(f"[INFO] {team_name} için {len(matches)} Şampiyonlar Ligi maçı bulundu")
            
            # İstatistikleri hesapla
            stats = {
                'team_name': team_name,
                'total_matches': len(matches),
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
                'win_rate': 0.0
            }
            
            for match in matches:
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                home_score = match['score']['fullTime']['home']
                away_score = match['score']['fullTime']['away']
                
                if home_team == team_name:
                    stats['goals_for'] += home_score
                    stats['goals_against'] += away_score
                    if home_score > away_score:
                        stats['wins'] += 1
                    elif home_score == away_score:
                        stats['draws'] += 1
                    else:
                        stats['losses'] += 1
                else:
                    stats['goals_for'] += away_score
                    stats['goals_against'] += home_score
                    if away_score > home_score:
                        stats['wins'] += 1
                    elif away_score == home_score:
                        stats['draws'] += 1
                    else:
                        stats['losses'] += 1
            
            if stats['total_matches'] > 0:
                stats['win_rate'] = stats['wins'] / stats['total_matches']
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] {team_name} takım istatistikleri alma hatası: {str(e)}")
            return None
