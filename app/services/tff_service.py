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
    TFF1_LIG_ID = 204  # TFF 1. Lig ID'si
    
    @staticmethod
    def get_standings(season="2025"):
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
    def get_matches(season="2025", league='super'):
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
                        'home_goals': match['goals']['home'],
                        'away_goals': match['goals']['away'],
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
    
    @staticmethod
    def calculate_detailed_team_stats(team_name, matches_df, before_date=None):
        """Football-Data.org'taki gibi detaylı takım istatistiklerini hesaplar"""
        from datetime import datetime
        import numpy as np
        
        try:
            # Temel istatistikler
            stats = {
                'form': 0,
                'atilan_goller': 0,
                'yenilen_goller': 0,
                'galibiyetler': 0,
                'beraberlikler': 0,
                'maglubiyetler': 0,
                'toplam_mac': 0,
                'ev_sahibi_golleri': 0,
                'deplasman_golleri': 0,
                'ev_sahibi_mac_sayisi': 0,
                'deplasman_mac_sayisi': 0,
                'ilk_yari_golleri': 0,
                'ilk_yari_yenilen': 0,
                'kg_var_sayisi': 0,
                'gol_yemeden': 0,
                'iki_takimda_gol': 0,
                'ust_2_5': 0,
                'son_5_form': 0,
                'son_5_gol': 0,
                'son_5_yenilen': 0,
                # Yeni özellikler
                'galibiyet_serisi': 0,
                'maglubiyetsiz_mac': 0,
                'gol_serisi': 0,
                'son_5_mac_trend': 0,
                'son_5_gol_trend': 0,
                'son_5_yenilen_trend': 0,
                'son_3_mac_gol_ort': 0,
                'son_3_mac_yenilen_ort': 0,
                'ilk_yari_ustunluk': 0,
                'ikinci_yari_ustunluk': 0,
                'mac_ici_geri_donus': 0
            }
            
            # Takımın maçlarını filtrele
            team_matches = matches_df[
                (matches_df['home_team'] == team_name) | 
                (matches_df['away_team'] == team_name)
            ].copy()
            
            if team_matches.empty:
                return stats
            
            # Tarih sıralaması
            team_matches['date'] = pd.to_datetime(team_matches['date'])
            team_matches = team_matches.sort_values('date', ascending=False)
            
            # Son 20 maçı al
            recent_matches = team_matches.head(20)
            
            # Seri istatistikleri için geçici değişkenler
            current_win_streak = 0
            current_unbeaten_streak = 0
            current_scoring_streak = 0
            
            # Son 5 maç için ayrı hesaplama
            last_5_matches = recent_matches.head(5)
            
            for idx, match in recent_matches.iterrows():
                is_home = match['home_team'] == team_name
                team_goals = match['home_goals'] if is_home else match['away_goals']
                opponent_goals = match['away_goals'] if is_home else match['home_goals']
                result = match['result']
                
                # Temel istatistikler
                stats['toplam_mac'] += 1
                stats['atilan_goller'] += team_goals
                stats['yenilen_goller'] += opponent_goals
                
                if is_home:
                    stats['ev_sahibi_golleri'] += team_goals
                    stats['ev_sahibi_mac_sayisi'] += 1
                else:
                    stats['deplasman_golleri'] += team_goals
                    stats['deplasman_mac_sayisi'] += 1
                
                # Sonuç istatistikleri
                if result == 'H' and is_home:
                    stats['galibiyetler'] += 1
                    current_win_streak += 1
                    current_unbeaten_streak += 1
                elif result == 'A' and not is_home:
                    stats['galibiyetler'] += 1
                    current_win_streak += 1
                    current_unbeaten_streak += 1
                elif result == 'D':
                    stats['beraberlikler'] += 1
                    current_unbeaten_streak += 1
                    current_win_streak = 0
                else:
                    stats['maglubiyetler'] += 1
                    current_win_streak = 0
                    current_unbeaten_streak = 0
                
                # Gol serisi
                if team_goals > 0:
                    current_scoring_streak += 1
                else:
                    current_scoring_streak = 0
                
                # Karşılıklı gol
                if team_goals > 0 and opponent_goals > 0:
                    stats['kg_var_sayisi'] += 1
                
                # Gol yemeden
                if opponent_goals == 0:
                    stats['gol_yemeden'] += 1
                
                # 2.5 üst
                if team_goals + opponent_goals > 2:
                    stats['ust_2_5'] += 1
                
                # İlk yarı analizi (basit yaklaşım)
                if team_goals > 0:
                    stats['ilk_yari_golleri'] += 1
                if opponent_goals > 0:
                    stats['ilk_yari_yenilen'] += 1
                
                # İlk yarı üstünlük
                if team_goals > opponent_goals:
                    stats['ilk_yari_ustunluk'] += 1
                elif team_goals < opponent_goals:
                    stats['ikinci_yari_ustunluk'] += 1
            
            # Form hesaplama (son 5 maç)
            if len(last_5_matches) > 0:
                wins = 0
                for _, match in last_5_matches.iterrows():
                    is_home = match['home_team'] == team_name
                    result = match['result']
                    if (result == 'H' and is_home) or (result == 'A' and not is_home):
                        wins += 1
                
                stats['son_5_form'] = (wins / len(last_5_matches)) * 100
                stats['son_5_gol'] = last_5_matches.apply(
                    lambda x: x['home_goals'] if x['home_team'] == team_name else x['away_goals'], axis=1
                ).sum()
                stats['son_5_yenilen'] = last_5_matches.apply(
                    lambda x: x['away_goals'] if x['home_team'] == team_name else x['home_goals'], axis=1
                ).sum()
            
            # Genel form hesaplama
            if stats['toplam_mac'] > 0:
                stats['form'] = ((stats['galibiyetler'] * 3 + stats['beraberlikler']) / (stats['toplam_mac'] * 3)) * 100
            
            # Seri istatistikleri
            stats['galibiyet_serisi'] = current_win_streak
            stats['maglubiyetsiz_mac'] = current_unbeaten_streak
            stats['gol_serisi'] = current_scoring_streak
            
            # Trend analizleri
            if len(last_5_matches) >= 3:
                # Son 3 maç gol ortalaması
                last_3_goals = last_5_matches.head(3).apply(
                    lambda x: x['home_goals'] if x['home_team'] == team_name else x['away_goals'], axis=1
                ).mean()
                last_3_conceded = last_5_matches.head(3).apply(
                    lambda x: x['away_goals'] if x['home_team'] == team_name else x['home_goals'], axis=1
                ).mean()
                
                stats['son_3_mac_gol_ort'] = last_3_goals
                stats['son_3_mac_yenilen_ort'] = last_3_conceded
            
            # Maç başı ortalamalar
            if stats['toplam_mac'] > 0:
                stats['mac_basi_gol'] = stats['atilan_goller'] / stats['toplam_mac']
                stats['mac_basi_yenilen'] = stats['yenilen_goller'] / stats['toplam_mac']
            
            if stats['ev_sahibi_mac_sayisi'] > 0:
                stats['ev_sahibi_mac_basi_gol'] = stats['ev_sahibi_golleri'] / stats['ev_sahibi_mac_sayisi']
            
            if stats['deplasman_mac_sayisi'] > 0:
                stats['deplasman_mac_basi_gol'] = stats['deplasman_golleri'] / stats['deplasman_mac_sayisi']
            
            # Yüzde hesaplamaları
            if stats['toplam_mac'] > 0:
                stats['kg_var_yuzde'] = (stats['kg_var_sayisi'] / stats['toplam_mac']) * 100
                stats['gol_yemeden_yuzde'] = (stats['gol_yemeden'] / stats['toplam_mac']) * 100
                stats['ust_2_5_yuzde'] = (stats['ust_2_5'] / stats['toplam_mac']) * 100
            
            return stats
            
        except Exception as e:
            print(f"Detaylı istatistik hesaplama hatası: {str(e)}")
            return {} 