from flask import current_app
import requests
from datetime import datetime, timedelta
import time
from app.utils.constants import LEAGUE_IDS
from app.services.training_service import TrainingService
import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
import scipy.stats as stats
from scipy.stats import poisson
from collections import Counter
import traceback

class FootballService:
    def __init__(self):
        self.api_key = current_app.config['FOOTBALL_API_KEY']
        self.base_url = current_app.config['FOOTBALL_API_BASE_URL']
        self.training_service = TrainingService()
        self.data_dir = os.path.join('app', 'data')
        
        # Veri dizinini oluştur
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_headers(self):
        return {
            'X-Auth-Token': self.api_key
        }

    def collect_data(self, days=365):
        """Belirtilen gün sayısı kadar maç verisi toplar"""
        try:
            print(f"\n[DEBUG] Son {days} günün maç verileri toplanıyor...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            training_data = []
            team_matches = {}
            
            for league_id in LEAGUE_IDS:
                print(f"[INFO] Lig ID {league_id} için maçlar alınıyor...")
                
                url = f"{self.base_url}/competitions/{league_id}/matches"
                params = {
                    'dateFrom': start_date.strftime('%Y-%m-%d'),
                    'dateTo': end_date.strftime('%Y-%m-%d'),
                    'status': 'FINISHED'
                }
                
                response = requests.get(url, headers=self.get_headers(), params=params)
                
                if response.status_code != 200:
                    print(f"[ERROR] Lig {league_id} için API hatası: {response.status_code}")
                    continue
                
                matches = response.json().get('matches', [])
                print(f"[INFO] Lig {league_id} için {len(matches)} maç bulundu")
                
                # Maç geçmişlerini güncelle
                for match in matches:
                    home_id = match['homeTeam']['id']
                    away_id = match['awayTeam']['id']
                    
                    if home_id not in team_matches:
                        team_matches[home_id] = []
                    if away_id not in team_matches:
                        team_matches[away_id] = []
                    
                    team_matches[home_id].append(match)
                    team_matches[away_id].append(match)
                
                # Veri noktalarını oluştur
                for match in matches:
                    try:
                        match_date = datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ')
                        home_id = match['homeTeam']['id']
                        away_id = match['awayTeam']['id']
                        
                        home_stats = self.calculate_team_stats(team_matches[home_id], home_id, match_date)
                        away_stats = self.calculate_team_stats(team_matches[away_id], away_id, match_date)
                        
                        if not home_stats or not away_stats:
                            continue
                        
                        # Sonuçları belirle
                        result = 1 if match['score']['fullTime']['home'] > match['score']['fullTime']['away'] else (0 if match['score']['fullTime']['home'] == match['score']['fullTime']['away'] else 2)
                        kg_var = 1 if match['score']['fullTime']['home'] > 0 and match['score']['fullTime']['away'] > 0 else 0
                        over_25 = 1 if match['score']['fullTime']['home'] + match['score']['fullTime']['away'] > 2.5 else 0
                        total_goals = match['score']['fullTime']['home'] + match['score']['fullTime']['away']
                        first_half_goals = match['score']['halfTime']['home'] + match['score']['halfTime']['away']
                        
                        data_point = {
                            # Ev sahibi özellikleri
                            'home_team_form': home_stats['form'],
                            'home_team_goals_scored': home_stats['atilan_goller'],
                            'home_team_goals_conceded': home_stats['yenilen_goller'],
                            'home_team_wins': home_stats['galibiyetler'],
                            'home_team_draws': home_stats['beraberlikler'],
                            'home_team_losses': home_stats['maglubiyetler'],
                            'home_team_first_half_goals': home_stats['ilk_yari_golleri'],
                            'home_team_clean_sheets': home_stats['gol_yemeden'],
                            'home_team_both_scored': home_stats['kg_var_sayisi'],
                            'home_team_over_25': home_stats['ust_2_5'],
                            'home_team_last_5_form': home_stats['son_5_form'],
                            'home_team_last_5_goals': home_stats['son_5_gol'],
                            'home_team_win_streak': home_stats['galibiyet_serisi'],
                            'home_team_unbeaten': home_stats['maglubiyetsiz_mac'],
                            'home_team_scoring_streak': home_stats['gol_serisi'],
                            'home_team_form_trend': home_stats['son_5_mac_trend'],
                            'home_team_goals_trend': home_stats['son_5_gol_trend'],
                            'home_team_conceded_trend': home_stats['son_5_yenilen_trend'],
                            'home_team_last_3_goals_avg': home_stats['son_3_mac_gol_ort'],
                            'home_team_last_3_conceded_avg': home_stats['son_3_mac_yenilen_ort'],
                            'home_team_first_half_dominance': home_stats['ilk_yari_ustunluk'],
                            'home_team_second_half_dominance': home_stats['ikinci_yari_ustunluk'],
                            'home_team_comebacks': home_stats['mac_ici_geri_donus'],
                            
                            # Deplasman özellikleri
                            'away_team_form': away_stats['form'],
                            'away_team_goals_scored': away_stats['atilan_goller'],
                            'away_team_goals_conceded': away_stats['yenilen_goller'],
                            'away_team_wins': away_stats['galibiyetler'],
                            'away_team_draws': away_stats['beraberlikler'],
                            'away_team_losses': away_stats['maglubiyetler'],
                            'away_team_first_half_goals': away_stats['ilk_yari_golleri'],
                            'away_team_clean_sheets': away_stats['gol_yemeden'],
                            'away_team_both_scored': away_stats['kg_var_sayisi'],
                            'away_team_over_25': away_stats['ust_2_5'],
                            'away_team_last_5_form': away_stats['son_5_form'],
                            'away_team_last_5_goals': away_stats['son_5_gol'],
                            'away_team_win_streak': away_stats['galibiyet_serisi'],
                            'away_team_unbeaten': away_stats['maglubiyetsiz_mac'],
                            'away_team_scoring_streak': away_stats['gol_serisi'],
                            'away_team_form_trend': away_stats['son_5_mac_trend'],
                            'away_team_goals_trend': away_stats['son_5_gol_trend'],
                            'away_team_conceded_trend': away_stats['son_5_yenilen_trend'],
                            'away_team_last_3_goals_avg': away_stats['son_3_mac_gol_ort'],
                            'away_team_last_3_conceded_avg': away_stats['son_3_mac_yenilen_ort'],
                            'away_team_first_half_dominance': away_stats['ilk_yari_ustunluk'],
                            'away_team_second_half_dominance': away_stats['ikinci_yari_ustunluk'],
                            'away_team_comebacks': away_stats['mac_ici_geri_donus'],
                            
                            # Hedef değişkenler
                            'result': result,
                            'both_scored': kg_var,
                            'over_25': over_25,
                            'total_goals': total_goals,
                            'first_half_goals': first_half_goals
                        }
                        
                        training_data.append(data_point)
                        print(f"[INFO] {match['homeTeam']['name']} vs {match['awayTeam']['name']} verisi eklendi (Sonuç: {result})")
                    
                    except Exception as e:
                        print(f"[ERROR] Maç verisi işleme hatası: {str(e)}")
                        continue
                
                time.sleep(1)  # API rate limit için bekleme
            
            if not training_data:
                return {
                    'durum': 'hata',
                    'mesaj': 'Hiç veri toplanamadı'
                }
            
            # Verileri CSV'ye kaydet
            df = pd.DataFrame(training_data)
            csv_path = os.path.join(self.data_dir, f'training_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            df.to_csv(csv_path, index=False)
            
            # Modeli eğit
            training_result = self.training_service.train_model(csv_path)
            
            if training_result['durum'] == 'hata':
                return {
                    'durum': 'hata',
                    'mesaj': f"Model eğitimi başarısız: {training_result['mesaj']}"
                }
            
            return {
                'durum': 'basarili',
                'mesaj': f'Toplam {len(training_data)} maç verisi toplandı ve model eğitildi',
                'dogruluk': training_result['sonuclar']['mac_sonucu']['dogruluk'],
                'veri_sayisi': len(training_data)
            }
            
        except Exception as e:
            print(f"[ERROR] Veri toplama hatası: {str(e)}")
            return {
                'durum': 'hata',
                'mesaj': str(e)
            }

    def calculate_team_stats(self, matches, team_id, before_date):
        """Belirli bir tarihten önceki maçlara göre takım istatistiklerini hesaplar"""
        try:
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
                'ilk_yari_ustunluk': 0,  # İlk yarıyı önde bitirme sayısı
                'ikinci_yari_ustunluk': 0,  # İkinci yarıyı önde bitirme sayısı
                'mac_ici_geri_donus': 0  # Geriye düştüğü halde puan aldığı maç sayısı
            }
            
            # Son 20 maçı al
            recent_matches = sorted(
                [m for m in matches if datetime.strptime(m['utcDate'], '%Y-%m-%dT%H:%M:%SZ') < before_date],
                key=lambda x: datetime.strptime(x['utcDate'], '%Y-%m-%dT%H:%M:%SZ'),
                reverse=True
            )[:20]
            
            # Seri istatistikleri için geçici değişkenler
            current_win_streak = 0
            current_unbeaten_streak = 0
            current_scoring_streak = 0
            last_5_results = []
            last_5_goals = []
            last_5_conceded = []
            
            for i, match in enumerate(recent_matches):
                if match['status'] != 'FINISHED':
                    continue
                
                is_home = match['homeTeam']['id'] == team_id
                team_goals = match['score']['fullTime']['home'] if is_home else match['score']['fullTime']['away']
                opponent_goals = match['score']['fullTime']['away'] if is_home else match['score']['fullTime']['home']
                
                # İlk yarı skorları
                team_first_half = match['score']['halfTime']['home'] if is_home else match['score']['halfTime']['away']
                opponent_first_half = match['score']['halfTime']['away'] if is_home else match['score']['halfTime']['home']
                
                # Ev/deplasman gol istatistikleri
                if is_home:
                    stats['ev_sahibi_golleri'] += team_goals
                    stats['ev_sahibi_mac_sayisi'] += 1
                else:
                    stats['deplasman_golleri'] += team_goals
                    stats['deplasman_mac_sayisi'] += 1
                
                # Maç sonucu istatistikleri
                if team_goals > opponent_goals:
                    stats['galibiyetler'] += 1
                    stats['form'] += 1
                    current_win_streak += 1
                    current_unbeaten_streak += 1
                    last_5_results.append(3)
                elif team_goals == opponent_goals:
                    stats['beraberlikler'] += 1
                    stats['form'] += 0.5
                    current_win_streak = 0
                    current_unbeaten_streak += 1
                    last_5_results.append(1)
                else:
                    stats['maglubiyetler'] += 1
                    current_win_streak = 0
                    current_unbeaten_streak = 0
                    last_5_results.append(0)
                
                # Gol serisi
                if team_goals > 0:
                    current_scoring_streak += 1
                else:
                    current_scoring_streak = 0
                
                # Son 5 maç istatistikleri
                if i < 5:
                    stats['son_5_gol'] += team_goals
                    stats['son_5_yenilen'] += opponent_goals
                    last_5_goals.append(team_goals)
                    last_5_conceded.append(opponent_goals)
                
                # Son 3 maç ortalamaları
                if i < 3:
                    stats['son_3_mac_gol_ort'] += team_goals
                    stats['son_3_mac_yenilen_ort'] += opponent_goals
                
                # İlk yarı/ikinci yarı üstünlükleri
                if team_first_half > opponent_first_half:
                    stats['ilk_yari_ustunluk'] += 1
                
                second_half_team = team_goals - team_first_half
                second_half_opponent = opponent_goals - opponent_first_half
                if second_half_team > second_half_opponent:
                    stats['ikinci_yari_ustunluk'] += 1
                
                # Geri dönüş istatistiği
                if opponent_first_half > team_first_half and team_goals >= opponent_goals:
                    stats['mac_ici_geri_donus'] += 1
                
                # Genel gol istatistikleri
                stats['atilan_goller'] += team_goals
                stats['yenilen_goller'] += opponent_goals
                stats['ilk_yari_golleri'] += team_first_half
                stats['ilk_yari_yenilen'] += opponent_first_half
                
                # KG var/yok ve clean sheet istatistikleri
                if team_goals > 0 and opponent_goals > 0:
                    stats['kg_var_sayisi'] += 1
                    stats['iki_takimda_gol'] += 1
                if opponent_goals == 0:
                    stats['gol_yemeden'] += 1
                
                # 2.5 üst/alt istatistikleri
                if team_goals + opponent_goals > 2.5:
                    stats['ust_2_5'] += 1
                
                stats['toplam_mac'] += 1
            
            if stats['toplam_mac'] > 0:
                # Seri istatistiklerini kaydet
                stats['galibiyet_serisi'] = current_win_streak
                stats['maglubiyetsiz_mac'] = current_unbeaten_streak
                stats['gol_serisi'] = current_scoring_streak
                
                # Son 3 maç ortalamalarını hesapla
                stats['son_3_mac_gol_ort'] = round(stats['son_3_mac_gol_ort'] / min(3, stats['toplam_mac']), 2)
                stats['son_3_mac_yenilen_ort'] = round(stats['son_3_mac_yenilen_ort'] / min(3, stats['toplam_mac']), 2)
                
                # Form trendlerini hesapla
                if len(last_5_results) >= 3:
                    # Son 3 maçın ortalaması ile önceki 2 maçın ortalaması arasındaki fark
                    recent_form = sum(last_5_results[:3]) / 3
                    previous_form = sum(last_5_results[3:]) / len(last_5_results[3:]) if len(last_5_results[3:]) > 0 else recent_form
                    stats['son_5_mac_trend'] = round(recent_form - previous_form, 2)
                
                if len(last_5_goals) >= 3:
                    recent_goals = sum(last_5_goals[:3]) / 3
                    previous_goals = sum(last_5_goals[3:]) / len(last_5_goals[3:]) if len(last_5_goals[3:]) > 0 else recent_goals
                    stats['son_5_gol_trend'] = round(recent_goals - previous_goals, 2)
                
                if len(last_5_conceded) >= 3:
                    recent_conceded = sum(last_5_conceded[:3]) / 3
                    previous_conceded = sum(last_5_conceded[3:]) / len(last_5_conceded[3:]) if len(last_5_conceded[3:]) > 0 else recent_conceded
                    stats['son_5_yenilen_trend'] = round(recent_conceded - previous_conceded, 2)
                
                # Diğer yüzdesel istatistikler
                stats['form'] = (stats['form'] / stats['toplam_mac']) * 100
                stats['son_5_form'] = (stats['son_5_form'] / min(5, stats['toplam_mac'])) * 100
                stats['mac_basi_gol'] = round(stats['atilan_goller'] / stats['toplam_mac'], 2)
                stats['yenilen_gol_ortalama'] = round(stats['yenilen_goller'] / stats['toplam_mac'], 2)
                stats['ev_sahibi_mac_basi_gol'] = round(stats['ev_sahibi_golleri'] / max(stats['ev_sahibi_mac_sayisi'], 1), 2)
                stats['deplasman_mac_basi_gol'] = round(stats['deplasman_golleri'] / max(stats['deplasman_mac_sayisi'], 1), 2)
                stats['ilk_yari_gol_ortalama'] = round(stats['ilk_yari_golleri'] / stats['toplam_mac'], 2)
                stats['ilk_yari_yenilen_ortalama'] = round(stats['ilk_yari_yenilen'] / stats['toplam_mac'], 2)
                stats['kg_var_yuzde'] = round((stats['kg_var_sayisi'] / stats['toplam_mac']) * 100, 2)
                stats['gol_yemeden_yuzde'] = round((stats['gol_yemeden'] / stats['toplam_mac']) * 100, 2)
                stats['ust_2_5_yuzde'] = round((stats['ust_2_5'] / stats['toplam_mac']) * 100, 2)
                
                return stats
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Takım istatistikleri hesaplama hatası: {str(e)}")
            return None

    def get_team_stats(self, team_id):
        """Takım istatistiklerini API'den alır"""
        try:
            url = f"{self.base_url}/teams/{team_id}/matches"
            params = {
                'status': 'FINISHED',
                'limit': 20  # Son 20 maç
            }
            
            response = requests.get(url, headers=self.get_headers(), params=params)
            
            if response.status_code != 200:
                return None
            
            matches = response.json().get('matches', [])
            
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
                'son_5_yenilen': 0
            }
            
            for i, match in enumerate(matches):
                if match['status'] != 'FINISHED':
                    continue
                
                is_home = match['homeTeam']['id'] == team_id
                team_goals = match['score']['fullTime']['home'] if is_home else match['score']['fullTime']['away']
                opponent_goals = match['score']['fullTime']['away'] if is_home else match['score']['fullTime']['home']
                
                # İlk yarı skorları
                team_first_half = match['score']['halfTime']['home'] if is_home else match['score']['halfTime']['away']
                opponent_first_half = match['score']['halfTime']['away'] if is_home else match['score']['halfTime']['home']
                
                # Ev/deplasman gol istatistikleri
                if is_home:
                    stats['ev_sahibi_golleri'] += team_goals
                    stats['ev_sahibi_mac_sayisi'] += 1
                else:
                    stats['deplasman_golleri'] += team_goals
                    stats['deplasman_mac_sayisi'] += 1
                
                # Maç sonucu istatistikleri
                if team_goals > opponent_goals:
                    stats['galibiyetler'] += 1
                    stats['form'] += 1
                elif team_goals == opponent_goals:
                    stats['beraberlikler'] += 1
                    stats['form'] += 0.5
                else:
                    stats['maglubiyetler'] += 1
                
                # Genel gol istatistikleri
                stats['atilan_goller'] += team_goals
                stats['yenilen_goller'] += opponent_goals
                stats['ilk_yari_golleri'] += team_first_half
                stats['ilk_yari_yenilen'] += opponent_first_half
                
                # KG var/yok ve clean sheet istatistikleri
                if team_goals > 0 and opponent_goals > 0:
                    stats['kg_var_sayisi'] += 1
                    stats['iki_takimda_gol'] += 1
                if opponent_goals == 0:
                    stats['gol_yemeden'] += 1
                
                # 2.5 üst/alt istatistikleri
                if team_goals + opponent_goals > 2.5:
                    stats['ust_2_5'] += 1
                
                # Son 5 maç istatistikleri
                if i < 5:
                    stats['son_5_gol'] += team_goals
                    stats['son_5_yenilen'] += opponent_goals
                    if team_goals > opponent_goals:
                        stats['son_5_form'] += 1
                    elif team_goals == opponent_goals:
                        stats['son_5_form'] += 0.5
                
                stats['toplam_mac'] += 1
            
            if stats['toplam_mac'] > 0:
                # Form ve yüzdesel istatistikler
                stats['form'] = (stats['form'] / stats['toplam_mac']) * 100
                stats['son_5_form'] = (stats['son_5_form'] / min(5, stats['toplam_mac'])) * 100
                
                # Maç başı ortalamalar
                stats['mac_basi_gol'] = round(stats['atilan_goller'] / stats['toplam_mac'], 2)
                stats['yenilen_gol_ortalama'] = round(stats['yenilen_goller'] / stats['toplam_mac'], 2)
                stats['ev_sahibi_mac_basi_gol'] = round(stats['ev_sahibi_golleri'] / max(stats['ev_sahibi_mac_sayisi'], 1), 2)
                stats['deplasman_mac_basi_gol'] = round(stats['deplasman_golleri'] / max(stats['deplasman_mac_sayisi'], 1), 2)
                
                # İlk yarı ortalamaları
                stats['ilk_yari_gol_ortalama'] = round(stats['ilk_yari_golleri'] / stats['toplam_mac'], 2)
                stats['ilk_yari_yenilen_ortalama'] = round(stats['ilk_yari_yenilen'] / stats['toplam_mac'], 2)
                
                # Yüzdesel istatistikler
                stats['kg_var_yuzde'] = round((stats['kg_var_sayisi'] / stats['toplam_mac']) * 100, 2)
                stats['gol_yemeden_yuzde'] = round((stats['gol_yemeden'] / stats['toplam_mac']) * 100, 2)
                stats['ust_2_5_yuzde'] = round((stats['ust_2_5'] / stats['toplam_mac']) * 100, 2)
                
                print(f"[INFO] {team_id} için {stats['toplam_mac']} maç verisi kullanıldı")
                print(f"[DEBUG] Maç başı gol: {stats['mac_basi_gol']}, Yenilen: {stats['yenilen_gol_ortalama']}")
                return stats
            
            print(f"[WARNING] {team_id} için hiç geçerli maç bulunamadı")
            return None
            
        except Exception as e:
            print(f"[ERROR] Takım istatistikleri alma hatası: {str(e)}")
            return None

    def predict_match(self, home_team_id, away_team_id):
        """Maç sonucunu tahmin eder"""
        try:
            home_stats = self.get_team_stats(home_team_id)
            away_stats = self.get_team_stats(away_team_id)
            
            if not home_stats or not away_stats:
                return {
                    'durum': 'hata',
                    'mesaj': 'Takım istatistikleri alınamadı'
                }
            
            prediction = self.training_service.predict_match(home_stats, away_stats)
            return prediction
            
        except Exception as e:
            print(f"[ERROR] Tahmin hatası: {str(e)}")
            return {
                'durum': 'hata',
                'mesaj': str(e)
            }

    def get_daily_matches(self):
        """Günün maçlarını getirir"""
        try:
            print("[INFO] Günün maçları alınıyor...")
            today = datetime.now().strftime('%Y-%m-%d')
            matches = []

            # Her lig için günün maçlarını al
            for league_id in LEAGUE_IDS:
                try:
                    url = f"{self.base_url}/competitions/{league_id}/matches"
                    params = {
                        'dateFrom': today,
                        'dateTo': today,
                        'status': 'SCHEDULED'
                    }
                    
                    response = requests.get(url, headers=self.get_headers(), params=params)
                    
                    if response.status_code == 200:
                        league_matches = response.json().get('matches', [])
                        for match in league_matches:
                            matches.append({
                                'mac_id': str(match['id']),
                                'ev_sahibi': match['homeTeam']['name'],
                                'deplasman': match['awayTeam']['name'],
                                'lig': LEAGUE_IDS.get(league_id, 'Bilinmeyen Lig'),
                                'tarih': datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M')
                            })
                        print(f"[INFO] {LEAGUE_IDS.get(league_id)} için {len(league_matches)} maç bulundu")
                    else:
                        print(f"[WARNING] {league_id} için API yanıtı: {response.status_code}")
                    
                    time.sleep(1)  # API rate limit için bekleme
                    
                except Exception as e:
                    print(f"[ERROR] {league_id} ligi için hata: {str(e)}")
                    continue

            # Eğer API'den maç gelmezse test maçlarını kullan
            if not matches:
                print("[INFO] API'den maç bulunamadı, test maçları kullanılıyor...")
                test_matches = [
                    {
                        'mac_id': '1',
                        'ev_sahibi': 'Bayern Münih',
                        'deplasman': 'Dortmund',
                        'lig': 'Bundesliga',
                        'tarih': datetime.now().strftime('%Y-%m-%d %H:%M')
                    },
                    {
                        'mac_id': '2',
                        'ev_sahibi': 'PSG',
                        'deplasman': 'Leverkusen',
                        'lig': 'Champions League',
                        'tarih': datetime.now().strftime('%Y-%m-%d %H:%M')
                    },
                    {
                        'mac_id': '3',
                        'ev_sahibi': 'RB Leipzig',
                        'deplasman': 'Stuttgart',
                        'lig': 'Bundesliga',
                        'tarih': datetime.now().strftime('%Y-%m-%d %H:%M')
                    }
                ]
                matches.extend(test_matches)
                print(f"[INFO] {len(test_matches)} adet test maçı eklendi")

            print(f"[INFO] Toplam {len(matches)} adet maç bulundu")
            for match in matches:
                print(f"[DEBUG] Maç: {match['ev_sahibi']} vs {match['deplasman']} ({match['lig']})")
            
            return matches

        except Exception as e:
            print(f"[ERROR] Günün maçları alınırken hata: {str(e)}")
            print(traceback.format_exc())
            return []

    def get_available_teams(self):
        """Erişilebilir takımları ve liglerini getirir"""
        try:
            from app.utils.constants import TEAM_ID_TO_LEAGUE, LEAGUE_IDS
            available_teams = {}
            
            for team_id, league_code in TEAM_ID_TO_LEAGUE.items():
                try:
                    # Takım istatistiklerini kontrol et
                    team_stats = self.get_team_stats(team_id)
                    
                    if team_stats:  # Eğer istatistikler alınabiliyorsa
                        league_name = LEAGUE_IDS.get(league_code, league_code)
                        
                        if league_name not in available_teams:
                            available_teams[league_name] = []
                        
                        # API'den takım bilgisini al
                        url = f"{self.base_url}/teams/{team_id}"
                        response = requests.get(url, headers=self.get_headers())
                        
                        if response.status_code == 200:
                            team_data = response.json()
                            team_info = {
                                'id': team_id,
                                'name': team_data.get('name', 'Bilinmeyen'),
                                'shortName': team_data.get('shortName', 'Bilinmeyen'),
                                'tla': team_data.get('tla', '???'),
                                'founded': team_data.get('founded', None),
                                'venue': team_data.get('venue', 'Bilinmeyen'),
                                'stats_available': True
                            }
                            available_teams[league_name].append(team_info)
                        
                        time.sleep(0.5)  # API rate limit için bekleme
                        
                except Exception as e:
                    print(f"[WARNING] {team_id} ID'li takım için hata: {str(e)}")
                    continue
            
            # Boş ligleri temizle
            available_teams = {k: v for k, v in available_teams.items() if v}
            
            # Her lig için takımları isme göre sırala
            for league in available_teams:
                available_teams[league] = sorted(available_teams[league], key=lambda x: x['name'])
            
            return {
                'durum': 'basarili',
                'ligler': available_teams,
                'toplam_takim': sum(len(teams) for teams in available_teams.values())
            }
            
        except Exception as e:
            print(f"[ERROR] Erişilebilir takımları alma hatası: {str(e)}")
            return {
                'durum': 'hata',
                'mesaj': str(e)
            }

    def get_all_teams(self):
        """Tüm liglerdeki takımları getirir"""
        try:
            all_teams = {}
            
            for league_id in LEAGUE_IDS:
                try:
                    # Her lig için takımları al
                    url = f"{self.base_url}/competitions/{league_id}/teams"
                    response = requests.get(url, headers=self.get_headers())
                    
                    if response.status_code == 200:
                        data = response.json()
                        teams = data.get('teams', [])
                        
                        league_name = LEAGUE_IDS[league_id]
                        if league_name not in all_teams:
                            all_teams[league_name] = []
                        
                        for team in teams:
                            team_info = {
                                'id': team['id'],
                                'name': team['name'],
                                'shortName': team.get('shortName', team['name']),
                                'tla': team.get('tla', '???'),
                                'founded': team.get('founded', None),
                                'venue': team.get('venue', 'Bilinmeyen'),
                                'website': team.get('website', None),
                                'crest': team.get('crest', None)
                            }
                            all_teams[league_name].append(team_info)
                            
                        print(f"[INFO] {league_name} için {len(teams)} takım bulundu")
                    else:
                        print(f"[ERROR] {league_id} ligi için API hatası: {response.status_code}")
                    
                    time.sleep(1)  # API rate limit için bekleme
                    
                except Exception as e:
                    print(f"[ERROR] {league_id} ligi için hata: {str(e)}")
                    continue
            
            # Her lig için takımları isme göre sırala
            for league in all_teams:
                all_teams[league] = sorted(all_teams[league], key=lambda x: x['name'])
            
            return {
                'durum': 'basarili',
                'ligler': all_teams,
                'toplam_takim': sum(len(teams) for teams in all_teams.values())
            }
            
        except Exception as e:
            print(f"[ERROR] Takımları alma hatası: {str(e)}")
            return {
                'durum': 'hata',
                'mesaj': str(e)
            }

    def get_team_id(self, team_name):
        """Takım adından ID bulan yardımcı fonksiyon"""
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
            "Werder Bremen": 727,
            "Stuttgart": 10,
            "PSG": 524
        }
        return takim_id_listesi.get(team_name)

class MLService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.initialize_model()

    def initialize_model(self):
        """Model ve scaler'ı yükler veya yeni oluşturur"""
        try:
            self.model = joblib.load('app/models/match_prediction_model.joblib')
            self.scaler = joblib.load('app/models/match_prediction_scaler.joblib')
            print("[INFO] Model ve scaler başarıyla yüklendi")
        except:
            print("[INFO] Model ve scaler bulunamadı, yeni model oluşturulacak")
            self._create_new_model()
    
    def _create_new_model(self):
        """Yeni bir model oluşturur"""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()