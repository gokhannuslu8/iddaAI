from flask import current_app
import requests
import pandas as pd
import os
from app.services.football_service import FootballService
from app.services.ml_service import MLService
from app.utils.helpers import get_team_id
import traceback
from scipy.stats import poisson
from datetime import datetime

class MatchService:
    def __init__(self):
        self.football_service = FootballService()
        self.ml_service = MLService()
        
    def train_model(self):
        try:
            return {
                'status': 'success',
                'message': 'Model başarıyla eğitildi'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def get_model_status(self):
        try:
            model_exists = os.path.exists(self.model_path)
            data_exists = os.path.exists(self.data_path)
            
            return {
                'model_trained': model_exists,
                'data_available': data_exists,
                'status': 'ready' if model_exists and data_exists else 'not_ready'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def predict_match(self, data):
        """Maç tahminlerini yapar"""
        try:
            # Gerekli verileri kontrol et
            if not data or 'ev_sahibi' not in data or 'deplasman' not in data:
                print("[ERROR] Eksik veri: ev_sahibi veya deplasman")
                return {
                    'status': 'error',
                    'message': 'Ev sahibi ve deplasman takımları gerekli'
                }
                
            # Takım isimlerini al
            ev_sahibi = data['ev_sahibi'].strip()
            deplasman = data['deplasman'].strip()
            
            print(f"[INFO] Tahmin yapılıyor: {ev_sahibi} vs {deplasman}")
            
            # Takım ID'lerini al
            ev_sahibi_id = self.football_service.get_team_id(ev_sahibi)
            deplasman_id = self.football_service.get_team_id(deplasman)
            
            if not ev_sahibi_id or not deplasman_id:
                print(f"[ERROR] Takım ID'si bulunamadı: {ev_sahibi if not ev_sahibi_id else deplasman}")
                return {
                    'status': 'error',
                    'message': f'Takım bulunamadı: {ev_sahibi if not ev_sahibi_id else deplasman}'
                }
                
            # Takım istatistiklerini al
            ev_sahibi_stats = self.football_service.get_team_stats(ev_sahibi_id)
            deplasman_stats = self.football_service.get_team_stats(deplasman_id)
            
            if not ev_sahibi_stats or not deplasman_stats:
                return {
                    'status': 'error',
                    'message': 'Takım istatistikleri alınamadı'
                }
            
            # Güç hesaplamaları
            ev_guc = round((
                ev_sahibi_stats['form'] * 0.3 +  # Form ağırlığını düşür
                ev_sahibi_stats['mac_basi_gol'] * 25 +  # Gol ağırlığını düşür
                (1 - ev_sahibi_stats['yenilen_gol_ortalama'] * 0.4) * 15 +  # Defans ağırlığını düşür
                ev_sahibi_stats['son_5_form'] * 0.2 +  # Son form ekle
                ev_sahibi_stats['kg_var_yuzde'] * 0.1  # KG var yüzdesini ekle
            ))
            
            dep_guc = round((
                deplasman_stats['form'] * 0.3 +
                deplasman_stats['mac_basi_gol'] * 25 +
                (1 - deplasman_stats['yenilen_gol_ortalama'] * 0.4) * 15 +
                deplasman_stats['son_5_form'] * 0.2 +
                deplasman_stats['kg_var_yuzde'] * 0.1
            ))
            
            guc_farki = ev_guc - dep_guc

            # Beklenen gol hesaplamaları
            ev_beklenen_gol = round(ev_sahibi_stats['mac_basi_gol'] * 1.1, 2)  # Ev sahibi avantajı
            dep_beklenen_gol = round(deplasman_stats['mac_basi_gol'], 2)
            toplam_beklenen_gol = round(ev_beklenen_gol + dep_beklenen_gol, 2)
            
            # İlk yarı gol beklentisi
            ilk_yari_beklenen = round(toplam_beklenen_gol * 0.35, 2)  # Genelde gollerin %35'i ilk yarıda

            # ML ve istatistik ağırlıkları
            ML_WEIGHT = 0.70  # ML modeli ağırlığını artır (%70)
            STATS_WEIGHT = 0.30  # İstatistik ağırlığını azalt (%30)

            # Model tahminlerini al
            mac_sonucu = self.ml_service.predict_match_result('mac_sonucu', ev_sahibi_stats, deplasman_stats)
            kg_var = self.ml_service.predict_match_result('kg_var', ev_sahibi_stats, deplasman_stats)
            ust_2_5 = self.ml_service.predict_match_result('ust_2_5', ev_sahibi_stats, deplasman_stats)

            # İstatistiksel tahminleri hesapla
            stats_mac_sonucu = {
                'MS1': round((ev_guc / (ev_guc + dep_guc)) * 100),
                'MS2': round((dep_guc / (ev_guc + dep_guc)) * 100),
                'MSX': round(100 - ((ev_guc / (ev_guc + dep_guc)) * 100) - ((dep_guc / (ev_guc + dep_guc)) * 100))
            }

            # İstatistiksel KG Var hesaplaması
            stats_kg_var = round(
                (ev_sahibi_stats['kg_var_yuzde'] + deplasman_stats['kg_var_yuzde']) / 2 * 0.4 +  # Geçmiş KG Var yüzdesi
                (min(ev_sahibi_stats['mac_basi_gol'], deplasman_stats['mac_basi_gol']) * 15) +   # Gol beklentisi etkisi
                (min(ev_sahibi_stats['son_5_gol'], deplasman_stats['son_5_gol']) / 5 * 20) +     # Son form etkisi
                (max(ev_sahibi_stats['gol_yemeden_yuzde'], deplasman_stats['gol_yemeden_yuzde']) * 0.2)  # Defans etkisi
            )
            stats_kg_var = min(stats_kg_var, 85)  # Maximum %85 ile sınırla
            stats_kg_yok = 100 - stats_kg_var
            
            # ML ve istatistik tahminlerini birleştir
            if mac_sonucu:
                tahminler = {
                    'mac_sonucu': {
                        'MS1': round(mac_sonucu['olasiliklar']['MS1'] * ML_WEIGHT + stats_mac_sonucu['MS1'] * STATS_WEIGHT),
                        'MS2': round(mac_sonucu['olasiliklar']['MS2'] * ML_WEIGHT + stats_mac_sonucu['MS2'] * STATS_WEIGHT),
                        'MSX': round(mac_sonucu['olasiliklar']['MSX'] * ML_WEIGHT + stats_mac_sonucu['MSX'] * STATS_WEIGHT)
                    },
                    'cifte_sans': {
                        '1-2': round(mac_sonucu['olasiliklar']['MS1'] + mac_sonucu['olasiliklar']['MS2']),
                        '1-X': round(mac_sonucu['olasiliklar']['MS1'] + mac_sonucu['olasiliklar']['MSX']),
                        'X-2': round(mac_sonucu['olasiliklar']['MSX'] + mac_sonucu['olasiliklar']['MS2'])
                    },
                    'ilk_yari': {
                        'iy1': round(ev_beklenen_gol * 0.35 * 100 / ilk_yari_beklenen),
                        'iy2': round(dep_beklenen_gol * 0.35 * 100 / ilk_yari_beklenen),
                        'iyX': round(100 - (ev_beklenen_gol * 0.35 * 100 / ilk_yari_beklenen) - 
                                          (dep_beklenen_gol * 0.35 * 100 / ilk_yari_beklenen))
                    },
                    'iy_ms': {
                        'analizler': {
                            'ev_sahibi_one_gecer': round(ev_beklenen_gol * 0.35 * 100 / ilk_yari_beklenen),
                            'deplasman_one_gecer': round(dep_beklenen_gol * 0.35 * 100 / ilk_yari_beklenen),
                            'skor_degisir': 64,  # İstatistiksel ortalama
                            'skor_degismez': 36,
                            'en_olasilik': 'X/1'
                        },
                        'olasiliklar': {
                            '1/1': 13,
                            '1/2': 5,
                            '1/X': 4,
                            '2/1': 5,
                            '2/2': 10,
                            '2/X': 4,
                            'X/1': 24,
                            'X/2': 21,
                            'X/X': 13
                        }
                    },
                    'kombinasyonlar': {
                        'en_yuksek_olasilikli': {
                            'tahmin1': {
                                'secim': '1.5 Üst',
                                'oran': round(self._calculate_over_probability(1.5, toplam_beklenen_gol) * 100, 2)
                            },
                            'tahmin2': {
                                'secim': 'KG Var',
                                'oran': kg_var['olasiliklar']['VAR'] if kg_var else 62.0
                            },
                            'kombinasyon_olasiligi': round(
                                self._calculate_over_probability(1.5, toplam_beklenen_gol) * 100 * 
                                (kg_var['olasiliklar']['VAR'] if kg_var else 62.0) / 100,
                                2
                            ),
                            'aciklama': f"1.5 Üst ({round(self._calculate_over_probability(1.5, toplam_beklenen_gol) * 100, 2)}%) ve KG Var ({kg_var['olasiliklar']['VAR'] if kg_var else 62.0}%) birlikte gerçekleşme olasılığı: {round(self._calculate_over_probability(1.5, toplam_beklenen_gol) * 100 * (kg_var['olasiliklar']['VAR'] if kg_var else 62.0) / 100, 2)}%"
                        },
                        'ust_kg_var': {
                            'tahmin1': {
                                'secim': '2.5 Üst',
                                'oran': round(self._calculate_over_probability(2.5, toplam_beklenen_gol) * 100, 2)
                            },
                            'tahmin2': {
                                'secim': 'KG Var',
                                'oran': kg_var['olasiliklar']['VAR'] if kg_var else 62.0
                            },
                            'kombinasyon_olasiligi': round(
                                self._calculate_over_probability(2.5, toplam_beklenen_gol) * 100 * 
                                (kg_var['olasiliklar']['VAR'] if kg_var else 62.0) / 100,
                                2
                            ),
                            'aciklama': f"2.5 Üst ({round(self._calculate_over_probability(2.5, toplam_beklenen_gol) * 100, 2)}%) ve KG Var ({kg_var['olasiliklar']['VAR'] if kg_var else 62.0}%) birlikte gerçekleşme olasılığı: {round(self._calculate_over_probability(2.5, toplam_beklenen_gol) * 100 * (kg_var['olasiliklar']['VAR'] if kg_var else 62.0) / 100, 2)}%"
                        }
                    },
                    'gol_beklentisi': {
                        'ev_sahibi': round(ev_beklenen_gol),
                        'deplasman': round(dep_beklenen_gol),
                        'toplam': round(toplam_beklenen_gol)
                    },
                    'beklenen_toplam_gol': round(toplam_beklenen_gol),
                    'beklenen_ilk_yari_gol': round(ilk_yari_beklenen),
                    'gol_sinirlari': {
                        '1.5 Alt': round((1 - self._calculate_over_probability(1.5, toplam_beklenen_gol)) * 100),
                        '1.5 Üst': round(self._calculate_over_probability(1.5, toplam_beklenen_gol) * 100),
                        '2.5 Alt': round((1 - self._calculate_over_probability(2.5, toplam_beklenen_gol)) * 100),
                        '2.5 Üst': round(self._calculate_over_probability(2.5, toplam_beklenen_gol) * 100),
                        '3.5 Alt': round((1 - self._calculate_over_probability(3.5, toplam_beklenen_gol)) * 100),
                        '3.5 Üst': round(self._calculate_over_probability(3.5, toplam_beklenen_gol) * 100)
                    },
                    'gol_tahminleri': {
                        '0-1 Gol': round((1 - self._calculate_over_probability(1.5, toplam_beklenen_gol)) * 100),
                        '2-3 Gol': round((self._calculate_over_probability(1.5, toplam_beklenen_gol) - 
                                        self._calculate_over_probability(3.5, toplam_beklenen_gol)) * 100),
                        '4-5 Gol': round((self._calculate_over_probability(3.5, toplam_beklenen_gol) - 
                                        self._calculate_over_probability(5.5, toplam_beklenen_gol)) * 100),
                        '6+ Gol': round(self._calculate_over_probability(5.5, toplam_beklenen_gol) * 100),
                        'KG Var': kg_var['olasiliklar']['VAR'] if kg_var else 50,
                        'KG Yok': kg_var['olasiliklar']['YOK'] if kg_var else 50
                    },
                    'skor_tahminleri': self._calculate_score_probabilities(
                        ev_beklenen_gol, 
                        dep_beklenen_gol,
                        ev_sahibi_stats,
                        deplasman_stats
                    ),
                    'ek_istatistikler': {
                        'form_farki': guc_farki,
                        'guc_farki': guc_farki,
                        'takim1_guc': ev_guc,
                        'takim2_guc': dep_guc,
                        'takim1_mac_basi_gol': ev_sahibi_stats['mac_basi_gol'],
                        'takim2_mac_basi_gol': deplasman_stats['mac_basi_gol'],
                        'beklenen_toplam_gol': toplam_beklenen_gol,
                        'beklenen_ilk_yari_gol': ilk_yari_beklenen,
                        'ml_guven': mac_sonucu['guven'] if mac_sonucu else 0,
                        'ml_kullanildi': True,
                        'yakin_guc': abs(guc_farki) < 15,
                        'ev_sahibi_guclu': guc_farki > 15
                    }
                }
                ml_guven = mac_sonucu['guven']

            if kg_var:
                # ML modeli tahminleri (%70 ağırlık)
                ml_kg_var = kg_var['olasiliklar']['VAR']
                
                # İstatistiksel tahminler (%30 ağırlık)
                stats_kg_var = round(
                    (ev_sahibi_stats['kg_var_yuzde'] + deplasman_stats['kg_var_yuzde']) / 2 * 0.4 +  # Geçmiş KG Var yüzdesi
                    (min(ev_sahibi_stats['mac_basi_gol'], deplasman_stats['mac_basi_gol']) * 15) +   # Gol beklentisi etkisi
                    (min(ev_sahibi_stats['son_5_gol'], deplasman_stats['son_5_gol']) / 5 * 20) +     # Son form etkisi
                    (max(ev_sahibi_stats['gol_yemeden_yuzde'], deplasman_stats['gol_yemeden_yuzde']) * 0.2)  # Defans etkisi
                )
                stats_kg_var = min(stats_kg_var, 85)  # Maximum %85 ile sınırla
                
                # Ağırlıklı ortalama
                tahminler['gol_tahminleri']['KG Var'] = round(
                    ml_kg_var * ML_WEIGHT +
                    stats_kg_var * STATS_WEIGHT
                )
                tahminler['gol_tahminleri']['KG Yok'] = 100 - tahminler['gol_tahminleri']['KG Var']

            if ust_2_5:
                stats_over_prob = self._calculate_over_probability(2.5, toplam_beklenen_gol) * 100
                ust_2_5_oran = round(ust_2_5['olasiliklar']['ÜST'] * ML_WEIGHT + stats_over_prob * STATS_WEIGHT)
                alt_2_5_oran = 100 - ust_2_5_oran

                # Diğer gol sınırlarını hesapla
                stats_1_5_over = self._calculate_over_probability(1.5, toplam_beklenen_gol) * 100
                stats_3_5_over = self._calculate_over_probability(3.5, toplam_beklenen_gol) * 100
                
                tahminler['gol_sinirlari'] = {
                    '1.5 Alt': round(100 - stats_1_5_over),
                    '1.5 Üst': round(stats_1_5_over),
                    '2.5 Alt': alt_2_5_oran,
                    '2.5 Üst': ust_2_5_oran,
                    '3.5 Alt': round(100 - stats_3_5_over),
                    '3.5 Üst': round(stats_3_5_over)
                }

                # Gol tahminlerini güncelle
                tahminler['gol_tahminleri'].update({
                    '0-1 Gol': tahminler['gol_sinirlari']['1.5 Alt'],
                    '2-3 Gol': round(tahminler['gol_sinirlari']['2.5 Üst'] - tahminler['gol_sinirlari']['3.5 Üst']),
                    '4-5 Gol': round(tahminler['gol_sinirlari']['3.5 Üst'] * 0.7),
                    '6+ Gol': round(tahminler['gol_sinirlari']['3.5 Üst'] * 0.3)
                })

                # Kombinasyonları güncelle
                tahminler['kombinasyonlar'] = {
                    'en_yuksek_olasilikli': {
                        'tahmin1': {
                            'secim': '1.5 Üst',
                            'oran': tahminler['gol_sinirlari']['1.5 Üst']
                        },
                        'tahmin2': {
                            'secim': 'KG Var',
                            'oran': tahminler['gol_tahminleri']['KG Var']
                        },
                        'kombinasyon_olasiligi': round(
                            tahminler['gol_sinirlari']['1.5 Üst'] * 
                            tahminler['gol_tahminleri']['KG Var'] / 100,
                            2
                        ),
                        'aciklama': f"1.5 Üst ({tahminler['gol_sinirlari']['1.5 Üst']}%) ve KG Var ({tahminler['gol_tahminleri']['KG Var']}%) birlikte gerçekleşme olasılığı: {round(tahminler['gol_sinirlari']['1.5 Üst'] * tahminler['gol_tahminleri']['KG Var'] / 100, 2)}%"
                    },
                    'ust_kg_var': {
                        'tahmin1': {
                            'secim': '2.5 Üst',
                            'oran': ust_2_5_oran
                        },
                        'tahmin2': {
                            'secim': 'KG Var',
                            'oran': tahminler['gol_tahminleri']['KG Var']
                        },
                        'kombinasyon_olasiligi': round(
                            ust_2_5_oran * 
                            tahminler['gol_tahminleri']['KG Var'] / 100,
                            2
                        ),
                        'aciklama': f"2.5 Üst ({ust_2_5_oran}%) ve KG Var ({tahminler['gol_tahminleri']['KG Var']}%) birlikte gerçekleşme olasılığı: {round(ust_2_5_oran * tahminler['gol_tahminleri']['KG Var'] / 100, 2)}%"
                    }
                }

            # İlk yarı ve İY/MS tahminlerini hesapla
            ilk_yari_tahminleri = self._calculate_first_half_probabilities(
                ev_beklenen_gol,
                dep_beklenen_gol,
                ev_sahibi_stats,
                deplasman_stats
            )

            tahminler.update(ilk_yari_tahminleri)

            # Tahmin sonuçlarını döndürmeden önce loglama ekleyelim
            print(f"[DEBUG] Tahmin sonuçları: {tahminler}")
            
            response = {
                'durum': 'basarili',
                'tahminler': tahminler,
                'takim1': {
                    'id': ev_sahibi_id,
                    'isim': ev_sahibi,
                    'istatistikler': ev_sahibi_stats
                },
                'takim2': {
                    'id': deplasman_id,
                    'isim': deplasman,
                    'istatistikler': deplasman_stats
                }
            }
            
            print(f"[DEBUG] Response: {response}")
            return response
            
        except Exception as e:
            print(f"[ERROR] Tahmin hatası: {str(e)}")
            print(f"[ERROR] Detay: {traceback.format_exc()}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _calculate_over_probability(self, limit, expected_goals):
        """Belirli bir gol limitinin üstünde olma olasılığını hesaplar"""
        try:
            # Poisson olasılığını hesapla
            poisson_prob = 1 - sum(poisson.pmf(k, expected_goals) for k in range(int(limit)))
            
            # Form faktörünü ekle
            form_adjustment = 0.85  # Olasılıkları biraz düşür
            
            # Düzeltilmiş olasılık
            adjusted_prob = poisson_prob * form_adjustment
            
            return adjusted_prob
            
        except Exception as e:
            print(f"[ERROR] Olasılık hesaplama hatası: {str(e)}")
            return 0.5  # Hata durumunda 50-50 dön

    def _calculate_score_probabilities(self, home_expected, away_expected, home_stats, away_stats):
        """En olası skorları hesaplar"""
        try:
            scores = []
            total_probability = 0
            
            # Olası skorları hesapla (0-0'dan 3-3'e kadar)
            for home_goals in range(4):
                for away_goals in range(4):
                    prob_home = poisson.pmf(home_goals, home_expected)
                    prob_away = poisson.pmf(away_goals, away_expected)
                    
                    # Form ve güç farkını hesaba kat
                    form_factor = (home_stats['form'] - away_stats['form']) / 200  # -0.5 ile 0.5 arası
                    
                    # Skor olasılığını hesapla
                    score_prob = prob_home * prob_away * (1 + form_factor)
                    total_probability += score_prob
                    
                    scores.append({
                        'skor': f"{home_goals}-{away_goals}",
                        'oran': score_prob
                    })
            
            # Olasılıkları normalize et (toplam %100 olacak şekilde)
            for score in scores:
                score['oran'] = round((score['oran'] / total_probability) * 100)
            
            # En yüksek olasılıklı 5 skoru döndür
            scores.sort(key=lambda x: x['oran'], reverse=True)
            top_5 = scores[:5]
            
            # Top 5'in toplamını kontrol et ve gerekirse normalize et
            top_5_total = sum(score['oran'] for score in top_5)
            if top_5_total != 100:
                normalize_factor = 100 / top_5_total
                for score in top_5:
                    score['oran'] = round(score['oran'] * normalize_factor)
            
            # Son bir kontrol yap ve gerekirse düzelt
            final_total = sum(score['oran'] for score in top_5)
            if final_total != 100:
                diff = 100 - final_total
                top_5[0]['oran'] += diff  # Farkı en olası skora ekle
            
            return top_5
            
        except Exception as e:
            print(f"[ERROR] Skor olasılığı hesaplama hatası: {str(e)}")
            return [
                {'skor': '1-1', 'oran': 25},
                {'skor': '1-0', 'oran': 20},
                {'skor': '0-1', 'oran': 20},
                {'skor': '2-1', 'oran': 18},
                {'skor': '1-2', 'oran': 17}
            ]

    def _calculate_first_half_probabilities(self, home_expected, away_expected, home_stats, away_stats):
        """İlk yarı olasılıklarını hesaplar"""
        try:
            # İlk yarı gol beklentileri (genelde toplam gollerin %35'i ilk yarıda)
            home_first_half = home_expected * 0.35
            away_first_half = away_expected * 0.35
            
            # Form faktörünü ekle
            form_diff = (home_stats['form'] - away_stats['form']) / 200
            
            # İlk yarı olasılıkları
            iy1 = round(poisson.pmf(1, home_first_half) * (1 + form_diff) * 100)
            iy2 = round(poisson.pmf(1, away_first_half) * (1 - form_diff) * 100)
            iyx = round(100 - iy1 - iy2)  # Kalan olasılık beraberlik
            
            # İY/MS olasılıkları
            iy_ms = {
                '1/1': round(iy1 * 0.6),  # İlk yarı önde bitirenlerin %60'ı maçı kazanır
                '1/2': round(iy1 * 0.15),
                '1/X': round(iy1 * 0.25),
                '2/1': round(iy2 * 0.15),
                '2/2': round(iy2 * 0.6),
                '2/X': round(iy2 * 0.25),
                'X/1': round(iyx * 0.35),
                'X/2': round(iyx * 0.35),
                'X/X': round(iyx * 0.3)
            }
            
            # Toplamların 100 olmasını sağla
            total_iy = iy1 + iy2 + iyx
            if total_iy != 100:
                iy1 = round(iy1 * (100/total_iy))
                iy2 = round(iy2 * (100/total_iy))
                iyx = 100 - iy1 - iy2
                
            total_iy_ms = sum(iy_ms.values())
            if total_iy_ms != 100:
                factor = 100/total_iy_ms
                for key in iy_ms:
                    iy_ms[key] = round(iy_ms[key] * factor)
                # Son düzeltme
                diff = 100 - sum(iy_ms.values())
                iy_ms['X/X'] += diff
                
            return {
                'ilk_yari': {
                    'iy1': iy1,
                    'iy2': iy2,
                    'iyX': iyx
                },
                'iy_ms': {
                    'olasiliklar': iy_ms,
                    'analizler': {
                        'ev_sahibi_one_gecer': iy1,
                        'deplasman_one_gecer': iy2,
                        'skor_degisir': round((100 - sum(v for k, v in iy_ms.items() if k[0] == k[2])) * 0.8),  # Skor değişme olasılığı
                        'skor_degismez': round(sum(v for k, v in iy_ms.items() if k[0] == k[2]) * 1.2),  # Skor değişmeme olasılığı
                        'en_olasilik': max(iy_ms.items(), key=lambda x: x[1])[0]  # En yüksek olasılıklı sonuç
                    }
                }
            }
            
        except Exception as e:
            print(f"[ERROR] İlk yarı olasılıkları hesaplama hatası: {str(e)}")
            return {
                'ilk_yari': {'iy1': 35, 'iy2': 35, 'iyX': 30},
                'iy_ms': {
                    'olasiliklar': {
                        '1/1': 15, '1/2': 5, '1/X': 10,
                        '2/1': 5, '2/2': 15, '2/X': 10,
                        'X/1': 15, 'X/2': 15, 'X/X': 10
                    },
                    'analizler': {
                        'ev_sahibi_one_gecer': 35,
                        'deplasman_one_gecer': 35,
                        'skor_degisir': 60,
                        'skor_degismez': 40,
                        'en_olasilik': '1/1'
                    }
                }
            }

    def get_daily_matches(self):
        """Günün maçlarını getirir"""
        try:
            print("[INFO] Günün maçları isteniyor...")
            matches = self.football_service.get_daily_matches()
            
            if not matches:
                print("[WARNING] Günün maçları bulunamadı")
                return []
            
            print(f"[INFO] {len(matches)} adet maç bulundu")
            
            # Maç detaylarını logla
            for match in matches:
                print(f"[DEBUG] Maç: {match['ev_sahibi']} vs {match['deplasman']}")
            
            return matches
        
        except Exception as e:
            print(f"[ERROR] Günün maçları alınırken hata: {str(e)}")
            print(traceback.format_exc())
            return []

    def create_daily_coupon(self):
        """Günün kuponunu oluşturur"""
        try:
            print("[INFO] Günün kuponu oluşturuluyor...")
            matches = self.get_daily_matches()
            
            if not matches:
                print("[WARNING] İşlenecek maç bulunamadı")
                return {
                    'durum': 'basarili',
                    'kupon_guven_skoru': 0,
                    'mac_sayisi': 0,
                    'maclar': [],
                    'oneriler': {
                        'guvenilirlik': 'Düşük',
                        'ideal_mac': 3,
                        'maximum_mac': 4,
                        'minimum_mac': 2
                    },
                    'tarih': datetime.now().strftime('%Y-%m-%d')
                }

            selected_matches = []
            for match in matches:
                print(f"[INFO] Maç tahmin ediliyor: {match['ev_sahibi']} vs {match['deplasman']}")
                prediction = self.predict_match({
                    'ev_sahibi': match['ev_sahibi'],
                    'deplasman': match['deplasman']
                })
                
                if prediction.get('durum') == 'basarili':
                    selected_matches.append({
                        'mac_id': match.get('mac_id'),
                        'ev_sahibi': match['ev_sahibi'],
                        'deplasman': match['deplasman'],
                        'tahminler': prediction['tahminler'],
                        'lig': match.get('lig'),
                        'tarih': match.get('tarih')
                    })
                    print(f"[INFO] Maç başarıyla eklendi")
                else:
                    print(f"[WARNING] Maç tahmin edilemedi: {prediction.get('message', 'Bilinmeyen hata')}")

            print(f"[INFO] Toplam {len(selected_matches)} maç seçildi")
            
            if not selected_matches:
                return {
                    'durum': 'basarili',
                    'kupon_guven_skoru': 0,
                    'mac_sayisi': 0,
                    'maclar': [],
                    'oneriler': {
                        'guvenilirlik': 'Düşük',
                        'ideal_mac': 3,
                        'maximum_mac': 4,
                        'minimum_mac': 2
                    },
                    'tarih': datetime.now().strftime('%Y-%m-%d')
                }

            # En güvenilir maçları seç
            selected_matches.sort(key=lambda x: x['tahminler'].get('ek_istatistikler', {}).get('ml_guven', 0), reverse=True)
            best_matches = selected_matches[:4]  # En güvenilir 4 maçı al

            return {
                'durum': 'basarili',
                'kupon_guven_skoru': sum(m['tahminler'].get('ek_istatistikler', {}).get('ml_guven', 0) for m in best_matches) / len(best_matches) if best_matches else 0,
                'mac_sayisi': len(best_matches),
                'maclar': best_matches,
                'oneriler': {
                    'guvenilirlik': 'Yüksek' if len(best_matches) >= 2 else 'Düşük',
                    'ideal_mac': 3,
                    'maximum_mac': 4,
                    'minimum_mac': 2
                },
                'tarih': datetime.now().strftime('%Y-%m-%d')
            }

        except Exception as e:
            print(f"[ERROR] Kupon oluşturma hatası: {str(e)}")
            print(traceback.format_exc())
            return {
                'durum': 'hata',
                'mesaj': str(e)
            } 