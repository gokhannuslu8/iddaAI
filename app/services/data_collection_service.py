from datetime import datetime, timedelta
import pandas as pd
import os
from app.services.football_service import FootballService, LEAGUE_IDS
import time

class DataCollectionService:
    def __init__(self):
        self.data_path = os.path.join('app', 'data')
        self.matches_file = os.path.join(self.data_path, 'matches_data.csv')
        
        # Dizini oluştur
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        
    def collect_historical_matches(self, days_back=30):
        """Son X günün maç sonuçlarını toplar"""
        try:
            matches_data = []
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            print(f"\nVeri toplama başladı: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                print(f"\n{date_str} tarihi için veri toplanıyor...")
                
                matches = self._get_matches_for_date(date_str)
                if matches:
                    matches_data.extend(matches)
                    print(f"{date_str} için {len(matches)} maç verisi eklendi")
                else:
                    print(f"{date_str} için maç verisi bulunamadı")
                
                # Rate limit'e takılmamak için her gün arasında biraz bekleyelim
                time.sleep(2)
                current_date += timedelta(days=1)
            
            if matches_data:
                self._save_matches_data(matches_data)
                print(f"\nToplam {len(matches_data)} maç verisi kaydedildi")
            else:
                print("\nHiç maç verisi toplanamadı!")
            
            return len(matches_data)
            
        except Exception as e:
            print(f"Veri toplama hatası: {str(e)}")
            return 0
    
    def _get_matches_for_date(self, date):
        """Belirli bir tarihteki maçları ve sonuçlarını alır"""
        try:
            matches = []
            # API'den maçları çek
            daily_matches = FootballService.get_matches_by_date(date)
            
            if not daily_matches:
                print(f"{date} tarihi için maç bulunamadı")
                return []
            
            print(f"{date} tarihi için {len(daily_matches)} maç bulundu")  # Debug için
            
            for match in daily_matches:
                try:
                    # Maç durumunu kontrol et
                    if match.get('status') != 'FINISHED':
                        print(f"Maç henüz tamamlanmamış: {match.get('homeTeam', {}).get('name')} vs {match.get('awayTeam', {}).get('name')}")
                        continue
                    
                    # Lig kontrolü
                    competition = match.get('competition', {})
                    competition_code = competition.get('code')
                    
                    if competition_code not in LEAGUE_IDS:
                        print(f"Desteklenmeyen lig: {competition.get('name', 'Bilinmeyen')} ({competition_code})")
                        continue
                        
                    print(f"İşlenen lig: {LEAGUE_IDS[competition_code]}")
                    
                    home_team_id = match.get('homeTeam', {}).get('id')
                    away_team_id = match.get('awayTeam', {}).get('id')
                    
                    print(f"Maç işleniyor: {match.get('homeTeam', {}).get('name')} vs {match.get('awayTeam', {}).get('name')}")
                    
                    # Maç öncesi takım istatistiklerini al
                    home_stats = FootballService.get_team_stats_at_date(home_team_id, date)
                    if not home_stats:
                        print(f"Ev sahibi takım istatistikleri alınamadı: {match.get('homeTeam', {}).get('name')}")
                        continue
                    
                    away_stats = FootballService.get_team_stats_at_date(away_team_id, date)
                    if not away_stats:
                        print(f"Deplasman takımı istatistikleri alınamadı: {match.get('awayTeam', {}).get('name')}")
                        continue
                    
                    # Maç sonucunu belirle (1: Ev sahibi kazandı, 0: Berabere, 2: Deplasman kazandı)
                    home_goals = match['score']['fullTime']['home']
                    away_goals = match['score']['fullTime']['away']
                    
                    if home_goals > away_goals:
                        result = '1'
                    elif home_goals == away_goals:
                        result = 'X'
                    else:
                        result = '2'
                    
                    # Özellik vektörünü oluştur
                    match_data = {
                        'tarih': date,
                        'mac_id': match['id'],
                        'ev_sahibi': match['homeTeam']['name'],
                        'deplasman': match['awayTeam']['name'],
                        'sonuc': result,
                        'skor': f"{home_goals}-{away_goals}",
                        
                        # Ev sahibi özellikleri
                        'ev_puan_ort': home_stats['puan'] / home_stats['oynadigi_mac'],
                        'ev_gol_ort': home_stats['attigi_gol'] / home_stats['oynadigi_mac'],
                        'ev_yenilen_gol_ort': home_stats['yedigi_gol'] / home_stats['oynadigi_mac'],
                        'ev_galibiyet_orani': home_stats['galibiyet'] / home_stats['oynadigi_mac'],
                        'ev_lig_sirasi': home_stats['lig_sirasi'],
                        
                        # Deplasman özellikleri
                        'dep_puan_ort': away_stats['puan'] / away_stats['oynadigi_mac'],
                        'dep_gol_ort': away_stats['attigi_gol'] / away_stats['oynadigi_mac'],
                        'dep_yenilen_gol_ort': away_stats['yedigi_gol'] / away_stats['oynadigi_mac'],
                        'dep_galibiyet_orani': away_stats['galibiyet'] / away_stats['oynadigi_mac'],
                        'dep_lig_sirasi': away_stats['lig_sirasi']
                    }
                    
                    matches.append(match_data)
                    print(f"Maç verisi başarıyla eklendi")
                
                except Exception as e:
                    print(f"Maç işleme hatası: {str(e)}")
                    continue
            
            print(f"{date} tarihi için toplam {len(matches)} maç verisi işlendi")
            return matches
            
        except Exception as e:
            print(f"Maç verisi alma hatası: {str(e)}")
            return []
    
    def _save_matches_data(self, matches):
        """Maç verilerini CSV dosyasına kaydeder"""
        try:
            df = pd.DataFrame(matches)
            
            # Eğer dosya varsa, mevcut verilere ekle
            if os.path.exists(self.matches_file):
                existing_df = pd.read_csv(self.matches_file)
                # Tekrar eden maçları önle
                existing_df = existing_df[~existing_df['mac_id'].isin(df['mac_id'])]
                df = pd.concat([existing_df, df], ignore_index=True)
            
            df.to_csv(self.matches_file, index=False)
            print(f"{len(matches)} maç verisi kaydedildi.")
            
        except Exception as e:
            print(f"Veri kaydetme hatası: {str(e)}")

    def _merge_match_and_standings_data(self, matches_df, standings_df):
        """Maç ve puan durumu verilerini birleştirir"""
        try:
            merged_data = []
            
            for _, match in matches_df.iterrows():
                # Ev sahibi ve deplasman takımlarının puan durumu verilerini bul
                home_stats = standings_df[standings_df['team'] == match['home_team']].iloc[0]
                away_stats = standings_df[standings_df['team'] == match['away_team']].iloc[0]
                
                # Maç verisi oluştur
                match_data = {
                    'date': match['date'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'home_rank': home_stats['rank'],
                    'away_rank': away_stats['rank'],
                    'home_points': home_stats['points'],
                    'away_points': away_stats['points'],
                    'home_played': home_stats['played'],
                    'away_played': away_stats['played'],
                    'home_won': home_stats['won'],
                    'away_won': away_stats['won'],
                    'home_drawn': home_stats['drawn'],
                    'away_drawn': away_stats['drawn'],
                    'home_lost': home_stats['lost'],
                    'away_lost': away_stats['lost'],
                    'home_goals_for': home_stats['goals_for'],
                    'away_goals_for': away_stats['goals_for'],
                    'home_goals_against': home_stats['goals_against'],
                    'away_goals_against': away_stats['goals_against'],
                    'result': match['result']
                }
                
                merged_data.append(match_data)
            
            return pd.DataFrame(merged_data)
            
        except Exception as e:
            print(f"Veri birleştirme hatası: {str(e)}")
            return pd.DataFrame()
        
    def load_saved_data(self):
        """Kaydedilmiş veriyi yükler"""
        try:
            # Önce matches_data.csv'yi kontrol et
            if os.path.exists(self.matches_file):
                df = pd.read_csv(self.matches_file)
                print(f"\n[INFO] {len(df)} maç verisi yüklendi")
                return df
            
            # Eğer matches_data.csv yoksa, data klasöründeki en son training verisi dosyasını kontrol et
            csv_files = [f for f in os.listdir(self.data_path) if f.startswith('training_data_')]
            if csv_files:
                latest_file = sorted(csv_files)[-1]
                file_path = os.path.join(self.data_path, latest_file)
                df = pd.read_csv(file_path)
                print(f"\n[INFO] {len(df)} maç verisi yüklendi ({latest_file})")
                return df
                
            print("\n[INFO] Kaydedilmiş veri bulunamadı")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"[ERROR] Veri yükleme hatası: {str(e)}")
            return pd.DataFrame() 