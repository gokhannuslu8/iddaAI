import pandas as pd
import os
from datetime import datetime
from app.services.tff_service import TFFService
import time

class TFFDataCollectionService:
    def __init__(self):
        self.data_path = 'app/data'
        self.matches_file = f'{self.data_path}/tff_matches_data.csv'
        os.makedirs(self.data_path, exist_ok=True)
        
    def collect_season_data(self, season="2023-2024"):
        """Belirli bir sezonun tüm verilerini toplar"""
        try:
            print(f"\n{season} sezonu için veri toplama başladı...")
            
            # Puan durumu verilerini al
            standings = TFFService.get_standings()
            if not standings:
                print("Puan durumu verileri alınamadı!")
                return 0
                
            # Maç verilerini al
            matches = TFFService.get_matches(season)
            if not matches:
                print("Maç verileri alınamadı!")
                return 0
                
            # Her maç için takım istatistiklerini ekle
            enriched_matches = []
            for match in matches:
                home_team_stats = next((team for team in standings if team['takim_adi'] == match['ev_sahibi']), None)
                away_team_stats = next((team for team in standings if team['takim_adi'] == match['deplasman']), None)
                
                if home_team_stats and away_team_stats:
                    match_data = {
                        'tarih': match['tarih'],
                        'ev_sahibi': match['ev_sahibi'],
                        'deplasman': match['deplasman'],
                        'sonuc': match['sonuc'],
                        'skor': match['skor'],
                        'sezon': match['sezon'],
                        
                        # Ev sahibi özellikleri
                        'ev_puan_ort': home_team_stats['puan'] / home_team_stats['oynadigi_mac'],
                        'ev_gol_ort': home_team_stats['attigi_gol'] / home_team_stats['oynadigi_mac'],
                        'ev_yenilen_gol_ort': home_team_stats['yedigi_gol'] / home_team_stats['oynadigi_mac'],
                        'ev_galibiyet_orani': home_team_stats['galibiyet'] / home_team_stats['oynadigi_mac'],
                        'ev_lig_sirasi': home_team_stats['lig_sirasi'],
                        
                        # Deplasman özellikleri
                        'dep_puan_ort': away_team_stats['puan'] / away_team_stats['oynadigi_mac'],
                        'dep_gol_ort': away_team_stats['attigi_gol'] / away_team_stats['oynadigi_mac'],
                        'dep_yenilen_gol_ort': away_team_stats['yedigi_gol'] / away_team_stats['oynadigi_mac'],
                        'dep_galibiyet_orani': away_team_stats['galibiyet'] / away_team_stats['oynadigi_mac'],
                        'dep_lig_sirasi': away_team_stats['lig_sirasi']
                    }
                    enriched_matches.append(match_data)
            
            if enriched_matches:
                self._save_matches_data(enriched_matches)
                print(f"\nToplam {len(enriched_matches)} maç verisi kaydedildi")
            else:
                print("\nHiç maç verisi toplanamadı!")
            
            return len(enriched_matches)
            
        except Exception as e:
            print(f"Veri toplama hatası: {str(e)}")
            return 0
    
    def _save_matches_data(self, matches):
        """Maç verilerini CSV dosyasına kaydeder"""
        try:
            df = pd.DataFrame(matches)
            
            # Eğer dosya varsa, mevcut verilere ekle
            if os.path.exists(self.matches_file):
                existing_df = pd.read_csv(self.matches_file)
                # Tekrar eden maçları önle (tarih ve takım kombinasyonuna göre)
                df = pd.concat([existing_df, df]).drop_duplicates(
                    subset=['tarih', 'ev_sahibi', 'deplasman'], 
                    keep='last'
                )
            
            # Tarihe göre sırala
            df['tarih'] = pd.to_datetime(df['tarih'], format='%d.%m.%Y')
            df = df.sort_values('tarih', ascending=False)
            
            df.to_csv(self.matches_file, index=False)
            print(f"{len(matches)} maç verisi kaydedildi.")
            
        except Exception as e:
            print(f"Veri kaydetme hatası: {str(e)}") 